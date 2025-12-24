import sys
import os
import json
import ctypes
import keyboard
from PyQt6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QMessageBox, QFileDialog, QTableWidgetItem, QInputDialog)
from PyQt6.QtGui import QIcon, QAction, QFont
from PyQt6.QtCore import QTimer, pyqtSignal, pyqtSlot, Qt

from gui import MainWindowUI, HotkeySettingDialog
from executor import TaskExecutor
from hotkey import HotkeyManager
from config import ConfigManager
from utils import WindowMgr, TextUtils, IconUtils

DEFAULT_CONFIG_FILE = "default_config.json"

class AutoKeyApp(MainWindowUI):
    sig_bind_window = pyqtSignal(int, str)

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

        self.sig_bind_window.connect(self.on_bind_window_signal)

    def bind_events(self):
        self.btn_mod_hotkey.clicked.connect(self.open_hotkey_settings)
        self.btn_add.clicked.connect(lambda: self.add_row_data("a", 1000))
        self.btn_del.clicked.connect(self.remove_row)
        self.btn_up.clicked.connect(self.move_up)
        self.btn_down.clicked.connect(self.move_down)
        self.btn_refresh_win.clicked.connect(self.refresh_windows)
        self.btn_start.clicked.connect(self.start_task)
        self.btn_stop.clicked.connect(self.stop_task)
        
        # 绑定保存与加载按钮
        self.btn_save.clicked.connect(self.handle_save_file)
        self.btn_load.clicked.connect(self.handle_load_file)
        
        self.executor.sig_progress.connect(self.update_status)
        self.executor.sig_finished.connect(self.on_finished)
        self.hotkey_mgr.sig_start.connect(self.start_task)
        self.hotkey_mgr.sig_stop.connect(self.stop_task)
        self.hotkey_mgr.sig_bind.connect(self.do_bind_window)

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

    def apply_hotkeys(self):
        ok, msg = self.hotkey_mgr.register_hotkeys(
            self.current_start_key, 
            self.current_stop_key, 
            self.current_bind_key
        )
        self.update_status(msg)

    def do_bind_window(self):
        try:
            hwnd, title = WindowMgr.get_foreground_window_info()
            if title and "AutoKey Pro" in title:
                self.update_status("⚠️ 提示: 你绑定了本程序窗口")
            if hwnd:
                self._bind_window_ui(hwnd, title)
            else:
                self.update_status("⚠️ 未检测到有效窗口句柄")
        except Exception as e:
            self.update_status(f"❌ 绑定出错: {e}")

    def _bind_window_ui(self, hwnd, title):
        display_title = title if title and title.strip() else "无标题窗口"
        idx = self.combo_win.findData(hwnd)
        if idx == -1:
            self.combo_win.addItem(f"[{hwnd}] {display_title[:25]}...", hwnd)
            idx = self.combo_win.count() - 1
        self.combo_win.setCurrentIndex(idx)
        self.update_status(f"✅ 已绑定: [{hwnd}] {display_title[:15]}...")
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("绑定成功")
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setText(f"目标窗口已锁定！\n\n句柄ID: {hwnd}\n窗口名: {display_title}\n\n现在您可以最小化该窗口，按 {TextUtils.format_key_text(self.current_start_key)} 开始后台挂机。")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        msg_box.exec()

    @pyqtSlot(int, str)
    def on_bind_window_signal(self, hwnd, title):
        self._bind_window_ui(hwnd, title)

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

    def register_bind_hotkey(self):
        # 兼容性方法，实际由 apply_hotkeys 统一处理
        pass

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

    def update_status(self, msg):
        self.lbl_status.setText(msg)

    # --- 表格逻辑 ---
    def get_table_data(self):
        data = []
        for r in range(self.table.rowCount()):
            k_text = self.table.item(r, 1).text()
            d_text = self.table.item(r, 2).text()
            data.append({"key": k_text, "delay": int(d_text)})
        return data

    def add_row_data(self, key="a", delay=500):
        r = self.table.rowCount()
        self.table.insertRow(r)
        
        item_idx = QTableWidgetItem(str(r + 1))
        item_idx.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(r, 0, item_idx)

        item_key = QTableWidgetItem(TextUtils.format_key_text(key))
        item_key.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(r, 1, item_key)

        item_delay = QTableWidgetItem(str(delay))
        item_delay.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(r, 2, item_delay)

    def renumber_rows(self):
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item: item.setText(str(r + 1))

    def remove_row(self):
        r = self.table.currentRow()
        if r >= 0:
            self.table.removeRow(r)
            self.renumber_rows()
        
    def move_up(self):
        r = self.table.currentRow()
        if r > 0: self.swap_row(r, r-1)

    def move_down(self):
        r = self.table.currentRow()
        if r < self.table.rowCount()-1: self.swap_row(r, r+1)
        
    def swap_row(self, r1, r2):
        k1 = self.table.item(r1, 1).text(); d1 = self.table.item(r1, 2).text()
        k2 = self.table.item(r2, 1).text(); d2 = self.table.item(r2, 2).text()
        self.table.item(r1, 1).setText(k2); self.table.item(r1, 2).setText(d2)
        self.table.item(r2, 1).setText(k1); self.table.item(r2, 2).setText(d1)
        self.table.selectRow(r2)

    def on_table_double_click(self, row, col):
        if col == 1:
            from gui import KeyRecorderDialog
            rec = KeyRecorderDialog(parent=self)
            if rec.exec():
                key = rec.final_key
                item = QTableWidgetItem(TextUtils.format_key_text(key))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)
        elif col == 2:
            current_val = self.table.item(row, col).text()
            try: val_int = int(current_val)
            except: val_int = 1000
            new_val, ok = QInputDialog.getInt(self, "修改延时", "请输入等待时长(ms):", val_int, 0, 100000, 100)
            if ok:
                item = QTableWidgetItem(str(new_val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

    def refresh_windows(self):
        current_idx = self.combo_win.currentIndex()
        self.combo_win.clear()
        self.combo_win.addItem("🌐 全局模式 (前台)", 0)
        wins = WindowMgr.get_window_list()
        for hwnd, title in wins:
            display_title = title if title else "无标题窗口"
            self.combo_win.addItem(f"[{hwnd}] {display_title[:20]}...", hwnd)
        if current_idx > 0 and current_idx < self.combo_win.count():
            self.combo_win.setCurrentIndex(current_idx)

    # --- 配置管理逻辑 ---

    def load_startup_config(self):
        """加载或创建默认配置"""
        if not os.path.exists(DEFAULT_CONFIG_FILE):
            default_data = {
                "start": "f9", "stop": "f10", "bind": "f11", 
                "loop": 0, 
                "actions": [
                    {"key": "A", "delay": 1000}, 
                    {"key": "S", "delay": 1000}, 
                    {"key": "D", "delay": 1000}
                ],
                "mode": "keyboard", "mouse_cps": 5, "minimize_to_tray": False
            }
            ConfigManager.save_config(DEFAULT_CONFIG_FILE, default_data)
        
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
        self.spin_loop.setValue(data.get("loop", 0))
        self.chk_tray.setChecked(data.get("minimize_to_tray", False))
        
        self.table.setRowCount(0)
        for a in data.get("actions", []):
            self.add_row_data(a["key"], a["delay"])
            
        if data.get("mode") == "mouse":
            self.rb_mouse.setChecked(True)
            self.spin_m_cps.setValue(data.get("mouse_cps", 5))
        else:
            self.rb_keyboard.setChecked(True)

    def _get_current_config_dict(self):
        return {
            "start": self.current_start_key,
            "stop": self.current_stop_key,
            "bind": self.current_bind_key,
            "loop": self.spin_loop.value(),
            "actions": self.get_table_data(),
            "mode": "mouse" if self.rb_mouse.isChecked() else "keyboard",
            "mouse_cps": self.spin_m_cps.value(),
            "minimize_to_tray": self.chk_tray.isChecked()
        }

    # 【修复】重新添加 save_current_config 方法
    def save_current_config(self, filepath):
        data = self._get_current_config_dict()
        ConfigManager.save_config(filepath, data)

    def handle_save_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存配置", "config.json", "JSON Files (*.json)")
        if path:
            if not path.lower().endswith(".json"):
                path += ".json"
            self.save_current_config(path)
            self.update_status(f"配置已保存: {os.path.basename(path)}")

    def handle_load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "加载配置", "", "JSON Files (*.json)")
        if path:
            data, msg = ConfigManager.load_config(path)
            if data:
                self.restore_ui_from_data(data)
                self.update_status(f"配置已加载: {os.path.basename(path)}")
            else:
                QMessageBox.critical(self, "加载失败", msg)

    # --- 生命周期 ---
    def closeEvent(self, event):
        self.save_current_config(DEFAULT_CONFIG_FILE)
        if self.chk_tray.isChecked():
            self.hide()
            event.ignore()
            self.update_status("程序已最小化到托盘")
        else:
            self.perform_cleanup()
            event.accept()
            QApplication.quit()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()
            self.activateWindow()

    def perform_cleanup(self):
        self.executor.stop()
        self.executor.wait()
        try: keyboard.unhook_all()
        except: pass

    def quit_app(self):
        self.save_current_config(DEFAULT_CONFIG_FILE)
        self.perform_cleanup()
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Microsoft YaHei", 9) 
    app.setFont(font)
    app.setQuitOnLastWindowClosed(False)
    window = AutoKeyApp()
    window.show()
    sys.exit(app.exec())