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
from utils import WindowMgr, TextUtils, IconUtils # 引入 IconUtils

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
        self.init_tray() # 初始化托盘
        
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
        
        # 修复 1: 设置生成的图标，解决 setVisible 报错和托盘隐形问题
        icon_pixmap = IconUtils.create_default_icon()
        self.tray_icon.setIcon(QIcon(icon_pixmap))
        
        menu = QMenu()
        action_show = QAction("显示主界面", self)
        action_quit = QAction("退出程序", self)
        
        action_show.triggered.connect(self.showNormal)
        action_quit.triggered.connect(self.quit_app) # 连接到自定义退出
        
        menu.addAction(action_show)
        menu.addAction(action_quit)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        
        self.tray_icon.activated.connect(self.on_tray_activated)

    def register_bind_hotkey(self):
        try: keyboard.remove_hotkey(self.do_bind_window)
        except: pass
        try: keyboard.add_hotkey(self.current_bind_key, self.do_bind_window)
        except Exception as e: self.update_status(f"绑定热键注册失败: {e}")

    def do_bind_window(self):
        hwnd, title = WindowMgr.get_foreground_window_info()
        if title and "AutoKey Pro" not in title:
            idx = self.combo_win.findData(hwnd)
            if idx == -1:
                self.combo_win.addItem(f"[{hwnd}] {title[:20]}...", hwnd)
                idx = self.combo_win.count() - 1
            QTimer.singleShot(0, lambda: self._select_window_safe(idx, title))

    def _select_window_safe(self, idx, title):
        self.combo_win.setCurrentIndex(idx)
        self.update_status(f"已绑定: {title[:15]}...")

    def open_hotkey_settings(self):
        dlg = HotkeySettingDialog(self.current_start_key, self.current_stop_key, self.current_bind_key, self)
        if dlg.exec():
            self.current_start_key = dlg.results['start']
            self.current_stop_key = dlg.results['stop']
            self.current_bind_key = dlg.results['bind']
            
            # 更新顶部标签
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

    # --- 修复 2 & 3: 生命周期管理 ---
    def closeEvent(self, event):
        # 无论如何先保存配置
        self.save_current_config(DEFAULT_CONFIG_FILE)
        
        # 检查是否应该最小化
        if self.chk_tray.isChecked():
            if self.tray_icon.isVisible():
                self.hide() # 只是隐藏窗口
                # 注意：不要调用 event.ignore() 除非你确定不希望窗口销毁
                # 在 PyQt 中，如果 hide() 了，ignore() 是合理的
                event.ignore()
                self.update_status("已最小化到托盘")
                return

        # 如果不最小化，或者托盘不可用，则执行真正的退出清理
        self.perform_cleanup()
        event.accept()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()
            self.activateWindow()

    def perform_cleanup(self):
        """执行彻底的清理操作，防止进程残留"""
        self.executor.stop()
        self.executor.wait() # 等待线程结束
        
        # 关键修复: 卸载 keyboard 所有的钩子
        # 否则 Python 进程会因为 keyboard 的后台线程而无法退出
        try:
            keyboard.unhook_all()
        except:
            pass

    def quit_app(self):
        """托盘菜单点击退出时调用"""
        self.save_current_config(DEFAULT_CONFIG_FILE)
        self.perform_cleanup()
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 修复 Font 报错：设置全局字体大小
    font = QFont("Microsoft YaHei", 9) 
    app.setFont(font)
    
    # 确保窗口关闭时不直接退出 App (配合托盘使用)
    app.setQuitOnLastWindowClosed(False)
    
    window = AutoKeyApp()
    window.show()
    sys.exit(app.exec())