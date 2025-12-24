import win32gui
import win32con
import win32api
from PyQt6.QtGui import QPixmap, QPainter, QColor

class WindowMgr:
    @staticmethod
    def get_window_list():
        titles = []
        def enum_window_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                titles.append((hwnd, win32gui.GetWindowText(hwnd)))
        win32gui.EnumWindows(enum_window_callback, None)
        titles.sort(key=lambda x: x[1])
        return titles

    @staticmethod
    def get_foreground_window_info():
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        return hwnd, title

class BackgroundInput:    
    VK_MAP = {
        'enter': win32con.VK_RETURN,
        'space': win32con.VK_SPACE,
        'tab': win32con.VK_TAB,
        'backspace': win32con.VK_BACK,
        'esc': win32con.VK_ESCAPE,
        'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 
        'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
        'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
        'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
        'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A,
        '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
        '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39
    }

    @staticmethod
    def send_key(hwnd, key_str):
        key_lower = key_str.lower()
        vk_code = BackgroundInput.VK_MAP.get(key_lower)
        if not vk_code and len(key_str) == 1:
            vk_code = ord(key_str.upper())
        if vk_code:
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_code, 0)
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk_code, 0)
            return True
        return False
    
class TextUtils:
    @staticmethod
    def format_key_text(key_str):
        if not key_str: return ""
        parts = key_str.lower().replace(" ", "").split('+')
        formatted_parts = [p.capitalize() for p in parts]       
        final_parts = []
        for p in formatted_parts:
            if p in ["Win", "Windows", "Left windows", "Right windows"]:
                final_parts.append("Win")
            else:
                final_parts.append(p)                
        return " + ".join(final_parts)

class IconUtils:
    @staticmethod
    def create_default_icon():
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setBrush(QColor("#4CAF50"))
        painter.setPen(QColor("#388E3C"))
        painter.drawRoundedRect(4, 4, 56, 56, 10, 10)
        painter.setPen(QColor("white"))
        font = painter.font()
        font.setPixelSize(40)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(0, 0, 64, 64, 0x0084, "A")
        painter.end()
        return pixmap