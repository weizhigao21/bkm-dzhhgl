import datetime
import json
import os
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

import requests

from .constants import *
from .utils import build_multipart, decrypt_response, encrypt_sensitive, decrypt_sensitive
from .app_ui import AppUIMixin
from .app_network import AppNetworkMixin
from .notify import NotifyManager
from .settings_dialog import SettingsDialog, DEFAULT_NOTIFY_CONFIG


class App(AppUIMixin, AppNetworkMixin):
    def __init__(self, root):
        self.root = root
        self.root.title(f"宝可梦多账号管家 v{VERSION}")
        self.root.configure(bg=C_BG)
        self.root.minsize(880, 600)

        try:
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, "1.ico")
            else:
                icon_path = os.path.join(_BASE_DIR, "1.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass

        self.saved_users = []
        self._user_cache = {}
        self._active_user_email = None
        self._displayed_email = None
        self._sub_url_full = None
        self._current_plan_id = None
        self._saved_email = None
        self._saved_password = None
        self._log_lines = []
        self._fetching_email = None
        self._relogin_attempted_tokens = set()
        self._last_relogin_attempt_time = {}
        self.log_text = None
        self.info_labels = {}
        self.token_var = tk.StringVar()
        self._data_lock = threading.Lock()
        self._session = requests.Session()
        self._session.trust_env = False

        self._notify_config = dict(DEFAULT_NOTIFY_CONFIG)
        self.notify = NotifyManager(self)

        self.root.geometry("940x680")
        center_window_early(self.root)

        self._setup_styles()

        self.main_container = tk.Frame(self.root, bg=C_BG)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._build_sidebar()
        self._build_right_content()

        self._load_config()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        if self.saved_users:
            first = self.saved_users[0]
            self.token_var.set(first['token'])
            email = first['email']
            self._active_user_email = email
            self._highlight_user(email)
            if email in self._user_cache:
                self._log(f"启动加载缓存  {email}", "info")
                self._display_user_data(self._user_cache[email], first['token'])
            # 启动后自动刷新所有账号数据（并行）
            threading.Thread(target=self._fetch_all_data, daemon=True).start()

        self._apply_notify_config()

    def _log(self, msg, level="info"):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._log_lines.append((ts, msg, level))
        print(f"[{ts}] [{level}] {msg}")
        if hasattr(self, 'log_text') and self.log_text:
            try:
                self.root.after(0, self._append_log, ts, msg, level)
            except Exception:
                pass

    def _append_log(self, ts, msg, level):
        if not self.log_text:
            return
        try:
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, ts + "  ", "time")
            self.log_text.insert(tk.END, msg + "\n", level)
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
        except Exception:
            pass

    def _load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self._log(f"配置文件格式错误: {e}", "error")
            return
        except PermissionError:
            self._log("无法读取配置文件，权限不足", "error")
            return
        except Exception as e:
            self._log(f"加载配置失败: {e}", "error")
            return

        try:
            last_token = data.get('last_token', '')
            if last_token:
                self.token_var.set(last_token)

            self.saved_users = data.get('users', [])

            for user in self.saved_users:
                if 'password' in user and user['password']:
                    user['password'] = decrypt_sensitive(user['password'])
                cached = user.get('cached_data')
                if cached:
                    self._user_cache[user['email']] = cached
                self._add_user_item(
                    user['email'],
                    user.get('remaining_gb', 0),
                    user.get('total_gb', 0),
                    user['token'],
                    activate=False
                )

            if self.saved_users:
                last_user = self.saved_users[0]
                self._saved_email = last_user.get('email', '')
                self._saved_password = last_user.get('password', '')

            self._coupon_history = data.get('coupon_history', [])
            if hasattr(self, '_coupon_history') and self._coupon_history:
                self._update_coupon_history_ui()

            saved_notify = data.get('notify', {})
            if isinstance(saved_notify, dict):
                merged = dict(DEFAULT_NOTIFY_CONFIG)
                merged.update(saved_notify)
                self._notify_config = merged
        except Exception as e:
            self._log(f"解析配置数据失败: {e}", "error")

    def _save_config(self, last_token):
        try:
            with self._data_lock:
                users_to_save = []
                for u in self.saved_users:
                    saved = dict(u)
                    if 'password' in saved and saved['password']:
                        saved['password'] = encrypt_sensitive(saved['password'])
                    users_to_save.append(saved)
            data = {
                "last_token": last_token,
                "users": users_to_save,
                "coupon_history": self._coupon_history,
                "notify": self._notify_config,
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log(f"保存配置失败: {e}", "error")

    def _save_notify_config(self):
        """单独保存通知配置（写入 config.json）。"""
        try:
            self._save_config(self.token_var.get())
        except Exception as e:
            self._log(f"保存通知配置失败: {e}", "error")

    def _apply_notify_config(self):
        """根据配置启停后台通知线程。"""
        if not hasattr(self, 'notify'):
            return
        if self._notify_config.get("enabled", False):
            self.notify.restart()
        else:
            self.notify.stop()

    def _on_open_settings(self):
        SettingsDialog(self)

    def _on_close(self):
        """窗口关闭：停止通知线程后退出。"""
        try:
            if hasattr(self, 'notify'):
                self.notify.stop()
        except Exception:
            pass
        self.root.destroy()

    def _on_user_click(self, email):
        self._active_user_email = email
        for user in self.saved_users:
            if user['email'] == email:
                self.token_var.set(user['token'])
                self._highlight_user(email)
                self._displayed_email = email
                self._refresh_redeem_info()
                if email in self._user_cache:
                    # 已有缓存：点击即刷新，强制走网络
                    self._log(f"刷新数据  {email}", "info")
                    threading.Thread(
                        target=self._fetch_data, args=(user['token'], True), daemon=True).start()
                else:
                    self.sub_url_label.config(text="加载中...")
                    self.sub_url_label.update_idletasks()
                    self._fetching_email = email
                    threading.Thread(
                        target=self._fetch_data, args=(user['token'], False), daemon=True).start()
                break

    def _show_user_context_menu(self, event, email):
        menu = tk.Menu(self.root, tearoff=0, bg=C_CARD, fg=C_TEXT,
                       font=(FONT_FAMILY, 9), borderwidth=0,
                       activebackground=C_ACTIVE_BG, activeforeground=C_DANGER)
        menu.add_command(label=f"删除 {email}", command=lambda: self._delete_user(email))
        menu.post(event.x_root, event.y_root)

    def _delete_user(self, email):
        if not messagebox.askyesno("确认", f"确定删除训练师 {email} 吗？", parent=self.root):
            return
        for widget in self.user_list_inner.winfo_children():
            if hasattr(widget, 'user_email') and widget.user_email == email:
                widget.destroy()
                break
        with self._data_lock:
            self.saved_users = [u for u in self.saved_users if u['email'] != email]
            self._user_cache.pop(email, None)
            self._relogin_attempted_tokens.discard(email)
            self._last_relogin_attempt_time.pop(email, None)
            if email == self._active_user_email:
                self._active_user_email = None
                self._displayed_email = None
                self.result_frame.pack_forget()
                self._refresh_redeem_info()
        count = sum(1 for w in self.user_list_inner.winfo_children() if hasattr(w, 'user_email'))
        self.user_count_label.config(text=f"{count} 位训练师")
        if not self.saved_users:
            self.empty_hint.pack(expand=True, pady=40)
        self._save_config(self.token_var.get())

    def _on_open_login(self):
        LoginDialog(self)

    def _on_login_success(self, token, email, password):
        self._saved_email = email
        self._saved_password = password
        self.token_var.set(token)
        with self._data_lock:
            found = False
            for u in self.saved_users:
                if u['email'] == email:
                    u['password'] = password
                    u['token'] = token
                    found = True
                    break
            if not found:
                self.saved_users.append({
                    'email': email, 'token': token, 'password': password,
                    'remaining_gb': 0, 'total_gb': 0,
                })
            self._relogin_attempted_tokens.clear()
            self._last_relogin_attempt_time.pop(email, None)
        self._save_config(token)
        self._displayed_email = None
        self._log(f"登录成功，自动查询  {email}", "success")
        self.result_frame.pack_forget()
        self.root.config(cursor="watch")
        threading.Thread(target=self._fetch_data, args=(token, True), daemon=True).start()

    def _on_query(self):
        token = self.token_var.get().strip()
        if not token:
            messagebox.showwarning("提示", "请先输入 Token")
            return

        self._fetching_email = None

        cached_email = None
        for u in self.saved_users:
            if u['token'] == token:
                cached_email = u['email']
                break

        if cached_email and cached_email in self._user_cache:
            self._log(f"使用缓存  {cached_email}", "info")
            self._displayed_email = cached_email
            self._highlight_user(cached_email)
            self._refresh_redeem_info()
            self._display_user_data_fast(self._user_cache[cached_email], token)
        else:
            self._log("正在查询...", "info")
            self._displayed_email = None
            self.result_frame.pack_forget()
            self.root.config(cursor="watch")
            threading.Thread(target=self._fetch_data, args=(token, True), daemon=True).start()

    def _on_force_refresh(self):
        if not self.saved_users:
            messagebox.showwarning("提示", "暂无训练师可刷新")
            return

        self._fetching_email = None
        self._log("全局刷新...", "info")
        self.root.config(cursor="watch")
        threading.Thread(target=self._fetch_all_data, daemon=True).start()

    def _display_user_data(self, user, token):
        email = user.get('email', '')
        plan_name = (user.get('plan_name', '') or user.get('name', '')
                     or user.get('plan', {}).get('name', '--'))
        uuid = user.get('uuid', '') or user.get('token', '--')

        expire_at = user.get('expired_at', '') or user.get('expire_at', '')
        if not expire_at:
            expire_at = user.get('plan', {}).get('expired_at', '--')

        # 到期时间格式化：时间戳 → 日期 + 剩余天数，并按剩余天数着色
        expire_display = '--'
        expire_color = C_TEXT
        if expire_at:
            try:
                ts = int(expire_at)
                dt = datetime.datetime.fromtimestamp(ts)
                remain_days = (dt - datetime.datetime.now()).days
                if remain_days >= 0:
                    expire_display = f"{dt.strftime('%Y-%m-%d')}（剩 {remain_days} 天）"
                else:
                    expire_display = f"{dt.strftime('%Y-%m-%d')}（已过期）"
                if remain_days < 0:
                    expire_color = C_DANGER
                elif remain_days < 7:
                    expire_color = C_WARNING
                else:
                    expire_color = C_SUCCESS
            except (ValueError, TypeError, OverflowError, OSError):
                expire_display = str(expire_at)

        device_limit = user.get('device_limit', '--')

        sub_url = user.get('subscribe_url', '') or user.get('sub_url', '')
        plan_id = user.get('plan_id', user.get('id', ''))

        upload = user.get('u', 0) or 0
        download = user.get('d', 0) or 0
        total = user.get('transfer_enable', 0) or 0

        u_gb = round(upload / 1073741824, 2)
        d_gb = round(download / 1073741824, 2)
        used_gb = round(u_gb + d_gb, 2)
        total_gb = round(total / 1073741824, 2)
        remain_gb = round(max(0, total_gb - used_gb), 2)

        self.info_labels['plan_name'].config(text=str(plan_name))
        self.info_labels['email'].config(text=str(email))
        self.info_labels['uuid'].config(text=str(uuid))
        self.info_labels['expire_at'].config(text=expire_display, fg=expire_color)
        self.info_labels['device_limit'].config(text=str(device_limit))

        self.total_label.config(text=f"{total_gb:.2f} GB")
        self.used_label.config(text=f"{used_gb:.2f} GB")
        self.remain_label.config(text=f"{remain_gb:.2f} GB")

        used_pct = round(used_gb / total_gb * 100, 1) if total_gb > 0 else 0
        if used_pct >= 90:
            style = "danger.Horizontal.TProgressbar"
        elif used_pct >= 70:
            style = "warning.Horizontal.TProgressbar"
        else:
            style = "success.Horizontal.TProgressbar"
        self.progress.configure(style=style, value=used_pct, maximum=100)
        self.progress_text.config(text=f"已使用 {used_pct:.1f}%")

        if sub_url:
            self._sub_url_full = sub_url
            self.sub_url_label.config(text=sub_url, fg=C_PRIMARY)
        else:
            self._sub_url_full = None
            self.sub_url_label.config(text="--", fg=C_TEXT_MUTED)

        try:
            self._current_plan_id = int(plan_id) if plan_id else None
        except (ValueError, TypeError):
            self._current_plan_id = None

        self.result_frame.pack(fill=tk.BOTH, expand=True)
        self._refresh_redeem_info()
        return remain_gb, total_gb

    def _display_user_data_fast(self, user, token):
        return self._calc_remain(user)

    def _calc_remain(self, user):
        upload = user.get('u', 0) or 0
        download = user.get('d', 0) or 0
        total = user.get('transfer_enable', 0) or 0
        used_gb = round((upload + download) / 1073741824, 2)
        total_gb = round(total / 1073741824, 2)
        remain_gb = round(max(0, total_gb - used_gb), 2)
        return remain_gb, total_gb

    def _update_ui(self, user, token, password=None):
        email = user.get('email', '')
        if email:
            self._user_cache[email] = user

        should_display = self._displayed_email is None or email == self._displayed_email
        remain_gb, transfer_gb = (self._display_user_data(user, token)
                                  if should_display else self._calc_remain(user))

        if email:
            self._update_user_list(email, remain_gb, transfer_gb, token, password)
            for u in self.saved_users:
                if u['email'] == email:
                    u['cached_data'] = user
                    break

        self._save_config(token)

    def _update_user_list(self, email, remaining_gb, total_gb, token, password=None):
        with self._data_lock:
            found = False
            for u in self.saved_users:
                if u['email'] == email:
                    u['remaining_gb'] = round(remaining_gb, 2)
                    u['total_gb'] = round(total_gb, 2)
                    u['token'] = token
                    if password is not None:
                        u['password'] = password
                    found = True
                    break

            if not found:
                entry = {
                    'email': email,
                    'token': token,
                    'remaining_gb': round(remaining_gb, 2),
                    'total_gb': round(total_gb, 2),
                }
                if password is not None:
                    entry['password'] = password
                self.saved_users.append(entry)

        self._add_user_item(email, round(remaining_gb, 2), round(total_gb, 2), token, activate=False)
        count = sum(1 for w in self.user_list_inner.winfo_children() if hasattr(w, 'user_email'))
        self.user_count_label.config(text=f"{count} 位训练师")

    def _on_use_coupon(self):
        code = self.coupon_var.get().strip()
        if not code:
            messagebox.showwarning("提示", "请输入兑换码")
            return
        if not self._sub_url_full:
            messagebox.showwarning("提示", "请先查询订阅信息")
            return
        if not self._current_plan_id:
            messagebox.showwarning("提示", "未获取到套餐 ID，无法兑换")
            return
        self._add_coupon_to_history(code)
        token = self.token_var.get().strip()
        self.use_coupon_btn.config(text="使用中...", state=tk.DISABLED)
        threading.Thread(target=self._do_redeem, args=(token, code), daemon=True).start()

    def _on_use_coupon_all(self):
        code = self.coupon_var.get().strip()
        if not code:
            messagebox.showwarning("提示", "请输入兑换码")
            return
        if not self.saved_users:
            messagebox.showwarning("提示", "暂无训练师可兑换")
            return
        count = len(self.saved_users)
        if not messagebox.askyesno("确认", f"确定给全部 {count} 个账户兑换吗？"):
            return
        self._add_coupon_to_history(code)
        self.use_coupon_all_btn.config(text="兑换中...", state=tk.DISABLED)
        self.use_coupon_btn.config(state=tk.DISABLED)
        self.root.config(cursor="watch")
        threading.Thread(target=self._do_redeem_all, args=(code,), daemon=True).start()

    def _on_redeem_result(self, trade_no, error, email=None, code=None):
        self.use_coupon_btn.config(text="使用", state=tk.NORMAL)
        if error:
            self._log(f"兑换失败: {error}", "error")
            messagebox.showerror("兑换失败", error, parent=self.root)
        else:
            self._log(f"兑换成功  trade_no={trade_no}", "success")
            if email and code:
                self._record_redeem(email, code, trade_no)
            messagebox.showinfo("兑换成功", f"兑换完成\n订单号: {trade_no}", parent=self.root)

    def _on_redeem_all_result(self, results, code):
        self.use_coupon_all_btn.config(text="全部兑换", state=tk.NORMAL)
        self.use_coupon_btn.config(state=tk.NORMAL)
        self.root.config(cursor="")
        for r in results:
            if r.get('success'):
                self._record_redeem(r.get('email', ''), code, r.get('trade_no'))
        RedeemResultDialog(self, results, code)

    def _record_redeem(self, email, code, trade_no):
        """记录一次成功的兑换历史（时间 + 兑换码 + 订单号），并持久化。"""
        if not email or not code:
            return
        entry = {
            'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'code': code,
            'trade_no': trade_no or '--',
        }
        with self._data_lock:
            for u in self.saved_users:
                if u['email'] == email:
                    history = u.setdefault('redeem_history', [])
                    history.append(entry)
                    if len(history) > 50:
                        del history[:-50]
                    break
        self._save_config(self.token_var.get())
        self._refresh_redeem_info()

    def _on_open_log(self):
        LogDialog(self)

    def _show_error(self, msg):
        self._log(msg, "error")
        self.result_frame.pack_forget()
        self._fetching_email = None
        messagebox.showerror("错误", msg)

    def _notify_token_expired(self):
        self.sub_url_label.config(text="Token 已过期，请重新登录")
        self._fetching_email = None

    def _on_copy_url(self):
        if self._sub_url_full:
            self.root.clipboard_clear()
            self.root.clipboard_append(self._sub_url_full)
            self._log("已复制订阅地址到剪贴板", "success")
            self._show_copy_feedback()

    def _show_copy_feedback(self):
        btn = getattr(self, '_copy_btn', None)
        if not btn:
            return
        btn.config(text="已复制!", style="Success.TButton")
        self.root.after(1500, lambda: btn.config(text="复制链接", style="Primary.TButton"))

    def _add_coupon_to_history(self, code):
        if code not in self._coupon_history:
            self._coupon_history.insert(0, code)
            if len(self._coupon_history) > 20:
                self._coupon_history = self._coupon_history[:20]
            self._update_coupon_history_ui()

    def _update_coupon_history_ui(self):
        if hasattr(self, 'coupon_entry') and self.coupon_entry:
            self.coupon_entry['values'] = self._coupon_history


def center_window_early(root):
    root.update_idletasks()
    w, h = 940, 680
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")


from .widgets import LoginDialog, LogDialog, RedeemResultDialog