"""
controllers/auth_controller.py
Xác thực đăng nhập và ghi nhật ký đầy đủ vào NhatKyDangNhap.
"""

from database.db_config import get_session, ghi_nhat_ky_dang_nhap
from database.models import NhanVien


def authenticate_user(username: str, password: str):
    """
    Xác thực nhân viên.
    Trả về object NhanVien nếu thành công, None nếu thất bại.
    Tự động ghi NhatKyDangNhap cho mọi trường hợp.
    """
    if not username or not password:
        ghi_nhat_ky_dang_nhap(
            ten_dang_nhap=username or "(trống)",
            hanh_dong="Đăng nhập",
            ket_qua="Thất bại",
            ghi_chu="Tên đăng nhập hoặc mật khẩu để trống",
        )
        return None

    session = get_session()
    try:
        user = (session.query(NhanVien)
                .filter_by(ten_dang_nhap=username)
                .first())

        if user is None:
            # Tài khoản không tồn tại
            ghi_nhat_ky_dang_nhap(
                ten_dang_nhap=username,
                hanh_dong="Đăng nhập",
                ket_qua="Sai mật khẩu",
                ghi_chu="Tài khoản không tồn tại",
            )
            return None

        if user.trang_thai == "Tạm khóa":
            # Tài khoản bị khóa
            ghi_nhat_ky_dang_nhap(
                ten_dang_nhap=username,
                hanh_dong="Đăng nhập",
                ket_qua="Tài khoản khóa",
                ma_nv=user.id,
                ghi_chu=f"Tài khoản '{username}' đang bị tạm khóa",
            )
            return None

        if user.mat_khau != password:
            # Sai mật khẩu
            ghi_nhat_ky_dang_nhap(
                ten_dang_nhap=username,
                hanh_dong="Đăng nhập",
                ket_qua="Sai mật khẩu",
                ma_nv=user.id,
                ghi_chu="Mật khẩu không đúng",
            )
            return None

        # ── Đăng nhập thành công ────────────────────────────────
        ghi_nhat_ky_dang_nhap(
            ten_dang_nhap=username,
            hanh_dong="Đăng nhập",
            ket_qua="Thành công",
            ma_nv=user.id,
            ghi_chu=f"Chức vụ: {user.chuc_vu}",
        )

        # Trả về bản sao dữ liệu để dùng sau khi session đóng
        session.expunge(user)
        return user

    except Exception as e:
        ghi_nhat_ky_dang_nhap(
            ten_dang_nhap=username,
            hanh_dong="Đăng nhập",
            ket_qua="Thất bại",
            ghi_chu=f"Lỗi DB: {e}",
        )
        return None
    finally:
        session.close()


def logout_user(user: NhanVien, ma_phien: int = None):
    """
    Ghi nhật ký đăng xuất và đóng phiên làm việc (nếu có).
    Gọi từ POSWindow.logout() trước khi đóng cửa sổ.
    """
    if user:
        ghi_nhat_ky_dang_nhap(
            ten_dang_nhap=user.ten_dang_nhap,
            hanh_dong="Đăng xuất",
            ket_qua="Thành công",
            ma_nv=user.id,
        )

    if ma_phien:
        try:
            from database.db_config import dang_xuat
            dang_xuat(ma_phien)
        except Exception:
            pass