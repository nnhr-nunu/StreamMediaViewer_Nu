DARK_QSS = """
QMainWindow, QWidget {
  background: #121212;
  color: #e8e8e8;
  font-size: 14px;
}
QListWidget {
  background: #1b1b1b;
  border: none;
  outline: none;
  padding: 8px;
}
QListWidget::item {
  color: #cfcfcf;
  font-size: 12px;
  padding: 4px;
}
QListWidget::item:selected {
  background: #3d2a4f;
  border-radius: 10px;
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
QCheckBox { spacing: 8px; }
QComboBox, QDateEdit, QDialog {
  background: #1b1b1b;
  color: #e8e8e8;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 4px 8px;
  min-height: 32px;
}
QDateEdit {
  min-width: 150px;
}
QComboBox QAbstractItemView {
  background: #1b1b1b;
  color: #e8e8e8;
  selection-background-color: #3d2a4f;
}
QGroupBox {
  border: 1px solid #333;
  border-radius: 10px;
  margin-top: 12px;
  padding: 8px 8px 4px 8px;
  color: #e8e8e8;
}
QGroupBox::title {
  subcontrol-origin: margin;
  left: 12px;
  padding: 0 6px;
  color: #c9a0ff;
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
  background: #121212;
  padding: 28px;
}
QLabel#preview {
  background: #000;
  border-radius: 12px;
}
"""
