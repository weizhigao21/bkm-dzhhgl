import base64
import os
import sys
import tkinter as tk
from tkinter import ttk

VERSION = "1.7"

_A = base64.b64decode(
    "bnN6e2dBV3JrWGx4MDhKNkVxOlY0W2RlTzFEUVRDd20yb0IzdHk5alNZSV03Uk01YkhpVWFmLGN9S3VQR3BOaFpMdkY="
).decode()
_B = base64.b64decode(
    "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXpBQkNERUZHSElKS0xNTk9QUVJTVFVWV1hZWjAxMjM0NTY3ODksW117fTo="
).decode()

if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_FILE = os.path.join(_BASE_DIR, "config.json")

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