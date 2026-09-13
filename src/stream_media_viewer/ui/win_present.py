"""画面外の窓でも絵の全体を書き直す（Windows）。"""

from __future__ import annotations

import sys
from ctypes import POINTER, Structure, byref, c_int, c_void_p, memmove, sizeof, wintypes
from ctypes.wintypes import BYTE, DWORD, POINT, SIZE, WORD

from PySide6.QtGui import QImage, QPixmap

_ULW_OPAQUE = 0x00000004
_ULW_ALPHA = 0x00000002
_WS_EX_LAYERED = 0x00080000
_GWL_EXSTYLE = -20
_AC_SRC_OVER = 0x00
_AC_SRC_ALPHA = 0x01
_BI_RGB = 0
_DIB_RGB_COLORS = 0
_SWP_NOSIZE = 0x0001
_SWP_NOMOVE = 0x0002
_SWP_NOZORDER = 0x0004
_SWP_NOACTIVATE = 0x0010
_SWP_FRAMECHANGED = 0x0020
_RDW_INVALIDATE = 0x0001
_RDW_ERASE = 0x0004
_RDW_ALLCHILDREN = 0x0080
_RDW_UPDATENOW = 0x0100
_RDW_FRAME = 0x0400


class _BLENDFUNCTION(Structure):
    _fields_ = [
        ("BlendOp", BYTE),
        ("BlendFlags", BYTE),
        ("SourceConstantAlpha", BYTE),
        ("AlphaFormat", BYTE),
    ]


class _BITMAPINFOHEADER(Structure):
    _fields_ = [
        ("biSize", DWORD),
        ("biWidth", c_int),
        ("biHeight", c_int),
        ("biPlanes", WORD),
        ("biBitCount", WORD),
        ("biCompression", DWORD),
        ("biSizeImage", DWORD),
        ("biXPelsPerMeter", c_int),
        ("biYPelsPerMeter", c_int),
        ("biClrUsed", DWORD),
        ("biClrImportant", DWORD),
    ]


class _BITMAPINFO(Structure):
    _fields_ = [("bmiHeader", _BITMAPINFOHEADER)]


def redraw_hwnd(hwnd: int) -> bool:
    """画面外の領域も含め、既存の HWND を再描画する。重ね描きはしない。"""
    if sys.platform != "win32" or hwnd <= 0:
        return False
    try:
        import ctypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.RedrawWindow.restype = wintypes.BOOL
        user32.RedrawWindow.argtypes = [wintypes.HWND, c_void_p, c_void_p, DWORD]
        return bool(
            user32.RedrawWindow(
                wintypes.HWND(hwnd),
                None,
                None,
                _RDW_INVALIDATE | _RDW_ERASE | _RDW_ALLCHILDREN | _RDW_UPDATENOW | _RDW_FRAME,
            )
        )
    except (AttributeError, OSError, ValueError, TypeError):
        return False


def present_opaque_pixmap(hwnd: int, pixmap: QPixmap) -> bool:
    """HWND の全体へ不透明な絵を載せる。失敗したら False。"""
    if sys.platform != "win32" or hwnd <= 0 or pixmap.isNull():
        return False
    image = pixmap.toImage()
    if image.isNull():
        return False
    if image.format() != QImage.Format.Format_ARGB32:
        image = image.convertToFormat(QImage.Format.Format_ARGB32)
    width, height = image.width(), image.height()
    if width < 1 or height < 1:
        return False
    try:
        import ctypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
        _bind_win32(user32, gdi32)
        handle = wintypes.HWND(hwnd)
        _enable_layered(user32, handle)
        hdc_screen = user32.GetDC(None)
        if not hdc_screen:
            return _redraw(user32, handle)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        if not hdc_mem:
            user32.ReleaseDC(None, hdc_screen)
            return _redraw(user32, handle)
        info = _BITMAPINFO()
        info.bmiHeader.biSize = sizeof(_BITMAPINFOHEADER)
        info.bmiHeader.biWidth = width
        info.bmiHeader.biHeight = -height
        info.bmiHeader.biPlanes = 1
        info.bmiHeader.biBitCount = 32
        info.bmiHeader.biCompression = _BI_RGB
        bits = c_void_p()
        hbmp = gdi32.CreateDIBSection(
            hdc_mem, byref(info), _DIB_RGB_COLORS, byref(bits), None, 0
        )
        if not hbmp or not bits.value:
            gdi32.DeleteDC(hdc_mem)
            user32.ReleaseDC(None, hdc_screen)
            return _redraw(user32, handle)
        _copy_image(image, bits.value, width, height)
        old = gdi32.SelectObject(hdc_mem, hbmp)
        size = SIZE(width, height)
        src = POINT(0, 0)
        ok = bool(
            user32.UpdateLayeredWindow(
                handle, hdc_screen, None, byref(size), hdc_mem, byref(src), 0, None, _ULW_OPAQUE
            )
        )
        if not ok:
            blend = _BLENDFUNCTION(_AC_SRC_OVER, 0, 255, _AC_SRC_ALPHA)
            ok = bool(
                user32.UpdateLayeredWindow(
                    handle,
                    hdc_screen,
                    None,
                    byref(size),
                    hdc_mem,
                    byref(src),
                    0,
                    byref(blend),
                    _ULW_ALPHA,
                )
            )
        gdi32.SelectObject(hdc_mem, old)
        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(None, hdc_screen)
        if ok:
            return True
        return _redraw(user32, handle)
    except (AttributeError, OSError, ValueError, TypeError):
        return False


def _bind_win32(user32, gdi32) -> None:
    user32.GetDC.restype = wintypes.HDC
    user32.GetDC.argtypes = [wintypes.HWND]
    user32.ReleaseDC.restype = c_int
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    user32.RedrawWindow.restype = wintypes.BOOL
    user32.RedrawWindow.argtypes = [wintypes.HWND, c_void_p, c_void_p, DWORD]
    user32.UpdateLayeredWindow.restype = wintypes.BOOL
    user32.UpdateLayeredWindow.argtypes = [
        wintypes.HWND,
        wintypes.HDC,
        POINTER(POINT),
        POINTER(SIZE),
        wintypes.HDC,
        POINTER(POINT),
        DWORD,
        c_void_p,
        DWORD,
    ]
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.SetWindowPos.argtypes = [
        wintypes.HWND,
        wintypes.HWND,
        c_int,
        c_int,
        c_int,
        c_int,
        DWORD,
    ]
    gdi32.CreateCompatibleDC.restype = wintypes.HDC
    gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
    gdi32.CreateDIBSection.restype = wintypes.HBITMAP
    gdi32.CreateDIBSection.argtypes = [
        wintypes.HDC,
        POINTER(_BITMAPINFO),
        DWORD,
        POINTER(c_void_p),
        wintypes.HANDLE,
        DWORD,
    ]
    gdi32.SelectObject.restype = wintypes.HGDIOBJ
    gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    gdi32.DeleteObject.restype = wintypes.BOOL
    gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi32.DeleteDC.restype = wintypes.BOOL
    gdi32.DeleteDC.argtypes = [wintypes.HDC]


def _enable_layered(user32, hwnd) -> None:
    getter = getattr(user32, "GetWindowLongPtrW", None)
    setter = getattr(user32, "SetWindowLongPtrW", None)
    if getter is None or setter is None:
        getter = user32.GetWindowLongW
        setter = user32.SetWindowLongW
        getter.restype = c_int
        getter.argtypes = [wintypes.HWND, c_int]
        setter.restype = c_int
        setter.argtypes = [wintypes.HWND, c_int, c_int]
    else:
        getter.restype = c_void_p
        getter.argtypes = [wintypes.HWND, c_int]
        setter.restype = c_void_p
        setter.argtypes = [wintypes.HWND, c_int, c_void_p]
    style = getter(hwnd, _GWL_EXSTYLE) or 0
    if int(style) & _WS_EX_LAYERED:
        return
    setter(hwnd, _GWL_EXSTYLE, int(style) | _WS_EX_LAYERED)
    user32.SetWindowPos(
        hwnd,
        None,
        0,
        0,
        0,
        0,
        _SWP_NOMOVE | _SWP_NOSIZE | _SWP_NOZORDER | _SWP_NOACTIVATE | _SWP_FRAMECHANGED,
    )


def _redraw(user32, hwnd) -> bool:
    return bool(
        user32.RedrawWindow(
            hwnd,
            None,
            None,
            _RDW_INVALIDATE | _RDW_ERASE | _RDW_ALLCHILDREN | _RDW_UPDATENOW | _RDW_FRAME,
        )
    )


def _copy_image(image: QImage, dest: int, width: int, height: int) -> None:
    stride = width * 4
    src_stride = image.bytesPerLine()
    raw = bytes(image.constBits())
    if src_stride == stride:
        memmove(dest, raw, height * stride)
        return
    for row in range(height):
        start = row * src_stride
        memmove(dest + row * stride, raw[start : start + stride], stride)
