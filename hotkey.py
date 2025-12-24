# hotkey.py
import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

class HotkeyManager(QObject):
    # 定义信号：当监测到热键时，发送信号给主线程
    sig_start = pyqtSignal()
    sig_stop = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.start_key = "f9"
        self.stop_key = "f10"

    def register_hotkeys(self, start_key, stop_key):
        """
        注册全局热键
        注意：需要管理员权限才能完全生效
        """
        # 1. 清理旧的热键钩子
        try:
            keyboard.unhook_all_hotkeys()
        except:
            pass

        self.start_key = start_key
        self.stop_key = stop_key

        # 2. 注册新热键
        # 这里的 lambda 会在 keyboard 的独立线程中执行，所以需要 emit 信号
        try:
            keyboard.add_hotkey(self.start_key, self._on_start_triggered)
            keyboard.add_hotkey(self.stop_key, self._on_stop_triggered)
            return True, f"热键已生效: 启动[{self.start_key}] / 停止[{self.stop_key}]"
        except Exception as e:
            return False, f"热键注册失败 (请尝试管理员身份运行): {str(e)}"

    def _on_start_triggered(self):
        # 转发信号
        self.sig_start.emit()

    def _on_stop_triggered(self):
        # 转发信号
        self.sig_stop.emit()