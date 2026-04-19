"""Windows activity collector.

Purpose:
- Detect the current foreground application
- Detect idle time (seconds since last user input)

This is Windows-specific and should only be used on Windows.
"""

from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import psutil


user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]


@dataclass(slots=True)
class ForegroundApp:
    app_key: str
    pid: int
    process_name: str
    exe_path: str
    window_title: str
    collected_at: str


class WindowsActivityCollector:
    """Collect foreground app and idle time information on Windows."""

    def get_idle_seconds(self) -> float:
        """Return seconds since last keyboard/mouse input."""
        info = LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(LASTINPUTINFO)

        if not user32.GetLastInputInfo(ctypes.byref(info)):
            return 0.0

        tick_count = kernel32.GetTickCount()
        idle_ms = tick_count - info.dwTime
        return max(idle_ms / 1000.0, 0.0)

    def get_foreground_app(self) -> ForegroundApp | None:
        """Return metadata for the current foreground app."""
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None

        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process_id = int(pid.value)

        if process_id <= 0:
            return None

        window_title = self._get_window_title(hwnd)
        exe_path = self._get_process_path(process_id)
        process_name = self._get_process_name(process_id, exe_path)
        app_key = self._build_app_key(exe_path, process_name)

        return ForegroundApp(
            app_key=app_key,
            pid=process_id,
            process_name=process_name,
            exe_path=exe_path,
            window_title=window_title,
            collected_at=datetime.now().isoformat(timespec="seconds"),
        )

    def _get_window_title(self, hwnd: int) -> str:
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return ""

        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, len(buffer))
        return buffer.value.strip()

    def _get_process_path(self, pid: int) -> str:
        """Try to read full executable path for a PID."""
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return ""

        try:
            buffer_len = wintypes.DWORD(32768)
            buffer = ctypes.create_unicode_buffer(buffer_len.value)

            query_full_image_name = kernel32.QueryFullProcessImageNameW
            query_full_image_name.argtypes = [
                wintypes.HANDLE,
                wintypes.DWORD,
                wintypes.LPWSTR,
                ctypes.POINTER(wintypes.DWORD),
            ]
            query_full_image_name.restype = wintypes.BOOL

            success = query_full_image_name(handle, 0, buffer, ctypes.byref(buffer_len))
            if not success:
                return ""

            return buffer.value.strip()
        finally:
            kernel32.CloseHandle(handle)

    def _get_process_name(self, pid: int, exe_path: str) -> str:
        """Get process name from psutil or fall back to exe filename."""
        try:
            return psutil.Process(pid).name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            if exe_path:
                return Path(exe_path).name()
            return f"pid_{pid}"

    def _build_app_key(self, exe_path: str, process_name: str) -> str:
        """Create a stable identifier for the app."""
        if exe_path:
            return exe_path.lower()
        return process_name.lower()


if __name__ == "__main__":
    collector = WindowsActivityCollector()
    app = collector.get_foreground_app()
    idle = collector.get_idle_seconds()

    print("Idle seconds:", idle)
    if app:
        print("Foreground app:")
        print("  app_key      :", app.app_key)
        print("  pid          :", app.pid)
        print("  process_name :", app.process_name)
        print("  exe_path     :", app.exe_path)
        print("  window_title :", app.window_title)
        print("  collected_at :", app.collected_at)
    else:
        print("No foreground app detected.")