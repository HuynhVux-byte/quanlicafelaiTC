"""
views/ingredient_manager.py
NguyenLieu đã bị loại khỏi models (thay bằng gia_nhap trực tiếp trên SanPham).
Module này hiển thị thông báo thay thế.
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt


class InventoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quản Lý Kho")
        self.resize(450, 220)
        self.setStyleSheet("""
            QDialog { background-color: #F3F4F6; }
            QLabel { color: #1F2937; font-size: 14px; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        lbl = QLabel(
            "📦 <b>Tính năng Quản lý Nguyên liệu đã được tích hợp vào từng Sản phẩm.</b><br><br>"
            "Giá vốn của mỗi món được quản lý trực tiếp trong:<br>"
            "<b>⚙️ MENU → Sửa Món → Giá vốn (đ)</b>.<br><br>"
            "<span style='color:#64748B; font-size:12px;'>"
            "Nếu cần module kho nguyên liệu riêng, vui lòng liên hệ kỹ thuật viên.</span>"
        )
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        btn = QPushButton("Đã hiểu")
        btn.setMinimumHeight(40)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #1E293B; color: white; font-weight: bold;
                border-radius: 8px; font-size: 14px; border: none;
            }
            QPushButton:hover { background-color: #334155; }
        """)
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)