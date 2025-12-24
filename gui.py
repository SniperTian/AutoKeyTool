# gui.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QLabel, QHeaderView, QAbstractItemView, 
    QSpinBox, QFrame, QRadioButton, QButtonGroup, QComboBox, QStackedWidget,
    QDialog, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
import keyboard
from utils import TextUtils

# --- 录制弹窗保持不变 ---
class KeyRecorderDialog(QDialog):
    sig_key_recorded = pyqtSignal(str)
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
        layout.addWidget(self.lbl_tip)
        
        self.lbl_preview = QLabel("")
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setStyleSheet("font-size: 24px; font-weight: bold; color: #1976D2;")
        layout.addWidget(self.lbl_preview)
        self.setLayout(layout)

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
        modifiers = {'ctrl', 'right ctrl', 'shift', 'right shift', 'alt', 'right alt', 'windows'}
        
        if key_name in modifiers:
            simple_mod = key_name.replace('right ', '')
            self.pressed_modifiers.add(simple_mod)
            self._update_preview()
        else:
            mods = sorted(list(self.pressed_modifiers))
            if mods: result = "+".join(mods + [key_name])
            else: result = key_name
            self.final_key = result
            self.sig_key_recorded.emit(result)
            self.accept()

    def _update_preview(self):
        mods = sorted(list(self.pressed_modifiers))
        text = " + ".join([m.capitalize() for m in mods] + ["..."])
        self.lbl_preview.setText(text)

# --- 热键设置窗口 (保持不变) ---
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

# --- 主界面 ---
class MainWindowUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("AutoKey Pro v3.1")
        self.resize(600, 780)
        # 修复：移除了全局 font-size 设置，解决 Point size <= 0 错误
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI', 'Microsoft YaHei'; } 
            QGroupBox { border: 1px solid #ddd; border-radius: 5px; margin-top: 10px; }
            QPushButton { padding: 6px 12px; border-radius: 4px; background-color: #f5f5f5; border: 1px solid #ccc; }
            QPushButton:hover { background-color: #e0e0e0; }
            QTableWidget { selection-background-color: #BBDEFB; selection-color: black; }
        """)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # 1. 顶部热键显示区 (已修改：增加绑定热键)
        hk_frame = QFrame()
        hk_frame.setStyleSheet("background-color: #FAFAFA; border-radius: 8px; border: 1px solid #DDD;")
        hk_layout = QHBoxLayout(hk_frame)
        
        self.lbl_start_hk = QLabel("启动: F9")
        self.lbl_stop_hk = QLabel("停止: F10")
        self.lbl_bind_hk = QLabel("绑定: F11") # 新增
        
        for lbl in [self.lbl_start_hk, self.lbl_stop_hk, self.lbl_bind_hk]:
            lbl.setStyleSheet("font-weight: bold; color: #333; padding: 4px; margin-right: 10px;")
        
        hk_layout.addWidget(self.lbl_start_hk)
        hk_layout.addWidget(self.lbl_stop_hk)
        hk_layout.addWidget(self.lbl_bind_hk)
        hk_layout.addStretch()
        
        self.btn_mod_hotkey = QPushButton("🛠️ 修改热键")
        self.btn_mod_hotkey.setStyleSheet("background-color: #E3F2FD; color: #1565C0; border: 1px solid #2196F3;")
        hk_layout.addWidget(self.btn_mod_hotkey)
        main_layout.addWidget(hk_frame)

        # 2. 模式选择
        mode_layout = QHBoxLayout()
        self.rb_keyboard = QRadioButton("🎹 键盘自动化")
        self.rb_mouse = QRadioButton("🖱️ 鼠标连点器")
        self.rb_keyboard.setChecked(True)
        mode_grp = QButtonGroup(self)
        mode_grp.addButton(self.rb_keyboard)
        mode_grp.addButton(self.rb_mouse)
        mode_layout.addWidget(self.rb_keyboard)
        mode_layout.addWidget(self.rb_mouse)
        mode_layout.addStretch()
        self.chk_tray = QCheckBox("关闭时最小化到托盘")
        mode_layout.addWidget(self.chk_tray)
        main_layout.addLayout(mode_layout)

        # 3. 堆叠窗口
        self.stack = QStackedWidget()
        
        # Page A: Keyboard
        page_kb = QWidget()
        layout_kb = QVBoxLayout(page_kb)
        win_layout = QHBoxLayout()
        win_layout.addWidget(QLabel("目标窗口:"))
        self.combo_win = QComboBox()
        self.combo_win.addItem("🌐 全局模式 (所有窗口)", 0)
        win_layout.addWidget(self.combo_win, 1)
        self.btn_refresh_win = QPushButton("🔄")
        self.btn_refresh_win.setFixedWidth(40)
        win_layout.addWidget(self.btn_refresh_win)
        layout_kb.addLayout(win_layout)
        
        # 移除旧的 Bind Tip，因为已经做到顶部了
        
        loop_layout = QHBoxLayout()
        loop_layout.addWidget(QLabel("循环次数 (0=无限):"))
        self.spin_loop = QSpinBox()
        self.spin_loop.setRange(0, 999999)
        self.spin_loop.setValue(1)
        loop_layout.addWidget(self.spin_loop)
        loop_layout.addStretch()
        layout_kb.addLayout(loop_layout)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["按键内容", "等待时长 (ms)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.on_table_double_click)
        layout_kb.addWidget(self.table)
        
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

        # Page B: Mouse
        page_mouse = QWidget()
        layout_mouse = QVBoxLayout(page_mouse)
        m_frame = QFrame()
        m_frame.setStyleSheet("background-color: #FFF3E0; border-radius: 8px; border: 1px solid #FFE0B2;")
        m_layout = QVBoxLayout(m_frame)
        
        row_m1 = QHBoxLayout()
        row_m1.addWidget(QLabel("按键类型:"))
        self.combo_m_type = QComboBox()
        self.combo_m_type.addItems(["左键 (Left)", "右键 (Right)"])
        row_m1.addWidget(self.combo_m_type)
        m_layout.addLayout(row_m1)
        
        row_m2 = QHBoxLayout()
        row_m2.addWidget(QLabel("点击方式:"))
        self.combo_m_click = QComboBox()
        self.combo_m_click.addItems(["单击 (Single)", "双击 (Double)"])
        row_m2.addWidget(self.combo_m_click)
        m_layout.addLayout(row_m2)

        row_m3 = QHBoxLayout()
        row_m3.addWidget(QLabel("点击速度:"))
        self.spin_m_cps = QSpinBox() 
        self.spin_m_cps.setRange(1, 100)
        self.spin_m_cps.setValue(5)
        self.spin_m_cps.setSuffix(" 次/秒")
        row_m3.addWidget(self.spin_m_cps)
        m_layout.addLayout(row_m3)
        m_layout.addStretch()
        layout_mouse.addWidget(m_frame)
        layout_mouse.addStretch()
        self.stack.addWidget(page_mouse)
        
        main_layout.addWidget(self.stack)

        # 4. 底部控制
        self.lbl_status = QLabel("系统就绪")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #666; padding: 5px;")
        main_layout.addWidget(self.lbl_status)
        
        ctrl_layout = QHBoxLayout()
        self.btn_start = QPushButton("▶ 开始运行")
        self.btn_start.setFixedHeight(45)
        self.btn_start.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 16px;")
        self.btn_stop = QPushButton("⛔ 停止运行")
        self.btn_stop.setFixedHeight(45)
        self.btn_stop.setStyleSheet("background-color: #F44336; color: white; font-weight: bold; font-size: 16px;")
        self.btn_stop.setEnabled(False)
        ctrl_layout.addWidget(self.btn_start)
        ctrl_layout.addWidget(self.btn_stop)
        main_layout.addLayout(ctrl_layout)

        self.rb_keyboard.toggled.connect(lambda: self.stack.setCurrentIndex(0))
        self.rb_mouse.toggled.connect(lambda: self.stack.setCurrentIndex(1))

    # --- 逻辑占位 ---
    def on_table_double_click(self, row, col):
        if col == 0:
            rec = KeyRecorderDialog(parent=self)
            if rec.exec():
                key = rec.final_key
                self.table.item(row, col).setText(TextUtils.format_key_text(key))
    
    def add_row_data(self, key="a", delay=500):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QTableWidgetItem(TextUtils.format_key_text(key)))
        self.table.setItem(r, 1, QTableWidgetItem(str(delay)))