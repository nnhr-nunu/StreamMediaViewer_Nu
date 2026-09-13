DARK_QSS = """
QMainWindow, QDialog {
  background: #121212;
  color: #e8e8e8;
  font-size: 14px;
}
QMainWindow > QWidget, QDialog > QWidget {
  background: #121212;
  color: #e8e8e8;
}
QWidget {
  color: #e8e8e8;
  font-size: 14px;
}
QLabel, QCheckBox, QGroupBox, QFormLayout, QDialogButtonBox {
  background: transparent;
}
QListWidget {
  background: #1b1b1b;
  border: none;
  outline: none;
  padding: 4px;
}
QListWidget::item {
  color: #cfcfcf;
  font-size: 12px;
  padding: 0px;
}
QListWidget::item:selected {
  background: #3d2a4f;
  border-radius: 8px;
}
QToolButton, QPushButton {
  background: #2a2a2a;
  border: none;
  border-radius: 10px;
  padding: 6px 8px;
  min-width: 56px;
  min-height: 48px;
  color: #f0f0f0;
}
QDialog QPushButton {
  min-height: 36px;
  min-width: 72px;
}
QToolButton:hover, QPushButton:hover {
  background: #3a3a3a;
}
QToolButton:checked {
  background: #6b3fa0;
}
QSlider::groove:horizontal {
  height: 6px;
  background: #333;
  border-radius: 3px;
}
QSlider::handle:horizontal {
  width: 16px;
  margin: -6px 0;
  background: #c9a0ff;
  border-radius: 8px;
}
QSlider#rangeIn::handle:horizontal {
  background: #7dcea0;
}
QSlider#rangeOut::handle:horizontal {
  background: #e8a070;
}
QCheckBox { spacing: 4px; padding: 2px 6px 2px 2px; }
QComboBox, QDateEdit {
  background: #1b1b1b;
  color: #e8e8e8;
  border: 1px solid #555;
  border-radius: 8px;
  padding: 4px 18px 4px 8px;
  min-height: 32px;
}
QDateEdit {
  min-width: 92px;
  max-width: 104px;
}
QComboBox::drop-down, QDateEdit::drop-down {
  subcontrol-origin: padding;
  subcontrol-position: center right;
  width: 16px;
  border: none;
  background: transparent;
}
QComboBox::down-arrow, QDateEdit::down-arrow {
  image: none;
  width: 0;
  height: 0;
}
QComboBox QAbstractItemView {
  background: #1b1b1b;
  color: #e8e8e8;
  selection-background-color: #3d2a4f;
  border: 1px solid #555;
}
QCalendarWidget {
  background: #1b1b1b;
  color: #e8e8e8;
}
QCalendarWidget QWidget {
  background: #1b1b1b;
  color: #e8e8e8;
  alternate-background-color: #1b1b1b;
}
QCalendarWidget QAbstractItemView {
  background: #1b1b1b;
  color: #e8e8e8;
  selection-background-color: #6b3fa0;
  selection-color: #f5f5f5;
  outline: none;
}
QCalendarWidget QToolButton {
  min-width: 28px;
  min-height: 28px;
  background: transparent;
  color: #e8e8e8;
}
QCalendarWidget QMenu {
  background: #1b1b1b;
  color: #e8e8e8;
}
QGroupBox {
  border: 1px solid #333;
  border-radius: 10px;
  margin-top: 12px;
  padding: 8px 8px 4px 8px;
  color: #e8e8e8;
  background: transparent;
}
QGroupBox::title {
  subcontrol-origin: margin;
  left: 12px;
  padding: 0 6px;
  color: #c9a0ff;
  background: transparent;
}
QFrame#manualTools {
  background: #1a1520;
  border: 1px solid #6b3fa0;
  border-left: 4px solid #c9a0ff;
  border-radius: 10px;
}
QFrame#outputChrome {
  background: transparent;
}
QToolButton#outputChrome {
  background: rgba(18, 18, 18, 200);
  font-size: 20px;
  min-width: 44px;
  min-height: 44px;
  max-width: 48px;
  padding: 4px;
  border-radius: 10px;
}
QToolButton#outputChrome:hover {
  background: rgba(60, 42, 80, 220);
}
QToolButton#outputChrome:checked {
  background: #6b3fa0;
}
QSlider#outputLoupe {
  min-width: 96px;
  max-width: 140px;
}
QToolButton#starOverlay {
  background: rgba(18, 18, 18, 170);
  font-size: 22px;
  min-width: 44px;
  min-height: 44px;
  padding: 4px;
  border-radius: 24px;
}
QToolButton#starOverlay:hover {
  background: rgba(60, 42, 80, 210);
}
QProgressBar {
  background: #2a2a2a;
  border: none;
  border-radius: 6px;
  height: 16px;
  text-align: center;
  color: #e8e8e8;
}
QProgressBar::chunk {
  background: #6b3fa0;
  border-radius: 6px;
}
QLabel#guide {
  color: #e8e8e8;
  font-size: 16px;
  background: transparent;
  padding: 28px;
}
QLabel#preview {
  background: #000;
  border-radius: 12px;
}
QLabel#meta, QLabel#shortcutsBody {
  background: transparent;
}
QLineEdit {
  background: #1b1b1b;
  color: #e8e8e8;
  border: 1px solid #555;
  border-radius: 8px;
  padding: 6px 10px;
  min-height: 28px;
}
"""
