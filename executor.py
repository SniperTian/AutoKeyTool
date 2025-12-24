# executor.py
import time
import keyboard
import win32gui
from PyQt6.QtCore import QThread, pyqtSignal
# 【必要修复】引入 BackgroundInput
from utils import TextUtils, WindowMgr, BackgroundInput

class TaskExecutor(QThread):
    sig_progress = pyqtSignal(str)
    sig_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._is_running = False
        self.mode = "keyboard"
        
        self.kb_actions = []
        self.kb_loop = 1
        self.kb_hwnd = 0
        
        self.mouse_type = "left"
        self.mouse_click = "click"
        self.mouse_cps = 1

    def setup_keyboard(self, actions, loop, hwnd=0):
        self.mode = "keyboard"
        self.kb_actions = actions
        self.kb_loop = loop
        self.kb_hwnd = hwnd

    def setup_mouse(self, m_type, m_click, cps):
        self.mode = "mouse"
        self.mouse_type = m_type
        self.mouse_click = m_click
        self.mouse_cps = cps

    def stop(self):
        self._is_running = False

    def run(self):
        self._is_running = True
        self.sig_progress.emit(f"🚀 {self.mode.upper()} 任务开始...")

        if self.mode == "keyboard":
            self._run_keyboard()
        else:
            self._run_mouse()
            
        self._is_running = False
        self.sig_finished.emit()

    def _run_keyboard(self):
        current_loop = 0
        while self._is_running:
            if self.kb_loop > 0 and current_loop >= self.kb_loop:
                break
            
            current_loop += 1
            for idx, action in enumerate(self.kb_actions):
                if not self._is_running: break
                
                key_raw = action.get('key')
                delay = action.get('delay', 100)
                
                # 格式化显示
                fmt_key = TextUtils.format_key_text(key_raw)
                
                # 检查句柄有效性
                target_hwnd = self.kb_hwnd
                if target_hwnd != 0 and not win32gui.IsWindow(target_hwnd):
                    self.sig_progress.emit(f"⚠️ 窗口已失效，切换至前台模式")
                    target_hwnd = 0

                self.sig_progress.emit(f"第 {current_loop} 轮 | 按键: {fmt_key}")

                try:
                    if target_hwnd == 0:
                        keyboard.send(key_raw)
                    else:
                        # 【必要修复】调用后台发送函数
                        # 确保不是 pass
                        BackgroundInput.send_key(target_hwnd, key_raw)
                except Exception as e:
                    self.sig_progress.emit(f"❌ 错误: {e}")

                self._smart_sleep(delay / 1000.0)
            
            if self._is_running: time.sleep(0.05)

    def _run_mouse(self):
        import ctypes
        MOUSEEVENTF_LEFTDOWN = 0x0002
        MOUSEEVENTF_LEFTUP = 0x0004
        MOUSEEVENTF_RIGHTDOWN = 0x0008
        MOUSEEVENTF_RIGHTUP = 0x0010

        interval = 1.0 / self.mouse_cps

        while self._is_running:
            self.sig_progress.emit(f"🖱️ 点击中... (速度: {self.mouse_cps} 次/秒)")
            
            if self.mouse_type == 'left':
                ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                if self.mouse_click == 'double':
                    time.sleep(0.05)
                    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            else:
                ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

            self._smart_sleep(interval)

    def _smart_sleep(self, seconds):
        end = time.time() + seconds
        while time.time() < end:
            if not self._is_running: return
            time.sleep(0.01)