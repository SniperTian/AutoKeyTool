import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

class HotkeyManager(QObject):
    # 定义三个信号
    sig_start = pyqtSignal()
    sig_stop = pyqtSignal()
    sig_bind = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.start_key = "f9"
        self.stop_key = "f10"
        self.bind_key = "f11"

    def register_hotkeys(self, start_key, stop_key, bind_key):
        """
        统一注册所有热键
        """
        # 先清理旧的
        self.unregister_all()

        self.start_key = start_key
        self.stop_key = stop_key
        self.bind_key = bind_key

        try:
            # 注册新热键
            keyboard.add_hotkey(self.start_key, self._on_start_triggered)
            keyboard.add_hotkey(self.stop_key, self._on_stop_triggered)
            keyboard.add_hotkey(self.bind_key, self._on_bind_triggered)
            
            return True, f"热键已更新: 启动[{self.start_key}] 停止[{self.stop_key}] 绑定[{self.bind_key}]"
        except Exception as e:
            return False, f"热键注册失败: {str(e)}"

    def unregister_all(self):
        """临时卸载所有热键 (防止录制时触发)"""
        try:
            keyboard.unhook_all_hotkeys()
        except:
            pass

    # --- 内部回调 ---
    def _on_start_triggered(self):
        self.sig_start.emit()

    def _on_stop_triggered(self):
        self.sig_stop.emit()

    def _on_bind_triggered(self):
        self.sig_bind.emit()