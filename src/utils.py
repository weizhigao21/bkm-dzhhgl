import base64
import hashlib
import json
import os
import platform
import sys

from .constants import _BASE_DIR, _A, _B


def _machine_key():
    raw = f"{platform.node()}|{os.getlogin()}" if hasattr(os, 'getlogin') else f"{platform.node()}|unknown"
    return hashlib.sha256(raw.encode()).digest()[:16]


def encrypt_sensitive(text):
    if not text:
        return text
    key = _machine_key()
    data = text.encode('utf-8')
    encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return base64.b64encode(encrypted).decode('ascii')


def decrypt_sensitive(text):
    if not text:
        return text
    key = _machine_key()
    try:
        data = base64.b64decode(text)
        decrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        return decrypted.decode('utf-8')
    except Exception:
        return text


def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = _BASE_DIR
    return os.path.join(base, relative_path)


def decrypt(encrypted_str):
    return ''.join(_B[_A.find(ch)] if ch in _A else ch for ch in encrypted_str)


def decrypt_response(base64_text):
    try:
        raw = base64.b64decode(base64_text).decode('utf-8', errors='ignore')
    except Exception:
        raise ValueError("响应内容不是有效的 Base64 编码")
    plain = raw
    for _ in range(10):
        plain = decrypt(plain)
    try:
        return json.loads(plain)
    except json.JSONDecodeError as e:
        raise ValueError(f"解密后的内容不是有效 JSON: {e}")


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