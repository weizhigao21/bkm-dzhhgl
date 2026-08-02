import tkinter as tk
from tkinter import ttk

from .constants import *
from .user_list_item import UserListItem


class AppUIMixin:
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
        header_row.pack(fill=tk.X)

        tk.Label(header_row, text=f"宝可梦多账号管家 v{VERSION}", bg=C_CARD, fg=C_TEXT,
                 font=(FONT_FAMILY, 13, "bold")).pack(side=tk.LEFT)

        log_btn = ttk.Button(header_row, text="日志", style="Secondary.TButton",
                             width=6, command=self._on_open_log)
        log_btn.pack(side=tk.RIGHT, padx=(0, 6))

        settings_btn = ttk.Button(header_row, text="设置", style="Secondary.TButton",
                                  width=6, command=self._on_open_settings)
        settings_btn.pack(side=tk.RIGHT, padx=(0, 6))

        self.main_login_btn = ttk.Button(header_row, text="登录",
                                         style="Danger.TButton", width=10,
                                         command=self._on_open_login)
        self.main_login_btn.pack(side=tk.RIGHT)

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
            ("最近兑换", "last_redeem"),
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
                                      highlightbackground=C_BORDER, wraplength=800,
                                      justify=tk.LEFT)
        self.sub_url_label.pack(fill=tk.X, pady=(0, 8))

        copy_btn = ttk.Button(sub_row, text="复制链接", style="Primary.TButton",
                              command=self._on_copy_url)
        copy_btn.pack(anchor=tk.E)
        self._copy_btn = copy_btn

        coupon_card, coupon_inner = self._build_card(self.result_frame, padx=18, pady=14)
        coupon_card.pack(fill=tk.X)

        tk.Label(coupon_inner, text="兑换码", bg=C_CARD, fg=C_TEXT,
                 font=(FONT_FAMILY, 12, "bold")).pack(anchor=tk.W, pady=(0, 10))

        coupon_input_frame = tk.Frame(coupon_inner, bg=C_CARD)
        coupon_input_frame.pack(fill=tk.X, pady=(0, 10))

        self.coupon_var = tk.StringVar()
        self._coupon_history = []
        self.coupon_entry = ttk.Combobox(coupon_input_frame, textvariable=self.coupon_var,
                                         font=(FONT_FAMILY, 10), width=30)
        self.coupon_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.use_coupon_btn = ttk.Button(coupon_input_frame, text="使用",
                                         style="Danger.TButton", width=8,
                                         command=self._on_use_coupon)
        self.use_coupon_btn.pack(side=tk.RIGHT, padx=(6, 0))

        self.use_coupon_all_btn = ttk.Button(coupon_input_frame, text="全部兑换",
                                             style="Primary.TButton", width=10,
                                             command=self._on_use_coupon_all)
        self.use_coupon_all_btn.pack(side=tk.RIGHT)

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
            existing.update_state(is_active, remaining_gb)
            return

        UserListItem(
            self.user_list_inner,
            email=email,
            remaining_gb=remaining_gb,
            total_gb=total_gb,
            token=token,
            is_active=is_active,
            on_click=self._on_user_click,
            on_right_click=self._show_user_context_menu,
            update_count_callback=self._update_user_count,
        )

    def _update_user_count(self):
        count = sum(1 for w in self.user_list_inner.winfo_children()
                    if hasattr(w, 'user_email'))
        self.user_count_label.config(text=f"{count} 位训练师")

    def _highlight_user(self, email):
        self._active_user_email = email
        for widget in self.user_list_inner.winfo_children():
            if hasattr(widget, 'user_email'):
                is_active = widget.user_email == email
                widget.update_state(is_active, widget._remaining_gb)

    def _refresh_redeem_info(self):
        """刷新信息卡片中的最近兑换信息（时间 + 兑换码）。"""
        if not hasattr(self, 'info_labels'):
            return
        history = []
        email = getattr(self, '_active_user_email', None)
        if email:
            with self._data_lock:
                for u in self.saved_users:
                    if u['email'] == email:
                        history = list(u.get('redeem_history', []) or [])
                        break

        if history:
            last = history[-1]
            self.info_labels['last_redeem'].config(
                text=f"{last.get('time', '--')}  兑换码 {last.get('code', '--')}")
        else:
            self.info_labels['last_redeem'].config(text="--")
