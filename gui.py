import base64
import json
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import requests

_A = base64.b64decode(
    "bnN6e2dBV3JrWGx4MDhKNkVxOlY0W2RlTzFEUVRDd20yb0IzdHk5alNZSV03Uk01YkhpVWFmLGN9S3VQR3BOaFpMdkY="
).decode()
_B = base64.b64decode(
    "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXpBQkNERUZHSElKS0xNTk9QUVJTVFVWV1hZWjAxMjM0NTY3ODksW117fTo="
).decode()

if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(_BASE_DIR, "config.json")


def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)

API_URL = "https://api123.136470.xyz/api/v1/user/getSubscribe"
API_COUPON_CHECK = "https://api123.136470.xyz/api/v1/user/coupon/check"
API_ORDER_SAVE = "https://api123.136470.xyz/api/v1/user/order/save"
API_ORDER_CHECKOUT = "https://api123.136470.xyz/api/v1/user/order/checkout"
API_ORDER_CHECK = "https://api123.136470.xyz/api/v1/user/order/check"
API_ORDER_FETCH = "https://api123.136470.xyz/api/v1/user/order/fetch"
API_LOGIN = "https://api123.136470.xyz/api/v1/passport/auth/login"

DEFAULT_HEADERS = {
    "theme-ua": "mala-pro",
    "origin": "https://love.52pokemon66.cc",
    "referer": "https://love.52pokemon66.cc/",
    "accept": "application/json, text/plain, */*",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0",
}

# ── Color palette ──────────────────────────────
C_BG = "#f0f2f5"
C_CARD = "#ffffff"
C_PRIMARY = "#4f6ef7"
C_PRIMARY_HOVER = "#3b5de7"
C_SUCCESS = "#22c55e"
C_SUCCESS_HOVER = "#16a34a"
C_WARNING = "#f59e0b"
C_DANGER = "#ef4444"
C_DANGER_HOVER = "#dc2626"
C_TEXT = "#1e293b"
C_TEXT_SECONDARY = "#64748b"
C_TEXT_MUTED = "#94a3b8"
C_BORDER = "#e2e8f0"
C_INPUT_BG = "#f8fafc"
C_HOVER = "#f1f5f9"
C_ACTIVE_BG = "#eff6ff"
C_ACTIVE_ACCENT = "#4f6ef7"

FONT_FAMILY = "Microsoft YaHei UI"


def decrypt(encrypted_str):
    return ''.join(_B[_A.find(ch)] if ch in _A else ch for ch in encrypted_str)


def decrypt_response(base64_text):
    raw = base64.b64decode(base64_text).decode('utf-8', errors='ignore')
    plain = raw
    for _ in range(10):
        plain = decrypt(plain)
    return json.loads(plain)


def decrypt_response_raw(base64_text):
    raw = base64.b64decode(base64_text).decode('utf-8', errors='ignore')
    plain = raw
    for _ in range(10):
        plain = decrypt(plain)
    return plain.strip()


def try_decrypt_body(body_text):
    try:
        return decrypt_response(body_text)
    except Exception:
        pass
    try:
        return decrypt_response_raw(body_text)
    except Exception:
        pass
    return body_text[:300]


def build_multipart(fields):
    boundary = "----WebKitFormBoundaryFZrKS3m9Wn0LquJY"
    lines = []
    for name, value in fields.items():
        lines.append(f"--{boundary}")
        lines.append(f'Content-Disposition: form-data; name="{name}"')
        lines.append("")
        lines.append(value)
    lines.append(f"--{boundary}--")
    body = "\r\n".join(lines)
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


def center_window(dialog, parent, w, h):
    parent.update_idletasks()
    px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
    py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
    dialog.geometry(f"{w}x{h}+{px}+{py}")


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("宝可梦多账号管家")
        self.root.iconbitmap(resource_path("1.ico"))
        self.root.geometry("940x760")
        self.root.resizable(True, True)
        self.root.minsize(940, 700)
        self.root.configure(bg=C_BG)

        self.saved_users = []
        self._user_cache = {}
        self._active_user_email = None
        self._displayed_email = None
        self._sub_url_full = None
        self._current_plan_id = None
        self._saved_email = None
        self._saved_password = None
        self._log_lines = []

        self._setup_styles()

        self.main_container = tk.Frame(self.root, bg=C_BG)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self._build_sidebar()
        self._build_right_content()

        self._load_config()

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure(".", font=(FONT_FAMILY, 10), background=C_BG)

        self.style.configure("TLabel", background=C_BG, foreground=C_TEXT)
        self.style.configure("TFrame", background=C_BG)
        self.style.configure("TLabelframe", background=C_BG)
        self.style.configure("TLabelframe.Label", background=C_BG, foreground=C_TEXT,
                             font=(FONT_FAMILY, 11, "bold"))

        self.style.configure("TButton",
                             font=(FONT_FAMILY, 9, "bold"),
                             borderwidth=0,
                             relief=tk.FLAT,
                             padding=(16, 8))

        self.style.configure("Primary.TButton",
                             background=C_PRIMARY,
                             foreground="white",
                             borderwidth=0)
        self.style.map("Primary.TButton",
                       background=[("active", C_PRIMARY_HOVER), ("disabled", "#93b4f5")],
                       foreground=[("disabled", "#e2e8f0")])

        self.style.configure("Success.TButton",
                             background=C_SUCCESS,
                             foreground="white",
                             borderwidth=0)
        self.style.map("Success.TButton",
                       background=[("active", C_SUCCESS_HOVER), ("disabled", "#86efac")])

        self.style.configure("Danger.TButton",
                             background=C_DANGER,
                             foreground="white",
                             borderwidth=0)
        self.style.map("Danger.TButton",
                       background=[("active", C_DANGER_HOVER), ("disabled", "#fca5a5")])

        self.style.configure("Outline.TButton",
                             background=C_CARD,
                             foreground=C_PRIMARY,
                             borderwidth=1,
                             bordercolor=C_BORDER)
        self.style.map("Outline.TButton",
                       background=[("active", C_ACTIVE_BG)],
                       bordercolor=[("active", C_PRIMARY)])

        self.style.configure("Secondary.TButton",
                             background=C_HOVER,
                             foreground=C_TEXT,
                             borderwidth=0)
        self.style.map("Secondary.TButton",
                       background=[("active", C_BORDER)])

        self.style.configure("Card.TFrame", background=C_CARD)
        self.style.configure("Card.TLabel", background=C_CARD, foreground=C_TEXT)

        self.style.configure("Heading.TLabel",
                             font=(FONT_FAMILY, 12, "bold"),
                             foreground=C_TEXT,
                             background=C_CARD)
        self.style.configure("SubHeading.TLabel",
                             font=(FONT_FAMILY, 9),
                             foreground=C_TEXT_SECONDARY,
                             background=C_CARD)
        self.style.configure("Value.TLabel",
                             font=(FONT_FAMILY, 10, "bold"),
                             foreground=C_TEXT,
                             background=C_CARD)
        self.style.configure("Muted.TLabel",
                             font=(FONT_FAMILY, 9),
                             foreground=C_TEXT_MUTED,
                             background=C_CARD)
        self.style.configure("Accent.TLabel",
                             font=(FONT_FAMILY, 9, "bold"),
                             foreground=C_PRIMARY,
                             background=C_CARD)

        self.style.configure("Sidebar.TFrame", background=C_CARD)
        self.style.configure("Sidebar.TLabel", background=C_CARD)
        self.style.configure("SidebarHeading.TLabel",
                             font=(FONT_FAMILY, 13, "bold"),
                             foreground=C_TEXT,
                             background=C_CARD)

        self.style.configure("TEntry",
                             fieldbackground=C_INPUT_BG,
                             foreground=C_TEXT,
                             borderwidth=1,
                             relief=tk.FLAT,
                             padding=(10, 6))
        self.style.map("TEntry",
                       bordercolor=[("focus", C_PRIMARY)],
                       fieldbackground=[("focus", C_CARD)])

        self.style.configure("TProgressbar",
                             troughcolor=C_BORDER,
                             background=C_PRIMARY,
                             thickness=8,
                             borderwidth=0)
        self.style.configure("success.Horizontal.TProgressbar",
                             troughcolor=C_BORDER,
                             background=C_SUCCESS,
                             thickness=8)
        self.style.configure("warning.Horizontal.TProgressbar",
                             troughcolor=C_BORDER,
                             background=C_WARNING,
                             thickness=8)
        self.style.configure("danger.Horizontal.TProgressbar",
                             troughcolor=C_BORDER,
                             background=C_DANGER,
                             thickness=8)

        self.style.configure("TSeparator", background=C_BORDER)

    def _build_card(self, parent, padx=20, pady=16):
        card = tk.Frame(parent, bg=C_CARD, highlightthickness=1,
                        highlightbackground=C_BORDER, highlightcolor=C_BORDER)
        inner = tk.Frame(card, bg=C_CARD)
        inner.pack(fill=tk.BOTH, expand=True, padx=padx, pady=pady)
        return card, inner

    def _build_sidebar(self):
        self.sidebar = tk.Frame(self.main_container, width=240, bg=C_CARD,
                                highlightthickness=0)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        sidebar_inner = tk.Frame(self.sidebar, bg=C_CARD)
        sidebar_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=12)

        header_frame = tk.Frame(sidebar_inner, bg=C_CARD)
        header_frame.pack(fill=tk.X, pady=(4, 4))

        tk.Label(header_frame, text="训练师列表", bg=C_CARD, fg=C_TEXT,
                 font=(FONT_FAMILY, 14, "bold")).pack(anchor=tk.W)

        self.user_count_label = tk.Label(header_frame, text="0 位训练师", bg=C_CARD,
                                         fg=C_TEXT_MUTED, font=(FONT_FAMILY, 9))
        self.user_count_label.pack(anchor=tk.W, pady=(2, 0))

        tk.Frame(sidebar_inner, bg=C_BORDER, height=1).pack(fill=tk.X, pady=(8, 6))

        canvas_container = tk.Frame(sidebar_inner, bg=C_CARD)
        canvas_container.pack(fill=tk.BOTH, expand=True)

        self.user_canvas = tk.Canvas(canvas_container, bg=C_CARD, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL,
                                  command=self.user_canvas.yview)
        self.user_list_inner = tk.Frame(self.user_canvas, bg=C_CARD)

        self.user_list_inner.bind("<Configure>",
                                  lambda e: self.user_canvas.configure(
                                      scrollregion=self.user_canvas.bbox("all")))

        self.canvas_window_id = self.user_canvas.create_window(
            (0, 0), window=self.user_list_inner, anchor="nw")
        self.user_canvas.bind("<Configure>", self._on_canvas_configure)
        self.user_canvas.configure(yscrollcommand=scrollbar.set)

        self.user_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.empty_hint = tk.Label(self.user_list_inner, text="暂无训练师\n查询后自动添加",
                                   bg=C_CARD, fg=C_TEXT_MUTED,
                                   font=(FONT_FAMILY, 10), justify=tk.CENTER)
        self.empty_hint.pack(expand=True, pady=40)

    def _on_canvas_configure(self, event):
        self.user_canvas.itemconfig(self.canvas_window_id, width=event.width)

    def _build_right_content(self):
        self.right_frame = tk.Frame(self.main_container, bg=C_BG)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(20, 0))

        self._build_token_section()
        self._build_info_section()

    def _build_token_section(self):
        card, inner = self._build_card(self.right_frame, padx=18, pady=14)
        card.pack(fill=tk.X, pady=(0, 14))

        header_row = tk.Frame(inner, bg=C_CARD)
        header_row.pack(fill=tk.X, pady=(0, 10))

        tk.Label(header_row, text="宝可梦多账号管家", bg=C_CARD, fg=C_TEXT,
                 font=(FONT_FAMILY, 13, "bold")).pack(side=tk.LEFT)

        self.main_login_btn = ttk.Button(header_row, text="登录",
                                         style="Danger.TButton", width=10,
                                         command=self._on_open_login)
        self.main_login_btn.pack(side=tk.RIGHT)

        log_btn = ttk.Button(header_row, text="日志", style="Secondary.TButton",
                             width=6, command=self._on_open_log)
        log_btn.pack(side=tk.RIGHT, padx=(0, 6))

        input_row = tk.Frame(inner, bg=C_CARD)
        input_row.pack(fill=tk.X)

        self.token_var = tk.StringVar()
        token_entry = tk.Entry(input_row, textvariable=self.token_var,
                               font=(FONT_FAMILY, 10), bg=C_INPUT_BG, fg=C_TEXT,
                               relief=tk.FLAT, bd=1, highlightthickness=1,
                               highlightcolor=C_PRIMARY, highlightbackground=C_BORDER,
                               insertbackground=C_TEXT)
        token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 10))

        btn_frame = tk.Frame(input_row, bg=C_CARD)
        btn_frame.pack(side=tk.RIGHT)

        query_btn = ttk.Button(btn_frame, text="查询", style="Primary.TButton",
                               width=8, command=self._on_query)
        query_btn.pack(side=tk.LEFT, padx=(0, 6))

        refresh_btn = ttk.Button(btn_frame, text="刷新", style="Success.TButton",
                                 width=8, command=self._on_force_refresh)
        refresh_btn.pack(side=tk.LEFT)

    def _build_info_section(self):
        self.result_frame = tk.Frame(self.right_frame, bg=C_BG)

        overview_card, overview_inner = self._build_card(self.result_frame, padx=18, pady=14)
        overview_card.pack(fill=tk.X, pady=(0, 14))

        tk.Label(overview_inner, text="训练师信息", bg=C_CARD, fg=C_TEXT,
                 font=(FONT_FAMILY, 12, "bold")).pack(anchor=tk.W, pady=(0, 10))

        cols = tk.Frame(overview_inner, bg=C_CARD)
        cols.pack(fill=tk.X)

        left_col = tk.Frame(cols, bg=C_CARD)
        left_col.pack(side=tk.LEFT, fill=tk.Y)

        labels_info = [
            ("套餐名称", "plan_name"),
            ("邮箱", "email"),
            ("UUID", "uuid"),
            ("到期时间", "expire_at"),
            ("设备限制", "device_limit"),
        ]
        self.info_labels = {}
        for text, key in labels_info:
            row_frame = tk.Frame(left_col, bg=C_CARD)
            row_frame.pack(fill=tk.X, pady=2)
            tk.Label(row_frame, text=text, bg=C_CARD, fg=C_TEXT_SECONDARY,
                     font=(FONT_FAMILY, 9), anchor=tk.W, width=8).pack(side=tk.LEFT)
            val_label = tk.Label(row_frame, text="--", bg=C_CARD, fg=C_TEXT,
                                 font=(FONT_FAMILY, 9, "bold"), anchor=tk.W)
            val_label.pack(side=tk.LEFT, padx=(6, 0))
            self.info_labels[key] = val_label

        tk.Frame(cols, bg=C_BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=16)

        right_col = tk.Frame(cols, bg=C_CARD)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.total_label = tk.Label(right_col, text="--", bg=C_CARD, fg=C_TEXT,
                                    font=(FONT_FAMILY, 22, "bold"), anchor=tk.W)
        self.total_label.pack(anchor=tk.W)

        tk.Label(right_col, text="总流量", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=(FONT_FAMILY, 9)).pack(anchor=tk.W, pady=(0, 10))

        stats_row = tk.Frame(right_col, bg=C_CARD)
        stats_row.pack(fill=tk.X, pady=(0, 8))

        used_box = tk.Frame(stats_row, bg=C_CARD)
        used_box.pack(side=tk.LEFT, padx=(0, 16))
        self.used_label = tk.Label(used_box, text="--", bg=C_CARD, fg=C_DANGER,
                                   font=(FONT_FAMILY, 13, "bold"), anchor=tk.W)
        self.used_label.pack(anchor=tk.W)
        tk.Label(used_box, text="已用", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=(FONT_FAMILY, 9)).pack(anchor=tk.W)

        remain_box = tk.Frame(stats_row, bg=C_CARD)
        remain_box.pack(side=tk.LEFT)
        self.remain_label = tk.Label(remain_box, text="--", bg=C_CARD, fg=C_SUCCESS,
                                     font=(FONT_FAMILY, 13, "bold"), anchor=tk.W)
        self.remain_label.pack(anchor=tk.W)
        tk.Label(remain_box, text="剩余", bg=C_CARD, fg=C_TEXT_MUTED,
                 font=(FONT_FAMILY, 9)).pack(anchor=tk.W)

        progress_frame = tk.Frame(right_col, bg=C_CARD)
        progress_frame.pack(fill=tk.X)

        self.progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL,
                                        mode="determinate",
                                        style="success.Horizontal.TProgressbar")
        self.progress.pack(fill=tk.X, pady=(0, 4))

        self.progress_text = tk.Label(progress_frame, text="", bg=C_CARD, fg=C_TEXT_MUTED,
                                      font=(FONT_FAMILY, 9), anchor=tk.W)
        self.progress_text.pack(anchor=tk.W)

        sub_card, sub_inner = self._build_card(self.result_frame, padx=18, pady=14)
        sub_card.pack(fill=tk.X, pady=(0, 14))

        tk.Label(sub_inner, text="订阅地址", bg=C_CARD, fg=C_TEXT,
                 font=(FONT_FAMILY, 12, "bold")).pack(anchor=tk.W, pady=(0, 10))

        sub_row = tk.Frame(sub_inner, bg=C_CARD)
        sub_row.pack(fill=tk.X)

        self.sub_url_label = tk.Label(sub_row, text="--", bg=C_INPUT_BG, fg=C_PRIMARY,
                                      font=(FONT_FAMILY, 9), anchor=tk.W, padx=10, pady=6,
                                      relief=tk.FLAT, bd=1, highlightthickness=1,
                                      highlightbackground=C_BORDER, wraplength=500,
                                      justify=tk.LEFT)
        self.sub_url_label.pack(fill=tk.X, pady=(0, 8))

        copy_btn = ttk.Button(sub_row, text="复制链接", style="Primary.TButton",
                              command=self._on_copy_url)
        copy_btn.pack(anchor=tk.E)

        coupon_card, coupon_inner = self._build_card(self.result_frame, padx=18, pady=14)
        coupon_card.pack(fill=tk.X)

        tk.Label(coupon_inner, text="兑换码", bg=C_CARD, fg=C_TEXT,
                 font=(FONT_FAMILY, 12, "bold")).pack(anchor=tk.W, pady=(0, 10))

        coupon_input_frame = tk.Frame(coupon_inner, bg=C_CARD)
        coupon_input_frame.pack(fill=tk.X, pady=(0, 10))

        self.coupon_var = tk.StringVar()
        coupon_entry = tk.Entry(coupon_input_frame, textvariable=self.coupon_var,
                                font=(FONT_FAMILY, 10), bg=C_INPUT_BG, fg=C_TEXT,
                                relief=tk.FLAT, bd=1, highlightthickness=1,
                                highlightcolor=C_PRIMARY, highlightbackground=C_BORDER,
                                insertbackground=C_TEXT)
        coupon_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 10))

        self.use_coupon_btn = ttk.Button(coupon_input_frame, text="使用",
                                         style="Danger.TButton", width=8,
                                         command=self._on_use_coupon)
        self.use_coupon_btn.pack(side=tk.RIGHT)

    def _log(self, msg, level="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_lines.append((ts, msg, level))
        self.root.after(0, lambda: self._append_log(ts, msg, level))
        if len(self._log_lines) > 1000:
            self._log_lines = self._log_lines[-500:]

    def _append_log(self, ts, msg, level):
        lt = getattr(self, 'log_text', None)
        if lt and lt.winfo_exists():
            lt.configure(state=tk.NORMAL)
            lt.insert(tk.END, ts + "  ", "time")
            lt.insert(tk.END, msg + "\n", level)
            lt.see(tk.END)
            lt.configure(state=tk.DISABLED)

    def _load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    last_token = data.get('last_token') or data.get('token', '')
                    if last_token:
                        self.token_var.set(last_token)
                    self.saved_users = data.get('users', [])
                    self._saved_email = data.get('email', '') or None
                    self._saved_password = data.get('password', '') or None
                    for user in self.saved_users:
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
        except Exception:
            self.saved_users = []

        if self.saved_users:
            first = self.saved_users[0]
            self.root.after(100, lambda e=first['email']: self._on_user_click(e))

    def _save_config(self, token=None):
        try:
            data = {
                "last_token": token if token else self.token_var.get(),
                "users": self.saved_users,
                "email": self._saved_email or '',
                "password": self._saved_password or '',
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _add_user_item(self, email, remaining_gb, total_gb, token, activate=False):
        self.empty_hint.pack_forget()

        existing = None
        for widget in self.user_list_inner.winfo_children():
            if hasattr(widget, 'user_email') and widget.user_email == email:
                existing = widget
                break

        is_active = activate or email == self._active_user_email

        if existing is not None:
            existing.user_token = token
            existing._update_state(is_active, remaining_gb)
            return

        frame = tk.Frame(self.user_list_inner, bg=C_CARD, cursor="hand2",
                         highlightthickness=1, highlightbackground=C_BORDER,
                         highlightcolor=C_BORDER)
        frame.pack(fill=tk.X, pady=2)
        frame.user_email = email
        frame.user_token = token
        frame._is_active = is_active
        frame._remaining_gb = remaining_gb

        inner = tk.Frame(frame, bg=C_CARD)
        inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        initial = email[0].upper() if email else "?"
        avatar = tk.Label(inner, text=initial, bg=C_BORDER, fg=C_TEXT_SECONDARY,
                          font=(FONT_FAMILY, 11, "bold"), width=3, height=2,
                          anchor=tk.CENTER)
        avatar.pack(side=tk.LEFT)

        text_frame = tk.Frame(inner, bg=C_CARD)
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

        display_email = email if len(email) <= 24 else email[:21] + "..."
        email_label = tk.Label(text_frame, text=display_email, bg=C_CARD, fg=C_TEXT,
                               font=(FONT_FAMILY, 10, "bold"), anchor=tk.W)
        email_label.pack(fill=tk.X)

        remain_color = C_SUCCESS if remaining_gb > 50 else (
            C_WARNING if remaining_gb > 10 else C_DANGER)
        remain_label = tk.Label(text_frame, text=f"剩余 {remaining_gb:.1f} GB",
                                bg=C_CARD, fg=remain_color,
                                font=(FONT_FAMILY, 9), anchor=tk.W)
        remain_label.pack(fill=tk.X)

        if is_active:
            frame.configure(highlightbackground=C_PRIMARY,
                            highlightcolor=C_PRIMARY, bg=C_ACTIVE_BG)
            inner.configure(bg=C_ACTIVE_BG)
            text_frame.configure(bg=C_ACTIVE_BG)
            email_label.configure(bg=C_ACTIVE_BG)
            remain_label.configure(bg=C_ACTIVE_BG)
            avatar.configure(bg=C_PRIMARY, fg="white")

        def _update_state(active, rem_gb):
            if active:
                frame.configure(highlightbackground=C_PRIMARY,
                                highlightcolor=C_PRIMARY, bg=C_ACTIVE_BG)
                inner.configure(bg=C_ACTIVE_BG)
                text_frame.configure(bg=C_ACTIVE_BG)
                email_label.configure(bg=C_ACTIVE_BG)
                remain_label.configure(bg=C_ACTIVE_BG)
                avatar.configure(bg=C_PRIMARY, fg="white")
            else:
                frame.configure(highlightbackground=C_BORDER,
                                highlightcolor=C_BORDER, bg=C_CARD)
                inner.configure(bg=C_CARD)
                text_frame.configure(bg=C_CARD)
                email_label.configure(bg=C_CARD)
                remain_label.configure(bg=C_CARD)
                avatar.configure(bg=C_BORDER, fg=C_TEXT_SECONDARY)
            r_color = C_SUCCESS if rem_gb > 50 else (
                C_WARNING if rem_gb > 10 else C_DANGER)
            remain_label.configure(text=f"剩余 {rem_gb:.1f} GB", fg=r_color)
            frame._remaining_gb = rem_gb

        frame._update_state = _update_state

        def on_enter(e):
            if not frame._is_active:
                frame.configure(bg=C_HOVER)
                inner.configure(bg=C_HOVER)
                text_frame.configure(bg=C_HOVER)
                email_label.configure(bg=C_HOVER)
                remain_label.configure(bg=C_HOVER)

        def on_leave(e):
            if not frame._is_active:
                frame.configure(bg=C_CARD)
                inner.configure(bg=C_CARD)
                text_frame.configure(bg=C_CARD)
                email_label.configure(bg=C_CARD)
                remain_label.configure(bg=C_CARD)

        def on_click(e):
            self._on_user_click(email)

        for w in (frame, inner, text_frame, email_label, remain_label, avatar):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)

        count = sum(1 for w in self.user_list_inner.winfo_children() if hasattr(w, 'user_email'))
        self.user_count_label.config(text=f"{count} 位训练师")

    def _highlight_user(self, email):
        self._active_user_email = email
        for widget in self.user_list_inner.winfo_children():
            if hasattr(widget, 'user_email'):
                is_active = widget.user_email == email
                widget._is_active = is_active
                widget._update_state(is_active, widget._remaining_gb)

    def _on_user_click(self, email):
        for user in self.saved_users:
            if user['email'] == email:
                self.token_var.set(user['token'])
                self._highlight_user(email)
                self._displayed_email = email
                self._log(f"切换用户  {email}", "info")
                if email in self._user_cache:
                    self._display_user_data_fast(self._user_cache[email], user['token'])
                else:
                    self.sub_url_label.config(text="加载中...")
                    self.sub_url_label.update_idletasks()
                    threading.Thread(
                        target=self._fetch_data, args=(user['token'], False), daemon=True).start()
                break

    def _on_open_login(self):
        LoginDialog(self)

    def _on_login_success(self, token, email, password):
        self._saved_email = email
        self._saved_password = password
        self.token_var.set(token)
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

        cached_email = None
        for u in self.saved_users:
            if u['token'] == token:
                cached_email = u['email']
                break

        if cached_email and cached_email in self._user_cache:
            self._log(f"使用缓存  {cached_email}", "info")
            self._displayed_email = cached_email
            self._highlight_user(cached_email)
            self._display_user_data_fast(self._user_cache[cached_email], token)
        else:
            self._log("正在查询...", "info")
            self._displayed_email = None
            self.result_frame.pack_forget()
            self.root.config(cursor="watch")
            threading.Thread(target=self._fetch_data, args=(token, True), daemon=True).start()

    def _on_force_refresh(self):
        token = self.token_var.get().strip()
        if not token:
            messagebox.showwarning("提示", "请先输入 Token")
            return

        self._log("强制刷新...", "info")
        self._displayed_email = None
        self.result_frame.pack_forget()
        self.root.config(cursor="watch")
        threading.Thread(target=self._fetch_data, args=(token, True), daemon=True).start()

    def _fetch_data(self, token, show_loading=True):
        try:
            session = requests.Session()
            session.trust_env = False
            headers = {**DEFAULT_HEADERS, "Authorization": token}
            headers = {k: v.encode('ascii', errors='ignore').decode()
                       for k, v in headers.items()}

            resp = session.get(API_URL, headers=headers, timeout=15)

            if resp.status_code != 200:
                if show_loading:
                    self._log(f"查询订阅失败  HTTP {resp.status_code}", "error")
                    self.root.after(0, lambda: self._show_error(
                        f"请求失败，状态码: {resp.status_code}"))
                return

            result = decrypt_response(resp.text)
            user = result['data']
            email = user.get('email', '')
            self._log(f"查询成功  {email}" if email else "查询成功", "success")
            self.root.after(0, lambda u=user, t=token: self._update_ui(u, t))
        except json.JSONDecodeError:
            if show_loading:
                self._log("解密失败，Token 可能已过期", "error")
                self.root.after(0, lambda: self._show_error("解密失败，Token 可能已过期"))
        except requests.RequestException as e:
            if show_loading:
                self._log(f"网络错误: {e}", "error")
                self.root.after(0, lambda: self._show_error(f"网络错误: {e}"))
        except Exception as e:
            if show_loading:
                self._log(f"未知错误: {e}", "error")
                self.root.after(0, lambda: self._show_error(f"未知错误: {e}"))
        finally:
            if show_loading:
                self.root.after(0, lambda: self.root.config(cursor=""))

    def _display_user_data(self, user, token):
        email = user.get('email', '')
        if email:
            self._displayed_email = email

        if not self.result_frame.winfo_ismapped():
            self.result_frame.pack(fill=tk.X, pady=(0, 10))

        plan_name = user.get('plan', {}).get('name', '--')
        self.info_labels["plan_name"].config(text=plan_name)
        self._current_plan_id = user.get('plan', {}).get('id')
        self.info_labels["email"].config(text=user.get('email', '--'))
        self.info_labels["uuid"].config(text=user.get('uuid', '--'))

        expire_ts = user.get('expired_at')
        expire_str = datetime.fromtimestamp(expire_ts).strftime(
            '%Y-%m-%d %H:%M:%S') if expire_ts else '未知'
        self.info_labels["expire_at"].config(text=expire_str)

        device_limit = user.get('device_limit', '--')
        self.info_labels["device_limit"].config(
            text=f"{device_limit} 台" if isinstance(device_limit, (int, float))
            else str(device_limit))

        transfer_b = user.get('transfer_enable', 0)
        used_b = user.get('u', 0) + user.get('d', 0)
        remain_b = transfer_b - used_b

        transfer_gb = transfer_b / 1073741824
        used_gb = used_b / 1073741824
        remain_gb = remain_b / 1073741824
        pct = (used_gb / transfer_gb * 100) if transfer_gb > 0 else 0

        self.total_label.config(text=f"{transfer_gb:.2f} GB")
        self.used_label.config(text=f"{used_gb:.2f} GB")
        self.remain_label.config(text=f"{remain_gb:.2f} GB")

        self.progress['value'] = pct
        if pct < 60:
            self.progress.configure(style="success.Horizontal.TProgressbar")
        elif pct < 85:
            self.progress.configure(style="warning.Horizontal.TProgressbar")
        else:
            self.progress.configure(style="danger.Horizontal.TProgressbar")

        self.progress_text.config(text=f"已使用 {pct:.1f}%  |  剩余 {100 - pct:.1f}%")

        sub_url = user.get('subscribe_url', '--')
        self._sub_url_full = sub_url
        self.sub_url_label.config(text=sub_url)

        return remain_gb, transfer_gb

    def _display_user_data_fast(self, user, token):
        result = self._display_user_data(user, token)
        self.sub_url_label.update_idletasks()
        return result

    def _calc_remain(self, user):
        transfer_b = user.get('transfer_enable', 0)
        used_b = user.get('u', 0) + user.get('d', 0)
        remain_b = transfer_b - used_b
        return remain_b / 1073741824, transfer_b / 1073741824

    def _update_ui(self, user, token):
        email = user.get('email', '')
        if email:
            self._user_cache[email] = user

        should_display = self._displayed_email is None or email == self._displayed_email
        remain_gb, transfer_gb = (self._display_user_data_fast(user, token)
                                  if should_display else self._calc_remain(user))

        if email:
            self._update_user_list(email, remain_gb, transfer_gb, token)
            for u in self.saved_users:
                if u['email'] == email:
                    u['cached_data'] = user
                    break

        self._save_config(token)

    def _update_user_list(self, email, remaining_gb, total_gb, token):
        found = False
        for u in self.saved_users:
            if u['email'] == email:
                u['remaining_gb'] = round(remaining_gb, 2)
                u['total_gb'] = round(total_gb, 2)
                u['token'] = token
                found = True
                break

        if not found:
            self.saved_users.append({
                'email': email,
                'token': token,
                'remaining_gb': round(remaining_gb, 2),
                'total_gb': round(total_gb, 2),
            })

        self._add_user_item(email, remaining_gb, total_gb, token, activate=False)

    def _on_use_coupon(self):
        token = self.token_var.get().strip()
        if not token:
            messagebox.showwarning("提示", "请先输入 Token")
            return
        code = self.coupon_var.get().strip()
        if not code:
            messagebox.showwarning("提示", "请输入兑换码")
            return
        plan_id = self._current_plan_id
        if not plan_id:
            messagebox.showwarning("提示", "请先查询用户信息，获取当前套餐")
            return

        self.use_coupon_btn.configure(text="使用中...", state=tk.DISABLED)
        self._log(f"使用兑换码  code={code}  plan={plan_id}", "info")
        threading.Thread(target=self._do_redeem, args=(token, code), daemon=True).start()

    def _do_redeem(self, token, code):
        try:
            session = requests.Session()
            session.trust_env = False
            headers = {**DEFAULT_HEADERS, "Authorization": token}
            headers = {k: v.encode('ascii', errors='ignore').decode()
                       for k, v in headers.items()}

            save_data = {
                "plan_id": str(self._current_plan_id),
                "period": "month_price",
                "coupon_code": code,
            }
            self._log(f"正在下单  plan={self._current_plan_id}", "info")
            resp = session.post(API_ORDER_SAVE, data=save_data, headers=headers, timeout=15)
            if resp.status_code != 200:
                err_body = try_decrypt_body(resp.text)
                self._log(f"下单失败  HTTP {resp.status_code}  {err_body}", "error")
                self.root.after(0, lambda: self._on_redeem_result(
                    None, f"下单失败，状态码: {resp.status_code}"))
                return
            result = decrypt_response(resp.text)
            trade_no = result.get('data', '')
            if not trade_no:
                trade_no = decrypt_response_raw(resp.text)
            self._log(f"下单成功  trade_no={trade_no}", "success")

            self._log("正在支付...", "info")
            resp = session.post(API_ORDER_CHECKOUT,
                                data={"trade_no": trade_no, "method": "1"},
                                headers=headers, timeout=15)
            if resp.status_code != 200:
                err_body = try_decrypt_body(resp.text)
                self._log(f"支付失败  HTTP {resp.status_code}  {err_body}", "error")
                self.root.after(0, lambda: self._on_redeem_result(
                    None, f"支付失败，状态码: {resp.status_code}"))
                return
            self._log("支付成功", "success")

            self._log("正在校验...", "info")
            resp = session.get(f"{API_ORDER_CHECK}?trade_no={trade_no}",
                               headers=headers, timeout=15)
            if resp.status_code != 200:
                self._log(f"校验失败  HTTP {resp.status_code}", "error")
                self.root.after(0, lambda: self._on_redeem_result(
                    None, f"校验失败，状态码: {resp.status_code}"))
                return
            self._log("兑换完成", "success")
            self.root.after(0, lambda: self._on_redeem_result(trade_no, None))
        except json.JSONDecodeError:
            self._log("兑换时解密失败", "error")
            self.root.after(0, lambda: self._on_redeem_result(
                None, "解密失败，Token 可能已过期"))
        except requests.RequestException as e:
            self._log(f"兑换网络错误: {e}", "error")
            self.root.after(0, lambda: self._on_redeem_result(None, f"网络错误: {e}"))
        except Exception as e:
            self._log(f"兑换未知错误: {e}", "error")
            self.root.after(0, lambda: self._on_redeem_result(None, f"未知错误: {e}"))

    def _on_redeem_result(self, trade_no, error):
        self.use_coupon_btn.configure(text="使用", state=tk.NORMAL)
        if error:
            messagebox.showerror("错误", error)
            return
        self._log(f"兑换成功  trade_no={trade_no}", "success")
        self.coupon_var.set("")
        messagebox.showinfo("完成", "兑换码使用成功！\n请刷新查看最新流量")

    def _on_open_log(self):
        LogDialog(self)

    def _show_error(self, msg):
        self._log(msg, "error")
        self.result_frame.pack_forget()
        messagebox.showerror("错误", msg)

    def _on_copy_url(self):
        url = self._sub_url_full or self.sub_url_label.cget("text")
        if not url or url == "--":
            messagebox.showwarning("提示", "暂无订阅地址可复制")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        self._log("订阅地址已复制到剪贴板", "success")
        messagebox.showinfo("成功", "订阅地址已复制到剪贴板")


class LoginDialog:
    def __init__(self, app):
        self.app = app
        self.dialog = tk.Toplevel(app.root)
        self.dialog.title("宝可梦 · 登录")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=C_CARD)
        self.dialog.transient(app.root)
        self.dialog.grab_set()

        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)

        center_window(self.dialog, app.root, 400, 300)

        tk.Label(self.dialog, text="宝可梦 · 登录", bg=C_CARD, fg=C_TEXT,
                 font=(FONT_FAMILY, 16, "bold")).pack(pady=(24, 20))

        form_frame = tk.Frame(self.dialog, bg=C_CARD)
        form_frame.pack(fill=tk.X, padx=36)

        tk.Label(form_frame, text="邮箱", bg=C_CARD, fg=C_TEXT_SECONDARY,
                 font=(FONT_FAMILY, 10)).pack(anchor=tk.W, pady=(0, 4))
        self.email_var = tk.StringVar()
        self.email_entry = tk.Entry(form_frame, textvariable=self.email_var,
                                    font=(FONT_FAMILY, 10), bg=C_INPUT_BG,
                                    fg=C_TEXT, relief=tk.FLAT, bd=1,
                                    highlightthickness=1,
                                    highlightcolor=C_PRIMARY,
                                    highlightbackground=C_BORDER,
                                    insertbackground=C_TEXT)
        self.email_entry.pack(fill=tk.X, ipady=5, pady=(0, 12))

        tk.Label(form_frame, text="密码", bg=C_CARD, fg=C_TEXT_SECONDARY,
                 font=(FONT_FAMILY, 10)).pack(anchor=tk.W, pady=(0, 4))
        self.password_var = tk.StringVar()
        self.pass_entry = tk.Entry(form_frame, textvariable=self.password_var,
                                   show="*", font=(FONT_FAMILY, 10),
                                   bg=C_INPUT_BG, fg=C_TEXT, relief=tk.FLAT,
                                   bd=1, highlightthickness=1,
                                   highlightcolor=C_PRIMARY,
                                   highlightbackground=C_BORDER,
                                   insertbackground=C_TEXT)
        self.pass_entry.pack(fill=tk.X, ipady=5, pady=(0, 16))

        self.login_btn = ttk.Button(form_frame, text="登录",
                                    style="Danger.TButton", width=20,
                                    command=self._on_login)
        self.login_btn.pack()

        if app._saved_email:
            self.email_var.set(app._saved_email)
        if app._saved_password:
            self.password_var.set(app._saved_password)
            self.pass_entry.focus_set()
        else:
            self.email_entry.focus_set()

        self.dialog.bind("<Return>", lambda e: self._on_login())
        self.dialog.wait_window()

    def _on_close(self):
        self.dialog.destroy()

    def _on_login(self):
        email = self.email_var.get().strip()
        password = self.password_var.get().strip()
        if not email:
            messagebox.showwarning("提示", "请输入邮箱", parent=self.dialog)
            return
        if not password:
            messagebox.showwarning("提示", "请输入密码", parent=self.dialog)
            return

        self.login_btn.config(text="登录中...", state=tk.DISABLED)
        self.email_entry.config(state=tk.DISABLED)
        self.pass_entry.config(state=tk.DISABLED)
        threading.Thread(target=self._do_login, args=(email, password), daemon=True).start()

    def _do_login(self, email, password):
        try:
            session = requests.Session()
            session.trust_env = False
            headers = {k: v.encode('ascii', errors='ignore').decode()
                       for k, v in DEFAULT_HEADERS.items()}
            body, ct = build_multipart({"email": email, "password": password})
            headers["content-type"] = ct
            resp = session.post(API_LOGIN, data=body, headers=headers, timeout=15)
            if resp.status_code != 200:
                self.app._log(f"登录失败  HTTP {resp.status_code}", "error")
                self.dialog.after(0, lambda: self._on_result(
                    None, f"登录失败，状态码: {resp.status_code}"))
                return
            result = decrypt_response(resp.text)
            data = result.get('data', result)
            token = data.get('auth_data')
            if not token:
                for key in ['token', 'access_token', 'auth', 'session']:
                    val = data.get(key)
                    if val:
                        token = val
                        break
            if not token:
                raw = json.dumps(result, ensure_ascii=False)
                self.app._log("登录响应中未找到 token 字段", "error")
                self.dialog.after(0, lambda r=raw: self._on_result(
                    None, f"未找到 token 字段\n响应:\n{r}"))
                return
            self.app._log(f"登录成功  {email}", "success")
            self.dialog.after(0, lambda t=token: self._on_result(t, None))
        except Exception as e:
            self.app._log(f"登录错误: {e}", "error")
            self.dialog.after(0, lambda: self._on_result(None, f"登录错误: {e}"))

    def _on_result(self, token, error):
        if error:
            self.login_btn.config(text="登录", state=tk.NORMAL)
            self.email_entry.config(state=tk.NORMAL)
            self.pass_entry.config(state=tk.NORMAL)
            messagebox.showerror("登录失败", error, parent=self.dialog)
            return
        self.dialog.destroy()
        self.app._on_login_success(
            token, self.email_var.get().strip(), self.password_var.get().strip())


class LogDialog:
    def __init__(self, app):
        self.app = app
        self.dialog = tk.Toplevel(app.root)
        self.dialog.title("运行日志")
        self.dialog.geometry("700x480")
        self.dialog.resizable(True, True)
        self.dialog.minsize(500, 300)
        self.dialog.configure(bg=C_CARD)
        self.dialog.transient(app.root)
        self.dialog.grab_set()

        center_window(self.dialog, app.root, 700, 480)

        title_frame = tk.Frame(self.dialog, bg=C_CARD)
        title_frame.pack(fill=tk.X, padx=16, pady=(14, 8))

        tk.Label(title_frame, text="运行日志 · 宝可梦多账号管家", bg=C_CARD, fg=C_TEXT,
                 font=(FONT_FAMILY, 13, "bold")).pack(side=tk.LEFT)

        clear_btn = ttk.Button(title_frame, text="清空", style="Secondary.TButton",
                               width=6, command=self._on_clear)
        clear_btn.pack(side=tk.RIGHT)

        text_frame = tk.Frame(self.dialog, bg=C_CARD)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 14))

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(text_frame, bg=C_INPUT_BG, fg=C_TEXT,
                                font=("Consolas", 9), relief=tk.FLAT, bd=1,
                                highlightthickness=1, highlightbackground=C_BORDER,
                                highlightcolor=C_BORDER, wrap=tk.WORD,
                                state=tk.NORMAL, padx=8, pady=6,
                                yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.configure(command=self.log_text.yview)

        self.log_text.tag_configure("error", foreground=C_DANGER)
        self.log_text.tag_configure("warn", foreground=C_WARNING)
        self.log_text.tag_configure("success", foreground=C_SUCCESS)
        self.log_text.tag_configure("info", foreground=C_TEXT_SECONDARY)
        self.log_text.tag_configure("time", foreground=C_TEXT_MUTED,
                                    font=("Consolas", 8))

        self.app.log_text = self.log_text

        for ts, msg, level in app._log_lines:
            self.log_text.insert(tk.END, ts + "  ", "time")
            self.log_text.insert(tk.END, msg + "\n", level)

        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
        self.dialog.wait_window()

    def _on_close(self):
        self.app.log_text = None
        self.dialog.destroy()

    def _on_clear(self):
        self.app._log_lines.clear()
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()