import requests
import base64
import json
from datetime import datetime

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


HEADERS = {
    "Authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6MzI1NzczLCJzZXNzaW9uIjoiYzkzMDUwYWYyZmIzYzE4OWFkYTdjODAyNGY5ZDkxMDcifQ.ScUNnsa_58sVEoM7TqdGVhowN0HmDpPLx6gT8mFerV4",
    "theme-ua": "mala-pro",
    "origin": "https://love.52pokemon66.cc",
    "referer": "https://love.52pokemon66.cc/",
    "accept": "application/json, text/plain, */*",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0",
}


def check_coupon():
    url_check = "https://api123.136470.xyz/api/v1/user/coupon/check"

    re_url_check = requests.post(
        url_check,
        headers=HEADERS,
        data={"code":"雷丘",
        "plan_id":8},
        timeout=15
    )

    result = decrypt_response(re_url_check.text)
    print(result)

def fetch_order():
    url_fetch = "https://api123.136470.xyz/api/v1/user/order/fetch?id=8"

    re_url_fetch = requests.get(
        url_fetch,
        headers=HEADERS,
        timeout=15
    )

    result = decrypt_response(re_url_fetch.text)
    print(result)

def save_order():
    url_save = "https://api123.136470.xyz/api/v1/user/order/save"

    re_url_save = requests.post(
        url_save,
        headers=HEADERS,
        data={"plan_id":8,
            "period":"month_price",
            "coupon_code":"雷丘"},
        timeout=15
    )

    result = decrypt_response(re_url_save.text)
    print(result)
    return result
def detail_order(id):
    url_detail = "https://api123.136470.xyz/api/v1/user/order/detail?trade_no=" + id

    re_url_detail = requests.get(
        url_detail,
        headers=HEADERS,
        timeout=15
    )

    result = decrypt_response(re_url_detail.text)
    print(result)
   
def checkout_order(id):
    url_checkout = "https://api123.136470.xyz/api/v1/user/order/checkout" 

    re_url_checkout = requests.post(
        url_checkout,
        headers=HEADERS,
        data={"trade_no":id,
        "method":1},
        timeout=15
    )

    result = decrypt_response(re_url_checkout.text)
    print(result)
def check_order(id):
    url_check = "https://api123.136470.xyz/api/v1/user/order/check?trade_no=" + id

    re_url_check = requests.get(
        url_check,
        headers=HEADERS,
        timeout=15
    )

    result = decrypt_response(re_url_check.text)
    print(result)



check_coupon()
fetch_order()
save_ID = save_order()
detail_order(save_ID["data"])
checkout_order(save_ID["data"])
check_order(save_ID["data"])
