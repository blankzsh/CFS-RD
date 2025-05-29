#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CFS Team Editor - An application for managing and editing football team data.
Author: 卡尔纳斯
Version: 2.0.0 (PySide6 Refactored Version)
"""

import json
import logging
import os
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QImage, QFont, QColor, QPalette
from PySide6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QFormLayout, QFrame, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QSplitter, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget, QGraphicsDropShadowEffect
)
from qt_material import apply_stylesheet

# Constants
APP_TITLE = "CFS球队编辑器 BY.卡尔纳斯"
DEFAULT_WINDOW_SIZE = (1100, 750)
MIN_WINDOW_SIZE = (900, 650)
ICON_PATH = "favicon.ico"
LOGO_SIZE = (128, 128)

# Modern color scheme
COLORS = {
    "primary": "#1E88E5",         # 主色调蓝色
    "primary_dark": "#1565C0",    # 深蓝色
    "primary_light": "#42A5F5",   # 浅蓝色
    "secondary": "#455A64",       # 深灰蓝色
    "secondary_light": "#607D8B", # 浅灰蓝色
    "accent": "#29B6F6",          # 亮蓝色强调色
    "background": "#F5F7FA",      # 浅灰背景色
    "card": "#FFFFFF",            # 白色卡片
    "text": "#263238",            # 深色文本
    "light_text": "#546E7A",      # 浅色文本
    "divider": "#ECEFF1",         # 分隔线
    "border": "#E0E0E0",          # 边框颜色
    "hover": "#E3F2FD",           # 悬停背景
    "error": "#EF5350",           # 错误红色
    "warning": "#FFA726",         # 警告橙色
    "success": "#66BB6A",         # 成功绿色
    "info": "#29B6F6",            # 信息蓝色
    "shadow": "rgba(0, 0, 0, 0.1)",# 阴影颜色
    "disabled": "#BDBDBD",        # 禁用状态颜色
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("team_editor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TeamEditor")


def create_horizontal_line():
    """Create a horizontal separator line."""
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    line.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px;")
    return line


def apply_shadow(widget, radius=6, x_offset=0, y_offset=3, color=QColor(0, 0, 0, 20)):
    """为控件添加阴影效果。"""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(radius)
    shadow.setXOffset(x_offset)
    shadow.setYOffset(y_offset)
    shadow.setColor(color)
    widget.setGraphicsEffect(shadow)


def create_default_icon():
    """创建默认应用图标文件，如果图标不存在的话。"""
    if os.path.exists(ICON_PATH):
        return

    try:
        # 创建一个简单的32x32蓝色图标
        icon_size = 32
        icon_image = QImage(icon_size, icon_size, QImage.Format_ARGB32)
        
        # 设置背景色为透明
        icon_image.fill(QColor(0, 0, 0, 0))
        
        # 填充简单的蓝色背景
        for y in range(icon_size):
            for x in range(icon_size):
                # 计算到中心的距离
                dx = x - icon_size/2
                dy = y - icon_size/2
                dist = (dx*dx + dy*dy) ** 0.5
                
                # 绘制一个简单的圆形图标
                if dist <= icon_size/2:
                    icon_image.setPixelColor(x, y, QColor(COLORS['primary']))
        
        # 保存图标
        icon_image.save(ICON_PATH)
        logger.info(f"已创建默认图标: {ICON_PATH}")
    except Exception as e:
        logger.error(f"创建默认图标失败: {e}")
        # 创建图标失败不是致命错误，可以继续运行


class TeamRecord:
    """Team record data class."""

    def __init__(self, record_data: tuple):
        """Initialize team data from database record."""
        self.id = record_data[0]
        self.name = record_data[1]
        self.wealth = record_data[2]
        self.found_year = record_data[3]
        self.location = record_data[4]
        self.supporter_count = record_data[5]
        self.stadium_name = record_data[6]
        self.nickname = record_data[7]
        self.league_id = record_data[8]

    def __str__(self) -> str:
        """Return string representation of the team."""
        return f"{self.name} (ID: {self.id})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert team record to dictionary."""
        return {
            "ID": self.id,
            "TeamName": self.name,
            "TeamWealth": self.wealth,
            "TeamFoundYear": self.found_year,
            "TeamLocation": self.location,
            "SupporterCount": self.supporter_count,
            "StadiumName": self.stadium_name,
            "Nickname": self.nickname,
            "BelongingLeague": self.league_id
        }

    def as_search_string(self) -> str:
        """Return string used for searching."""
        return f"{self.id}{self.name}{self.wealth}{self.found_year}{self.location}{self.supporter_count}{self.stadium_name}{self.nickname}{self.league_id}"


class StaffRecord:
    """Staff record data class."""

    def __init__(self, record_data: tuple):
        """Initialize staff data from database record."""
        self.id = record_data[0]
        self.name = record_data[1]
        self.ability_json = record_data[2]
        self.fame = record_data[3]
        self.team_id = record_data[4]

    def get_ability(self) -> int:
        """Parse ability value from JSON."""
        try:
            ability_data = json.loads(self.ability_json)
            return ability_data.get('rawAbility', 0)
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            logger.error(f"Failed to parse ability JSON: {e}")
            return 0

    def update_ability(self, new_ability: int) -> str:
        """Update ability value JSON."""
        return json.dumps({"rawAbility": int(new_ability)})


class StaffEditDialog(QDialog):
    """员工信息编辑对话框。"""

    def __init__(self, parent, staff_record: StaffRecord, update_callback):
        super().__init__(parent)
        self.staff_record = staff_record
        self.update_callback = update_callback

        self.setWindowTitle(f"编辑员工 - {staff_record.name}")
        self.setMinimumSize(480, 320)
        self.setObjectName("staffEditDialog")

        # 设置对话框样式
        self.setStyleSheet(f"""
            #staffEditDialog {{
                background-color: {COLORS['background']};
                border-radius: 10px;
            }}
            QLabel {{
                color: {COLORS['text']};
            }}
            QLineEdit {{
                padding: 10px;
                border-radius: 4px;
                border: 1px solid {COLORS['border']};
                background-color: {COLORS['card']};
                selection-background-color: {COLORS['primary']};
                selection-color: white;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS['primary']};
                background-color: #F8FDFF;
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                border: none;
                min-width: 100px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
            QPushButton[class="secondary"] {{
                background-color: {COLORS['secondary']};
            }}
            QPushButton[class="secondary"]:hover {{
                background-color: #455A64;
            }}
            #titleCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_dark']});
                border-radius: 8px;
                color: white;
            }}
            #contentCard {{
                background-color: {COLORS['card']};
                border-radius: 8px;
                border: 1px solid {COLORS['border']};
            }}
        """)

        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题卡片
        title_card = QWidget()
        title_card.setObjectName("titleCard")
        apply_shadow(title_card)
        
        title_layout = QHBoxLayout(title_card)
        title_layout.setContentsMargins(15, 12, 15, 12)
        
        # 标题标签
        title_label = QLabel("<span style='font-size:14px; font-weight:bold;'>编辑员工信息</span>")
        title_label.setStyleSheet("color: white;")
        title_layout.addWidget(title_label)
        
        # ID标签
        id_label = QLabel(f"ID: {staff_record.id}")
        id_label.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 12px;")
        title_layout.addWidget(id_label, alignment=Qt.AlignRight)
        
        layout.addWidget(title_card)

        # 内容卡片
        content_card = QWidget()
        content_card.setObjectName("contentCard")
        apply_shadow(content_card)
        
        # 表单布局
        form_layout = QFormLayout(content_card)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # 表单标签样式
        label_style = f"color: {COLORS['text']}; font-weight: bold; font-size: 13px;"

        # 输入框
        self.name_edit = QLineEdit(staff_record.name)
        self.ability_edit = QLineEdit(str(staff_record.get_ability()))
        self.fame_edit = QLineEdit(str(staff_record.fame))
        
        # 设置输入框样式
        input_widgets = [self.name_edit, self.ability_edit, self.fame_edit]
        for widget in input_widgets:
            widget.setMinimumWidth(280)
        
        # 添加表单项
        name_label = QLabel("姓名:")
        name_label.setStyleSheet(label_style)
        form_layout.addRow(name_label, self.name_edit)
        
        ability_label = QLabel("能力值:")
        ability_label.setStyleSheet(label_style)
        form_layout.addRow(ability_label, self.ability_edit)
        
        fame_label = QLabel("知名度:")
        fame_label.setStyleSheet(label_style)
        form_layout.addRow(fame_label, self.fame_edit)

        # 添加提示信息
        hint_label = QLabel("提示: 能力值与知名度必须为正整数")
        hint_label.setStyleSheet(f"color: {COLORS['light_text']}; font-style: italic; font-size: 11px;")
        hint_label.setAlignment(Qt.AlignCenter)
        form_layout.addRow("", hint_label)

        layout.addWidget(content_card)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.setProperty("class", "secondary")
        cancel_button.setMinimumWidth(100)
        
        # 保存按钮
        save_button = QPushButton("保存")
        save_button.setMinimumWidth(100)

        # 绑定按钮事件
        save_button.clicked.connect(self.save_changes)
        cancel_button.clicked.connect(self.reject)

        # 添加到布局
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)

        # 设置初始焦点
        self.name_edit.setFocus()
        
    def save_changes(self):
        """保存员工信息更改。"""
        try:
            # 获取输入值
            new_name = self.name_edit.text().strip()
            new_ability_str = self.ability_edit.text().strip()
            new_fame_str = self.fame_edit.text().strip()

            # 验证姓名不能为空
            if not new_name:
                QMessageBox.critical(self, "错误", "姓名不能为空")
                self.name_edit.setFocus()
                return

            # 验证数值输入
            try:
                new_ability = int(new_ability_str)
                if new_ability < 0:
                    raise ValueError("能力值必须为正数")
            except ValueError:
                QMessageBox.critical(self, "错误", "能力值必须为有效的整数")
                self.ability_edit.setFocus()
                return

            try:
                new_fame = int(new_fame_str)
                if new_fame < 0:
                    raise ValueError("知名度必须为正数")
            except ValueError:
                QMessageBox.critical(self, "错误", "知名度必须为有效的整数")
                self.fame_edit.setFocus()
                return

            # 调用更新回调
            self.update_callback(
                self.staff_record.id,
                new_name,
                new_ability,
                new_fame
            )

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新失败: {str(e)}")


class TeamDatabaseViewer(QMainWindow):
    """CFS Team Database Viewer and Editor."""

    def __init__(self):
        """初始化应用程序。"""
        super().__init__()

        # 设置应用程序基本属性
        self.setWindowTitle(APP_TITLE)
        self.resize(*DEFAULT_WINDOW_SIZE)
        self.setMinimumSize(*MIN_WINDOW_SIZE)

        # 设置应用程序样式
        self.setup_style()

        # 设置图标
        self._set_application_icon()

        # 初始化数据
        self._init_data()

        # 创建界面
        self._create_widgets()
        self._create_layout()
        self._connect_signals()

        # 设置初始状态栏消息
        self.statusBar().showMessage("就绪")
        self.statusBar().setStyleSheet(f"font-weight: normal;")

        logger.info("应用程序已启动")

    def setup_style(self):
        """设置全局应用样式。"""
        font_family = "Microsoft YaHei, Segoe UI, Arial, sans-serif"
        self.setStyleSheet(f"""
            QMainWindow, QDialog, QMessageBox, QScrollArea, QWidget {{
                background-color: {COLORS['background']};
                font-family: {font_family};
                font-size: 12px;
                color: {COLORS['text']};
            }}
            QGroupBox {{
                background-color: {COLORS['card']};
                border-radius: 8px;
                border: none;
                margin-top: 20px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QLabel {{
                background-color: transparent;
            }}
            QListWidget, QTreeWidget {{
                background-color: {COLORS['card']};
                border-radius: 6px;
                border: none;
                outline: none;
                padding: 5px;
                selection-background-color: {COLORS['primary']};
                selection-color: white;
            }}
            QListWidget::item, QTreeWidget::item {{
                padding: 8px;
                border-radius: 4px;
                margin: 2px 0px;
                transition: background-color 0.3s;
            }}
            QListWidget::item:hover, QTreeWidget::item:hover {{
                background-color: {COLORS['hover']};
            }}
            QListWidget::item:selected, QTreeWidget::item:selected {{
                background-color: {COLORS['primary']};
                color: white;
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: 500;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
                transition: background-color 0.2s;
            }}
            QPushButton:pressed {{
                background-color: {COLORS['primary_dark']};
                padding: 9px 14px 7px 16px;
            }}
            QPushButton:disabled {{
                background-color: {COLORS['disabled']};
                color: {COLORS['light_text']};
            }}
            QLineEdit, QComboBox, QSpinBox, QDateEdit {{
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 8px;
                background-color: white;
                selection-background-color: {COLORS['primary']};
                selection-color: white;
                transition: border 0.2s, background-color 0.2s;
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{
                border: 1px solid {COLORS['primary']};
                background-color: white;
            }}
            QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDateEdit:hover {{
                background-color: {COLORS['hover']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                selection-background-color: {COLORS['primary']};
                selection-color: white;
                background-color: white;
            }}
            QScrollBar:vertical {{
                border: none;
                background-color: {COLORS['background']};
                width: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLORS['secondary_light']};
                border-radius: 6px;
                min-height: 30px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS['secondary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
            QScrollBar:horizontal {{
                border: none;
                background-color: {COLORS['background']};
                height: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {COLORS['secondary_light']};
                border-radius: 6px;
                min-width: 30px;
                margin: 2px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {COLORS['secondary']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
                width: 0px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {COLORS['border']};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS['primary']};
                border: 1px solid {COLORS['primary']};
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid {COLORS['primary']};
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {COLORS['border']};
                border-radius: 9px;
            }}
            QRadioButton::indicator:checked {{
                background-color: {COLORS['primary']};
                border: 1px solid {COLORS['primary']};
            }}
            QRadioButton::indicator:hover {{
                border: 1px solid {COLORS['primary']};
            }}
            QTabWidget::pane {{
                border: none;
                background-color: {COLORS['card']};
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background-color: {COLORS['background']};
                color: {COLORS['light_text']};
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 15px;
                min-width: 80px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['primary']};
                color: white;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {COLORS['hover']};
            }}
            QToolTip {{
                border: 1px solid {COLORS['border']};
                padding: 5px;
                border-radius: 4px;
                background-color: {COLORS['card']};
                color: {COLORS['text']};
            }}
            QMenuBar {{
                background-color: {COLORS['card']};
                padding: 5px;
            }}
            QMenuBar::item {{
                padding: 5px 10px;
                border-radius: 4px;
            }}
            QMenuBar::item:selected {{
                background-color: {COLORS['hover']};
            }}
            QMenu {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
            QMenu::item {{
                padding: 8px 20px;
                border-radius: 4px;
                margin: 2px 5px;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['hover']};
            }}
            QStatusBar {{
                background-color: {COLORS['card']};
                color: {COLORS['text']};
                border-top: 1px solid {COLORS['border']};
            }}
            QStatusBar::item {{
                border: none;
            }}
            QProgressBar {{
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                text-align: center;
                background-color: {COLORS['background']};
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['primary']};
                border-radius: 3px;
            }}
            QHeaderView::section {{
                background-color: {COLORS['secondary']};
                color: white;
                padding: 8px;
                border: none;
                font-weight: 500;
            }}
        """)

    def _set_application_icon(self):
        """Set application icon."""
        try:
            # 如果图标不存在，创建一个默认图标
            if not os.path.exists(ICON_PATH):
                create_default_icon()
                
            if os.path.exists(ICON_PATH):
                self.setWindowIcon(QIcon(ICON_PATH))
            else:
                logger.warning(f"无法设置图标，文件不存在: {ICON_PATH}")
        except Exception as e:
            logger.error(f"设置图标失败: {e}")

    def _init_data(self):
        """初始化应用数据。"""
        # 字段信息
        self.fields = [
            "ID", "TeamName", "TeamWealth", "TeamFoundYear",
            "TeamLocation", "SupporterCount", "StadiumName", "Nickname", "BelongingLeague"
        ]

        self.field_labels = {
            "ID": "编号",
            "BelongingLeague": "联赛ID",
            "TeamName": "球队名称",
            "TeamWealth": "球队财富（万）",
            "TeamFoundYear": "成立年份",
            "TeamLocation": "所在地区",
            "SupporterCount": "支持者数量",
            "StadiumName": "主场名称",
            "Nickname": "球队昵称",
        }

        # 应用数据
        self.team_records = []
        self.displayed_team_records = []
        self.staff_records = []
        self.conn = None
        self.cursor = None
        self.current_team_id = None
        self.current_search = ""
        self.db_directory = ""
        self.leagues = {}
        self.temp_data = {}
        
        # UI对象引用
        self.logo_label = None
        self.logo_hint = None
        self.league_label = None  # 将在_create_team_detail_panel中创建
        self.entries = {}
        self.team_list = None
        self.staff_tree = None
        self.list_status_label = None

    def _create_widgets(self):
        """创建界面组件。"""
        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 控制面板
        self.load_btn = QPushButton("加载数据库")
        
        self.save_btn = QPushButton("保存球队修改")
        self.save_btn.setProperty("class", "success")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索关键词...")
        
        self.search_btn = QPushButton("搜索")
        
        self.clear_search_btn = QPushButton("清除")
        self.clear_search_btn.setProperty("class", "secondary")

        # 球队列表
        self.team_list = QListWidget()
        self.list_status_label = QLabel("总计: 0 个球队")
        self.list_status_label.setStyleSheet(f"color: {COLORS['light_text']}; font-size: 11px;")
        
        self.refresh_list_btn = QPushButton("刷新列表")
        
        self.export_list_btn = QPushButton("导出列表")
        self.export_list_btn.setProperty("class", "secondary")

        # 球队详情区域
        self.detail_scroll_area = QScrollArea()
        self.detail_scroll_area.setWidgetResizable(True)
        self.detail_content = QWidget()
        self.detail_scroll_area.setWidget(self.detail_content)
        apply_shadow(self.detail_scroll_area)

        # Logo区域
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setMinimumSize(150, 150)
        self.logo_label.setStyleSheet(f"""
            background-color: {COLORS['card']};
            border: 1px dashed {COLORS['border']};
            border-radius: 75px;
        """)
        
        self.logo_hint = QLabel("点击可更改Logo")
        self.logo_hint.setAlignment(Qt.AlignCenter)
        self.logo_hint.setStyleSheet(f"color: {COLORS['light_text']}; font-size: 11px;")

        # 基本信息区域
        self.entries = {}

        # 创建字段输入框
        for field in self.fields:
            if field == "BelongingLeague":
                continue
            self.entries[field] = QLineEdit()
            if field == "ID":
                self.entries[field].setReadOnly(True)
                self.entries[field].setStyleSheet(f"""
                    background-color: {COLORS['background']}; 
                    color: {COLORS['light_text']};
                """)

        # 员工表格
        self.staff_tree = QTreeWidget()
        self.staff_tree.setHeaderLabels(["ID", "姓名", "能力值", "知名度"])
        self.staff_tree.setColumnWidth(0, 70)
        self.staff_tree.setColumnWidth(1, 120)
        self.staff_tree.setColumnWidth(2, 80)
        self.staff_tree.setColumnWidth(3, 80)
        self.staff_tree.setMinimumHeight(200)
        self.staff_tree.setAlternatingRowColors(True)
        self.staff_tree.setStyleSheet(f"""
            QTreeView::item:alternate {{
                background-color: {COLORS['background']};
            }}
        """)
        
    def _create_layout(self):
        """创建应用界面布局。"""
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # 顶部控制面板卡片
        control_card = QWidget()
        control_card.setObjectName("controlPanel")
        control_card.setStyleSheet(f"""
            #controlPanel {{
                background-color: {COLORS['card']};
                border-radius: 10px;
                padding: 8px;
            }}
        """)
        apply_shadow(control_card)
        
        # 控制面板内部布局
        control_layout = QHBoxLayout(control_card)
        control_layout.setContentsMargins(15, 10, 15, 10)
        control_layout.setSpacing(15)
        
        # 左侧操作按钮组
        button_group = QWidget()
        button_group.setObjectName("buttonGroup")
        button_layout = QHBoxLayout(button_group)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        
        # 为按钮添加统一的大小
        self.load_btn.setMinimumWidth(100)
        self.save_btn.setMinimumWidth(100)
        
        # 添加导出数据库按钮
        self.export_db_btn = QPushButton("导出数据库")
        self.export_db_btn.setMinimumWidth(100)
        self.export_db_btn.setStyleSheet(f"""
            background-color: {COLORS['secondary']};
            color: white;
        """)
        
        button_layout.addWidget(self.load_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.export_db_btn)
        control_layout.addWidget(button_group)

        # 中间分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"background-color: {COLORS['border']}; max-width: 1px;")
        control_layout.addWidget(separator)

        # 右侧搜索组
        search_group = QWidget()
        search_group.setObjectName("searchGroup")
        search_layout = QHBoxLayout(search_group)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(8)
        
        search_label = QLabel("搜索:")
        search_label.setStyleSheet(f"color: {COLORS['light_text']}; font-weight: bold;")
        
        # 设置搜索框样式和尺寸
        self.search_input.setMinimumWidth(200)
        self.search_input.setStyleSheet(f"""
            border-radius: 4px;
            padding: 5px 10px;
            border: 1px solid {COLORS['border']};
        """)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input, 1)  # 搜索框占据更多空间
        search_layout.addWidget(self.search_btn)
        search_layout.addWidget(self.clear_search_btn)
        
        control_layout.addWidget(search_group, 1)  # 搜索组占据更多空间

        main_layout.addWidget(control_card)

        # 内容区域 (使用分割器)
        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setHandleWidth(2)
        content_splitter.setChildrenCollapsible(False)
        content_splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {COLORS['border']};
            }}
        """)

        # 左侧球队列表面板
        team_panel = self._create_team_list_panel()
        content_splitter.addWidget(team_panel)

        # 右侧球队详情面板
        detail_panel = self._create_team_detail_panel()
        content_splitter.addWidget(detail_panel)

        # 设置分割器比例
        content_splitter.setSizes([300, 700])

        main_layout.addWidget(content_splitter, 1)  # 内容区域应该占据更多垂直空间
        
    def _create_team_list_panel(self):
        """创建左侧球队列表面板。"""
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(12)

        # 创建列表标题
        header = QWidget()
        header.setObjectName("listHeader")
        header.setStyleSheet(f"""
            #listHeader {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                             stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_light']});
                border-radius: 6px;
                padding: 8px;
                color: white;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(8)
        
        title_label = QLabel("球队列表")
        title_label.setStyleSheet("color: white; font-weight: 500; font-size: 14px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        header_layout.addWidget(self.list_status_label)
        self.list_status_label.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 11px;")
        
        panel_layout.addWidget(header)

        # 创建列表卡片
        list_card = QWidget()
        list_card.setObjectName("teamListCard")
        list_card.setStyleSheet(f"""
            #teamListCard {{
                background-color: {COLORS['card']};
                border-radius: 6px;
                padding: 2px;
                border: none;
            }}
        """)
        apply_shadow(list_card)
        
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(10, 10, 10, 10)
        list_layout.setSpacing(10)
        
        # 球队列表样式
        self.team_list.setStyleSheet(f"""
            QListWidget {{
                border: none;
                background-color: {COLORS['card']};
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 10px 8px;
                border-radius: 3px;
                margin: 1px 0px;
                border-bottom: 1px solid {COLORS['divider']};
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['primary']};
                color: white;
                border-bottom: 1px solid {COLORS['primary']};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {COLORS['hover']};
            }}
        """)
        
        list_layout.addWidget(self.team_list)

        # 底部按钮区域 - 使用卡片式设计
        button_card = QWidget()
        button_card.setObjectName("buttonCard")
        button_card.setStyleSheet(f"""
            #buttonCard {{
                background-color: {COLORS['divider']};
                border-radius: 4px;
                padding: 5px;
            }}
        """)
        
        buttons_layout = QHBoxLayout(button_card)
        buttons_layout.setContentsMargins(8, 8, 8, 8)
        buttons_layout.setSpacing(10)
        
        self.refresh_list_btn.setMinimumWidth(90)
        self.export_list_btn.setMinimumWidth(90)
        
        # 设置按钮图标材质（使用Unicode字符代替）
        self.refresh_list_btn.setText("↻ 刷新列表")
        self.export_list_btn.setText("↓ 导出列表")
        
        buttons_layout.addWidget(self.refresh_list_btn)
        buttons_layout.addWidget(self.export_list_btn)
        
        list_layout.addWidget(button_card)
        panel_layout.addWidget(list_card)
        
        return panel
        
    def _create_team_detail_panel(self):
        """创建右侧球队详情面板。"""
        # 详情滚动区域
        self.detail_scroll_area.setWidgetResizable(True)
        self.detail_scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: transparent;
            }}
        """)
        
        # 详情内容布局
        detail_layout = QVBoxLayout(self.detail_content)
        detail_layout.setContentsMargins(10, 5, 15, 15)
        detail_layout.setSpacing(15)

        # 顶部标题区域 - 使用渐变背景
        header = QWidget()
        header.setObjectName("detailHeader")
        header.setStyleSheet(f"""
            #detailHeader {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                             stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_light']});
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        apply_shadow(header)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 10, 12, 10)
        
        title_label = QLabel("球队详细信息")
        title_label.setStyleSheet("color: white; font-weight: 500; font-size: 14px;")
        header_layout.addWidget(title_label)
        
        detail_layout.addWidget(header)

        # Logo卡片
        logo_card = QWidget()
        logo_card.setObjectName("logoCard")
        logo_card.setStyleSheet(f"""
            #logoCard {{
                background-color: {COLORS['card']};
                border-radius: 6px;
                padding: 12px;
                border: none;
            }}
        """)
        apply_shadow(logo_card)
        
        logo_layout = QVBoxLayout(logo_card)
        logo_layout.setAlignment(Qt.AlignCenter)
        logo_layout.setContentsMargins(10, 15, 10, 15)
        logo_layout.setSpacing(15)
        
        # 标题和Logo区域使用水平布局
        logo_header = QHBoxLayout()
        logo_header.setSpacing(10)
        
        logo_icon = QLabel("🖼️")
        logo_icon.setStyleSheet(f"color: {COLORS['primary']}; font-size: 16px;")
        
        logo_title = QLabel("球队标志")
        logo_title.setStyleSheet(f"""
            color: {COLORS['primary']};
            font-weight: 500;
            font-size: 14px;
        """)
        
        logo_header.addWidget(logo_icon)
        logo_header.addWidget(logo_title)
        logo_header.addStretch()
        
        logo_layout.addLayout(logo_header)
        
        # 更新Logo标签样式
        self.logo_label.setStyleSheet(f"""
            background-color: {COLORS['card']};
            border: 2px dashed {COLORS['border']};
            border-radius: 75px;
            min-width: 150px;
            min-height: 150px;
            max-width: 150px;
            max-height: 150px;
        """)
        
        logo_layout.addWidget(self.logo_label)
        
        # 更新提示文本样式
        self.logo_hint.setStyleSheet(f"color: {COLORS['light_text']}; font-size: 11px;")
        logo_layout.addWidget(self.logo_hint)
        
        detail_layout.addWidget(logo_card)

        # 基本信息卡片
        info_card = QWidget()
        info_card.setObjectName("infoCard")
        info_card.setStyleSheet(f"""
            #infoCard {{
                background-color: {COLORS['card']};
                border-radius: 6px;
                padding: 0px;
                border: none;
            }}
        """)
        apply_shadow(info_card)
        
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(15, 15, 15, 15)
        info_layout.setSpacing(15)
        
        # 信息区域标题
        info_header = QHBoxLayout()
        info_header.setSpacing(10)
        
        info_icon = QLabel("📋")
        info_icon.setStyleSheet(f"color: {COLORS['primary']}; font-size: 16px;")
        
        info_title = QLabel("基本信息")
        info_title.setStyleSheet(f"""
            color: {COLORS['primary']};
            font-weight: 500;
            font-size: 14px;
        """)
        
        info_header.addWidget(info_icon)
        info_header.addWidget(info_title)
        info_header.addStretch()
        
        info_layout.addLayout(info_header)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background-color: {COLORS['divider']}; max-height: 1px;")
        info_layout.addWidget(separator)

        # 表单布局 (两列)
        fields_layout = QHBoxLayout()
        fields_layout.setSpacing(20)

        left_form = QFormLayout()
        left_form.setSpacing(12)
        left_form.setLabelAlignment(Qt.AlignRight)
        left_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        right_form = QFormLayout()
        right_form.setSpacing(12)
        right_form.setLabelAlignment(Qt.AlignRight)
        right_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # 表单标签样式
        label_style = f"color: {COLORS['light_text']}; font-weight: 500;"
        
        # 表单输入框样式
        entry_style = f"""
            padding: 10px;
            border-radius: 4px;
            border: 1px solid {COLORS['border']};
            background-color: white;
        """

        # 分配字段到左右两列
        field_list = [f for f in self.fields if f != "BelongingLeague"]
        for i, field in enumerate(field_list):
            form = left_form if i % 2 == 0 else right_form
            
            label = QLabel(f"{self.field_labels[field]}:")
            label.setStyleSheet(label_style)
            
            entry = self.entries[field]
            if field != "ID":  # ID 字段有特殊样式
                entry.setStyleSheet(entry_style)
                
            form.addRow(label, entry)

        left_widget = QWidget()
        left_widget.setLayout(left_form)

        right_widget = QWidget()
        right_widget.setLayout(right_form)

        fields_layout.addWidget(left_widget)
        fields_layout.addWidget(right_widget)
        info_layout.addLayout(fields_layout)

        # 联赛信息
        league_container = QWidget()
        league_container.setObjectName("leagueContainer")
        league_container.setStyleSheet(f"""
            #leagueContainer {{
                background-color: {COLORS['hover']};
                border-radius: 4px;
                padding: 8px;
            }}
        """)
        
        league_layout = QHBoxLayout(league_container)
        league_layout.setContentsMargins(10, 5, 10, 5)
        
        league_icon = QLabel("🏆")
        league_icon.setStyleSheet(f"color: {COLORS['secondary']}; font-size: 14px;")
        league_layout.addWidget(league_icon)
        
        league_title = QLabel("所在联赛：")
        league_title.setStyleSheet(label_style)
        league_layout.addWidget(league_title)
        
        # 确保league_label被添加到一个稳定的父对象
        self.league_label = QLabel()
        self.league_label.setStyleSheet(f"""
            color: {COLORS['primary']};
            font-weight: 500;
            padding: 5px;
        """)
        league_layout.addWidget(self.league_label)
        league_layout.addStretch()
        
        # 将联赛信息容器添加到基本信息卡片中
        info_layout.addWidget(league_container)
        detail_layout.addWidget(info_card)

        # 员工信息卡片
        staff_card = QWidget()
        staff_card.setObjectName("staffCard")
        staff_card.setStyleSheet(f"""
            #staffCard {{
                background-color: {COLORS['card']};
                border-radius: 6px;
                padding: 0px;
                border: none;
            }}
        """)
        apply_shadow(staff_card)
        
        staff_layout = QVBoxLayout(staff_card)
        staff_layout.setContentsMargins(15, 15, 15, 15)
        staff_layout.setSpacing(10)
        
        # 员工区域标题
        staff_header = QHBoxLayout()
        staff_header.setSpacing(10)
        
        staff_icon = QLabel("👥")
        staff_icon.setStyleSheet(f"color: {COLORS['primary']}; font-size: 16px;")
        
        staff_title = QLabel("员工信息")
        staff_title.setStyleSheet(f"""
            color: {COLORS['primary']};
            font-weight: 500;
            font-size: 14px;
        """)
        
        staff_header.addWidget(staff_icon)
        staff_header.addWidget(staff_title)
        staff_header.addStretch()
        
        staff_layout.addLayout(staff_header)
        
        # 添加分隔线
        staff_separator = QFrame()
        staff_separator.setFrameShape(QFrame.HLine)
        staff_separator.setStyleSheet(f"background-color: {COLORS['divider']}; max-height: 1px;")
        staff_layout.addWidget(staff_separator)
        
        # 员工树视图样式
        self.staff_tree.setStyleSheet(f"""
            QTreeWidget {{
                border: none;
                background-color: {COLORS['card']};
                padding: 5px;
            }}
            QTreeWidget::item {{
                padding: 8px 5px;
                border-bottom: 1px solid {COLORS['divider']};
            }}
            QTreeWidget::item:selected {{
                background-color: {COLORS['primary']};
                color: white;
                border-bottom: 1px solid {COLORS['primary']};
            }}
            QTreeWidget::item:hover:!selected {{
                background-color: {COLORS['hover']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['secondary']};
                color: white;
                padding: 8px;
                border: none;
                font-weight: 500;
            }}
        """)
        staff_layout.addWidget(self.staff_tree)
        
        # 添加提示信息 - 卡片式设计
        hint_container = QWidget()
        hint_container.setObjectName("hintContainer")
        hint_container.setStyleSheet(f"""
            #hintContainer {{
                background-color: {COLORS['hover']};
                border-radius: 4px;
                padding: 5px;
            }}
        """)
        
        hint_layout = QHBoxLayout(hint_container)
        hint_layout.setContentsMargins(8, 5, 8, 5)
        
        hint_icon = QLabel("💡")
        hint_icon.setStyleSheet(f"color: {COLORS['light_text']}; font-size: 14px;")
        hint_layout.addWidget(hint_icon)
        
        hint_text = QLabel("双击员工记录进行编辑")
        hint_text.setAlignment(Qt.AlignCenter)
        hint_text.setStyleSheet(f"color: {COLORS['light_text']}; font-style: italic;")
        hint_layout.addWidget(hint_text)
        hint_layout.addStretch()
        
        staff_layout.addWidget(hint_container)
        detail_layout.addWidget(staff_card)
        
        return self.detail_scroll_area

    def _connect_signals(self):
        """Connect signals and slots."""
        # Control buttons
        self.load_btn.clicked.connect(self.load_database)
        self.save_btn.clicked.connect(self.save_team_changes)
        self.export_db_btn.clicked.connect(self.export_database)  # 添加导出按钮事件

        # Search
        self.search_btn.clicked.connect(self.search)
        self.clear_search_btn.clicked.connect(self._clear_search)
        self.search_input.returnPressed.connect(self.search)

        # Team list
        self.team_list.itemClicked.connect(self.on_select)
        self.refresh_list_btn.clicked.connect(self._refresh_lists)
        self.export_list_btn.clicked.connect(self._export_team_list)

        # Logo click event
        self.logo_label.mousePressEvent = self.on_logo_click

        # Staff table double click
        self.staff_tree.itemDoubleClicked.connect(self.edit_staff)

    def load_database(self):
        """加载数据库文件。"""
        try:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "选择数据库文件",
                self.db_directory or os.path.expanduser("~"),
                "SQLite 数据库 (*.db);;所有文件 (*.*)"
            )

            if not path:
                return

            self.db_directory = os.path.dirname(path)

            # 关闭已有连接
            if self.conn:
                self.conn.close()

            # 建立新连接
            self.conn = sqlite3.connect(path)
            self.conn.row_factory = sqlite3.Row  # 使用命名列访问
            self.cursor = self.conn.cursor()

            # 加载联赛信息
            self.cursor.execute("SELECT ID, LeagueName FROM League")
            leagues = self.cursor.fetchall()
            self.leagues = {l['ID']: l['LeagueName'] for l in leagues}

            # 刷新数据
            self.refresh_team_data()
            self.refresh_staff_data()

            # 更新状态
            self.statusBar().showMessage(f"已加载数据库：{os.path.basename(path)}")
            self.show_message(
                "成功",
                f"数据库加载成功！\n已加载 {len(self.team_records)} 个球队和 {len(self.staff_records)} 名员工。"
            )

            logger.info(f"已加载数据库: {path}, 球队: {len(self.team_records)}, 员工: {len(self.staff_records)}")

        except sqlite3.Error as e:
            error_msg = f"数据库错误：{str(e)}"
            logger.error(error_msg)
            self.show_message("数据库错误", error_msg, QMessageBox.Critical)

        except Exception as e:
            error_msg = f"加载失败：{str(e)}"
            logger.error(error_msg, exc_info=True)
            self.show_message("错误", error_msg, QMessageBox.Critical)

    def refresh_team_data(self):
        """Refresh team data."""
        if not self.cursor:
            return

        try:
            query = """
                SELECT T.ID, T.TeamName, T.TeamWealth, T.TeamFoundYear,
                       T.TeamLocation, T.SupporterCount, T.StadiumName, 
                       T.Nickname, T.BelongingLeague
                FROM Teams T
                ORDER BY T.TeamName
            """
            self.cursor.execute(query)
            raw_records = self.cursor.fetchall()

            # Convert to TeamRecord objects
            self.team_records = [TeamRecord(record) for record in raw_records]

            # Apply search filter
            self.apply_search_filter()

            # Refresh list display
            self.refresh_list()

        except sqlite3.Error as e:
            error_msg = f"刷新球队数据失败：{str(e)}"
            logger.error(error_msg)
            self.statusBar().showMessage(error_msg)

    def refresh_staff_data(self):
        """Refresh staff data."""
        if not self.cursor:
            return

        try:
            query = """
                SELECT ID, Name, AbilityJSON, Fame, EmployedTeamID 
                FROM Staff
                ORDER BY Name
            """
            self.cursor.execute(query)
            raw_records = self.cursor.fetchall()

            # Convert to StaffRecord objects
            self.staff_records = [StaffRecord(record) for record in raw_records]

            # If there is a currently selected team, update its staff display
            if self.current_team_id:
                self.update_staff(self.current_team_id)

        except sqlite3.Error as e:
            error_msg = f"刷新员工数据失败：{str(e)}"
            logger.error(error_msg)
            self.statusBar().showMessage(error_msg)

    def on_select(self, item: QListWidgetItem):
        """处理列表选择事件。"""
        try:
            idx = self.team_list.currentRow()
            if idx < 0 or idx >= len(self.displayed_team_records):
                return

            # 获取选中的球队记录
            record = self.displayed_team_records[idx]
            self.current_team_id = record.id

            # 更新Logo显示
            self.update_logo(self.current_team_id)

            # 显示球队数据
            self._display_team_data(record)

            # 更新员工信息
            self.update_staff(self.current_team_id)

            # 更新状态栏
            self.statusBar().showMessage(f"已选择: {record}")

        except Exception as e:
            logger.error(f"选择球队时出错: {e}", exc_info=True)
            self.statusBar().showMessage(f"选择球队失败: {str(e)}")
            self.show_message("错误", f"选择球队时出错: {str(e)}", QMessageBox.Critical)

    def _display_team_data(self, record: TeamRecord):
        """显示球队数据。"""
        try:
            # 如果有临时数据，优先使用
            if self.current_team_id in self.temp_data:
                data = self.temp_data[self.current_team_id]
                for field in self.fields:
                    if field == "BelongingLeague":
                        continue
                    entry = self.entries[field]
                    entry.setText(str(data.get(field, "")))
            else:
                # 从数据库加载数据
                record_dict = record.to_dict()
                for field in self.fields:
                    if field == "BelongingLeague":
                        continue
                    entry = self.entries[field]
                    entry.setText(str(record_dict.get(field, "")))

            # 设置联赛名称
            league_name = self.leagues.get(record.league_id, "未知联赛")
            league_text = f"{league_name} (ID: {record.league_id})"
            
            # 确保league_label存在
            if hasattr(self, 'league_label') and self.league_label is not None:
                self.league_label.setText(league_text)
            else:
                logger.warning("联赛标签对象不存在，无法更新联赛信息")
                
        except Exception as e:
            logger.error(f"显示球队数据时出错: {e}", exc_info=True)
            self.statusBar().showMessage(f"显示球队数据失败: {str(e)}")
            
    def update_logo(self, team_id):
        """更新球队标志显示。"""
        # 清除现有标志
        self.logo_label.clear()
        self.logo_label.setText("")

        # 如果没有球队ID则返回
        if not team_id:
            return

        # 构建标志文件路径
        logo_path = os.path.join(self.db_directory, f"L{team_id}.png")

        # 检查文件是否存在
        if os.path.exists(logo_path):
            try:
                # 创建圆形Logo
                original = QImage(logo_path)
                # 将图像调整为正方形
                size = min(LOGO_SIZE)
                image = original.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                # 显示图像
                pixmap = QPixmap.fromImage(image)
                self.logo_label.setPixmap(pixmap)
                self.logo_label.setStyleSheet(f"""
                    background-color: {COLORS['card']};
                    border: 2px solid {COLORS['primary']};
                    border-radius: {size//2}px;
                    padding: 0px;
                    min-width: {size}px;
                    min-height: {size}px;
                    max-width: {size}px;
                    max-height: {size}px;
                """)
                
                # 更新提示文本
                self.logo_hint.setText("点击可更改Logo")
                self.logo_hint.setStyleSheet(f"color: {COLORS['light_text']}; font-size: 11px;")
                
            except Exception as e:
                logger.error(f"加载Logo失败: {str(e)}")
                self.logo_label.setText("Logo加载失败")
                self.logo_label.setStyleSheet(f"""
                    background-color: {COLORS['card']};
                    border: 2px dashed {COLORS['border']};
                    border-radius: 75px;
                    color: {COLORS['light_text']};
                    font-style: italic;
                """)
        else:
            # 如果Logo不存在则显示默认文本
            self.logo_label.setText("无Logo\n点击添加")
            self.logo_label.setStyleSheet(f"""
                background-color: {COLORS['card']};
                border: 2px dashed {COLORS['border']};
                border-radius: 75px;
                color: {COLORS['light_text']};
                font-style: italic;
            """)
            
    def on_logo_click(self, event):
        """处理Logo点击事件。"""
        if not self.current_team_id:
            self.show_message("警告", "请先选择一个球队", QMessageBox.Warning)
            return

        self.replace_logo(self.current_team_id)

    def replace_logo(self, team_id):
        """替换Logo。"""
        if not team_id:
            self.show_message("警告", "请先选择一个球队", QMessageBox.Warning)
            return

        # 打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择Logo图片",
            os.path.expanduser("~"),
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif);;所有文件 (*.*)"
        )

        if not file_path:
            return

        try:
            # 加载图像并调整大小
            image = QImage(file_path)
            size = min(LOGO_SIZE)
            image = image.scaled(
                size, size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            # 保存为PNG
            logo_path = os.path.join(self.db_directory, f"L{team_id}.png")
            image.save(logo_path, "PNG")

            # 更新显示
            self.update_logo(team_id)
            
            # 显示成功消息
            self.show_message("成功", "Logo已成功替换！")

            logger.info(f"球队 {team_id} Logo已更新")

        except Exception as e:
            error_msg = f"替换Logo失败：{str(e)}"
            logger.error(error_msg)
            self.show_message("错误", error_msg, QMessageBox.Critical)

    def search(self):
        """执行搜索操作。"""
        self.current_search = self.search_input.text().strip()
        self.apply_search_filter()
        self.refresh_list()

        # 更新状态
        results_count = len(self.displayed_team_records)
        if self.current_search:
            if results_count > 0:
                self.statusBar().showMessage(f"搜索 '{self.current_search}' 找到 {results_count} 个匹配项")
            else:
                self.statusBar().showMessage(f"搜索 '{self.current_search}' 没有找到匹配项")
                
            # 高亮搜索输入框，表示有活动的搜索
            self.search_input.setStyleSheet(f"""
                border-radius: 4px;
                padding: 5px 10px;
                border: 1px solid {COLORS['primary']};
                background-color: rgba(25, 118, 210, 0.05);
            """)
        else:
            self.statusBar().showMessage("显示全部球队")
            
            # 重置搜索输入框样式
            self.search_input.setStyleSheet(f"""
                border-radius: 4px;
                padding: 5px 10px;
                border: 1px solid {COLORS['border']};
            """)
            
    def _clear_search(self):
        """清除搜索并显示所有球队。"""
        self.search_input.clear()
        self.current_search = ""
        self.apply_search_filter()
        self.refresh_list()
        
        # 重置搜索输入框样式
        self.search_input.setStyleSheet(f"""
            border-radius: 4px;
            padding: 5px 10px;
            border: 1px solid {COLORS['border']};
        """)
        
        self.statusBar().showMessage("显示全部球队")
        
    def apply_search_filter(self):
        """对球队记录应用搜索过滤。"""
        if not self.current_search:
            self.displayed_team_records = self.team_records
        else:
            search_term = self.current_search.lower()
            self.displayed_team_records = [
                record for record in self.team_records
                if search_term in record.as_search_string().lower()
            ]
            
    def show_message(self, title, message, icon=QMessageBox.Information):
        """显示统一样式的消息框。"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.setStandardButtons(QMessageBox.Ok)
        
        # 应用样式
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {COLORS['card']};
            }}
            QLabel {{
                color: {COLORS['text']};
                min-width: 300px;
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                border: none;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
        """)
        
        return msg_box.exec_()
        
    def show_confirm(self, title, message):
        """显示确认对话框。"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        
        # 获取按钮并设置文本
        yes_button = msg_box.button(QMessageBox.Yes)
        if yes_button:
            yes_button.setText("确定")
            
        no_button = msg_box.button(QMessageBox.No)
        if no_button:
            no_button.setText("取消")
        
        # 应用样式
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {COLORS['card']};
            }}
            QLabel {{
                color: {COLORS['text']};
                min-width: 300px;
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                border: none;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
            QPushButton[text="取消"] {{
                background-color: {COLORS['secondary']};
            }}
            QPushButton[text="取消"]:hover {{
                background-color: #455A64;
            }}
        """)
        
        return msg_box.exec_() == QMessageBox.Yes
        
    def save_team_changes(self):
        """保存球队信息修改。"""
        if not self.conn:
            self.show_message("警告", "请先加载数据库", QMessageBox.Warning)
            return

        if not self.current_team_id:
            self.show_message("警告", "请选择要修改的记录", QMessageBox.Warning)
            return

        try:
            # 收集输入数据
            data = {}
            numeric_fields = ["TeamWealth", "SupporterCount", "TeamFoundYear"]

            # 验证并收集数据
            for field in self.fields:
                if field == "BelongingLeague":
                    continue

                value = self.entries[field].text().strip()

                # 验证必填字段
                if field in ["TeamName"] and not value:
                    self.show_message("输入错误", f"{self.field_labels[field]} 不能为空", QMessageBox.Critical)
                    self.entries[field].setFocus()
                    return

                # 验证数字字段
                if field in numeric_fields:
                    try:
                        data[field] = self.validate_number(value, self.field_labels[field])
                    except ValueError:
                        self.entries[field].setFocus()
                        return
                else:
                    data[field] = value

            # 确认保存
            if not self.show_confirm("确认保存", "您确定要保存对球队数据的修改吗？"):
                return

            # 构建更新SQL
            update_fields = [f for f in self.fields if f != "ID" and f != "BelongingLeague"]

            query = f"""
                UPDATE Teams SET
                    {','.join([f"{field}=?" for field in update_fields])}
                WHERE ID = ?
            """

            # 执行更新
            self.cursor.execute(
                query,
                [data[field] for field in update_fields] + [self.current_team_id]
            )

            self.conn.commit()

            # 清除临时数据
            if self.current_team_id in self.temp_data:
                self.temp_data.pop(self.current_team_id)

            # 刷新数据
            self.refresh_team_data()

            # 重新选择当前球队
            self.select_current_team()

            # 更新状态
            self.statusBar().showMessage(f"已保存球队 {data['TeamName']} 的修改")
            self.show_message("成功", "球队数据已保存")

            logger.info(f"保存了球队 {self.current_team_id} 的修改")

        except sqlite3.Error as e:
            error_msg = f"数据库错误：{str(e)}"
            logger.error(error_msg)
            self.show_message("数据库错误", error_msg, QMessageBox.Critical)

        except Exception as e:
            error_msg = f"保存失败：{str(e)}"
            logger.error(error_msg, exc_info=True)
            self.show_message("错误", error_msg, QMessageBox.Critical)

    def validate_number(self, value, field_name):
        """Validate numeric input."""
        if not value:
            return 0

        try:
            return int(value)
        except ValueError:
            self.show_message("输入错误", f"{field_name} 必须是有效的数字", QMessageBox.Critical)
            raise ValueError(f"Invalid number: {value}")

    def refresh_list(self):
        """刷新球队列表显示。"""
        self.team_list.clear()

        # 更新计数显示
        total = len(self.displayed_team_records)
        self.list_status_label.setText(f"共计: {total} 个球队")
        
        if total == 0:
            # 如果没有记录，显示提示信息
            empty_item = QListWidgetItem("没有找到球队记录")
            empty_item.setFlags(Qt.NoItemFlags)
            empty_item.setTextAlignment(Qt.AlignCenter)
            self.team_list.addItem(empty_item)
            return

        # 添加项目到列表
        for i, record in enumerate(self.displayed_team_records):
            item = QListWidgetItem()
            
            # 设置项目文本和提示
            name_text = record.name
            if record.nickname:
                name_text += f" ({record.nickname})"
                
            item.setText(name_text)
            item.setToolTip(f"ID: {record.id}\n地区: {record.location}\n成立年份: {record.found_year}")
            
            # 设置交替行颜色
            if i % 2 == 0:
                item.setBackground(QColor(COLORS['background']))
                
            self.team_list.addItem(item)

        # 如果有项目则选择第一项
        if self.team_list.count() > 0:
            self.team_list.setCurrentRow(0)
            self.on_select(self.team_list.item(0))
            
    def select_current_team(self):
        """在列表中重新选择当前球队。"""
        if not self.current_team_id:
            return

        # 在显示列表中查找球队
        for i, record in enumerate(self.displayed_team_records):
            if record.id == self.current_team_id:
                self.team_list.setCurrentRow(i)
                self.on_select(self.team_list.item(i))
                return
                
        # 如果未找到当前球队（可能由于过滤），显示提示
        self.statusBar().showMessage(f"当前选择的球队不在筛选结果中")
        
    def update_staff(self, team_id):
        """更新所选球队的员工信息。"""
        self.staff_tree.clear()

        if not team_id:
            return

        # 筛选此球队的员工
        team_staff = [s for s in self.staff_records if s.team_id == team_id]
        
        if not team_staff:
            # 如果没有员工，显示提示项
            empty_item = QTreeWidgetItem(self.staff_tree)
            empty_item.setText(0, "")
            empty_item.setText(1, "该球队暂无员工记录")
            empty_item.setTextAlignment(1, Qt.AlignCenter)
            empty_item.setFlags(Qt.NoItemFlags)
            return

        # 按能力值排序（降序）
        team_staff.sort(key=lambda s: s.get_ability(), reverse=True)

        # 添加到树形视图
        for staff in team_staff:
            item = QTreeWidgetItem(self.staff_tree)
            item.setText(0, str(staff.id))
            item.setText(1, staff.name)
            
            ability = staff.get_ability()
            item.setText(2, str(ability))
            
            # 根据能力值设置颜色
            if ability >= 80:
                item.setForeground(2, QColor(COLORS['success']))
            elif ability >= 60:
                item.setForeground(2, QColor(COLORS['primary']))
                
            item.setText(3, str(staff.fame))
            item.setData(0, Qt.UserRole, staff)

        self.staff_tree.resizeColumnToContents(1)

    def edit_staff(self, item, column):
        """编辑员工信息。"""
        if not self.conn:
            self.show_message("警告", "请先加载数据库", QMessageBox.Warning)
            return

        # 获取员工记录
        staff = item.data(0, Qt.UserRole)
        if not staff:
            return

        # 打开编辑对话框
        dialog = StaffEditDialog(self, staff, self.update_staff_record)
        dialog.exec_()

    def update_staff_record(self, staff_id, name, ability, fame):
        """在数据库中更新员工记录。"""
        try:
            # 查找员工记录
            staff = next((s for s in self.staff_records if s.id == staff_id), None)
            if not staff:
                raise ValueError(f"找不到ID为 {staff_id} 的员工")

            # 更新能力值JSON
            ability_json = staff.update_ability(ability)

            # 更新数据库
            self.cursor.execute(
                "UPDATE Staff SET Name = ?, AbilityJSON = ?, Fame = ? WHERE ID = ?",
                (name, ability_json, fame, staff_id)
            )
            self.conn.commit()

            # 刷新员工数据
            self.refresh_staff_data()

            self.statusBar().showMessage(f"已更新员工: {name}")
            logger.info(f"已更新员工 {staff_id}: {name}")

        except sqlite3.Error as e:
            error_msg = f"数据库错误：{str(e)}"
            logger.error(error_msg)
            self.show_message("数据库错误", error_msg, QMessageBox.Critical)

        except Exception as e:
            error_msg = f"更新员工失败：{str(e)}"
            logger.error(error_msg, exc_info=True)
            self.show_message("错误", error_msg, QMessageBox.Critical)

    def _refresh_lists(self):
        """Refresh lists data."""
        self.refresh_team_data()
        self.refresh_staff_data()
        self.statusBar().showMessage("列表已刷新")

    def _export_team_list(self):
        """导出球队列表到CSV文件。"""
        if not self.team_records:
            self.show_message("警告", "没有可导出的数据", QMessageBox.Warning)
            return

        try:
            # 选择保存文件
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出球队列表",
                os.path.join(self.db_directory or os.path.expanduser("~"), "team_list.csv"),
                "CSV文件 (*.csv);;所有文件 (*.*)"
            )

            if not file_path:
                return

            # 写入CSV
            with open(file_path, 'w', encoding='utf-8') as f:
                header = ','.join([self.field_labels.get(field, field) for field in self.fields])
                f.write(f"{header}\n")

                for team in self.team_records:
                    data = team.to_dict()
                    row = ','.join([str(data.get(field, '')) for field in self.fields])
                    f.write(f"{row}\n")

            self.show_message(
                "成功",
                f"已导出 {len(self.team_records)} 个球队数据至文件:\n{file_path}"
            )

            logger.info(f"已导出球队列表到: {file_path}")

        except Exception as e:
            error_msg = f"导出失败：{str(e)}"
            logger.error(error_msg, exc_info=True)
            self.show_message("错误", error_msg, QMessageBox.Critical)

    def export_database(self):
        """导出数据库文件。"""
        if not self.conn:
            self.show_message("警告", "请先加载数据库", QMessageBox.Warning)
            return

        try:
            # 获取当前数据库文件路径
            current_db_path = self.conn.execute("PRAGMA database_list").fetchone()[2]
            
            # 打开保存文件对话框
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出数据库",
                os.path.join(
                    self.db_directory or os.path.expanduser("~"),
                    f"CFS_Teams_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                ),
                "SQLite 数据库 (*.db);;所有文件 (*.*)"
            )

            if not file_path:
                return

            # 确保数据库处于一致状态
            self.conn.execute("PRAGMA wal_checkpoint(FULL)")
            
            # 关闭当前连接
            self.conn.close()
            self.conn = None
            
            try:
                # 复制数据库文件
                import shutil
                shutil.copy2(current_db_path, file_path)
                
                # 如果存在WAL和SHM文件，也复制它们
                for ext in ['-wal', '-shm']:
                    src = current_db_path + ext
                    if os.path.exists(src):
                        shutil.copy2(src, file_path + ext)
                
                self.show_message(
                    "成功",
                    f"数据库已导出到:\n{file_path}"
                )
                
                logger.info(f"数据库已导出到: {file_path}")
                
            finally:
                # 重新连接数据库
                self.conn = sqlite3.connect(current_db_path)
                self.conn.row_factory = sqlite3.Row
                self.cursor = self.conn.cursor()

        except Exception as e:
            error_msg = f"导出失败：{str(e)}"
            logger.error(error_msg, exc_info=True)
            self.show_message("错误", error_msg, QMessageBox.Critical)
            
            # 确保重新连接数据库
            if not self.conn and current_db_path:
                try:
                    self.conn = sqlite3.connect(current_db_path)
                    self.conn.row_factory = sqlite3.Row
                    self.cursor = self.conn.cursor()
                except Exception as conn_error:
                    logger.error(f"重新连接数据库失败: {conn_error}", exc_info=True)
                    self.show_message(
                        "严重错误",
                        "数据库连接已断开，请重新启动应用程序",
                        QMessageBox.Critical
                    )


def main():
    """Run main application."""
    try:
        # 尝试创建默认图标，但不要让它阻止程序启动
        create_default_icon()
    except Exception as e:
        logger.error(f"创建图标时发生错误: {e}")
    
    app = QApplication(sys.argv)
    
    # 设置应用程序全局属性
    app.setApplicationName("CFS球队编辑器")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("卡尔纳斯工作室")
    
    # 设置现代系统字体
    default_font = QFont()
    default_font.setPointSize(10)
    default_font.setFamily("Microsoft YaHei UI")  # 使用系统UI字体
    app.setFont(default_font)
    
    # 应用Material主题
    try:
        # 使用蓝色调的主题
        apply_stylesheet(app, theme='light_blue.xml', invert_secondary=True)
    except Exception as e:
        logger.warning(f"无法应用Material主题: {e}")
        
        # 如果Material主题失败，应用自定义调色板
        try:
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(COLORS['background']))
            palette.setColor(QPalette.WindowText, QColor(COLORS['text']))
            palette.setColor(QPalette.Base, QColor(COLORS['card']))
            palette.setColor(QPalette.AlternateBase, QColor(COLORS['background']))
            palette.setColor(QPalette.Text, QColor(COLORS['text']))
            palette.setColor(QPalette.Button, QColor(COLORS['primary']))
            palette.setColor(QPalette.ButtonText, QColor('white'))
            palette.setColor(QPalette.Link, QColor(COLORS['accent']))
            palette.setColor(QPalette.Highlight, QColor(COLORS['primary']))
            palette.setColor(QPalette.HighlightedText, QColor('white'))
            app.setPalette(palette)
        except Exception as e2:
            logger.warning(f"无法设置调色板: {e2}")

    # 创建并显示主窗口
    try:
        window = TeamDatabaseViewer()
        window.show()
    
        # 运行应用程序
        sys.exit(app.exec())
    except Exception as e:
        logger.critical(f"应用程序启动失败: {e}", exc_info=True)
        QMessageBox.critical(None, "错误", f"应用程序启动失败:\n{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

