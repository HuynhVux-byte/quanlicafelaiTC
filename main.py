import sys
from PySide6.QtWidgets import QApplication
from views.login_window import LoginDialog
from views.main_window import POSWindow
from database.db_config import init_db_and_seed, get_session
from database.models import NhanVien
from utils.session_manager import get_valid_session, save_session

def main():
    app = QApplication(sys.argv)
    init_db_and_seed()

    # Vòng lặp vô tận để xử lý chu kỳ Đăng nhập -> Bán hàng -> Đăng xuất
    while True:
        db = get_session()
        current_user = None

        # 1. KIỂM TRA PHIÊN LÀM VIỆC (Có bị quá 60 phút chưa?)
        saved_user_id = get_valid_session()
        if saved_user_id:
            current_user = db.get(NhanVien, saved_user_id)

        # 2. NẾU KHÔNG CÓ PHIÊN -> BẮT ĐĂNG NHẬP
        if not current_user:
            login = LoginDialog()
            if login.exec() == LoginDialog.Accepted:
                current_user = login.user_data
            else:
                db.close()
                break # Bấm dấu X tắt form login thì tắt luôn tool

        db.close()

        # 3. VÀO MÀN HÌNH CHÍNH
        if current_user:
            window = POSWindow(current_user=current_user)
            window.show()
            app.exec() # Chặn code ở đây, chờ đến khi POSWindow đóng lại

            # 4. KIỂM TRA LÝ DO ĐÓNG CỬA SỔ
            if getattr(window, 'is_logged_out', False):
                # Nếu do bấm Đăng xuất -> Vòng lặp chạy lại -> Hiện Login
                continue 
            else:
                # Nếu do bấm X để tắt tool -> Lưu thời gian hiện tại vào Session -> Tắt app
                save_session(current_user.id)
                break

if __name__ == "__main__":
    main()