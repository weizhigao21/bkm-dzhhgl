"""开机自启动管理（Windows）。

通过注册表 HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run 实现，
无需管理员权限。打包后的 exe 直接指向可执行文件；开发模式下指向
`pythonw main.py` 形式。
"""

import os
import sys

APP_NAME = "BkmDzhhglAutoStart"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _is_windows():
    return sys.platform.startswith("win")


def _target_command():
    """返回写入注册表的启动命令。"""
    if getattr(sys, "frozen", False):
        # PyInstaller 打包后的 exe
        exe = sys.executable
        return f'"{exe}"'
    # 开发模式：用当前 Python 解释器运行 main.py
    python = sys.executable
    main_py = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
    return f'"{python}" "{main_py}"'


def is_enabled():
    """返回当前是否已启用开机自启动。"""
    if not _is_windows():
        return False
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        finally:
            winreg.CloseKey(key)
    except FileNotFoundError:
        return False
    except OSError:
        return False
    except Exception:
        return False


def enable():
    """启用开机自启动，成功返回 True。"""
    if not _is_windows():
        return False
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _target_command())
        finally:
            winreg.CloseKey(key)
        return True
    except Exception:
        return False


def disable():
    """关闭开机自启动，成功返回 True。"""
    if not _is_windows():
        return False
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(key, APP_NAME)
        finally:
            winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return True
    except Exception:
        return False
