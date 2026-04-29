import base64
import json
import requests
from datetime import datetime

# ========== 解密模块 ==========
_A = base64.b64decode(
    "bnN6e2dBV3JrWGx4MDhKNkVxOlY0W2RlTzFEUVRDd20yb0IzdHk5alNZSV03Uk01YkhpVWFmLGN9S3VQR3BOaFpMdkY="
).decode()
_B = base64.b64decode(
    "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXpBQkNERUZHSElKS0xNTk9QUVJTVFVWV1hZWjAxMjM0NTY3ODksW117fTo="
).decode()

def decrypt(encrypted_str):
    return ''.join(_B[_A.find(ch)] if ch in _A else ch for ch in encrypted_str)

def decrypt_response(base64_text):
    raw = base64.b64decode(base64_text).decode('utf-8', errors='ignore')
    plain = raw
    for _ in range(10):          # 前端是10次
        plain = decrypt(plain)
    return json.loads(plain)

# ========== 配置 ==========
TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6MjY1NzM3LCJzZXNzaW9uIjoiZjI5NWY1YzVlM2NlZTFmMWI0ZjA2ZTJkM2NhNGZmMzgifQ.VQXL5IXiexflKFKFOlOt_K3jH5n14PM9fOIyJd5P59c"  # ← 替换成从 localStorage.getItem('auth_data') 获取的值

HEADERS = {
    "Authorization": TOKEN,
    "theme-ua": "mala-pro",
    "origin": "https://love.52pokemon66.cc",
    "referer": "https://love.52pokemon66.cc/",
    "accept": "application/json, text/plain, */*",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0",
}
HEADERS = {k: v.encode('ascii', errors='ignore').decode() for k, v in HEADERS.items()}

# ========== 请求 ==========
session = requests.Session()
session.trust_env = False

resp = session.get(
    "https://api123.136470.xyz/api/v1/user/plan/fetch?id=8",
    headers=HEADERS,
    timeout=15
)

if resp.status_code != 200:
    print(f"请求失败，状态码: {resp.status_code}")
    exit(1)

result = decrypt_response(resp.text)
# 关键数据都在 result['data'] 里
user = result['data']

print(user)

