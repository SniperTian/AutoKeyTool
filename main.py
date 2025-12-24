# main.py
import sys
import os
import json
import keyboard
from PyQt6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QMessageBox, QFileDialog)
from PyQt6.QtGui import QIcon, QAction, QFont
from PyQt6.QtCore import QTimer

from gui import MainWindowUI, HotkeySettingDialog
from executor import TaskExecutor
from hotkey import HotkeyManager
from config import ConfigManager
from utils import WindowMgr, TextUtils, IconUtils

DEFAULT_CONFIG_FILE = "default_config.json"

class AutoKeyApp(MainWindowUI):
    def __init__(self):
        super().__init__()
        
        self.executor = TaskExecutor()
        self.hotkey_mgr = HotkeyManager()
        self.config_mgr = ConfigManager()
        self.tray_icon = None
        
        self.current_start_key = "f9"
        self.current_stop_key = "f10"
        self.current_bind_key = "f11"

        self.bind_events()
        self.init_tray()
        
        self.load_startup_config()
        self.refresh_windows()
        self.register_bind_hotkey()

    def bind_events(self):
        self.btn_mod_hotkey.clicked.connect(self.open_hotkey_settings)
        self.btn_add.clicked.connect(lambda: self.add_row_data("a", 1000))
        self.btn_del.clicked.connect(self.remove_row)
        self.btn_up.clicked.connect(self.move_up)
        self.btn_down.clicked.connect(self.move_down)
        self.btn_refresh_win.clicked.connect(self.refresh_windows)
        self.btn_start.clicked.connect(self.start_task)
        self.btn_stop.clicked.connect(self.stop_task)
        self.executor.sig_progress.connect(self.update_status)
        self.executor.sig_finished.connect(self.on_finished)
        self.hotkey_mgr.sig_start.connect(self.start_task)
        self.hotkey_mgr.sig_stop.connect(self.stop_task)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("AutoKey Pro")
        icon_pixmap = IconUtils.create_default_icon()
        self.tray_icon.setIcon(QIcon(icon_pixmap))
        
        menu = QMenu()
        action_show = QAction("显示主界面", self)
        action_quit = QAction("退出程序", self)
        
        action_show.triggered.connect(self.showNormal)
        action_quit.triggered.connect(self.quit_app)
        
        menu.addAction(action_show)
        menu.addAction(action_quit)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_tray_activated)

    def register_bind_hotkey(self):
        # 注册 F11 绑定热键
        try: keyboard.remove_hotkey(self.do_bind_window)
        except: pass
        try: 
            # 这是一个后台热键
            keyboard.add_hotkey(self.current_bind_key, self.do_bind_window)
        except Exception as e: 
            self.update_status(f"绑定热键注册失败: {e}")

    def do_bind_window(self):
        """
        后台热键触发：绑定当前前台窗口。
        因为这是在后台线程运行，必须使用 QTimer.singleShot 转到主线程操作 UI
        """
        # 1. 获取当前前台窗口（用户当前正在操作的窗口）
        hwnd, title = WindowMgr.get_foreground_window_info()
        
        # 排除自己 (AutoKey) 和 空标题窗口
        if title and "AutoKey Pro" not in title:
            # 2. 转到主线程执行 UI 更新
            QTimer.singleShot(0, lambda: self._bind_window_ui_safe(hwnd, title))
        else:
            QTimer.singleShot(0, lambda: self.update_status("⚠️ 无法绑定：请激活目标窗口后再按热键"))

    def _bind_window_ui_safe(self, hwnd, title):
        """主线程槽函数：安全更新 ComboBox"""
        # 查找窗口是否已存在列表中
        idx = self.combo_win.findData(hwnd)
        
        if idx == -1:
            # 不存在则添加
            self.combo_win.addItem(f"[{hwnd}] {title[:25]}...", hwnd)
            idx = self.combo_win.count() - 1
            
        # 选中它
        self.combo_win.setCurrentIndex(idx)
        self.update_status(f"✅ 已绑定窗口: {title[:20]}...")

    def open_hotkey_settings(self):
        dlg = HotkeySettingDialog(self.current_start_key, self.current_stop_key, self.current_bind_key, self)
        if dlg.exec():
            self.current_start_key = dlg.results['start']
            self.current_stop_key = dlg.results['stop']
            self.current_bind_key = dlg.results['bind']
            
            self.lbl_start_hk.setText(f"启动: {TextUtils.format_key_text(self.current_start_key)}")
            self.lbl_stop_hk.setText(f"停止: {TextUtils.format_key_text(self.current_stop_key)}")
            self.lbl_bind_hk.setText(f"绑定: {TextUtils.format_key_text(self.current_bind_key)}")
            
            self.apply_hotkeys()
            self.register_bind_hotkey()

    def start_task(self):
        if self.executor.isRunning(): return
        is_mouse = self.rb_mouse.isChecked()
        if is_mouse:
            m_type = "left" if self.combo_m_type.currentIndex() == 0 else "right"
            m_click = "click" if self.combo_m_click.currentIndex() == 0 else "double"
            cps = self.spin_m_cps.value()
            self.executor.setup_mouse(m_type, m_click, cps)
        else:
            actions = self.get_table_data()
            if not actions:
                QMessageBox.warning(self, "提示", "请先添加按键！")
                return
            loop = self.spin_loop.value()
            hwnd = self.combo_win.currentData()
            self.executor.setup_keyboard(actions, loop, hwnd)
        self.toggle_ui(False)
        self.executor.start()

    def stop_task(self):
        if self.executor.isRunning():
            self.executor.stop()
            self.update_status("正在停止...")

    def on_finished(self):
        self.toggle_ui(True)
        self.update_status("运行结束")

    def toggle_ui(self, enabled):
        self.btn_start.setEnabled(enabled)
        self.btn_stop.setEnabled(not enabled)
        self.stack.setEnabled(enabled)
        self.btn_mod_hotkey.setEnabled(enabled)

    def apply_hotkeys(self):
        ok, msg = self.hotkey_mgr.register_hotkeys(self.current_start_key, self.current_stop_key)
        self.update_status(msg)

    def update_status(self, msg):
        self.lbl_status.setText(msg)

    def get_table_data(self):
        data = []
        for r in range(self.table.rowCount()):
            k_text = self.table.item(r, 0).text()
            d_text = self.table.item(r, 1).text()
            data.append({"key": k_text, "delay": int(d_text)})
        return data

    def remove_row(self):
        r = self.table.currentRow()
        if r >= 0: self.table.removeRow(r)
        
    def move_up(self):
        r = self.table.currentRow()
        if r > 0: self.swap_row(r, r-1)

    def move_down(self):
        r = self.table.currentRow()
        if r < self.table.rowCount()-1: self.swap_row(r, r+1)
        
    def swap_row(self, r1, r2):
        k1 = self.table.item(r1, 0).text(); d1 = self.table.item(r1, 1).text()
        k2 = self.table.item(r2, 0).text(); d2 = self.table.item(r2, 1).text()
        self.table.item(r1, 0).setText(k2); self.table.item(r1, 1).setText(d2)
        self.table.item(r2, 0).setText(k1); self.table.item(r2, 1).setText(d1)
        self.table.selectRow(r2)

    def refresh_windows(self):
        current_idx = self.combo_win.currentIndex()
        self.combo_win.clear()
        self.combo_win.addItem("🌐 全局模式 (前台)", 0)
        wins = WindowMgr.get_window_list()
        for hwnd, title in wins:
            self.combo_win.addItem(f"[{hwnd}] {title[:20]}...", hwnd)
        if current_idx > 0 and current_idx < self.combo_win.count():
            self.combo_win.setCurrentIndex(current_idx)

    def load_startup_config(self):
        if os.path.exists(DEFAULT_CONFIG_FILE):
            data, _ = ConfigManager.load_config(DEFAULT_CONFIG_FILE)
            if data: self.restore_ui_from_data(data)

    def restore_ui_from_data(self, data):
        self.current_start_key = data.get("start", "f9")
        self.current_stop_key = data.get("stop", "f10")
        self.current_bind_key = data.get("bind", "f11")
        
        self.lbl_start_hk.setText(f"启动: {TextUtils.format_key_text(self.current_start_key)}")
        self.lbl_stop_hk.setText(f"停止: {TextUtils.format_key_text(self.current_stop_key)}")
        self.lbl_bind_hk.setText(f"绑定: {TextUtils.format_key_text(self.current_bind_key)}")
        
        self.apply_hotkeys()
        
        self.spin_loop.setValue(data.get("loop", 1))
        self.chk_tray.setChecked(data.get("minimize_to_tray", False))
        
        self.table.setRowCount(0)
        for a in data.get("actions", []):
            self.add_row_data(a["key"], a["delay"])
            
        if data.get("mode") == "mouse":
            self.rb_mouse.setChecked(True)
            self.spin_m_cps.setValue(data.get("mouse_cps", 5))
        else:
            self.rb_keyboard.setChecked(True)

    def save_current_config(self, filepath):
        data = {
            "start": self.current_start_key,
            "stop": self.current_stop_key,
            "bind": self.current_bind_key,
            "loop": self.spin_loop.value(),
            "actions": self.get_table_data(),
            "mode": "mouse" if self.rb_mouse.isChecked() else "keyboard",
            "mouse_cps": self.spin_m_cps.value(),
            "minimize_to_tray": self.chk_tray.isChecked()
        }
        ConfigManager.save_config(filepath, data)

    # --- 核心修复：关闭事件 ---
    def closeEvent(self, event):
        """窗口关闭事件：决定是最小化还是退出"""
        # 1. 保存配置
        self.save_current_config(DEFAULT_CONFIG_FILE)
        
        # 2. 判断逻辑
        if self.chk_tray.isChecked():
            # 用户选择最小化
            self.hide()
            event.ignore() # 阻止窗口销毁
            self.update_status("程序已最小化到托盘")
        else:
            # 用户选择直接关闭
            self.perform_cleanup()
            event.accept() # 接受关闭事件
            QApplication.quit() # 【核心】显式调用退出，防止托盘导致的进程残留

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()
            self.activateWindow()

    def perform_cleanup(self):
        """退出前的清理"""
        self.executor.stop()
        self.executor.wait()
        try:
            keyboard.unhook_all()
        except: pass

    def quit_app(self):
        """托盘菜单退出"""
        self.save_current_config(DEFAULT_CONFIG_FILE)
        self.perform_cleanup()
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Microsoft YaHei", 9) 
    app.setFont(font)
    
    # 关键设置：关闭最后一个窗口时不退出（为了支持最小化到托盘）
    # 但我们已经在 closeEvent 中手动处理了 quit 逻辑，所以这里设为 False 是安全的
    app.setQuitOnLastWindowClosed(False)
    
    window = AutoKeyApp()
    window.show()
    sys.exit(app.exec())