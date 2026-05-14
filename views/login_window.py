from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox)
from PySide6.QtCore import Qt

from controllers.auth_controller import authenticate_user

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Đăng Nhập Hệ Thống")
        self.setFixedSize(350, 250)
        self.user_data = None # Nơi lưu thông tin sau khi đăng nhập thành công

        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("<b>TÊN ĐĂNG NHẬP</b>"))
        self.txt_username = QLineEdit()
        layout.addWidget(self.txt_username)

        layout.addWidget(QLabel("<b>MẬT KHẨU</b>"))
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.txt_password)

        self.btn_login = QPushButton("ĐĂNG NHẬP")
        self.btn_login.setFixedHeight(45)
        self.btn_login.setStyleSheet("background-color: #2980B9; color: white; font-weight: bold;")
        self.btn_login.clicked.connect(self.handle_login)
        layout.addWidget(self.btn_login)

        self.btn_forgot = QPushButton("❓ Quên mật khẩu")
        self.btn_forgot.setStyleSheet("background: none; color: #3498DB; border: none; text-decoration: underline;")
        self.btn_forgot.clicked.connect(self.forgot_password)
        layout.addWidget(self.btn_forgot)

    def handle_login(self):
        username = self.txt_username.text()
        password = self.txt_password.text()
        
        user = authenticate_user(username, password)
        if user:
            self.user_data = user
            self.accept() # Đóng dialog và trả về QDialog.Accepted
        else:
            QMessageBox.warning(self, "Thất bại", "Sai tài khoản hoặc mật khẩu!")

    # Thêm hàm này vào trong class LoginDialog (cùng cấp với handle_login)
    def forgot_password(self):
        QMessageBox.information(self, "Hỗ trợ", "Vui lòng liên hệ Chủ Quán (Admin) để được cấp lại mật khẩu.\n\nNếu bạn là Admin, hãy nhờ Kỹ thuật viên kiểm tra trong Database!")