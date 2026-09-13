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
}
QListWidget::item:selected {
  background: #3d2a4f;
}
QToolButton, QPushButton {
  background: #2a2a2a;
  border: none;
  border-radius: 10px;
  padding: 10px 12px;
  min-width: 44px;
  min-height: 40px;
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
QComboBox QAbstractItemView {
  background: #1b1b1b;
  color: #e8e8e8;
  selection-background-color: #3d2a4f;
}
QLabel#meta { color: #bdbdbd; }
QLabel#preview {
  background: #000;
  border-radius: 12px;
}
"""
