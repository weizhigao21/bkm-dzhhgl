"""设置弹窗。

不使用 ttk.Notebook，改用垂直卡片式布局，所有配置在同一页面内，
分组间用分割线隔开。支持滚动。

沿用项目现有 UI 风格（白底卡片、主色按钮）。
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from .constants import (
    C_BG, C_CARD, C_PRIMARY, C_DANGER, C_TEXT, C_TEXT_SECONDARY, C_TEXT_MUTED,
    C_BORDER, C_INPUT_BG, C_HOVER, FONT_FAMILY, VERSION, _BASE_DIR,
)
from .utils import center_window, encrypt_sensitive, decrypt_sensitive
from . import autostart


DEFAULT_NOTIFY_CONFIG = {
    "enabled": False,
    "smtp_server": "smtp.qq.com",
    "smtp_port": 465,
    "smtp_user": "",
    "smtp_password_encrypted": "",
    "from_addr": "",
    "to_addr": "",
    "threshold_gb": 5.0,
    "check_interval_minutes": 60,
    "daily_report": False,
    "daily_report_hour": 8,
    "last_threshold_notified": {},
    "last_daily_report_date": "",
}


def _make_entry(parent, var, width=0, show=None):
    """创建标准化的输入框。"""
    kwargs = dict(
        textvariable=var, font=(FONT_FAMILY, 10), bg=C_INPUT_BG,
        fg=C_TEXT, relief=tk.FLAT, bd=1, highlightthickness=1,
        highlightcolor=C_PRIMARY, highlightbackground=C_BORDER,
        insertbackground=C_TEXT,
    )
    if show:
        kwargs["show"] = show
    if width:
        kwargs["width"] = width
    return tk.Entry(parent, **kwargs)


def _make_label(parent, text, fg=C_TEXT_SECONDARY, size=9, bold=False):
    """创建标准化标签。"""
    weight = "bold" if bold else "normal"
    return tk.Label(parent, text=text, bg=C_CARD, fg=fg,
                    font=(FONT_FAMILY, size, weight), anchor=tk.W)


def _add_row(parent, label_text, var, placeholder="", width=0, show=None, suffix=None):
    """添加一行：标签 + 输入框 + 可选后缀文字。"""
    row = tk.Frame(parent, bg=C_CARD)
    row.pack(fill=tk.X, pady=3)
    _make_label(row, label_text).pack(side=tk.LEFT)
    entry = _make_entry(row, var, width=width, show=show)
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
    if suffix:
        _make_label(row, suffix, fg=C_TEXT_MUTED, size=8).pack(side=tk.LEFT, padx=(4, 0))
    return entry


class SettingsDialog:
    def __init__(self, app):
        self.app = app
        cfg = dict(DEFAULT_NOTIFY_CONFIG)
        cfg.update(app._notify_config or {})

        self.dialog = tk.Toplevel(app.root)
        self.dialog.withdraw()  # 先隐藏，构建完再显示（避免闪烁）
        self.dialog.title("设置")
        self.dialog.geometry("500x580")
        self.dialog.minsize(460, 480)
        self.dialog.configure(bg=C_BG)
        self.dialog.transient(app.root)
        self.dialog.grab_set()
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)

        # 设置图标
        try:
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, "1.ico")
            else:
                icon_path = os.path.join(_BASE_DIR, "1.ico")
            if os.path.exists(icon_path):
                self.dialog.iconbitmap(icon_path)
        except Exception:
            pass

        # 标题
        tk.Label(self.dialog, text="设置", bg=C_BG, fg=C_TEXT,
                 font=(FONT_FAMILY, 16, "bold")).pack(pady=(16, 2))
        tk.Label(self.dialog, text=f"宝可梦多账号管家 v{VERSION}", bg=C_BG, fg=C_TEXT_MUTED,
                 font=(FONT_FAMILY, 9)).pack(pady=(0, 8))

        # 卡片内容区域（可滚动）
        card = tk.Frame(self.dialog, bg=C_CARD, highlightthickness=1,
                        highlightbackground=C_BORDER, highlightcolor=C_BORDER)
        card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 8))

        canvas = tk.Canvas(card, bg=C_CARD, highlightthickness=0, bd=0, height=420)
        scrollbar = ttk.Scrollbar(card, orient=tk.VERTICAL, command=canvas.yview)
        inner = tk.Frame(canvas, bg=C_CARD)

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw", width=456)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._build_notify_section(inner, cfg)
        self._build_general_section(inner)

        # 底部按钮
        btn_frame = tk.Frame(self.dialog, bg=C_BG)
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 14))

        ttk.Button(btn_frame, text="取消", style="Secondary.TButton",
                   width=10, command=self._on_close).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(btn_frame, text="保存", style="Primary.TButton",
                   width=10, command=self._on_save).pack(side=tk.RIGHT)

        # 鼠标滚轮滚动
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # UI 构建完毕，移到屏幕中心再显示
        self.dialog.update_idletasks()
        center_window(self.dialog, app.root, 500, 580)
        self.dialog.deiconify()

        self.dialog.wait_window()

    # ---------- 邮箱通知区域 ----------

    def _build_notify_section(self, parent, cfg):
        """构建邮箱通知的全部内容。"""
        self.notify_enabled_var = tk.BooleanVar(value=bool(cfg.get("enabled", False)))
        cb = tk.Checkbutton(parent, text="启用邮件通知（定时检查流量并发送提醒）",
                            variable=self.notify_enabled_var, bg=C_CARD, fg=C_TEXT,
                            font=(FONT_FAMILY, 10, "bold"),
                            activebackground=C_CARD, selectcolor=C_CARD,
                            bd=0, highlightthickness=0, anchor=tk.W)
        cb.pack(anchor=tk.W, pady=(16, 12), padx=20)

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20)

        _make_label(parent, "SMTP 服务器配置", fg=C_TEXT, size=11, bold=True).pack(
            anchor=tk.W, pady=(14, 8), padx=20)

        fields = tk.Frame(parent, bg=C_CARD)
        fields.pack(fill=tk.X, padx=20)

        self.smtp_server_var = tk.StringVar(value=cfg.get("smtp_server", "smtp.qq.com"))
        _add_row(fields, "服务器地址", self.smtp_server_var)

        self.smtp_port_var = tk.StringVar(value=str(cfg.get("smtp_port", 465)))
        _add_row(fields, "端口", self.smtp_port_var, suffix="SSL:465 / STARTTLS:587")

        self.smtp_user_var = tk.StringVar(value=cfg.get("smtp_user", ""))
        _add_row(fields, "发件邮箱", self.smtp_user_var)

        enc = cfg.get("smtp_password_encrypted", "")
        self.smtp_pwd_var = tk.StringVar(value=decrypt_sensitive(enc) if enc else "")
        _add_row(fields, "授权码", self.smtp_pwd_var, show="*")

        self.to_addr_var = tk.StringVar(value=cfg.get("to_addr", ""))
        _add_row(fields, "收件邮箱", self.to_addr_var)

        ttk.Button(fields, text="发送测试邮件", style="Outline.TButton",
                   command=self._on_test).pack(anchor=tk.W, pady=(10, 4))

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=(10, 8))

        _make_label(parent, "通知规则", fg=C_TEXT, size=11, bold=True).pack(
            anchor=tk.W, pady=(4, 8), padx=20)

        rules = tk.Frame(parent, bg=C_CARD)
        rules.pack(fill=tk.X, padx=20)

        self.threshold_var = tk.StringVar(value=str(cfg.get("threshold_gb", 5.0)))
        _add_row(rules, "流量阈值（GB）", self.threshold_var, suffix="剩余低于此值时通知")

        self.interval_var = tk.StringVar(value=str(cfg.get("check_interval_minutes", 60)))
        _add_row(rules, "检查间隔（分钟）", self.interval_var)

        # 每日报告行
        report_row = tk.Frame(rules, bg=C_CARD)
        report_row.pack(fill=tk.X, pady=3)
        self.daily_report_var = tk.BooleanVar(value=bool(cfg.get("daily_report", False)))
        tk.Checkbutton(report_row, text="每日发送流量报告   时间：",
                       variable=self.daily_report_var, bg=C_CARD, fg=C_TEXT,
                       font=(FONT_FAMILY, 10), activebackground=C_CARD,
                       selectcolor=C_CARD, bd=0, highlightthickness=0).pack(side=tk.LEFT)
        self.daily_hour_var = tk.StringVar(value=str(cfg.get("daily_report_hour", 8)))
        _make_entry(report_row, self.daily_hour_var, width=4).pack(side=tk.LEFT)
        _make_label(report_row, "  时", fg=C_TEXT_SECONDARY).pack(side=tk.LEFT)

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=(14, 0))

    def _build_general_section(self, parent):
        """通用设置。"""
        _make_label(parent, "启动设置", fg=C_TEXT, size=11, bold=True).pack(
            anchor=tk.W, pady=(14, 8), padx=20)

        gen = tk.Frame(parent, bg=C_CARD)
        gen.pack(fill=tk.X, padx=20, pady=(0, 16))

        self.autostart_var = tk.BooleanVar(value=autostart.is_enabled())
        tk.Checkbutton(gen, text="开机自启动（通过 Windows 注册表实现）",
                       variable=self.autostart_var, bg=C_CARD, fg=C_TEXT,
                       font=(FONT_FAMILY, 10, "bold"),
                       activebackground=C_CARD, selectcolor=C_CARD,
                       bd=0, highlightthickness=0, anchor=tk.W).pack(anchor=tk.W)

    # ---------- 测试 ----------

    def _on_test(self):
        self._apply_to_config()
        if not self.app._notify_config.get("enabled", False):
            messagebox.showwarning("提示", "请先勾选「启用邮件通知」", parent=self.dialog)
            return
        if not self.app._notify_config.get("smtp_user"):
            messagebox.showwarning("提示", "请填写发件邮箱", parent=self.dialog)
            return
        if not self.app._notify_config.get("to_addr"):
            messagebox.showwarning("提示", "请填写收件邮箱", parent=self.dialog)
            return

        messagebox.showinfo("提示", "正在发送测试邮件，请稍候...", parent=self.dialog)
        threading.Thread(target=self._do_test, daemon=True).start()

    def _do_test(self):
        ok, err = self.app.notify.send_test_email()
        if ok:
            self.dialog.after(0, lambda: messagebox.showinfo("成功", "测试邮件已发送，请到收件箱查看", parent=self.dialog))
            self.app._log("测试邮件发送成功", "success")
        else:
            self.dialog.after(0, lambda e=err: messagebox.showerror("发送失败", e, parent=self.dialog))
            self.app._log(f"测试邮件发送失败: {err}", "error")

    # ---------- 保存 ----------

    def _apply_to_config(self):
        try:
            port = int(self.smtp_port_var.get().strip() or 465)
        except ValueError:
            port = 465
        try:
            threshold = float(self.threshold_var.get().strip() or 5.0)
        except ValueError:
            threshold = 5.0
        try:
            interval = int(self.interval_var.get().strip() or 60)
        except ValueError:
            interval = 60
        try:
            daily_hour = int(self.daily_hour_var.get().strip() or 8)
        except ValueError:
            daily_hour = 8

        cfg = self.app._notify_config
        cfg["enabled"] = self.notify_enabled_var.get()
        cfg["smtp_server"] = self.smtp_server_var.get().strip()
        cfg["smtp_port"] = port
        cfg["smtp_user"] = self.smtp_user_var.get().strip()
        pwd = self.smtp_pwd_var.get()
        cfg["smtp_password_encrypted"] = encrypt_sensitive(pwd) if pwd else ""
        cfg["from_addr"] = self.smtp_user_var.get().strip()
        cfg["to_addr"] = self.to_addr_var.get().strip()
        cfg["threshold_gb"] = threshold
        cfg["check_interval_minutes"] = max(5, interval)
        cfg["daily_report"] = self.daily_report_var.get()
        cfg["daily_report_hour"] = daily_hour

    def _on_save(self):
        self._apply_to_config()
        self.app._save_notify_config()
        self.app._apply_notify_config()

        want_autostart = self.autostart_var.get()
        current = autostart.is_enabled()
        if want_autostart and not current:
            if autostart.enable():
                self.app._log("已启用开机自启动", "success")
            else:
                messagebox.showerror("失败", "启用开机自启动失败", parent=self.dialog)
                return
        elif not want_autostart and current:
            if autostart.disable():
                self.app._log("已关闭开机自启动", "info")
            else:
                messagebox.showerror("失败", "关闭开机自启动失败", parent=self.dialog)
                return

        messagebox.showinfo("成功", "设置已保存", parent=self.dialog)
        self.dialog.destroy()

    def _on_close(self):
        self.dialog.destroy()
