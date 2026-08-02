import json
import time
import threading
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from .constants import *
from .utils import (
    build_multipart, decrypt_response, decrypt_response_raw, try_decrypt_body
)


class AppNetworkMixin:
    def _fetch_data(self, token, show_loading=True, reset_cursor=True):
        try:
            headers = {**DEFAULT_HEADERS, "Authorization": token,
                       "Cache-Control": "no-cache, no-store, must-revalidate",
                       "Pragma": "no-cache"}
            headers = {k: v.encode('ascii', errors='ignore').decode()
                       for k, v in headers.items()}

            resp = self._session.get(API_URL, headers=headers,
                               params={"_t": int(time.time() * 1000)},
                               timeout=15)

            if resp.status_code != 200:
                self._log(f"查询订阅失败  HTTP {resp.status_code}", "error")
                new_token = self._try_relogin(token)
                if new_token:
                    self._fetch_data(new_token, show_loading, reset_cursor)
                    return
                if show_loading:
                    self.root.after(0, lambda: self._show_error(
                        f"请求失败，状态码: {resp.status_code}"))
                else:
                    self.root.after(0, lambda: self._notify_token_expired())
                return

            result = decrypt_response(resp.text)
            user = result['data']
            email = user.get('email', '')

            fetching = getattr(self, '_fetching_email', None)
            if fetching and email != fetching:
                self._log(f"查询结果不匹配，跳过  {email} (期望 {fetching})", "warn")
                return

            self._log(f"查询成功  {email}" if email else "查询成功", "success")
            pwd = None
            with self._data_lock:
                for u in self.saved_users:
                    if u.get('email') == email:
                        pwd = u.get('password')
                        break
            self.root.after(0, lambda u=user, t=token, p=pwd: self._update_ui(u, t, p))
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
            if show_loading and reset_cursor:
                self.root.after(0, lambda: self.root.config(cursor=""))

    def _try_relogin(self, old_token):
        email = None
        password = None
        with self._data_lock:
            for u in self.saved_users:
                if u['token'] == old_token:
                    email = u['email']
                    password = u.get('password')
                    break

        if not email or not password:
            return None

        now = time.time()
        last_attempt = self._last_relogin_attempt_time.get(email, 0)
        if now - last_attempt < 300:
            return None
        self._last_relogin_attempt_time[email] = now
        self._relogin_attempted_tokens.add(old_token)

        self._log(f"Token 已过期，正在自动登录  {email}", "info")
        try:
            headers = {k: v.encode('ascii', errors='ignore').decode()
                       for k, v in DEFAULT_HEADERS.items()}
            body, ct = build_multipart({"email": email, "password": password})
            headers["content-type"] = ct
            resp = self._session.post(API_LOGIN, data=body, headers=headers, timeout=15)
            if resp.status_code != 200:
                self._log(f"自动登录失败  HTTP {resp.status_code}  {email}", "error")
                return None
            result = decrypt_response(resp.text)
            data = result.get('data', result)
            new_token = data.get('auth_data')
            if not new_token:
                for key in ['token', 'access_token', 'auth', 'session']:
                    val = data.get(key)
                    if val:
                        new_token = val
                        break
            if not new_token:
                self._log(f"自动登录失败，未获取到 Token  {email}", "error")
                return None
            for u in self.saved_users:
                if u['email'] == email:
                    u['token'] = new_token
                    break
            self._saved_email = email
            self._saved_password = password
            self.token_var.set(new_token)
            self._save_config(new_token)
            self._log(f"自动登录成功  {email}", "success")
            return new_token
        except Exception as e:
            self._log(f"自动登录异常: {e}", "error")
            return None

    def _redeem_flow(self, headers, plan_id, code):
        save_data = {
            "plan_id": str(plan_id),
            "period": "month_price",
            "coupon_code": code,
        }
        self._log(f"正在下单  plan={plan_id}", "info")
        resp = self._session.post(API_ORDER_SAVE, data=save_data, headers=headers, timeout=15)
        if resp.status_code != 200:
            err = try_decrypt_body(resp.text)
            return None, f"下单失败: {err}"

        result = decrypt_response(resp.text)
        trade_no = result.get('data', '')
        if not trade_no:
            trade_no = decrypt_response_raw(resp.text)
        self._log(f"下单成功  trade_no={trade_no}", "success")

        self._log("正在支付...", "info")
        resp = self._session.post(API_ORDER_CHECKOUT,
                            data={"trade_no": trade_no, "method": "1"},
                            headers=headers, timeout=15)
        if resp.status_code != 200:
            err = try_decrypt_body(resp.text)
            return None, f"支付失败: {err}"
        self._log("支付成功", "success")

        self._log("正在校验...", "info")
        resp = self._session.get(f"{API_ORDER_CHECK}?trade_no={trade_no}",
                           headers=headers, timeout=15)
        if resp.status_code != 200:
            return None, f"校验失败: HTTP {resp.status_code}"

        self._log("兑换完成", "success")
        return trade_no, None

    def _do_redeem(self, token, code):
        email = None
        with self._data_lock:
            for u in self.saved_users:
                if u['token'] == token:
                    email = u['email']
                    break
        try:
            headers = {**DEFAULT_HEADERS, "Authorization": token}
            headers = {k: v.encode('ascii', errors='ignore').decode()
                       for k, v in headers.items()}
            trade_no, error = self._redeem_flow(headers, self._current_plan_id, code)
            self.root.after(0, lambda: self._on_redeem_result(trade_no, error, email, code))
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

    def _redeem_one(self, user, code):
        email = user.get('email', '?')
        token = user.get('token', '')
        try:
            plan_id = user.get('plan_id') or (
                user.get('cached_data', {}).get('plan_id') if user.get('cached_data') else None)
            if not plan_id:
                return {'email': email, 'success': False, 'error': '未获取到套餐 ID'}

            headers = {**DEFAULT_HEADERS, "Authorization": token}
            headers = {k: v.encode('ascii', errors='ignore').decode()
                       for k, v in headers.items()}
            trade_no, error = self._redeem_flow(headers, plan_id, code)

            if error:
                return {'email': email, 'success': False, 'error': error}
            return {'email': email, 'success': True, 'trade_no': trade_no}
        except json.JSONDecodeError:
            return {'email': email, 'success': False, 'error': '解密失败，Token 可能已过期'}
        except requests.RequestException as e:
            return {'email': email, 'success': False, 'error': f'网络错误: {e}'}
        except Exception as e:
            return {'email': email, 'success': False, 'error': str(e)}

    def _do_redeem_all(self, code):
        with self._data_lock:
            users_snapshot = list(self.saved_users)
        total = len(users_snapshot)
        results = []

        self._log(f"批量兑换 {total} 个账户，兑换码: {code}", "info")

        def redeem_one(user):
            email = user.get('email', '?')
            self._log(f"兑换  {email}", "info")
            r = self._redeem_one(user, code)
            status = "成功" if r['success'] else f"失败: {r.get('error', '')}"
            self._log(f"兑换结果  {email}: {status}",
                       "success" if r['success'] else "error")
            return r

        with ThreadPoolExecutor(max_workers=min(total, 6)) as executor:
            futures = {executor.submit(redeem_one, u): u for u in users_snapshot}
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    results.append({
                        'email': futures[future].get('email', '?'),
                        'success': False, 'error': str(e)
                    })

        success_count = sum(1 for r in results if r['success'])
        fail_count = total - success_count
        self._log(f"批量兑换完成: {success_count} 成功, {fail_count} 失败", "info")

        self.root.after(0, lambda: self._on_redeem_all_result(results, code))

    def _fetch_all_data(self):
        with self._data_lock:
            users_snapshot = list(self.saved_users)
            active_email = self._active_user_email
        total = len(users_snapshot)
        self._log(f"全局刷新 {total} 个账户...", "info")

        def fetch_one(user):
            token = user['token']
            email = user['email']
            is_active = (email == active_email)
            self._log(f"刷新  {email}", "info")
            self._fetch_data(token, show_loading=is_active, reset_cursor=False)

        with ThreadPoolExecutor(max_workers=min(total, 6)) as executor:
            futures = [executor.submit(fetch_one, user) for user in users_snapshot]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self._log(f"刷新异常: {e}", "error")

        self.root.after(0, lambda: self.root.config(cursor=""))