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
    # 扩充常用的虚拟键码映射
    VK_MAP = {
        'backspace': 0x08, 'tab': 0x09, 'clear': 0x0C, 'enter': 0x0D, 'shift': 0x10, 
        'ctrl': 0x11, 'alt': 0x12, 'pause': 0x13, 'caps_lock': 0x14, 'esc': 0x1B, 
        'space': 0x20, 'page_up': 0x21, 'page_down': 0x22, 'end': 0x23, 'home': 0x24, 
        'left': 0x25, 'up': 0x26, 'right': 0x27, 'down': 0x28, 'select': 0x29, 
        'print': 0x2A, 'execute': 0x2B, 'print_screen': 0x2C, 'insert': 0x2D, 'delete': 0x2E, 
        'help': 0x2F,
        '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34, 
        '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
        'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'f': 0x46, 'g': 0x47, 
        'h': 0x48, 'i': 0x49, 'j': 0x4A, 'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 
        'o': 0x4F, 'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54, 'u': 0x55, 
        'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A,
        'left_win': 0x5B, 'right_win': 0x5C, 'apps': 0x5D, 'sleep': 0x5F,
        'numpad0': 0x60, 'numpad1': 0x61, 'numpad2': 0x62, 'numpad3': 0x63, 
        'numpad4': 0x64, 'numpad5': 0x65, 'numpad6': 0x66, 'numpad7': 0x67, 
        'numpad8': 0x68, 'numpad9': 0x69,
        'multiply': 0x6A, 'add': 0x6B, 'separator': 0x6C, 'subtract': 0x6D, 
        'decimal': 0x6E, 'divide': 0x6F,
        'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73, 'f5': 0x74, 'f6': 0x75, 
        'f7': 0x76, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
        'num_lock': 0x90, 'scroll_lock': 0x91,
    }

    @staticmethod
    def get_vk_code(key_str):
        """解析按键字符串获取虚拟键码"""
        key_lower = key_str.lower().strip()
        vk_code = BackgroundInput.VK_MAP.get(key_lower)
        
        # 尝试解析单字符 (如果是未映射的字母/数字)
        if not vk_code and len(key_str) == 1:
            vk_code = ord(key_str.upper())
        
        return vk_code

    @staticmethod
    def key_down(hwnd, vk_code):
        """按下按键消息"""
        if vk_code:
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_code, 0)

    @staticmethod
    def key_up(hwnd, vk_code):
        """抬起按键消息"""
        if vk_code:
            # lParam 设置为 0xC0000000 表示 keyup
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk_code, 0xC0000000)

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