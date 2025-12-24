# executor.py
import time
import keyboard
import win32api, win32con
from PyQt6.QtCore import QThread, pyqtSignal
from utils import TextUtils, WindowMgr

# ... (BackgroundInput 类保持不变，或根据需要引入) ...
# 为了节省篇幅，假设 BackgroundInput 已包含在 utils 或单独文件中，这里简化处理

class TaskExecutor(QThread):
    sig_progress = pyqtSignal(str)
    sig_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._is_running = False
        self.mode = "keyboard"
        
        # 键盘参数
        self.kb_actions = []
        self.kb_loop = 1
        self.kb_hwnd = 0
        
        # 鼠标参数
        self.mouse_type = "left"
        self.mouse_click = "click"
        self.mouse_cps = 1 # 频率

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
                # 确保格式化后的键也能被 keyboard 识别 (通常没问题)
                # 这里发送原始的小写按键可能更稳，但在 UI 上存的是 TextUtils 处理过的
                # keyboard.send 接受 "Ctrl+A" 这种格式
                
                delay = action.get('delay', 100)
                self.sig_progress.emit(f"第 {current_loop} 轮 | 按键: {key_raw}")

                try:
                    if self.kb_hwnd == 0:
                        keyboard.send(key_raw)
                    else:
                        # 后台发送逻辑 (需确保 utils.BackgroundInput 存在)
                        # BackgroundInput.send_key(self.kb_hwnd, key_raw)
                        pass 
                except Exception as e:
                    print(f"Key Error: {e}")

                self._smart_sleep(delay / 1000.0)
            
            if self._is_running: time.sleep(0.05)

    def _run_mouse(self):
        import ctypes
        MOUSEEVENTF_LEFTDOWN = 0x0002
        MOUSEEVENTF_LEFTUP = 0x0004
        MOUSEEVENTF_RIGHTDOWN = 0x0008
        MOUSEEVENTF_RIGHTUP = 0x0010

        # 计算间隔：1秒 / 次数
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