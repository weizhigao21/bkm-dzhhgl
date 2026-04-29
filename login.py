import base64
import json
import getpass
import requests

_A = base64.b64decode(
    "bnN6e2dBV3JrWGx4MDhKNkVxOlY0W2RlTzFEUVRDd20yb0IzdHk5alNZSV03Uk01YkhpVWFmLGN9S3VQR3BOaFpMdkY="
).decode()
_B = base64.b64decode(
    "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXpBQkNERUZHSElKS0xNTk9QUVJTVFVWV1hZWjAxMjM0NTY3ODksW117fTo="
).decode()

LOGIN_URL = "https://api123.136470.xyz/api/v1/passport/auth/login"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "origin": "https://love.52pokemon66.cc",
    "referer": "https://love.52pokemon66.cc/",
    "theme-ua": "mala-pro",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0",
}


def decrypt(encrypted_str):
    return ''.join(_B[_A.find(ch)] if ch in _A else ch for ch in encrypted_str)


def decrypt_response(base64_text):
    raw = base64.b64decode(base64_text).decode('utf-8', errors='ignore')
    plain = raw
    for _ in range(10):
        plain = decrypt(plain)
    return json.loads(plain)


def build_multipart(fields):
    boundary = "----WebKitFormBoundaryFZrKS3m9Wn0LquJY"
    lines = []
    for name, value in fields.items():
        lines.append(f"--{boundary}")
        lines.append(f'Content-Disposition: form-data; name="{name}"')
        lines.append("")
        lines.append(value)
    lines.append(f"--{boundary}--")
    return "\r\n".join(lines), f"multipart/form-data; boundary={boundary}"


def login(email, password):
    session = requests.Session()
    session.trust_env = False

    headers = {k: v.encode('ascii', errors='ignore').decode() for k, v in HEADERS.items()}
    body, content_type = build_multipart({"email": email, "password": password})
    headers["content-type"] = content_type

    resp = session.post(LOGIN_URL, data=body, headers=headers, timeout=15)

    if resp.status_code != 200:
        print(f"请求失败，状态码: {resp.status_code}")
        print(f"响应体: {resp.text}")
        return None

    result = decrypt_response(resp.text)
    print(f"\n登录响应（完整结构）:\n{json.dumps(result, ensure_ascii=False, indent=2)}")

    data = result.get('data', result)
    token = data.get('auth_data')
    if token:
        print(f"\n✅ 提取到 Token:\n{token}")
        return token

    alt_keys = ['token', 'access_token', 'auth', 'session']
    for key in alt_keys:
        val = data.get(key)
        if val:
            print(f"\n⚠️ 从 key='{key}' 提取到值，请确认是否可用:\n{val}")
            return val

    print("\n❌ 未找到 token 字段，请根据上方完整结构手动提取")
    return None


if __name__ == '__main__':
    print("Pokemon66 登录获取 Token")
    print("-" * 40)
    email = input("邮箱: ").strip()
    password = getpass.getpass("密码: ").strip()

    if not email or not password:
        print("邮箱和密码不能为空")
        exit(1)

    token = login(email, password)
    if token:
        print("\n复制此 Token 到 gui.py 或 GUI 界面中即可使用")
