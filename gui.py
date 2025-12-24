from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QLabel, QHeaderView, QAbstractItemView, 
    QSpinBox, QFrame, QRadioButton, QButtonGroup, QComboBox, QStackedWidget,
    QDialog, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QColor
import keyboard
from utils import TextUtils

# --- 按键录制窗口 ---
class KeyRecorderDialog(QDialog):
    sig_key_recorded = pyqtSignal(str)
    sig_update_preview = pyqtSignal(str)
    sig_close_dialog = pyqtSignal()

    def __init__(self, title="按键录制", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(350, 150)
        self.final_key = None
        self.hook = None
        self.pressed_modifiers = set()
        
        layout = QVBoxLayout()
        self.lbl_tip = QLabel("请按下按键...\n(支持 Ctrl+A 等组合键)")
        self.lbl_tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_tip.setStyleSheet("font-size: 14px; color: #555;")
        layout.addWidget(self.lbl_tip)
        
        self.lbl_preview = QLabel("")
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setStyleSheet("font-size: 24px; font-weight: bold; color: #1976D2;")
        layout.addWidget(self.lbl_preview)
        self.setLayout(layout)

        self.sig_update_preview.connect(self.update_preview_ui)
        self.sig_close_dialog.connect(self.close_dialog_ui)

    def showEvent(self, event):
        self.pressed_modifiers.clear()
        self.hook = keyboard.hook(self._on_key_event)
        super().showEvent(event)

    def closeEvent(self, event):
        if self.hook: keyboard.unhook(self.hook)
        super().closeEvent(event)

    def _on_key_event(self, e):
        if e.event_type == 'up': return
        key_name = e.name.lower()
        modifiers = {'ctrl', 'right ctrl', 'shift', 'right shift', 'alt', 'right alt', 'windows', 'left windows', 'right windows'}
        if key_name in modifiers:
            simple_mod = key_name.replace('right ', '').replace('left ', '').replace(' windows', 'win')
            if simple_mod == 'windows': simple_mod = 'win'
            self.pressed_modifiers.add(simple_mod)
            self._emit_preview_update()
        else:
            mods = sorted(list(self.pressed_modifiers))
            result = "+".join(mods + [key_name]) if mods else key_name
            self.final_key = result
            self.sig_key_recorded.emit(result)
            self.sig_close_dialog.emit()

    def _emit_preview_update(self):
        mods = sorted(list(self.pressed_modifiers))
        text = " + ".join([m.capitalize() for m in mods] + ["..."])
        self.sig_update_preview.emit(text)

    @pyqtSlot(str)
    def update_preview_ui(self, text):
        self.lbl_preview.setText(text)

    @pyqtSlot()
    def close_dialog_ui(self):
        if self.hook:
            keyboard.unhook(self.hook)
            self.hook = None
        self.accept()

# --- 热键设置窗口 ---
class HotkeySettingDialog(QDialog):
    def __init__(self, current_start, current_stop, current_bind, parent=None):
        super().__init__(parent)
        self.setWindowTitle("修改全局热键")
        self.resize(400, 250)
        self.results = {"start": current_start, "stop": current_stop, "bind": current_bind}
        
        layout = QVBoxLayout()
        def create_row(label_text, key_key):
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFixedWidth(120)
            val_lbl = QLabel(TextUtils.format_key_text(self.results[key_key]))
            val_lbl.setStyleSheet("font-weight: bold; border: 1px solid #ccc; padding: 5px; border-radius: 4px;")
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn = QPushButton("修改")
            btn.clicked.connect(lambda: self._record_key(key_key, val_lbl))
            row.addWidget(lbl)
            row.addWidget(val_lbl)
            row.addWidget(btn)
            return row

        layout.addLayout(create_row("🚀 启动热键:", "start"))
        layout.addLayout(create_row("⛔ 停止热键:", "stop"))
        layout.addLayout(create_row("📌 绑定热键:", "bind"))
        
        btn_box = QHBoxLayout()
        btn_ok = QPushButton("保存并关闭")
        btn_ok.clicked.connect(self.accept)
        btn_box.addStretch()
        btn_box.addWidget(btn_ok)
        layout.addStretch()
        layout.addLayout(btn_box)
        self.setLayout(layout)

    def _record_key(self, key_key, label_widget):
        rec = KeyRecorderDialog(title=f"录制新热键", parent=self)
        if rec.exec():
            new_key = rec.final_key
            if new_key:
                self.results[key_key] = new_key
                label_widget.setText(TextUtils.format_key_text(new_key))

# --- 主界面 UI ---
class MainWindowUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("AutoKey Tool")
        self.resize(600, 780)
        
        # 整体 UI 样式优化
        self.setStyleSheet("""
            QWidget { 
                font-family: 'Segoe UI', 'Microsoft YaHei'; 
                color: #333;
            } 
            QGroupBox { 
                border: 1px solid #ddd; 
                border-radius: 5px; 
                margin-top: 10px; 
            }
            QPushButton { 
                padding: 6px 12px; 
                border-radius: 4px; 
                background-color: #f5f5f5; 
                border: 1px solid #ccc; 
            }
            QPushButton:hover { 
                background-color: #e0e0e0; 
            }
            /* 表格样式 */
            QTableWidget { 
                selection-background-color: #1976D2; 
                selection-color: white; 
                gridline-color: #E0E0E0;
                alternate-background-color: #F9F9F9;
                border: 1px solid #ddd;
            }
            /* 输入框和下拉框统一样式 */
            QComboBox, QSpinBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                min-height: 25px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            /* 【修复】移除了对 QSpinBox::up-button 的自定义样式
               这会恢复系统默认的箭头显示，解决“看不见箭头”的问题
            */
        """)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        self.setLayout(main_layout)

        # 1. 顶部热键栏
        hk_frame = QFrame()
        hk_frame.setStyleSheet("background-color: #F5F5F5; border-radius: 6px; border: 1px solid #DDD;")
        hk_layout = QHBoxLayout(hk_frame)
        self.lbl_start_hk = QLabel("启动: F9")
        self.lbl_stop_hk = QLabel("停止: F10")
        self.lbl_bind_hk = QLabel("绑定: F11")
        for lbl in [self.lbl_start_hk, self.lbl_stop_hk, self.lbl_bind_hk]:
            lbl.setStyleSheet("font-weight: bold; color: #424242; padding: 4px; margin-right: 10px;")
        hk_layout.addWidget(self.lbl_start_hk)
        hk_layout.addWidget(self.lbl_stop_hk)
        hk_layout.addWidget(self.lbl_bind_hk)
        hk_layout.addStretch()
        self.btn_mod_hotkey = QPushButton("🛠️ 修改热键")
        self.btn_mod_hotkey.setStyleSheet("""
            QPushButton { background-color: #E3F2FD; color: #1565C0; border: 1px solid #90CAF9; font-weight: bold; }
            QPushButton:hover { background-color: #BBDEFB; }
        """)
        hk_layout.addWidget(self.btn_mod_hotkey)
        main_layout.addWidget(hk_frame)

        # 2. 模式选择 (新增：操作录制)
        mode_layout = QHBoxLayout()
        
        self.rb_keyboard = QRadioButton("🎹 键盘自动化")
        self.rb_mouse = QRadioButton("🖱️ 鼠标连点器")
        self.rb_record = QRadioButton("🔴 操作录制") # 新增功能
        
        self.rb_keyboard.setChecked(True)
        
        # 字体加粗
        font_mode = QFont(); font_mode.setBold(True); font_mode.setPointSize(10)
        for rb in [self.rb_keyboard, self.rb_mouse, self.rb_record]:
            rb.setFont(font_mode)
        
        mode_grp = QButtonGroup(self)
        mode_grp.addButton(self.rb_keyboard)
        mode_grp.addButton(self.rb_mouse)
        mode_grp.addButton(self.rb_record)
        
        mode_layout.addWidget(self.rb_keyboard)
        mode_layout.addSpacing(15)
        mode_layout.addWidget(self.rb_mouse)
        mode_layout.addSpacing(15)
        mode_layout.addWidget(self.rb_record)
        
        mode_layout.addStretch()
        self.chk_tray = QCheckBox("关闭时最小化到托盘")
        mode_layout.addWidget(self.chk_tray)
        main_layout.addLayout(mode_layout)

        # 3. 堆叠页面
        self.stack = QStackedWidget()
        
        # --- Page A: 键盘 ---
        page_kb = QWidget()
        layout_kb = QVBoxLayout(page_kb)
        layout_kb.setContentsMargins(0, 5, 0, 0)
        
        # 窗口选择
        win_layout = QHBoxLayout()
        win_layout.addWidget(QLabel("目标窗口:"))
        self.combo_win = QComboBox()
        self.combo_win.addItem("🌐 全局模式 (所有窗口)", 0)
        win_layout.addWidget(self.combo_win, 1)
        self.btn_refresh_win = QPushButton("🔄")
        self.btn_refresh_win.setFixedWidth(40)
        win_layout.addWidget(self.btn_refresh_win)
        layout_kb.addLayout(win_layout)
        
        # 循环设置
        loop_layout = QHBoxLayout()
        loop_layout.addWidget(QLabel("循环次数 (0=无限):"))
        self.spin_loop = QSpinBox()
        self.spin_loop.setRange(0, 999999)
        self.spin_loop.setValue(1)
        self.spin_loop.setFixedWidth(100)
        loop_layout.addWidget(self.spin_loop)
        
        lbl_hint = QLabel("💡 点击选中对应行 / 双击修改单元格内容 💡")
        lbl_hint.setStyleSheet("color: #757575; font-size: 12px; margin-left: 10px;")
        loop_layout.addWidget(lbl_hint)
        loop_layout.addStretch()
        layout_kb.addLayout(loop_layout)

        # 表格
        self.table = QTableWidget(0, 3) 
        self.table.setHorizontalHeaderLabels(["序号", "按键内容", "等待时长 (ms)"])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)   
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) 
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)   
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 110)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.on_table_double_click)
        layout_kb.addWidget(self.table)
        
        # 编辑按钮
        tb_btns = QHBoxLayout()
        self.btn_add = QPushButton("➕ 添加")
        self.btn_del = QPushButton("➖ 删除")
        self.btn_up = QPushButton("⬆️ 上移")
        self.btn_down = QPushButton("⬇️ 下移")
        tb_btns.addWidget(self.btn_add)
        tb_btns.addWidget(self.btn_del)
        tb_btns.addWidget(self.btn_up)
        tb_btns.addWidget(self.btn_down)
        layout_kb.addLayout(tb_btns)
        self.stack.addWidget(page_kb)

        # --- Page B: 鼠标 ---
        page_mouse = QWidget()
        layout_mouse = QVBoxLayout(page_mouse)
        layout_mouse.setContentsMargins(0, 20, 0, 0)
        
        m_frame = QFrame()
        m_frame.setStyleSheet("""
            QFrame { 
                background-color: #FFFFFF; 
                border: 1px solid #E0E0E0; 
                border-radius: 8px; 
            }
            QLabel { font-size: 14px; font-weight: bold; color: #424242; }
        """)
        m_layout = QVBoxLayout(m_frame)
        m_layout.setSpacing(20)
        m_layout.setContentsMargins(30, 30, 30, 30)
        
        row_m1 = QHBoxLayout()
        row_m1.addWidget(QLabel("🖱️ 按键类型:"))
        self.combo_m_type = QComboBox()
        self.combo_m_type.addItems(["左键 (Left)", "右键 (Right)"])
        self.combo_m_type.setMinimumHeight(35)
        row_m1.addWidget(self.combo_m_type)
        m_layout.addLayout(row_m1)
        
        row_m2 = QHBoxLayout()
        row_m2.addWidget(QLabel("⚡ 点击方式:"))
        self.combo_m_click = QComboBox()
        self.combo_m_click.addItems(["单击 (Single)", "双击 (Double)"])
        self.combo_m_click.setMinimumHeight(35)
        row_m2.addWidget(self.combo_m_click)
        m_layout.addLayout(row_m2)

        row_m3 = QHBoxLayout()
        row_m3.addWidget(QLabel("🚀 点击速度 (次/秒):"))
        
        # 整数框，恢复默认样式以显示箭头
        self.spin_m_cps = QSpinBox()
        self.spin_m_cps.setRange(1, 1000)
        self.spin_m_cps.setValue(100)
        self.spin_m_cps.setMinimumHeight(35)
        
        row_m3.addWidget(self.spin_m_cps)
        m_layout.addLayout(row_m3)
        
        m_layout.addStretch()
        layout_mouse.addWidget(m_frame)
        
        lbl_mouse_hint = QLabel("（💡 提示：鼠标连点与键盘自动化共享启动/停止热键）")
        lbl_mouse_hint.setStyleSheet("color: #757575; font-size: 12px; margin-top: 10px;")
        lbl_mouse_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_mouse.addWidget(lbl_mouse_hint)
        
        layout_mouse.addStretch()
        self.stack.addWidget(page_mouse)

        # --- Page C: 操作录制 (新增) ---
        page_record = QWidget()
        layout_rec = QVBoxLayout(page_record)
        
        lbl_coming_soon = QLabel("To be continued...")
        lbl_coming_soon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_coming_soon.setStyleSheet("font-size: 36px; font-weight: bold; color: #BDBDBD;")
        
        layout_rec.addStretch()
        layout_rec.addWidget(lbl_coming_soon)
        layout_rec.addStretch()
        
        self.stack.addWidget(page_record)
        
        main_layout.addWidget(self.stack)

        # 4. 底部控制
        self.lbl_status = QLabel("系统就绪")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #757575; font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(self.lbl_status)
        
        ctrl_layout = QHBoxLayout()
        self.btn_start = QPushButton("▶ 开始运行")
        self.btn_start.setFixedHeight(50)
        self.btn_start.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; font-weight: bold; font-size: 16px; border: none; border-radius: 6px; }
            QPushButton:hover { background-color: #43A047; }
            QPushButton:disabled { background-color: #E0E0E0; color: #9E9E9E; }
        """)
        
        self.btn_stop = QPushButton("⛔ 停止运行")
        self.btn_stop.setFixedHeight(50)
        self.btn_stop.setStyleSheet("""
            QPushButton { background-color: #F44336; color: white; font-weight: bold; font-size: 16px; border: none; border-radius: 6px; }
            QPushButton:hover { background-color: #E53935; }
            QPushButton:disabled { background-color: #E0E0E0; color: #9E9E9E; }
        """)
        self.btn_stop.setEnabled(False)
        
        ctrl_layout.addWidget(self.btn_start)
        ctrl_layout.addSpacing(15)
        ctrl_layout.addWidget(self.btn_stop)
        main_layout.addLayout(ctrl_layout)

        # 5. 文件操作
        file_layout = QHBoxLayout()
        self.btn_save = QPushButton("💾 保存配置")
        self.btn_load = QPushButton("📂 加载配置")
        
        for btn, color, hover in [(self.btn_save, "#2196F3", "#1E88E5"), (self.btn_load, "#FF9800", "#FB8C00")]:
            btn.setFixedHeight(45)
            btn.setStyleSheet(f"""
                QPushButton {{ background-color: {color}; color: white; font-weight: bold; font-size: 15px; border: none; border-radius: 6px; }}
                QPushButton:hover {{ background-color: {hover}; }}
            """)
        
        file_layout.addWidget(self.btn_save)
        file_layout.addSpacing(15)
        file_layout.addWidget(self.btn_load)
        main_layout.addLayout(file_layout)

        # 页面切换逻辑：操作录制模式下禁用开始按钮
        self.rb_keyboard.toggled.connect(lambda: self._switch_page(0))
        self.rb_mouse.toggled.connect(lambda: self._switch_page(1))
        self.rb_record.toggled.connect(lambda: self._switch_page(2))

    def _switch_page(self, index):
        """切换页面并处理按钮状态"""
        self.stack.setCurrentIndex(index)
        # 如果是“操作录制”模式 (index=2)，禁用开始按钮
        if index == 2:
            self.btn_start.setEnabled(False)
            self.lbl_status.setText("此模式开发中...")
        else:
            self.btn_start.setEnabled(True)
            self.lbl_status.setText("系统就绪")

    # --- 逻辑占位 ---
    def on_table_double_click(self, row, col):
        pass
    
    def add_row_data(self, key="a", delay=500):
        pass