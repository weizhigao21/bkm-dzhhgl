import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import requests

from .constants import *
from .utils import center_window, build_multipart, decrypt_response


class LoginDialog:
    def __init__(self, app):
        self.app = app
        self.dialog = tk.Toplevel(app.root)
        self.dialog.withdraw()
        self.dialog.title("宝可梦 · 登录")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=C_CARD)
        self.dialog.transient(app.root)
        self.dialog.grab_set()

        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)

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

        active_email = app._active_user_email
        if active_email:
            for u in app.saved_users:
                if u['email'] == active_email and u.get('password'):
                    self.email_var.set(active_email)
                    self.password_var.set(u['password'])
                    self.pass_entry.focus_set()
                    break
            else:
                if app._saved_email:
                    self.email_var.set(app._saved_email)
                if app._saved_password:
                    self.password_var.set(app._saved_password)
                    self.pass_entry.focus_set()
                else:
                    self.email_entry.focus_set()
        else:
            if app._saved_email:
                self.email_var.set(app._saved_email)
            if app._saved_password:
                self.password_var.set(app._saved_password)
                self.pass_entry.focus_set()
            else:
                self.email_entry.focus_set()

        self.dialog.bind("<Return>", lambda e: self._on_login())
        self.dialog.update_idletasks()
        center_window(self.dialog, app.root, 400, 300)
        self.dialog.deiconify()
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
        self.dialog.withdraw()
        self.dialog.title("运行日志")
        self.dialog.geometry("700x480")
        self.dialog.resizable(True, True)
        self.dialog.minsize(500, 300)
        self.dialog.configure(bg=C_CARD)
        self.dialog.transient(app.root)
        self.dialog.grab_set()

        title_frame = tk.Frame(self.dialog, bg=C_CARD)
        title_frame.pack(fill=tk.X, padx=16, pady=(14, 8))

        tk.Label(title_frame, text=f"运行日志 · 宝可梦多账号管家 v{VERSION}", bg=C_CARD, fg=C_TEXT,
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
        self.dialog.update_idletasks()
        center_window(self.dialog, app.root, 700, 480)
        self.dialog.deiconify()
        self.dialog.wait_window()

    def _on_close(self):
        self.app.log_text = None
        self.dialog.destroy()

    def _on_clear(self):
        self.app._log_lines.clear()
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)


class RedeemResultDialog:
    def __init__(self, app, results, code):
        self.dialog = tk.Toplevel(app.root)
        self.dialog.withdraw()
        self.dialog.title("批量兑换结果")
        self.dialog.geometry("520x420")
        self.dialog.resizable(True, True)
        self.dialog.minsize(420, 300)
        self.dialog.configure(bg=C_CARD)
        self.dialog.transient(app.root)
        self.dialog.grab_set()

        success = sum(1 for r in results if r['success'])
        fail = len(results) - success

        header_frame = tk.Frame(self.dialog, bg=C_CARD)
        header_frame.pack(fill=tk.X, padx=16, pady=(14, 8))

        tk.Label(header_frame, text="批量兑换结果", bg=C_CARD, fg=C_TEXT,
                 font=(FONT_FAMILY, 13, "bold")).pack(side=tk.LEFT)

        summary = f"共 {len(results)} 个账户: {success} 成功, {fail} 失败"
        tk.Label(header_frame, text=summary, bg=C_CARD, fg=C_TEXT_SECONDARY,
                 font=(FONT_FAMILY, 9)).pack(side=tk.RIGHT)

        tk.Frame(self.dialog, bg=C_BORDER, height=1).pack(fill=tk.X, padx=16)

        tree_frame = tk.Frame(self.dialog, bg=C_CARD)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(8, 8))

        columns = ('email', 'status', 'detail')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=10)
        tree.heading('email', text='邮箱')
        tree.heading('status', text='状态')
        tree.heading('detail', text='详情')
        tree.column('email', width=180)
        tree.column('status', width=70, anchor=tk.CENTER)
        tree.column('detail', width=230)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tree.tag_configure('success', foreground=C_SUCCESS)
        tree.tag_configure('error', foreground=C_DANGER)

        for r in results:
            email = r.get('email', '?')
            if r['success']:
                detail = f"订单号: {r.get('trade_no', '--')}"
                tree.insert('', tk.END, values=(email, '成功', detail), tags=('success',))
            else:
                detail = r.get('error', '未知错误')
                tree.insert('', tk.END, values=(email, '失败', detail), tags=('error',))

        btn_frame = tk.Frame(self.dialog, bg=C_CARD)
        btn_frame.pack(fill=tk.X, padx=16, pady=(0, 14))

        ttk.Button(btn_frame, text="关闭", style="Secondary.TButton",
                   width=10, command=self.dialog.destroy).pack(side=tk.RIGHT)

        self.dialog.update_idletasks()
        center_window(self.dialog, app.root, 520, 420)
        self.dialog.deiconify()
        self.dialog.wait_window()