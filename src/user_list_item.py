import tkinter as tk

from .constants import *


class UserListItem(tk.Frame):
    """训练师列表项组件，封装了 UI 创建、状态更新和事件处理"""

    def __init__(self, parent, email, remaining_gb, total_gb, token,
                 is_active=False, on_click=None, on_right_click=None,
                 update_count_callback=None):
        super().__init__(parent, bg=C_CARD, cursor="hand2",
                         highlightthickness=1, highlightbackground=C_BORDER,
                         highlightcolor=C_BORDER)
        self.parent = parent
        self.user_email = email
        self.user_token = token
        self._is_active = is_active
        self._remaining_gb = remaining_gb
        self._on_click_cb = on_click
        self._on_right_click_cb = on_right_click
        self._update_count_cb = update_count_callback

        self.pack(fill=tk.X, pady=2)

        self._build_widgets()
        self._bind_events()

        if is_active:
            self._apply_active_style()

        if update_count_callback:
            update_count_callback()

    def _build_widgets(self):
        inner = tk.Frame(self, bg=C_CARD)
        inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        initial = self.user_email[0].upper() if self.user_email else "?"
        avatar = tk.Label(inner, text=initial, bg=C_BORDER, fg=C_TEXT_SECONDARY,
                          font=(FONT_FAMILY, 11, "bold"), width=3, height=2,
                          anchor=tk.CENTER)
        avatar.pack(side=tk.LEFT)

        text_frame = tk.Frame(inner, bg=C_CARD)
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

        display_email = self.user_email if len(self.user_email) <= 24 else self.user_email[:21] + "..."
        email_label = tk.Label(text_frame, text=display_email, bg=C_CARD, fg=C_TEXT,
                               font=(FONT_FAMILY, 10, "bold"), anchor=tk.W)
        email_label.pack(fill=tk.X)

        remain_color = (C_SUCCESS if self._remaining_gb > 50 else
                        (C_WARNING if self._remaining_gb > 10 else C_DANGER))
        remain_label = tk.Label(text_frame, text=f"剩余 {self._remaining_gb:.2f} GB",
                                bg=C_CARD, fg=remain_color,
                                font=(FONT_FAMILY, 9), anchor=tk.W)
        remain_label.pack(fill=tk.X)

        self._widgets = {
            'inner': inner, 'text_frame': text_frame,
            'email_label': email_label, 'remain_label': remain_label, 'avatar': avatar
        }

    def _bind_events(self):
        def on_enter(e):
            if not self._is_active:
                self._set_bg(C_HOVER)

        def on_leave(e):
            if not self._is_active:
                self._set_bg(C_CARD)

        def on_click(e):
            if self._on_click_cb:
                self._on_click_cb(self.user_email)

        def on_right_click(e):
            if self._on_right_click_cb:
                self._on_right_click_cb(e, self.user_email)

        widgets = [self, self._widgets['inner'], self._widgets['text_frame'],
                   self._widgets['email_label'], self._widgets['remain_label'],
                   self._widgets['avatar']]
        for w in widgets:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)
            w.bind("<Button-3>", on_right_click)

    def _set_bg(self, bg):
        for key in ('inner', 'text_frame', 'email_label', 'remain_label'):
            self._widgets[key].configure(bg=bg)
        self.configure(bg=bg)

    def _apply_active_style(self):
        widgets = self._widgets
        self.configure(highlightbackground=C_PRIMARY, highlightcolor=C_PRIMARY,
                       bg=C_ACTIVE_BG)
        for key in ('inner', 'text_frame', 'email_label', 'remain_label'):
            widgets[key].configure(bg=C_ACTIVE_BG)
        widgets['avatar'].configure(bg=C_PRIMARY, fg="white")

    def update_state(self, active, rem_gb):
        """更新选中状态和剩余流量显示"""
        self._is_active = active
        self._remaining_gb = rem_gb
        widgets = self._widgets
        bg = C_ACTIVE_BG if active else C_CARD
        border = C_PRIMARY if active else C_BORDER
        self.configure(highlightbackground=border, highlightcolor=border, bg=bg)
        for key in ('inner', 'text_frame', 'email_label', 'remain_label'):
            widgets[key].configure(bg=bg)
        widgets['avatar'].configure(
            bg=C_PRIMARY if active else C_BORDER,
            fg="white" if active else C_TEXT_SECONDARY)
        r_color = (C_SUCCESS if rem_gb > 50 else
                   (C_WARNING if rem_gb > 10 else C_DANGER))
        widgets['remain_label'].configure(text=f"剩余 {rem_gb:.2f} GB", fg=r_color)