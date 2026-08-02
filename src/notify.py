"""邮件通知模块。

提供 SMTP 发送邮件 + 后台线程定时检查所有账号流量功能：
- 阈值通知：账号剩余流量低于阈值时发邮件，恢复后清除标记避免重复
- 每日报告：每天到点发送一封汇总邮件
- 测试发送：设置弹窗中可手动测试

授权码使用 utils.encrypt_sensitive 加密存储（机器绑定）。
"""

import datetime
import smtplib
import threading
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .utils import encrypt_sensitive, decrypt_sensitive


class NotifyManager:
    def __init__(self, app):
        self.app = app
        self._stop_event = threading.Event()
        self._thread = None
        self._lock = threading.Lock()

    @property
    def config(self):
        return getattr(self.app, "_notify_config", {}) or {}

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        """启动后台检查线程（幂等）。"""
        if not self.config.get("enabled", False):
            return
        if self.is_running():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="notify-checker")
        self._thread.start()
        self.app._log("邮件通知后台检查已启动", "info")

    def stop(self):
        """停止后台线程。"""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None

    def restart(self):
        """配置变更后重启线程。"""
        self.stop()
        self.start()

    # ---------- 邮件发送 ----------

    def _build_smtp(self):
        """根据配置建立 SMTP 连接并登录，返回 (smtp, error)。"""
        cfg = self.config
        server = cfg.get("smtp_server", "").strip()
        port = int(cfg.get("smtp_port", 465) or 465)
        user = cfg.get("smtp_user", "").strip()
        enc_pwd = cfg.get("smtp_password_encrypted", "")
        pwd = decrypt_sensitive(enc_pwd) if enc_pwd else ""

        if not server or not user or not pwd:
            return None, "SMTP 服务器/账号/授权码未配置完整"

        try:
            if port == 465:
                smtp = smtplib.SMTP_SSL(server, port, timeout=15)
            else:
                smtp = smtplib.SMTP(server, port, timeout=15)
                smtp.ehlo()
                try:
                    smtp.starttls()
                    smtp.ehlo()
                except Exception:
                    pass
            smtp.login(user, pwd)
            return smtp, None
        except Exception as e:
            return None, f"SMTP 连接失败: {e}"

    def send_email(self, subject, body_html):
        """同步发送一封邮件，返回 (success, error)。"""
        cfg = self.config
        from_addr = (cfg.get("from_addr", "") or cfg.get("smtp_user", "")).strip()
        to_addr = (cfg.get("to_addr", "") or "").strip()
        if not from_addr or not to_addr:
            return False, "发件人/收件人邮箱未配置"

        smtp, err = self._build_smtp()
        if err:
            return False, err

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_addr
            msg["To"] = to_addr
            msg.attach(MIMEText(body_html, "html", "utf-8"))
            smtp.sendmail(from_addr, [to_addr], msg.as_string())
            return True, None
        except Exception as e:
            return False, f"发送失败: {e}"
        finally:
            try:
                smtp.quit()
            except Exception:
                pass

    def send_test_email(self):
        """发送测试邮件。"""
        subject = "【宝可梦多账号管家】测试邮件"
        body = "<h3>测试邮件</h3><p>这是来自「宝可梦多账号管家」的测试邮件，如果你收到了说明 SMTP 配置正确。</p>"
        return self.send_email(subject, body)

    # ---------- 后台检查 ----------

    @staticmethod
    def _calc_remain_from_user(u):
        """从 saved_users 条目计算剩余流量。
        优先使用 cached_data（原始 API 字节数据），
        用 remaining_gb 作为降级方案。
        返回 (remain_gb, total_gb)。"""
        cached = u.get("cached_data")
        if cached:
            upload = cached.get("u", 0) or 0
            download = cached.get("d", 0) or 0
            total_bytes = cached.get("transfer_enable", 0) or 0
            total_gb = round(total_bytes / 1073741824, 2)
            remain_gb = round(max(0, total_bytes - upload - download) / 1073741824, 2)
            return remain_gb, total_gb
        remain = u.get("remaining_gb", 0) or 0
        total = u.get("total_gb", 0) or 0
        return float(remain), float(total)

    def _run(self):
        # 启动后先等 10 秒，避免与启动加载冲突
        for _ in range(10):
            if self._stop_event.is_set():
                return
            time.sleep(1)

        while not self._stop_event.is_set():
            try:
                if self.config.get("enabled", False):
                    self._check_once()
            except Exception as e:
                self.app._log(f"通知检查异常: {e}", "error")

            wait = max(5, int(self.config.get("check_interval_minutes", 60) or 60)) * 60
            for _ in range(wait):
                if self._stop_event.is_set():
                    return
                time.sleep(1)

    def _check_once(self):
        cfg = self.config
        now = datetime.datetime.now()

        # 1. 流量阈值检查
        threshold = float(cfg.get("threshold_gb", 5.0) or 5.0)
        notified_map = dict(cfg.get("last_threshold_notified", {}) or {})

        low_accounts = []
        with self.app._data_lock:
            users_snapshot = list(self.app.saved_users)

        changed = False
        for u in users_snapshot:
            email = u.get("email", "")
            remain, _total = self._calc_remain_from_user(u)
            if remain < threshold:
                if not notified_map.get(email, False):
                    low_accounts.append((email, remain))
                    notified_map[email] = True
                    changed = True
            else:
                if notified_map.get(email, False):
                    notified_map[email] = False
                    changed = True

        if low_accounts:
            self._send_low_traffic_alert(low_accounts, threshold)

        if changed:
            with self._lock:
                cfg["last_threshold_notified"] = notified_map
            self.app._save_notify_config()

        # 2. 每日报告
        if cfg.get("daily_report", False):
            report_hour = int(cfg.get("daily_report_hour", 8) or 8)
            today = now.strftime("%Y-%m-%d")
            last_date = cfg.get("last_daily_report_date", "")
            if now.hour >= report_hour and last_date != today:
                ok = self._send_daily_report()
                if ok:
                    with self._lock:
                        cfg["last_daily_report_date"] = today
                    self.app._save_notify_config()

    def _send_low_traffic_alert(self, low_accounts, threshold):
        rows = ""
        for email, remain in low_accounts:
            rows += f"<tr><td style='padding:6px 12px;border:1px solid #e2e8f0;'>{email}</td>" \
                    f"<td style='padding:6px 12px;border:1px solid #e2e8f0;color:#ef4444;font-weight:bold;'>" \
                    f"{remain:.2f} GB</td></tr>"
        body = f"""
        <div style='font-family:Microsoft YaHei UI,sans-serif;max-width:600px;margin:0 auto;'>
            <h3 style='color:#ef4444;'>⚠️ 流量不足提醒</h3>
            <p>以下账号剩余流量已低于阈值 <b>{threshold:.1f} GB</b>，请及时关注：</p>
            <table style='border-collapse:collapse;width:100%;margin:12px 0;'>
                <tr style='background:#f8fafc;'>
                    <th style='padding:6px 12px;border:1px solid #e2e8f0;text-align:left;'>账号</th>
                    <th style='padding:6px 12px;border:1px solid #e2e8f0;text-align:left;'>剩余流量</th>
                </tr>
                {rows}
            </table>
            <p style='color:#64748b;font-size:12px;'>本邮件由「宝可梦多账号管家」自动发送</p>
        </div>
        """
        ok, err = self.send_email("【流量提醒】账号流量不足", body)
        if ok:
            self.app._log(f"已发送流量不足提醒邮件，共 {len(low_accounts)} 个账号", "success")
        else:
            self.app._log(f"流量提醒邮件发送失败: {err}", "error")

    def _send_daily_report(self):
        with self.app._data_lock:
            users_snapshot = list(self.app.saved_users)

        if not users_snapshot:
            return False

        total_used = 0.0
        total_remain = 0.0
        total_all = 0.0
        rows = ""
        for u in users_snapshot:
            email = u.get("email", "")
            remain, total = self._calc_remain_from_user(u)
            used = max(0, total - remain)
            total_used += used
            total_remain += remain
            total_all += total
            pct = (used / total * 100) if total > 0 else 0
            color = "#22c55e" if pct < 70 else ("#f59e0b" if pct < 90 else "#ef4444")
            rows += (
                f"<tr>"
                f"<td style='padding:6px 12px;border:1px solid #e2e8f0;'>{email}</td>"
                f"<td style='padding:6px 12px;border:1px solid #e2e8f0;'>{total:.2f} GB</td>"
                f"<td style='padding:6px 12px;border:1px solid #e2e8f0;color:{color};'>{used:.2f} GB ({pct:.1f}%)</td>"
                f"<td style='padding:6px 12px;border:1px solid #e2e8f0;color:#22c55e;font-weight:bold;'>{remain:.2f} GB</td>"
                f"</tr>"
            )

        today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        body = f"""
        <div style='font-family:Microsoft YaHei UI,sans-serif;max-width:700px;margin:0 auto;'>
            <h3 style='color:#4f6ef7;'>📊 宝可梦多账号管家 · 每日报告</h3>
            <p style='color:#64748b;'>报告时间：{today}</p>
            <table style='border-collapse:collapse;width:100%;margin:12px 0;'>
                <tr style='background:#f8fafc;'>
                    <th style='padding:6px 12px;border:1px solid #e2e8f0;text-align:left;'>账号</th>
                    <th style='padding:6px 12px;border:1px solid #e2e8f0;text-align:left;'>总流量</th>
                    <th style='padding:6px 12px;border:1px solid #e2e8f0;text-align:left;'>已用</th>
                    <th style='padding:6px 12px;border:1px solid #e2e8f0;text-align:left;'>剩余</th>
                </tr>
                {rows}
                <tr style='background:#eff6ff;font-weight:bold;'>
                    <td style='padding:6px 12px;border:1px solid #e2e8f0;'>合计（{len(users_snapshot)} 个账号）</td>
                    <td style='padding:6px 12px;border:1px solid #e2e8f0;'>{total_all:.2f} GB</td>
                    <td style='padding:6px 12px;border:1px solid #e2e8f0;'>{total_used:.2f} GB</td>
                    <td style='padding:6px 12px;border:1px solid #e2e8f0;color:#22c55e;'>{total_remain:.2f} GB</td>
                </tr>
            </table>
            <p style='color:#64748b;font-size:12px;'>本邮件由「宝可梦多账号管家」自动发送</p>
        </div>
        """
        ok, err = self.send_email("【每日报告】宝可梦多账号流量汇总", body)
        if ok:
            self.app._log("已发送每日流量报告邮件", "success")
            return True
        else:
            self.app._log(f"每日报告邮件发送失败: {err}", "error")
            return False

    def trigger_check_now(self):
        """立即触发一次检查（在独立线程中执行，避免阻塞 UI）。"""
        if not self.config.get("enabled", False):
            return
        threading.Thread(target=self._check_once, daemon=True).start()
