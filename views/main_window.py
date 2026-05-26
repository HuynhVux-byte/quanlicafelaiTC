import sys
import os
from PySide6.QtWidgets import (QApplication, QLineEdit, QMainWindow, QWidget, QHBoxLayout,
                               QVBoxLayout, QPushButton, QTableWidget,
                               QTableWidgetItem, QHeaderView, QLabel, QMessageBox,
                               QGridLayout, QScrollArea, QFrame, QDialog, QListWidget,
                               QListWidgetItem, QAbstractItemView, QSizePolicy, QCheckBox,
                               QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QCursor, QFont, QColor, QPixmap
from PySide6.QtMultimedia import QSoundEffect


from utils.permissions import co_quyen, yeu_cau_quyen
from database.db_config import ghi_nhat_ky_hoat_dong as _log

# Thư mục lưu ảnh sản phẩm
PRODUCT_IMAGE_DIR = "product_images"


def get_product_image_path(product_id: int) -> str | None:
    """Trả về đường dẫn ảnh nếu tồn tại, None nếu chưa có."""
    for ext in ("jpg", "jpeg", "png", "webp"):
        path = os.path.join(PRODUCT_IMAGE_DIR, f"{product_id}.{ext}")
        if os.path.exists(path):
            return path
    return None


# ================= CLASS TẠO THẺ SẢN PHẨM =================
class ProductCard(QFrame):
    def __init__(self, product, available_qty, click_callback):
        super().__init__()
        self.product = product
        self.setFixedSize(185, 105)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.click_callback = click_callback

        self.setStyleSheet("""
            ProductCard { background-color: #F9FAFB; border-radius: 12px; border: 1px solid #E5E7EB; }
            ProductCard:hover { border: 2px solid #3498DB; background-color: #F3F4F6; }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # ── Ảnh sản phẩm hoặc icon emoji fallback ──────────────────
        img_label = QLabel()
        img_label.setFixedSize(65, 65)
        img_label.setAlignment(Qt.AlignCenter)

        img_path = get_product_image_path(product.id)
        if img_path:
            pixmap = QPixmap(img_path).scaled(
                65, 65, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            # Crop ở giữa nếu ảnh không vuông
            if pixmap.width() > 65 or pixmap.height() > 65:
                x = (pixmap.width() - 65) // 2
                y = (pixmap.height() - 65) // 2
                pixmap = pixmap.copy(x, y, 65, 65)
            img_label.setPixmap(pixmap)
            img_label.setStyleSheet(
                "background-color: #FFFFFF; border-radius: 12px; border: none;"
            )
        else:
            # Fallback icon tự động theo tên món
            name_lower = product.ten_sp.lower()
            icon = "📦"
            if any(x in name_lower for x in ["cà phê", "cafe", "bạc xỉu", "espresso", "đen"]):
                icon = "☕"
            elif any(x in name_lower for x in ["trà", "tea", "matcha", "đào"]):
                icon = "🍵"
            elif any(x in name_lower for x in ["sinh tố", "nước ép", "vải", "cam", "chanh"]):
                icon = "🍹"
            elif any(x in name_lower for x in ["bánh", "cake", "mì", "sandwich", "croissant"]):
                icon = "🍰"
            elif any(x in name_lower for x in ["cơm", "phở", "bún", "mì xào", "lẩu"]):
                icon = "🍲"
            elif any(x in name_lower for x in ["khoai tây", "hướng dương", "khô bò", "snack"]):
                icon = "🍟"
            img_label.setText(icon)
            img_label.setStyleSheet(
                "background-color: #FFFFFF; border-radius: 12px; font-size: 35px; border: none;"
            )

        layout.addWidget(img_label)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        name_lbl = QLabel(product.ten_sp)
        name_lbl.setStyleSheet(
            "color: #1C1E21; font-weight: bold; font-size: 16px; border: none;"
        )
        name_lbl.setWordWrap(True)

        price_lbl = QLabel(f"{product.gia_ban:,.0f} đ")
        price_lbl.setStyleSheet(
            "color: #F1C40F; font-size: 15px; font-weight: bold; border: none;"
        )

        stock_lbl = QLabel()
        stock_lbl.setStyleSheet("border: none;")
        if available_qty == 0:
            stock_lbl.setText("HẾT HÀNG")
            stock_lbl.setStyleSheet(
                "color: #E74C3C; font-size: 13px; font-weight: bold; border: none;"
            )
            self.setEnabled(False)
            self.setStyleSheet(
                "ProductCard { background-color: #F3F4F6; border-radius: 12px;"
                " border: 1px solid #EF4444; }"
            )
        elif available_qty == -1:
            stock_lbl.setText("")
        else:
            stock_lbl.setText(f"Còn: {int(available_qty)} ly")
            stock_lbl.setStyleSheet(
                "color: #2ECC71; font-size: 13px; font-weight: bold; border: none;"
            )

        info_layout.addWidget(name_lbl)
        info_layout.addWidget(price_lbl)
        info_layout.addWidget(stock_lbl)
        layout.addLayout(info_layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.isEnabled():
            self.click_callback()


# ─── Helper: parse ghi chú cũ → điền lại vào các control dialog ───────────
def _restore_note(note: str, da_btns, da_sel, da_opts,
                  duong_btns, duong_sel, duong_opts,
                  tp_checks, topping_opts, txt_note):
    """Phân tích chuỗi ghi chú đã lưu và khôi phục về các widget."""
    if not note:
        return
    parts = [p.strip() for p in note.split("|")]
    free_parts = []
    for part in parts:
        matched = False
        for opt in da_opts:
            if opt in part:
                # Kích hoạt nút đá tương ứng
                da_btns[opt].click()
                matched = True
                break
        if matched:
            continue
        for opt in duong_opts:
            if opt in part:
                duong_btns[opt].click()
                matched = True
                break
        if matched:
            continue
        if part.startswith("Topping:"):
            tp_text = part[len("Topping:"):].strip()
            tp_names = [t.strip() for t in tp_text.split(",")]
            for cb in tp_checks:
                if cb.text() in tp_names:
                    cb.setChecked(True)
            matched = True
        if not matched:
            free_parts.append(part)
    txt_note.setText(" | ".join(free_parts))


# ================= CLASS CỬA SỔ CHÍNH =================
class POSWindow(QMainWindow):
    
    def show_customer_manager(self):
        if not yeu_cau_quyen(self.user.chuc_vu, "quan_ly_khach_hang", self):
            return
        _log(self.user.id, "Mở Quản lý Khách hàng", o_dau="Khách hàng")
        from views.customer_manager import CustomerManagerDialog
        CustomerManagerDialog(self).exec()

    def show_system_log(self):
        if not yeu_cau_quyen(self.user.chuc_vu, "xem_nhat_ky", self):
            return
        _log(self.user.id, "Mở Nhật ký hệ thống", o_dau="Nhật ký")
        from views.system_log import SystemLogDialog
        SystemLogDialog(self, chuc_vu=self.user.chuc_vu).exec()

    def show_admin_settings(self):
        if not yeu_cau_quyen(self.user.chuc_vu, "cai_dat_he_thong", self):
            return
        _log(self.user.id, "Mở Cài đặt hệ thống", o_dau="Hệ thống")
        from views.admin_settings import AdminSettingsDialog
        AdminSettingsDialog(self, actor_id=self.user.id).exec()
        self.apply_permissions()

    def __init__(self, current_user, ma_phien: int = None):
        super().__init__()
        self.user        = current_user
        self.ma_phien    = ma_phien   # ID PhienLamViec để check-out khi logout
        self._da_checkout = False     # True sau khi nhân viên đã hoàn tất check-out ca

        # Kiểm tra có ca được phân công hôm nay không (độc lập với ma_phien)
        self._co_ca = self._kiem_tra_co_ca()
        self.setWindowTitle("Hệ Thống Quản Lý Quán Cà Phê")
        self.resize(1200, 750)
        self.setStyleSheet("QMainWindow { background-color: #F3F4F6; } QLabel { color: #1F2937; } QCheckBox { color: #1F2937; }")

        # Ghi nhật ký đăng nhập vào POS
        _log(self.user.id, "Đăng nhập POS",
             f"{self.user.ten_nv} ({self.user.chuc_vu}) mở màn hình bán hàng",
             o_dau="POS")

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # ── NỬA TRÁI: MENU ──────────────────────────────────────────
        left_panel = QWidget()
        left_panel.setObjectName("left_panel")
        left_panel.setStyleSheet("#left_panel { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 15px; }")
        
        shadow_left = QGraphicsDropShadowEffect(self)
        shadow_left.setBlurRadius(15)
        shadow_left.setXOffset(0)
        shadow_left.setYOffset(4)
        shadow_left.setColor(QColor(0, 0, 0, 18))
        left_panel.setGraphicsEffect(shadow_left)

        left_layout = QVBoxLayout(left_panel)

        header_layout = QHBoxLayout()
        title_lbl = QLabel("📋 DANH MỤC MÓN")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #3B82F6;")
        header_layout.addWidget(title_lbl)

        # Nút CHECK-OUT CA (kết thúc ca làm, tính công)
        self.btn_ca_checkout = QPushButton("⏱️ Check-out Ca")
        self.btn_ca_checkout.setCursor(Qt.PointingHandCursor)
        self.btn_ca_checkout.setStyleSheet("""
            QPushButton {
                background-color: #F97316; color: white; font-weight: bold;
                padding: 8px 14px; border-radius: 6px; border: none; font-size: 13px;
            }
            QPushButton:hover { background-color: #EA580C; }
            QPushButton:pressed { background-color: #C2410C; }
        """)
        self.btn_ca_checkout.setToolTip("Kết thúc ca làm việc — tính giờ & chốt số liệu")
        self.btn_ca_checkout.clicked.connect(self.handle_ca_checkout)
        header_layout.addWidget(self.btn_ca_checkout, alignment=Qt.AlignRight)

        # Nút ĐĂNG XUẤT (thoát phiên ứng dụng)
        self.btn_logout = QPushButton(f"🚪 Đăng xuất ({self.user.ten_dang_nhap})")
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.setStyleSheet("""
            QPushButton {
                background-color: #EF4444; color: white; font-weight: bold;
                padding: 8px 14px; border-radius: 6px; border: none; font-size: 13px;
            }
            QPushButton:hover { background-color: #DC2626; }
            QPushButton:pressed { background-color: #B91C1C; }
        """)
        self.btn_logout.clicked.connect(self.logout)
        header_layout.addWidget(self.btn_logout, alignment=Qt.AlignRight)
        left_layout.addLayout(header_layout)

        # Thanh tìm kiếm
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Nhập tên món để tìm kiếm nhanh...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: #F8FAFC; border: 1px solid #CBD5E1;
                border-radius: 20px; padding: 10px 15px; color: #1F2937; font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #3B82F6; background-color: #FFFFFF; }
        """)
        self.search_bar.textChanged.connect(self.filter_products)
        left_layout.addWidget(self.search_bar)

        # ── Thanh lọc phân loại nằm ngang ───────────────────────
        self._active_category  = "Tất cả"   # danh mục đang chọn
        self._cached_products  = []          # phải khai báo trước refresh_product_grid()

        cat_scroll = QScrollArea()
        cat_scroll.setWidgetResizable(True)
        cat_scroll.setFixedHeight(46)
        cat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        cat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        cat_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._cat_bar_widget = QWidget()
        self._cat_bar_widget.setStyleSheet("background: transparent;")
        self._cat_bar_layout = QHBoxLayout(self._cat_bar_widget)
        self._cat_bar_layout.setContentsMargins(0, 0, 0, 0)
        self._cat_bar_layout.setSpacing(8)
        self._cat_bar_layout.setAlignment(Qt.AlignLeft)

        cat_scroll.setWidget(self._cat_bar_widget)
        left_layout.addWidget(cat_scroll)
        self._cat_scroll = cat_scroll

        # Grid sản phẩm
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background-color: transparent;")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setAlignment(Qt.AlignTop)

        self.refresh_product_grid()
        scroll_area.setWidget(self.grid_widget)
        left_layout.addWidget(scroll_area)

        # Nút chức năng dưới cùng
        func_layout = QHBoxLayout()
        func_layout.setSpacing(8)

        self.history_btn = QPushButton("📜 LỊCH SỬ")
        self.report_btn  = QPushButton("📊 BÁO CÁO")
        self.menu_btn    = QPushButton("⚙️ MENU")
        self.func_btn    = QPushButton("☰ CHỨC NĂNG ▾")   # popup menu

        for btn in [self.history_btn, self.report_btn, self.menu_btn]:
            btn.setMinimumHeight(45)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF; color: #374151; font-weight: bold;
                    border-radius: 8px; border: 1px solid #CBD5E1; font-size: 13px;
                }
                QPushButton:hover { background-color: #F8FAFC; color: #1E293B; border-color: #94A3B8; }
                QPushButton:pressed { background-color: #F1F5F9; }
            """)
            func_layout.addWidget(btn)

        self.func_btn.setMinimumHeight(45)
        self.func_btn.setCursor(Qt.PointingHandCursor)
        self.func_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E293B; color: white; font-weight: bold;
                border-radius: 8px; border: none; font-size: 13px;
            }
            QPushButton:hover { background-color: #334155; }
            QPushButton:pressed { background-color: #0F172A; }
        """)
        func_layout.addWidget(self.func_btn)

        self.history_btn.clicked.connect(self.show_history_dialog)
        self.report_btn.clicked.connect(self.show_report)
        self.menu_btn.clicked.connect(self.show_product_manager)
        self.func_btn.clicked.connect(self._show_func_menu)

        left_layout.addLayout(func_layout)
        main_layout.addWidget(left_panel, stretch=6)

        # ── NỬA PHẢI: HÓA ĐƠN ──────────────────────────────────────
        right_panel = QWidget()
        right_panel.setObjectName("right_panel")
        right_panel.setMinimumWidth(395)
        right_panel.setStyleSheet("#right_panel { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 15px; }")
        
        shadow_right = QGraphicsDropShadowEffect(self)
        shadow_right.setBlurRadius(15)
        shadow_right.setXOffset(0)
        shadow_right.setYOffset(4)
        shadow_right.setColor(QColor(0, 0, 0, 18))
        right_panel.setGraphicsEffect(shadow_right)

        self.right_layout = QVBoxLayout(right_panel)

        inv_title = QLabel("🧾 HÓA ĐƠN")
        inv_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #10B981;")
        inv_title.setAlignment(Qt.AlignCenter)
        self.right_layout.addWidget(inv_title)

        # ── Hóa đơn dạng Card (InvoiceTable từ pos_screen.py) ───
        from views.pos_screen import InvoiceTable as _InvoiceTable
        self.order_table = _InvoiceTable()
        self.order_table.order_changed.connect(self.update_grand_total)
        self.right_layout.addWidget(self.order_table)

        # ── Hàng nút KM + Điểm TV ────────────────────────────────
        action_row = QHBoxLayout()
        action_row.setSpacing(6)

        self.btn_apply_km = QPushButton("🎉 Khuyến mãi")
        self.btn_apply_km.setMinimumHeight(38)
        self.btn_apply_km.setCursor(Qt.PointingHandCursor)
        self.btn_apply_km.setStyleSheet("""
            QPushButton {
                background-color: #F97316; color: white; font-weight: bold;
                border-radius: 8px; font-size: 14px; border: none;
            }
            QPushButton:hover { background-color: #EA580C; }
            QPushButton:pressed { background-color: #C2410C; }
        """)
        self.btn_apply_km.clicked.connect(self._apply_khuyen_mai)
        action_row.addWidget(self.btn_apply_km)

        self.btn_loyalty = QPushButton("⭐ Điểm TV")
        self.btn_loyalty.setMinimumHeight(38)
        self.btn_loyalty.setCursor(Qt.PointingHandCursor)
        self.btn_loyalty.setStyleSheet("""
            QPushButton {
                background-color: #8B5CF6; color: white; font-weight: bold;
                border-radius: 8px; font-size: 14px; border: none;
            }
            QPushButton:hover { background-color: #7C3AED; }
            QPushButton:pressed { background-color: #6D28D9; }
        """)
        self.btn_loyalty.clicked.connect(self._open_loyalty)
        action_row.addWidget(self.btn_loyalty)

        self.right_layout.addLayout(action_row)

        # Label hiển thị KM đang áp dụng (ẩn khi chưa có)
        self.lbl_km_applied = QLabel("")
        self.lbl_km_applied.setStyleSheet(
            "background-color: #FFF7ED; border: 1px solid #FED7AA;"
            " border-radius: 6px; padding: 6px 10px;"
            " font-size: 12px; color: #EA580C; font-weight: bold;"
        )
        self.lbl_km_applied.setWordWrap(True)
        self.lbl_km_applied.setVisible(False)
        self.right_layout.addWidget(self.lbl_km_applied)

        # Label hiển thị khách thành viên đang liên kết (ẩn khi chưa có)
        self.lbl_loyalty_info = QLabel("")
        self.lbl_loyalty_info.setStyleSheet(
            "background-color: #FAF5FF; border: 1px solid #E9D5FF;"
            " border-radius: 6px; padding: 6px 10px;"
            " font-size: 12px; color: #7E22CE; font-weight: bold;"
        )
        self.lbl_loyalty_info.setWordWrap(True)
        self.lbl_loyalty_info.setVisible(False)
        self.right_layout.addWidget(self.lbl_loyalty_info)

        self.total_label = QLabel("Tổng cộng: 0 Đ")
        self.total_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #EF4444; background-color: transparent;"
        )
        self.right_layout.addWidget(self.total_label)

        self.checkout_btn = QPushButton("XUẤT HÓA ĐƠN")
        self.checkout_btn.setMinimumHeight(60)
        self.checkout_btn.setCursor(Qt.PointingHandCursor)
        self.checkout_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981; color: white; font-size: 18px;
                font-weight: bold; border-radius: 10px; border: none;
            }
            QPushButton:hover { background-color: #059669; }
            QPushButton:pressed { background-color: #047857; }
        """)
        self.checkout_btn.clicked.connect(self.handle_checkout)
        self.right_layout.addWidget(self.checkout_btn)

        main_layout.addWidget(right_panel, stretch=4)

        # Biến lưu khuyến mãi đang áp dụng
        self._applied_km  = None   # dict: {id, ten, loai, kieu, gia_tri, tran}
        self._applied_voucher_id = None   # int id Voucher nếu áp dụng voucher
        self._km_discount = 0     # số tiền đã giảm thực tế
        self._linked_kh   = None  # dict: {id, ten, sdt, hang, diem}
        

        # ── ÂM THANH ────────────────────────────────────────────────
        self.sound_beep = QSoundEffect()
        if os.path.exists("sounds/beep.wav"):
            self.sound_beep.setSource(QUrl.fromLocalFile("sounds/beep.wav"))
        self.sound_cash = QSoundEffect()
        if os.path.exists("sounds/cash.wav"):
            self.sound_cash.setSource(QUrl.fromLocalFile("sounds/cash.wav"))

        self._history_dialog  = None
        self.apply_permissions()


    # ================================================================
    # CÁC HÀM XỬ LÝ
    # ================================================================

    
    def apply_permissions(self):
        role = getattr(self.user, 'chuc_vu', 'Phục vụ') or 'Phục vụ'

        # Nút luôn hiện với mọi role
        self.history_btn.setVisible(co_quyen(role, "xem_lich_su"))
        self.report_btn.setVisible(co_quyen(role, "xem_bao_cao"))
        self.menu_btn.setVisible(co_quyen(role, "quan_ly_menu"))

        # Nút Check-out Ca: luôn hiện để cho phép check-out thủ công
        self.btn_ca_checkout.setVisible(True)

        # Nút CHỨC NĂNG: hiện nếu có ít nhất 1 quyền trong menu
        func_quyen = [
            "quan_ly_khach_hang", "xem_nhat_ky", "quan_ly_ca_lam",
            "quan_ly_khuyen_mai", "quan_ly_nhan_su", "cai_dat_he_thong",
            "quan_ly_phan_loai",
        ]
        self.func_btn.setVisible(any(co_quyen(role, q) for q in func_quyen))

        self.setWindowTitle(f"☕ POS Cafe — {role}: {self.user.ten_nv}")

    def _kiem_tra_co_ca(self) -> bool:
        """Trả True nếu nhân viên có ca được phân công hôm nay."""
        try:
            from datetime import date
            from database.db_config import get_session
            from database.models import PhanCongCaLam
            s = get_session()
            try:
                count = (s.query(PhanCongCaLam)
                         .filter_by(ma_nv=self.user.id, ngay_lam=date.today())
                         .count())
                return count > 0
            finally:
                s.close()
        except Exception:
            return False  # lỗi → ẩn nút cho an toàn

    def show_change_password(self):
        """Nhân viên tự đổi mật khẩu của chính mình."""
        from views.admin_settings import ChangePasswordDialog
        dlg = ChangePasswordDialog(
            emp_id=self.user.id,
            actor_id=self.user.id,   # tự đổi → bắt buộc nhập MK cũ
            parent=self
        )
        dlg.exec()

    def _show_func_menu(self):
        """Hiện popup menu CHỨC NĂNG theo quyền của user."""
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        role = getattr(self.user, 'chuc_vu', 'Phục vụ') or 'Phục vụ'

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #F0F2F5; color: #1C1E21;
                border: 1px solid #CCD0D5; border-radius: 8px;
                padding: 6px 0;
            }
            QMenu::item { padding: 10px 24px; font-size: 13px; font-weight: bold; }
            QMenu::item:selected { background-color: #3498DB; border-radius: 4px; }
            QMenu::separator { height: 1px; background: #CCD0D5; margin: 4px 12px; }
        """)

        def _add(icon, label, slot, quyen):
            if co_quyen(role, quyen):
                act = QAction(f"{icon}  {label}", self)
                act.triggered.connect(slot)
                menu.addAction(act)

        _add("👥", "Quản lý Khách hàng",  self.show_customer_manager,  "quan_ly_khach_hang")
        _add("🎉", "Khuyến mãi",           self.show_khuyen_mai,         "quan_ly_khuyen_mai")
        _add("🏷️", "Quản lý Phân Loại",   self.show_category_manager,   "quan_ly_phan_loai")

        if co_quyen(role, "quan_ly_ca_lam") or co_quyen(role, "xem_nhat_ky") or co_quyen(role, "quan_ly_nhan_su") or co_quyen(role, "quan_ly_phan_loai"):
            menu.addSeparator()

        _add("📅", "Phân công Ca làm",     self.show_shift_manager,     "quan_ly_ca_lam")
        _add("✅", "Điểm danh",             self.show_attendance,         "quan_ly_ca_lam")
        _add("📋", "Nhật ký hệ thống",     self.show_system_log,         "xem_nhat_ky")

        if co_quyen(role, "cai_dat_he_thong") or co_quyen(role, "quan_ly_nhan_su"):
            menu.addSeparator()

        _add("👤", "Quản lý Nhân sự",      self.show_admin_settings,     "quan_ly_nhan_su")
        _add("🛡️", "Cài đặt Hệ thống",    self.show_admin_settings,     "cai_dat_he_thong")

        # Đổi mật khẩu — mọi nhân viên đều có quyền tự đổi MK của mình
        menu.addSeparator()
        act_pw = QAction("🔑  Đổi Mật Khẩu", self)
        act_pw.triggered.connect(self.show_change_password)
        menu.addAction(act_pw)

        if not menu.actions():
            return

        # Hiện menu ngay dưới nút func_btn
        pos = self.func_btn.mapToGlobal(self.func_btn.rect().bottomLeft())
        menu.exec(pos)


    def filter_products(self, text):
        search_text = text.lower().strip()
        for i in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if not hasattr(widget, 'product'):
                    widget.setVisible(True)
                    continue
                visible = (not search_text) or (search_text in widget.product.ten_sp.lower())
                widget.setVisible(visible)

    def _rebuild_category_bar(self, categories: list):
        """Xóa và vẽ lại thanh nút phân loại nằm ngang."""
        while self._cat_bar_layout.count():
            item = self._cat_bar_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        all_cats = ["Tất cả"] + categories

        for cat in all_cats:
            btn = QPushButton(cat)
            btn.setFixedHeight(34)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            is_active = (cat == self._active_category)
            self._style_cat_btn(btn, is_active)
            btn.clicked.connect(lambda checked=False, c=cat: self._select_category(c))
            self._cat_bar_layout.addWidget(btn)

        self._cat_bar_layout.addStretch()

    def _style_cat_btn(self, btn: QPushButton, active: bool):
        if active:
            btn.setStyleSheet(
                "QPushButton {"
                " background-color: #3498DB; color: white; font-weight: bold;"
                " border-radius: 17px; font-size: 14px; padding: 0 16px;"
                " border: none;"
                "}"
            )
        else:
            btn.setStyleSheet(
                "QPushButton {"
                " background-color: #F1F5F9; color: #4B5563; font-weight: bold;"
                " border-radius: 17px; font-size: 14px; padding: 0 16px;"
                " border: 1px solid #E2E8F0;"
                "}"
                "QPushButton:hover {"
                " background-color: #E2E8F0; color: #1F2937; border: 1px solid #CBD5E1;"
                "}"
            )

    def _select_category(self, cat: str):
        """Chọn tab phân loại -> cập nhật style nút + vẽ lại grid."""
        self._active_category = cat
        for i in range(self._cat_bar_layout.count()):
            item = self._cat_bar_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QPushButton):
                b = item.widget()
                self._style_cat_btn(b, b.text() == cat)
        self._draw_product_grid(self._cached_products)

    def refresh_product_grid(self):
        """Xóa và vẽ lại toàn bộ grid sản phẩm từ DB."""
        from database.db_config import get_session
        from database.models import SanPham
        session = get_session()
        try:
            self._cached_products = (
                session.query(SanPham)
                .filter(SanPham.trang_thai == 'Đang bán')
                .order_by(SanPham.danh_muc, SanPham.ten_sp)
                .all()
            )
        finally:
            session.close()

        seen = []
        for sp in self._cached_products:
            cat = (sp.danh_muc or "Khác").strip()
            if cat not in seen:
                seen.append(cat)

        self._rebuild_category_bar(seen)
        self._draw_product_grid(self._cached_products)

    def _draw_product_grid(self, products):
        """Vẽ lại grid theo _active_category, có header separator mỗi nhóm."""
        from collections import OrderedDict
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self._active_category == "Tất cả":
            filtered = products
        else:
            filtered = [p for p in products
                        if (p.danh_muc or "Khác").strip() == self._active_category]

        groups: OrderedDict = OrderedDict()
        for sp in filtered:
            cat = (sp.danh_muc or "Khác").strip()
            groups.setdefault(cat, []).append(sp)

        grid_row = 0
        COLS = 3

        for cat_name, sp_list in groups.items():
            if self._active_category == "Tất cả":
                header_widget = QWidget()
                header_widget.setStyleSheet("background: transparent;")
                h_layout = QHBoxLayout(header_widget)
                h_layout.setContentsMargins(4, 8, 4, 4)
                h_layout.setSpacing(8)

                lbl = QLabel(f"  {cat_name}")
                lbl.setStyleSheet(
                    "color: #3498DB; font-size: 16px; font-weight: bold;"
                    " background: transparent; border: none;"
                )
                h_layout.addWidget(lbl)

                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setStyleSheet("color: #CCD0D5; background-color: #CCD0D5; border: none;")
                line.setFixedHeight(1)
                h_layout.addWidget(line, stretch=1)

                self.grid_layout.addWidget(header_widget, grid_row, 0, 1, COLS)
                grid_row += 1

            col = 0
            for product in sp_list:
                p_data = {
                    'id':    product.id,
                    'name':  product.ten_sp,
                    'price': product.gia_ban,
                }
                card = ProductCard(
                    product, -1,
                    lambda p=p_data: self.add_to_order(p)
                )
                self.grid_layout.addWidget(card, grid_row, col)
                col += 1
                if col >= COLS:
                    col = 0
                    grid_row += 1

            if col != 0:
                grid_row += 1

    def highlight_total(self):
        original_style = self.total_label.styleSheet()
        highlight = original_style + " background-color: rgba(39,174,96,0.4); border-radius: 8px;"
        self.total_label.setStyleSheet(highlight)
        QTimer.singleShot(200, lambda: self.total_label.setStyleSheet(original_style))

    def update_grand_total(self):
        grand_total = self.order_table.grand_total()
        tax = grand_total * 0.10
        subtotal = grand_total + tax

        # Tự động tìm và áp dụng KM tốt nhất nếu người dùng không chọn thủ công
        if not getattr(self, '_km_user_picked', False):
            self._auto_apply_best_km()

        # Tính giảm KM
        self._km_discount = 0
        km_line = ""
        if self._applied_km:
            km = self._applied_km

            if km.get("_mxy"):
                # MuaXTangY — kiểm tra lại điều kiện mỗi khi hóa đơn thay đổi
                ten_x    = km["ten_x"]
                sl_can   = km["sl_can_mua"]
                sl_tang  = km["sl_tang"]
                ten_y    = km["ten_y"]
                qty_co   = sum(
                    it.get("qty", 0)
                    for it in self.order_table.get_items()
                    if not it.get("is_gift") and it.get("name", "") == ten_x
                )
                if qty_co < sl_can:
                    # Không còn đủ điều kiện → xóa quà + clear KM
                    self.order_table.remove_gifts()
                    self._applied_km = None
                    self._km_user_picked = False
                else:
                    # Cập nhật lại số lượng quà nếu qty_co thay đổi
                    so_bo     = qty_co // sl_can
                    tong_tang = sl_tang   # luôn tặng đúng sl_tang cố định
                    if tong_tang != km.get("tong_tang"):
                        km["tong_tang"] = tong_tang
                        self.order_table.remove_gifts()
                        self.order_table.add_gift(ten_y + " (Quà tặng)", tong_tang)
                    km_line = (
                        f"<span style='font-size:13px; color:#27AE60;'>"
                        f"🎁 KM [{km['ten']}]: Tặng {tong_tang}× {ten_y}"
                        f"</span><br>"
                    )
            elif km["kieu"] == "PhanTram":
                giam = subtotal * km["gia_tri"] / 100
                if km.get("tran") and giam > km["tran"]:
                    giam = km["tran"]
                self._km_discount = giam
                km_line = (
                    f"<span style='font-size:13px; color:#E67E22;'>"
                    f"🎉 KM [{km['ten']}]: -{int(self._km_discount):,.0f} đ"
                    f"</span><br>"
                )
            elif km["kieu"] == "TienMat":
                self._km_discount = min(km["gia_tri"], subtotal)
                km_line = (
                    f"<span style='font-size:13px; color:#E67E22;'>"
                    f"🎉 KM [{km['ten']}]: -{int(self._km_discount):,.0f} đ"
                    f"</span><br>"
                )

        total_to_pay = max(0, subtotal - self._km_discount)
        self.total_label.setText(
            f"<div style='text-align:right; background-color:transparent;'>"
            f"<span style='font-size:16px; color:#BDC3C7;'>Tổng tiền món: {int(grand_total):,.0f} đ</span><br>"
            f"<span style='font-size:16px; color:#E74C3C;'>Thuế VAT (10%): +{int(tax):,.0f} đ</span><br>"
            f"{km_line}"
            f"<b style='font-size:26px; color:#27AE60;'>CẦN THANH TOÁN: {int(total_to_pay):,.0f} Đ</b>"
            f"</div>"
        )

        # Cập nhật label KM đang áp dụng
        if self._applied_km:
            km = self._applied_km
            if km.get("_mxy"):
                tong_t = km.get("tong_tang", km["sl_tang"])
                mo_ta  = f"Mua {km['sl_can_mua']} {km['ten_x']}  →  Tặng {tong_t} {km['ten_y']} (miễn phí)"
                self.lbl_km_applied.setText(f"✓ {km['ten']}\n   {mo_ta}")
            elif km["kieu"] == "PhanTram":
                mo_ta = f"Giảm {int(km['gia_tri'])}%"
                if km.get("tran"):
                    mo_ta += f" (tối đa {int(km['tran']):,}đ)"
                self.lbl_km_applied.setText(
                    f"✓ {km['ten']}\n"
                    f"   {mo_ta}  →  -{int(self._km_discount):,}đ"
                )
            elif km["kieu"] == "TienMat":
                mo_ta = f"Giảm {int(km['gia_tri']):,}đ"
                self.lbl_km_applied.setText(
                    f"✓ {km['ten']}\n"
                    f"   {mo_ta}  →  -{int(self._km_discount):,}đ"
                )
            else:
                self.lbl_km_applied.setText(f"✓ {km['ten']}")
            self.lbl_km_applied.setVisible(True)
        else:
            self.lbl_km_applied.setVisible(False)

    def _rebuild_action_buttons(self):
        pass

    def change_qty(self, row, delta, price):
        pass

    def add_to_order(self, product):
        """Thêm món vào bảng order thông qua InvoiceTable."""
        self.order_table.add_item(product['name'], product['price'])
        try:
            self.sound_beep.play()
        except Exception:
            pass
        try:
            self.highlight_total()
        except Exception:
            pass
        self.update_grand_total()
        _log(self.user.id, "Thêm món vào order",
             f"Thêm '{product['name']}' — {int(product['price']):,}đ",
             o_dau="POS - Order")

    # ── Áp dụng khuyến mãi ─────────────────────────────────────
    def _auto_apply_best_km(self):
        """
        Tự động tìm và áp KM tốt nhất hợp lệ cho đơn hàng hiện tại.
        Chỉ áp dụng khi chưa có KM nào. Không hỏi xác nhận — âm thầm áp.

        Quy tắc bắt buộc:
          • KHÔNG auto-apply KM đổi điểm (la_doi_diem=1) — phải chọn thủ công
          • KHÔNG auto-apply khi chưa liên kết khách hàng với KM cá nhân
          • KHÔNG auto-apply MuaXTangY
        """
        try:
            from datetime import datetime, date
            from database.db_config import get_session
            from database.models import KhuyenMai

            grand_total = self.order_table.grand_total()
            if grand_total <= 0:
                return

            now   = datetime.now()
            today = date.today()

            s = get_session()
            try:
                kms = s.query(KhuyenMai).filter_by(trang_thai="Đang chạy").all()
            finally:
                s.close()

            best_km   = None
            best_giam = 0

            for km in kms:
                # ── Bỏ qua KM đổi điểm — phải chọn thủ công ──────
                if int(getattr(km, 'la_doi_diem', 0) or 0):
                    continue
                # Bỏ qua nếu loai_nhom là DoiDiem
                if getattr(km, 'loai_nhom', 'Chung') == 'DoiDiem':
                    continue

                # ── Bỏ qua MuaXTangY ──────────────────────────────
                if km.loai_km == "MuaXTangY":
                    continue

                # ── Kiểm tra ngày ──────────────────────────────────
                if km.ngay_bat_dau and today < km.ngay_bat_dau:
                    continue
                if km.ngay_ket_thuc and today > km.ngay_ket_thuc:
                    continue

                # ── Kiểm tra khung giờ ─────────────────────────────
                gio_tu  = getattr(km, 'gio_tu',  None)
                gio_den = getattr(km, 'gio_den', None)
                if gio_tu and gio_den:
                    t = now.time().replace(second=0, microsecond=0)
                    if not (gio_tu <= t <= gio_den):
                        continue

                # ── Kiểm tra lượt dùng ─────────────────────────────
                if km.so_luot_toi_da and km.so_luot_da_dung and \
                        km.so_luot_da_dung >= km.so_luot_toi_da:
                    continue

                # ── Kiểm tra điều kiện tổng tiền ──────────────────
                dk = km.dk_tong_tien_tu or 0
                if grand_total < dk:
                    continue

                # ── Tính tiền giảm ─────────────────────────────────
                if km.kieu_giam == "PhanTram":
                    giam = grand_total * (km.gia_tri_giam or 0) / 100
                    if km.toi_da_giam:
                        giam = min(giam, km.toi_da_giam)
                else:
                    giam = km.gia_tri_giam or 0

                if giam > best_giam:
                    best_giam = giam
                    best_km   = km

            if not best_km or best_giam <= 0:
                # Nếu trước đó đang áp dụng KM tự động -> gỡ bỏ
                self._applied_km  = None
                self._km_discount = 0.0
                return

            self._applied_km  = {
                "id":      best_km.id,
                "ten":     best_km.ten_km,
                "loai":    best_km.loai_km,
                "kieu":    best_km.kieu_giam,
                "gia_tri": best_km.gia_tri_giam,
                "tran":    best_km.toi_da_giam,
            }
            self._km_discount = best_giam
        except Exception:
            pass  # Lỗi auto-km không làm crash app

    # ── Auto-migrate: thêm cột la_doi_diem + diem_can nếu chưa có ──────────
    @staticmethod
    def _migrate_km_cols():
        try:
            from database.db_config import get_session as _gs
            import sqlalchemy as sa
            s = _gs()
            conn = s.get_bind().connect()
            insp = sa.inspect(conn)
            cols = {c["name"] for c in insp.get_columns("khuyen_mai")}
            new_cols = {
                "la_doi_diem": "INTEGER DEFAULT 0",
                "diem_can":    "INTEGER DEFAULT 0",
            }
            for col, typ in new_cols.items():
                if col not in cols:
                    conn.execute(sa.text(f"ALTER TABLE khuyen_mai ADD COLUMN {col} {typ}"))
            conn.commit(); conn.close(); s.close()
        except Exception:
            pass

    def _apply_khuyen_mai(self):
        """
        Dialog 2 tab:
          Tab 1 — KM Chung: hiển thị cho mọi KH, KHÔNG bao gồm KM đổi điểm.
          Tab 2 — Voucher & Đổi Điểm:
              - Voucher cá nhân: chỉ hiện khi có KH liên kết, thuộc về KH đó.
              - KM đổi điểm (la_doi_diem=1): chỉ hiện khi có KH liên kết + đủ điểm.
        """
        if self.order_table.rowCount() == 0:
            QMessageBox.warning(self, "Hóa đơn trống", "Hãy thêm món trước!")
            return

        # Kiểm tra tổng tiền thực sự > 0
        grand_total_check = self.order_table.grand_total()
        if grand_total_check <= 0:
            QMessageBox.warning(
                self, "Hóa đơn trống",
                "Tổng tiền đơn hàng = 0đ.\n"
                "Vui lòng thêm món có giá tiền hợp lệ trước khi áp dụng khuyến mãi."
            )
            return

        self._migrate_km_cols()

        from database.db_config import get_session
        from database.models import KhuyenMai, Voucher
        from datetime import date

        # Lấy tổng tiền trực tiếp từ InvoiceTable (đúng qty * price)
        grand_total = self.order_table.grand_total()
        subtotal = grand_total * 1.10

        session = get_session()
        try:
            today = date.today()
            kms   = session.query(KhuyenMai).filter_by(trang_thai="Đang chạy").all()

            def _tinh_giam(km):
                if km.kieu_giam == "PhanTram":
                    pct = min(float(km.gia_tri_giam or 0), 100.0)  # cap tối đa 100%
                    g   = subtotal * pct / 100
                    if km.toi_da_giam: g = min(g, float(km.toi_da_giam))
                    return g
                elif km.kieu_giam == "TienMat":
                    return min(float(km.gia_tri_giam or 0), subtotal)
                return 0

            def _base_ok(km):
                if km.ngay_bat_dau and km.ngay_bat_dau > today: return False
                if km.ngay_ket_thuc and km.ngay_ket_thuc < today: return False
                if km.dk_tong_tien_tu and subtotal < km.dk_tong_tien_tu: return False
                return True

            kh_id   = self._linked_kh["id"]   if self._linked_kh else None
            kh_diem = self._linked_kh["diem"] if self._linked_kh else 0

            # ── Nhóm 1: KM Chung (la_doi_diem = 0 hoặc NULL) ─────────────
            km_chung = []
            km_canhan = []
            for km in kms:
                if not _base_ok(km): continue
                if int(getattr(km, "la_doi_diem", 0) or 0): continue
                is_canhan = (getattr(km, "nhom_khuyen_mai", "") == "CaNhan")

                loai_km = km.loai_km or ""

                if loai_km == "MuaXTangY":
                    # Kiểm tra điều kiện ngay khi build list
                    ma_sp_mua   = km.ma_sp
                    sl_can_mua  = int(km.so_luong_mua or 1)
                    sl_tang     = int(km.so_luong_tang or 1)
                    ma_sp_tang  = km.ma_sp_tang
                    # Đếm qty sp mua trong hóa đơn
                    sp_cache    = {}
                    qty_co      = 0
                    ten_x = ten_y = "?"
                    try:
                        from database.models import SanPham as _SP
                        _s2 = get_session()
                        sp_x = _s2.get(_SP, ma_sp_mua) if ma_sp_mua else None
                        sp_y = _s2.get(_SP, ma_sp_tang) if ma_sp_tang else None
                        ten_x = sp_x.ten_sp if sp_x else f"SP#{ma_sp_mua}"
                        ten_y = sp_y.ten_sp if sp_y else f"SP#{ma_sp_tang}"
                        _s2.close()
                    except Exception:
                        pass
                    for it in self.order_table.get_items():
                        if not it.get("is_gift") and it.get("name","") == ten_x:
                            qty_co += it.get("qty", 0)
                    du_dk = qty_co >= sl_can_mua
                    tong_tang = sl_tang if du_dk else 0
                    g = 0.0  # MuaXTangY không tính tiền giảm số
                    d_km = {
                        "id": km.id, "ten": km.ten_km or "—",
                        "loai": loai_km, "kieu": "",
                        "gia_tri": 0.0, "tran": None, "dk_min": 0.0,
                        "diem_can": 0, "loai_nhom": "CaNhan" if is_canhan else "Chung", "_giam": 0.0,
                        # Extra fields cho MuaXTangY
                        "_mxy": True, "is_km_table": True,
                        "ten_x": ten_x, "ten_y": ten_y,
                        "sl_can_mua": sl_can_mua, "sl_tang": sl_tang,
                        "tong_tang": tong_tang, "du_dk": du_dk,
                        "msg": f"✅Mua {sl_can_mua} {ten_x}  →  Tặng {tong_tang} {ten_y} (miễn phí)"
                    }
                    if is_canhan: km_canhan.append(d_km)
                    else: km_chung.append(d_km)
                else:
                    g = _tinh_giam(km)
                    d_km = {
                        "id": km.id, "ten": km.ten_km or "—",
                        "loai": loai_km, "kieu": km.kieu_giam or "",
                        "gia_tri": float(km.gia_tri_giam or 0),
                        "tran": float(km.toi_da_giam or 0) or None,
                        "dk_min": float(km.dk_tong_tien_tu or 0),
                        "diem_can": 0, "loai_nhom": "CaNhan" if is_canhan else "Chung", "_giam": g,
                        "is_km_table": True
                    }
                    if is_canhan: km_canhan.append(d_km)
                    else: km_chung.append(d_km)
            km_chung.sort(key=lambda x: -x["_giam"])

            # ── Nhóm 2: KM Đổi Điểm (la_doi_diem = 1) + Voucher cá nhân ──
            km_doi_diem = []
            if kh_id:
                for km in kms:
                    if not _base_ok(km): continue
                    if not int(getattr(km, "la_doi_diem", 0) or 0): continue
                    diem_can = int(getattr(km, "diem_can", 0) or 0)
                    if diem_can > 0 and kh_diem < diem_can: continue

                    loai_km = km.loai_km or ""

                    if loai_km == "MuaXTangY":
                        # Lấy tên SP mua và tặng
                        try:
                            from database.models import SanPham as _SP2
                            _s3 = get_session()
                            _spx = _s3.get(_SP2, km.ma_sp)      if km.ma_sp      else None
                            _spy = _s3.get(_SP2, km.ma_sp_tang) if km.ma_sp_tang else None
                            _tx  = _spx.ten_sp if _spx else "sản phẩm"
                            _ty  = _spy.ten_sp if _spy else "sản phẩm"
                            _s3.close()
                        except Exception:
                            _tx = _ty = "sản phẩm"
                        sl_x = int(km.so_luong_mua  or 1)
                        sl_y = int(km.so_luong_tang or 1)
                        km_doi_diem.append({
                            "id": km.id, "ten": km.ten_km or "—",
                            "loai": loai_km, "kieu": "",
                            "gia_tri": 0.0, "tran": None,
                            "dk_min": float(km.dk_tong_tien_tu or 0),
                            "diem_can": diem_can, "loai_nhom": "DoiDiem", "_giam": 0.0,
                            "_mxy": True,
                            "ten_x": _tx, "ten_y": _ty,
                            "sl_can_mua": sl_x, "sl_tang": sl_y,
                            "tong_tang": sl_y, "du_dk": True,
                            "msg": f"Mua {sl_x} {_tx}  →  Tặng {sl_y} {_ty} miễn phí",
                        })
                    else:
                        g = _tinh_giam(km)
                        km_doi_diem.append({
                            "id": km.id, "ten": km.ten_km or "—",
                            "loai": loai_km, "kieu": km.kieu_giam or "",
                            "gia_tri": float(km.gia_tri_giam or 0),
                            "tran": float(km.toi_da_giam or 0) or None,
                            "dk_min": float(km.dk_tong_tien_tu or 0),
                            "diem_can": diem_can, "loai_nhom": "DoiDiem", "_giam": g,
                        })
                km_doi_diem.sort(key=lambda x: -x["_giam"])

            # Voucher cá nhân của KH đang liên kết
            vouchers = []
            if kh_id:
                vcs = (session.query(Voucher)
                       .filter_by(ma_kh=kh_id, trang_thai="Chưa dùng").all())
                for vc in vcs:
                    if vc.ngay_het_han and vc.ngay_het_han < today: continue
                    if vc.dieu_kien_toi_thieu and subtotal < vc.dieu_kien_toi_thieu: continue
                    if vc.loai_giam == "PhanTram":
                        g = subtotal * float(vc.gia_tri_giam or 0) / 100
                        if vc.toi_da_giam: g = min(g, float(vc.toi_da_giam))
                    else:
                        g = min(float(vc.gia_tri_giam or 0), subtotal)
                    vouchers.append({
                        "id": vc.id, "ten": vc.ten_voucher or f"Voucher {vc.ma_code}",
                        "ma_code": vc.ma_code,
                        "loai": "Voucher", "kieu": vc.loai_giam or "TienMat",
                        "gia_tri": float(vc.gia_tri_giam or 0),
                        "tran": float(vc.toi_da_giam or 0) or None,
                        "dk_min": float(vc.dieu_kien_toi_thieu or 0),
                        "diem_can": 0, "loai_nhom": "Voucher", "_giam": g,
                        "is_km_table": False
                    })
                vouchers.extend(km_canhan)
                vouchers.sort(key=lambda x: -x["_giam"])
            else:
                vouchers.extend(km_canhan)
                vouchers.sort(key=lambda x: -x["_giam"])

        finally:
            session.close()

        # ── Dialog 2 tab ─────────────────────────────────────────
        from PySide6.QtWidgets import (QTabWidget, QListWidget, QListWidgetItem,
            QTableWidget, QTableWidgetItem, QHeaderView)
        from PySide6.QtGui import QColor, QFont as _QFont

        DLG_STYLE = (
            "QDialog,QWidget{background:#FFFFFF;color: #1C1E21;}"
            "QLabel{background:transparent;}"
            "QTabWidget::pane{border:none;background:#FFFFFF;}"
            "QTabBar::tab{background:#F0F2F5;color:#606770;padding:9px 20px;"
            "  border-radius:6px 6px 0 0;font-weight:bold;font-size:13px;}"
            "QTabBar::tab:selected{background:#E67E22;color:white;}"
            "QTableWidget{background:#FFFFFF;border:none;border-radius:8px;"
            "  color: #1C1E21;font-size:13px;}"
            "QTableWidget::item{padding:8px 10px;border-bottom:1px solid #F0F2F5;}"
            "QTableWidget::item:selected{background:#CCD0D5;color: #1C1E21;}"
            "QHeaderView::section{background:#F0F2F5;color:#606770;padding:7px 10px;"
            "  border:none;font-weight:bold;font-size:12px;}"
            "QPushButton{border-radius:6px;font-weight:bold;font-size:13px;"
            "  color: #1C1E21;padding:8px 16px;border:none;}"
        )

        dlg = QDialog(self)
        dlg.setWindowTitle("🎉 Khuyến Mãi & Voucher")
        dlg.resize(560, 500)
        dlg.setStyleSheet(DLG_STYLE)
        dv = QVBoxLayout(dlg)
        dv.setContentsMargins(16, 14, 16, 14); dv.setSpacing(10)

        # Header
        hdr = QHBoxLayout()
        hdr_lbl = QLabel("<b style='color:#E67E22;font-size:15px;'>🎉  Chọn Khuyến Mãi / Voucher</b>")
        hdr_lbl.setTextFormat(Qt.RichText)
        hdr.addWidget(hdr_lbl); hdr.addStretch()
        total_lbl = QLabel(f"<span style='color:#606770;font-size:12px;'>Đơn: {int(subtotal):,.0f} đ</span>")
        total_lbl.setTextFormat(Qt.RichText)
        hdr.addWidget(total_lbl)
        dv.addLayout(hdr)

        # ── Helper tạo bảng KM ────────────────────────────────────
        def _make_km_table(data_list, show_diem=False):
            cols = ["Ưu đãi", "Tiết kiệm"]
            if show_diem: cols = ["Ưu đãi", "Cần điểm", "Tiết kiệm"]
            tbl = QTableWidget(0, len(cols))
            tbl.setHorizontalHeaderLabels(cols)
            tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            for c in range(1, len(cols)):
                tbl.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
            tbl.verticalHeader().setVisible(False)
            tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
            tbl.setSelectionMode(QAbstractItemView.SingleSelection)
            tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
            tbl.setShowGrid(False)

            row_data = []
            for d in data_list:
                dk = f"  ·  Đơn từ {int(d['dk_min']):,}đ" if d.get("dk_min") else ""
                _giam_val = d.get("_giam", 0) or 0

                if d.get("_mxy"):
                    # MuaXTangY — msg đã rõ
                    uu = d.get("msg") or (
                        f"Mua {d.get('sl_can_mua',1)} {d.get('ten_x','SP')}"
                        f"  →  Tặng {d.get('sl_tang',1)} {d.get('ten_y','SP')} miễn phí"
                    )
                    dk = ""
                    sv = (
                        f"Tặng {d.get('sl_tang',1)} {d.get('ten_y','SP')}"
                        if d.get("du_dk") else "Chưa đủ điều kiện"
                    )

                elif d["kieu"] == "PhanTram":
                    pct = min(float(d["gia_tri"]), 100.0)   # cap 100%
                    uu  = f"Giảm {int(pct)}% cho toàn đơn"
                    if d.get("tran"): uu += f" (tối đa {int(d['tran']):,}đ)"
                    sv  = f"-{int(_giam_val):,}đ" if _giam_val > 0 else "—"

                elif d["kieu"] == "TienMat":
                    uu = f"Giảm {int(d['gia_tri']):,}đ cho toàn đơn"
                    sv = f"-{int(_giam_val):,}đ" if _giam_val > 0 else "—"

                elif d.get("loai_nhom") == "Voucher":
                    # Voucher cá nhân — đọc kieu + gia_tri từ voucher
                    kieu_v = d.get("kieu", "")
                    gt_v   = float(d.get("gia_tri", 0))
                    tran_v = d.get("tran")
                    if kieu_v == "PhanTram" and gt_v > 0:
                        pct_v = min(gt_v, 100.0)
                        uu = f"Giảm {int(pct_v)}% cho toàn đơn"
                        if tran_v: uu += f" (tối đa {int(tran_v):,}đ)"
                    elif kieu_v == "TienMat" and gt_v > 0:
                        uu = f"Giảm {int(gt_v):,}đ cho toàn đơn"
                    else:
                        ten_v = (d.get("ten") or "Voucher")
                        uu = ten_v.replace("[Đổi điểm] ","").replace("[đổi điểm] ","")
                    sv = f"-{int(_giam_val):,}đ" if _giam_val > 0 else "—"

                else:
                    uu = d.get("ten") or d.get("loai") or "Ưu đãi"
                    sv = "—"

                # Đổi điểm: thêm số điểm cần ở đầu
                if d.get("loai_nhom") == "DoiDiem" and d.get("diem_can", 0):
                    uu = f"Dùng {int(d['diem_can']):,} điểm  →  {uu}"

                r = tbl.rowCount(); tbl.insertRow(r); tbl.setRowHeight(r, 44)
                row_text = f"  {d['ten']}  ·  {uu}{dk}"
                it0 = QTableWidgetItem(row_text)
                it0.setToolTip(f"{d['ten']}\n{uu}{dk}")
                if d.get("_mxy"):
                    it0.setForeground(QColor("#2ECC71" if d.get("du_dk") else "#E74C3C"))
                elif not d.get("du_dk", True):
                    it0.setForeground(QColor("#E74C3C"))
                else:
                    it0.setForeground(QColor("#1C1E21"))
                it0.setData(Qt.UserRole, d)
                tbl.setItem(r, 0, it0)

                if show_diem:
                    dc = d.get("diem_can", 0)
                    it_d = QTableWidgetItem(f"🔢 {dc:,}" if dc else "Không cần")
                    it_d.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                    it_d.setForeground(QColor("#F1C40F") if dc else QColor("#2ECC71"))
                    tbl.setItem(r, 1, it_d)
                    col_sv = 2
                else:
                    col_sv = 1

                it_sv = QTableWidgetItem(sv)
                it_sv.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                it_sv.setForeground(QColor("#2ECC71") if d.get("_giam") else QColor("#CCD0D5"))
                f2 = _QFont("Segoe UI", 13, _QFont.Bold); it_sv.setFont(f2)
                tbl.setItem(r, col_sv, it_sv)
                row_data.append(d)

            if row_data: tbl.selectRow(0)
            return tbl, row_data

        # ── Tab 1: KM Chung (mọi KH) ─────────────────────────────
        tab_chung = QWidget(); tab_chung.setStyleSheet("background:transparent;")
        tc = QVBoxLayout(tab_chung); tc.setContentsMargins(0,8,0,0); tc.setSpacing(8)

        if km_chung:
            best = km_chung[0]
            tip = QLabel(
                f"✨ <b>Tốt nhất:</b> {best['ten']}  —  "
                f"giảm <b style='color:#E67E22;'>{int(best['_giam']):,}đ</b>"
            )
            tip.setTextFormat(Qt.RichText)
            tip.setStyleSheet(
                "background:#F0F2F5;border:1px solid #27AE60;border-radius:6px;"
                "padding:7px 12px;font-size:12px;color:#A9DFBF;"
            )
            tc.addWidget(tip)
            tbl_chung, chung_data = _make_km_table(km_chung)
            tc.addWidget(tbl_chung)
        else:
            lbl_no = QLabel("😔  Không có khuyến mãi nào phù hợp với đơn này.")
            lbl_no.setStyleSheet("color:#606770;font-size:13px;padding:20px 0;")
            lbl_no.setAlignment(Qt.AlignCenter)
            tc.addWidget(lbl_no)
            tbl_chung, chung_data = None, []

        # ── Tab 2: Voucher & Đổi Điểm (chỉ khi có KH liên kết) ──
        tab_ca_nhan = QWidget(); tab_ca_nhan.setStyleSheet("background:transparent;")
        tca = QVBoxLayout(tab_ca_nhan); tca.setContentsMargins(0,8,0,0); tca.setSpacing(8)

        tbl_vc, vc_data = None, []
        tbl_dd, dd_data = None, []

        if vouchers:
            tca.addWidget(QLabel("<b style='color:#3498DB;'>🎟 Voucher:</b>"))
            tbl_vc, vc_data = _make_km_table(vouchers)
            tbl_vc.setMaximumHeight(160)
            tca.addWidget(tbl_vc)

        if not kh_id:
            lbl_login = QLabel(
                "🔒  Vui lòng <b>liên kết số điện thoại khách hàng</b>\n"
                "để xem voucher cá nhân và ưu đãi đổi điểm."
            )
            lbl_login.setTextFormat(Qt.RichText)
            lbl_login.setWordWrap(True)
            lbl_login.setAlignment(Qt.AlignCenter)
            lbl_login.setStyleSheet(
                "background:#F0F2F5;border:1px solid #E67E22;border-radius:8px;"
                "color:#E67E22;padding:24px;font-size:13px;"
            )
            tca.addWidget(lbl_login)
        else:
            kh_info = QLabel(
                f"👤 <b>{self._linked_kh['ten']}</b>"
                f"  |  SĐT: {self._linked_kh['sdt']}"
                f"  |  🌟 Điểm: <b style='color:#F1C40F;'>{kh_diem:,}</b>"
            )
            kh_info.setTextFormat(Qt.RichText)
            kh_info.setStyleSheet(
                "background:#F0F2F5;border:1px solid #27AE60;border-radius:6px;"
                "padding:8px 12px;font-size:12px;color:#A9DFBF;"
            )
            tca.addWidget(kh_info)

            if km_doi_diem:
                lbl_dd_title = QLabel(
                    f"<b style='color:#E67E22;'>🔢 Đổi điểm (bạn có {kh_diem:,} điểm):</b>"
                    f"<span style='color:#606770;font-size:11px;'>"
                    f"  — Đúp chuột vào dòng để đổi điểm lấy voucher</span>"
                )
                lbl_dd_title.setTextFormat(Qt.RichText)
                tca.addWidget(lbl_dd_title)
                tbl_dd, dd_data = _make_km_table(km_doi_diem, show_diem=True)

                # ── Double-click vào dòng đổi điểm → trừ điểm + tạo voucher ──
                def _on_dd_double_click(row, col):
                    if row < 0 or row >= len(dd_data):
                        return
                    d = dd_data[row]
                    diem_can = d.get("diem_can", 0)

                    # ── MuaXTangY: đổi điểm → áp quà tặng thẳng vào hóa đơn ──
                    if d.get("_mxy"):
                        # Nếu đã có KM MuaXTangY đang áp → không cho đổi thêm trong cùng 1 đơn
                        if self._applied_km and self._applied_km.get("_mxy"):
                            QMessageBox.warning(
                                dlg, "Không thể cộng dồn",
                                "Đơn này đã áp dụng 1 ưu đãi Mua X Tặng Y rồi.\n\n"
                                "Mỗi đơn hàng chỉ được áp dụng 1 ưu đãi loại này.\n"
                                "Bấm '❌ Bỏ KM' trước nếu muốn đổi sang ưu đãi khác."
                            )
                            return

                        # Kiểm tra điều kiện số lượng sp X trong hóa đơn hiện tại
                        ten_x    = d["ten_x"]
                        sl_can   = d["sl_can_mua"]
                        sl_tang  = d["sl_tang"]
                        ten_y    = d["ten_y"]
                        qty_co   = sum(
                            it.get("qty", 0)
                            for it in self.order_table.get_items()
                            if not it.get("is_gift") and it.get("name", "") == ten_x
                        )
                        if qty_co < sl_can:
                            QMessageBox.warning(
                                dlg, "Chưa đủ điều kiện",
                                f"⚠️ KM này yêu cầu mua ít nhất {sl_can}× {ten_x}.\n\n"
                                f"Hóa đơn hiện có: {qty_co}× {ten_x}.\n"
                                f"Vui lòng thêm món trước khi đổi điểm."
                            )
                            return

                        so_bo     = qty_co // sl_can
                        tong_tang = sl_tang   # luôn tặng đúng sl_tang cố định

                        # Xác nhận đổi điểm
                        if QMessageBox.question(
                            dlg, "Xác nhận đổi điểm",
                            f"Đổi <b>{diem_can:,} điểm</b> để nhận ưu đãi:<br><br>"
                            f"🎁 <b>{d['ten']}</b><br>"
                            f"→ Tặng <b>{tong_tang}× {ten_y}</b> miễn phí<br><br>"
                            f"Ưu đãi sẽ được áp dụng ngay vào hóa đơn.",
                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                        ) != QMessageBox.Yes:
                            return

                        # Trừ điểm
                        from database.models import KhachHang, LichSuDiemKH
                        s2 = get_session()
                        try:
                            kh_obj = s2.query(KhachHang).filter_by(id=kh_id).first()
                            if not kh_obj:
                                QMessageBox.critical(dlg, "Lỗi", "Không tìm thấy khách hàng!"); return
                            if (kh_obj.diem_tich_luy or 0) < diem_can:
                                QMessageBox.warning(dlg, "Không đủ điểm",
                                    f"Khách chỉ còn {kh_obj.diem_tich_luy or 0:,} điểm!"); return

                            kh_obj.diem_tich_luy = (kh_obj.diem_tich_luy or 0) - diem_can
                            s2.add(LichSuDiemKH(
                                ma_kh=kh_id,
                                loai="Đổi điểm",
                                so_diem=-diem_can,
                                mo_ta=f"Đổi điểm MuaXTangY tại POS: {d['ten']}",
                            ))
                            from database.models import KhuyenMai as _KM
                            km_obj2 = s2.get(_KM, d["id"])
                            if km_obj2:
                                km_obj2.so_luot_da_dung = (km_obj2.so_luot_da_dung or 0) + 1
                            s2.commit()
                            diem_con_lai = kh_obj.diem_tich_luy
                        except Exception as e2:
                            s2.rollback()
                            QMessageBox.critical(dlg, "Lỗi", str(e2)); return
                        finally:
                            s2.close()

                        # Cập nhật điểm UI
                        if self._linked_kh:
                            self._linked_kh["diem"] = diem_con_lai
                        self._update_loyalty_label()

                        # Xoá quà cũ (nếu có) rồi thêm quà mới — tránh cộng dồn
                        self.order_table.remove_gifts()
                        d["tong_tang"] = tong_tang
                        d["du_dk"]     = True
                        self.order_table.add_gift(ten_y + " (Quà tặng)", tong_tang)
                        self._applied_km         = d
                        self._km_user_picked     = True
                        self._applied_voucher_id = None
                        self._km_discount        = 0.0
                        self.update_grand_total()
                        _log(self.user.id, "Đổi điểm MuaXTangY",
                             f"{d['ten']}: trừ {diem_can:,} điểm, tặng {tong_tang}× {ten_y}",
                             o_dau="POS - Thanh toán")

                        QMessageBox.information(
                            dlg, "✅ Đổi điểm thành công",
                            f"Đã trừ {diem_can:,} điểm!\n\n"
                            f"Đã thêm {tong_tang}× {ten_y} (miễn phí) vào hóa đơn.\n"
                            f"Điểm còn lại: {diem_con_lai:,}"
                        )
                        dlg.accept()
                        return

                    # ── KM giảm tiền thường: validate + tạo voucher ──────
                    loai_giam = d.get("kieu", "")
                    gia_tri   = d.get("gia_tri", 0)
                    if loai_giam not in ("PhanTram", "TienMat"):
                        QMessageBox.warning(dlg, "Loại KM không hợp lệ",
                            f"KM '{d['ten']}' có loại '{loai_giam}' không thể tạo voucher.\n"
                            "Chỉ hỗ trợ: Giảm % hoặc Giảm tiền.")
                        return
                    if not gia_tri or gia_tri <= 0:
                        QMessageBox.warning(dlg, "Giá trị không hợp lệ",
                            f"KM '{d['ten']}' có giá trị giảm = 0.\n"
                            "Vui lòng kiểm tra lại cấu hình KM.")
                        return

                    # Xác nhận tạo voucher
                    if QMessageBox.question(
                        dlg, "Xác nhận đổi điểm",
                        f"Đổi <b>{diem_can:,} điểm</b> để nhận voucher:<br><br>"
                        f"🎁 <b>{d['ten']}</b><br><br>"
                        f"Voucher sẽ được lưu vào tài khoản khách hàng.",
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                    ) != QMessageBox.Yes:
                        return

                    import random, string
                    from database.models import KhachHang, LichSuDiemKH
                    from datetime import timedelta, date as _date

                    s2 = get_session()
                    try:
                        kh_obj = s2.query(KhachHang).filter_by(id=kh_id).first()
                        if not kh_obj:
                            QMessageBox.critical(dlg, "Lỗi", "Không tìm thấy khách hàng!"); return
                        if (kh_obj.diem_tich_luy or 0) < diem_can:
                            QMessageBox.warning(dlg, "Không đủ điểm",
                                f"Khách chỉ còn {kh_obj.diem_tich_luy or 0:,} điểm!"); return

                        kh_obj.diem_tich_luy = (kh_obj.diem_tich_luy or 0) - diem_can
                        s2.add(LichSuDiemKH(
                            ma_kh=kh_id,
                            loai="Đổi điểm",
                            so_diem=-diem_can,
                            mo_ta=f"Đổi điểm tại POS: {d['ten']}",
                        ))

                        vc_code = "VD" + "".join(random.choices(
                            string.ascii_uppercase + string.digits, k=8))
                        het_han = _date.today() + timedelta(days=90)
                        vc_new = Voucher(
                            ma_kh=kh_id,
                            ma_code=vc_code,
                            ten_voucher=f"[Đổi điểm] {d['ten']}",
                            loai_giam=loai_giam,
                            gia_tri_giam=gia_tri,
                            toi_da_giam=d.get("tran"),
                            dieu_kien_toi_thieu=d.get("dk_min", 0) or 0,
                            ngay_het_han=het_han,
                            trang_thai="Chưa dùng",
                        )
                        try: vc_new.ma_km = d["id"]
                        except Exception: pass
                        s2.add(vc_new)

                        from database.models import KhuyenMai as _KM
                        km_obj2 = s2.get(_KM, d["id"])
                        if km_obj2:
                            km_obj2.so_luot_da_dung = (km_obj2.so_luot_da_dung or 0) + 1
                        s2.commit()
                        diem_con_lai = kh_obj.diem_tich_luy

                        if self._linked_kh:
                            self._linked_kh["diem"] = diem_con_lai
                        self._update_loyalty_label()

                        QMessageBox.information(
                            dlg, "✅ Đổi điểm thành công",
                            f"Đã trừ {diem_can:,} điểm!\n\n"
                            f"Voucher: {vc_code}\n"
                            f"Ưu đãi: {d['ten']}\n"
                            f"Hiệu lực: đến {het_han.strftime('%d/%m/%Y')}\n"
                            f"Điểm còn lại: {diem_con_lai:,}\n\n"
                            f"Voucher đã được thêm vào danh sách bên trên.\n"
                            f"Chọn voucher vừa tạo rồi ấn Áp dụng."
                        )

                        # Reload danh sách voucher
                        s3 = get_session()
                        try:
                            vcs2 = s3.query(Voucher).filter_by(
                                ma_kh=kh_id, trang_thai="Chưa dùng").all()
                            vouchers.clear()
                            for vc2 in vcs2:
                                if vc2.ngay_het_han and vc2.ngay_het_han < _date.today(): continue
                                if vc2.dieu_kien_toi_thieu and subtotal < vc2.dieu_kien_toi_thieu: continue
                                if vc2.loai_giam == "PhanTram":
                                    g2 = subtotal * float(vc2.gia_tri_giam or 0) / 100
                                    if vc2.toi_da_giam: g2 = min(g2, float(vc2.toi_da_giam))
                                else:
                                    g2 = min(float(vc2.gia_tri_giam or 0), subtotal)
                                vouchers.append({
                                    "id": vc2.id, "ten": vc2.ten_voucher or f"Voucher {vc2.ma_code}",
                                    "ma_code": vc2.ma_code,
                                    "loai": "Voucher", "kieu": vc2.loai_giam or "TienMat",
                                    "gia_tri": float(vc2.gia_tri_giam or 0),
                                    "tran": float(vc2.toi_da_giam or 0) or None,
                                    "dk_min": float(vc2.dieu_kien_toi_thieu or 0),
                                    "diem_can": 0, "loai_nhom": "Voucher", "_giam": g2,
                                })
                        finally:
                            s3.close()
                        vouchers.sort(key=lambda x: -x["_giam"])

                        nonlocal tbl_vc, vc_data
                        if tbl_vc is not None:
                            tca.removeWidget(tbl_vc)
                            tbl_vc.deleteLater()
                        tbl_vc, vc_data = _make_km_table(vouchers)
                        tbl_vc.setMaximumHeight(160)
                        for idx in range(tca.count()):
                            w = tca.itemAt(idx).widget()
                            if w and isinstance(w, QLabel) and "Voucher cá nhân" in w.text():
                                tca.insertWidget(idx + 1, tbl_vc)
                                break
                        else:
                            lbl_vc2 = QLabel("<b style='color:#3498DB;'>🎟 Voucher cá nhân:</b>")
                            tca.insertWidget(1, tbl_vc)
                            tca.insertWidget(1, lbl_vc2)
                        if tbl_vc.rowCount() > 0:
                            tbl_vc.selectRow(0)

                    except Exception as e2:
                        s2.rollback()
                        QMessageBox.critical(dlg, "Lỗi", str(e2))
                    finally:
                        s2.close()

                tbl_dd.cellDoubleClicked.connect(_on_dd_double_click)
                tca.addWidget(tbl_dd)
            elif not vouchers:
                lbl_no2 = QLabel("Chưa có voucher hoặc KM đổi điểm nào khả dụng.")
                lbl_no2.setStyleSheet("color:#606770;font-size:13px;padding:12px 0;")
                lbl_no2.setAlignment(Qt.AlignCenter)
                tca.addWidget(lbl_no2)

        # ── Tab widget ────────────────────────────────────────────
        from PySide6.QtWidgets import QTabWidget
        tab_widget = QTabWidget()
        tab_widget.addTab(tab_chung,   "🌐  KM Chung")
        tab_widget.addTab(tab_ca_nhan,
            "👤  Voucher & Điểm" + (f" ({len(vouchers)+len(km_doi_diem)})" if kh_id and (vouchers or km_doi_diem) else "")
        )
        # Nếu không có KH: disable tab cá nhân tooltip
        if not kh_id:
            tab_widget.setTabToolTip(1, "Cần liên kết SĐT khách hàng")
        dv.addWidget(tab_widget, stretch=1)

        # ── Nút hành động ─────────────────────────────────────────
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        btn_cancel = QPushButton("✖ Hủy")
        btn_cancel.setStyleSheet("background:#CCD0D5;")
        btn_remove = QPushButton("❌ Bỏ KM / Voucher")
        btn_remove.setStyleSheet("background:#C0392B;")
        btn_ok = QPushButton("✅ Áp dụng")
        btn_ok.setStyleSheet("background:#27AE60;font-size:14px;padding:10px 20px;")
        btn_ok.setMinimumHeight(44)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_remove)
        btn_row.addStretch()
        btn_row.addWidget(btn_ok)
        dv.addLayout(btn_row)

        # ── Logic áp dụng ─────────────────────────────────────────
        def _get_selected():
            """Trả về km_data đang được chọn theo tab active."""
            tab = tab_widget.currentIndex()
            if tab == 0:
                if tbl_chung and tbl_chung.currentRow() >= 0:
                    return chung_data[tbl_chung.currentRow()] if chung_data else None
            else:
                # Ưu tiên bảng nào đang có row selected
                if tbl_vc and tbl_vc.currentRow() >= 0 and tbl_vc.hasFocus():
                    return vc_data[tbl_vc.currentRow()]
                if tbl_dd and tbl_dd.currentRow() >= 0:
                    return dd_data[tbl_dd.currentRow()]
                if tbl_vc and tbl_vc.currentRow() >= 0:
                    return vc_data[tbl_vc.currentRow()]
            return None

        def _do_apply():
            sel = _get_selected()
            if not sel:
                QMessageBox.warning(dlg, "Chưa chọn", "Hãy chọn một khuyến mãi hoặc voucher!")
                return

            # ── MuaXTangY: thêm món quà vào hóa đơn ──────────────
            if sel.get("_mxy"):
                # Chặn cộng dồn: không cho áp 2 KM MuaXTangY trong cùng 1 đơn
                if self._applied_km and self._applied_km.get("_mxy") and self._applied_km["id"] != sel["id"]:
                    QMessageBox.warning(
                        dlg, "Không thể cộng dồn",
                        "Đơn này đã áp dụng 1 ưu đãi Mua X Tặng Y rồi.\n\n"
                        "Mỗi đơn hàng chỉ được áp dụng 1 ưu đãi loại này.\n"
                        "Bấm '❌ Bỏ KM' trước nếu muốn đổi sang ưu đãi khác."
                    )
                    return
                if not sel["du_dk"]:
                    QMessageBox.warning(
                        dlg, "Chưa đủ điều kiện",
                        f"⚠️ {sel['msg']}\n\n"
                        f"Cần ít nhất {sel['sl_can_mua']}× {sel['ten_x']} trong hóa đơn."
                    )
                    return
                # Xóa quà cũ nếu có, thêm quà mới
                self.order_table.remove_gifts()
                self.order_table.add_gift(sel["ten_y"] + " (Quà tặng)", sel["tong_tang"])
                self._applied_km = sel
                self._km_user_picked = True
                self._applied_voucher_id = None
                self._km_discount = 0.0
                self.update_grand_total()
                _log(self.user.id, "Áp dụng KM MuaXTangY",
                     f"{sel['ten']}: tặng {sel['tong_tang']}× {sel['ten_y']}",
                     o_dau="POS - Thanh toán")
                dlg.accept()
                return

            # Kiểm tra KM đổi điểm: phải đúp chuột đổi trước
            if sel.get("loai_nhom") == "DoiDiem":
                QMessageBox.information(dlg, "Cần đổi điểm trước",
                    "Ưu đãi này yêu cầu đổi điểm.\n\n"
                    "Vui lòng <b>đúp chuột</b> vào dòng ưu đãi đó để đổi điểm "
                    "→ hệ thống sẽ tạo voucher cá nhân cho khách.\n\n"
                    "Sau đó chọn voucher vừa tạo ở mục "
                    "\"Voucher cá nhân\" rồi ấn Áp dụng.")
                return

            # Kiểm tra Voucher
            if sel.get("loai_nhom") == "Voucher" and not kh_id:
                QMessageBox.warning(dlg, "Cần KH liên kết",
                    "Voucher cá nhân yêu cầu liên kết số điện thoại khách hàng!")
                return

            # Bỏ quà tặng cũ nếu chuyển sang KM khác
            self.order_table.remove_gifts()

            self._applied_km = sel
            self._km_user_picked = True
            self._applied_voucher_id = sel["id"] if sel.get("loai_nhom") == "Voucher" else None
            self.update_grand_total()

            nhom = sel.get("loai_nhom", "Chung")
            _log(self.user.id,
                 "Áp dụng KM/Voucher",
                 f"[{nhom}] {sel['ten']} — giảm {int(self._km_discount):,}đ",
                 o_dau="POS - Thanh toán")
            dlg.accept()

        def _do_remove():
            old = self._applied_km["ten"] if self._applied_km else "—"
            self.order_table.remove_gifts()   # xóa quà tặng MuaXTangY nếu có
            self._applied_km = None
            self._km_discount = 0
            self._km_user_picked = False
            self._applied_voucher_id = None
            self.update_grand_total()
            _log(self.user.id, "Bỏ KM/Voucher", f"Gỡ '{old}' khỏi hóa đơn",
                 o_dau="POS - Thanh toán")
            dlg.accept()

        btn_ok.clicked.connect(_do_apply)
        btn_remove.clicked.connect(_do_remove)
        btn_cancel.clicked.connect(dlg.reject)
        dlg.exec()


    # ----------------------------------------------------------------
    # ĐIỂM THÀNH VIÊN
    # ----------------------------------------------------------------
    def _update_loyalty_label(self):
        """Cập nhật label hiển thị KH thành viên đang liên kết."""
        kh = self._linked_kh
        if kh:
            hang_color = {
                "Kim cương": "#00BCD4", "Vàng": "#F1C40F",
                "Bạc": "#BDC3C7", "Đồng": "#CD7F32",
            }.get(kh.get("hang", "Đồng"), "#C39BD3")
            self.lbl_loyalty_info.setText(
                f"⭐  {kh['ten']}  ({kh.get('hang','Đồng')})  |  "
                f"SĐT: {kh['sdt']}  |  Điểm: {kh.get('diem', 0):,}"
            )
            self.lbl_loyalty_info.setStyleSheet(
                f"background-color: #F0F2F5; border: 1px solid {hang_color};"
                f" border-radius: 6px; padding: 6px 10px;"
                f" font-size: 12px; color: {hang_color};"
            )
            self.lbl_loyalty_info.setVisible(True)
        else:
            self.lbl_loyalty_info.setVisible(False)

    def _open_loyalty(self):
        """
        Popup nhập SĐT để tìm / tạo khách thành viên, liên kết bill,
        hoặc đổi điểm lấy khuyến mãi (không bắt buộc phải liên kết bill trước).
        """
        from database.db_config import get_session
        from database.models import KhachHang

        dlg = QDialog(self)
        dlg.setWindowTitle("⭐ Điểm Thành Viên")
        dlg.resize(550, 300)
        dlg.setStyleSheet(
            "QDialog,QWidget{background:#FFFFFF;color: #1C1E21;font-family:'Segoe UI';}"
            "QLabel{background:transparent;}"
            "QLineEdit{background:#F0F2F5;border:1px solid #CCD0D5;border-radius:6px;"
            "  padding:8px 12px;color: #1C1E21;font-size:14px;}"
            "QLineEdit:focus{border-color:#8E44AD;}"
            "QPushButton{border-radius:6px;font-weight:bold;font-size:13px;"
            "  color: #1C1E21;padding:8px 14px;}"
        )
        dv = QVBoxLayout(dlg)
        dv.setContentsMargins(20, 18, 20, 18)
        dv.setSpacing(12)

        # Tiêu đề
        dv.addWidget(QLabel(
            "<b style='color:#C39BD3;font-size:15px;'>⭐  Tra cứu Thành Viên</b>"
        ))

        # Ô nhập SĐT
        from PySide6.QtWidgets import QLineEdit as QLE
        txt_sdt = QLE()
        txt_sdt.setPlaceholderText("Nhập số điện thoại khách hàng…")
        txt_sdt.setMaxLength(15)
        dv.addWidget(txt_sdt)

        # Khu vực kết quả
        lbl_result = QLabel("")
        lbl_result.setWordWrap(True)
        lbl_result.setTextFormat(Qt.RichText)
        lbl_result.setStyleSheet(
            "background:#F0F2F5; border-radius:8px; padding:10px 14px;"
            " font-size:13px; color:#1C1E21; min-height:60px;"
        )
        dv.addWidget(lbl_result)

        # Hàng nút 1: Tìm + Liên kết + Bỏ liên kết + Đóng
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_search = QPushButton("🔍  Tìm")
        btn_search.setStyleSheet("background:#8E44AD;color:white;font-weight:bold;border-radius:6px;")
        btn_link   = QPushButton("✅  Liên kết bill")
        btn_link.setStyleSheet("background:#27AE60;color:white;font-weight:bold;border-radius:6px;")
        btn_link.setEnabled(False)
        btn_unlink = QPushButton("🗑  Bỏ liên kết")
        btn_unlink.setStyleSheet("background:#C0392B;color:white;font-weight:bold;border-radius:6px;")
        btn_close  = QPushButton("Đóng")
        btn_close.setStyleSheet("background:#CCD0D5;color: #1C1E21;font-weight:bold;border-radius:6px;")

        btn_new = QPushButton("➕  Thêm TV mới")
        btn_new.setStyleSheet("background:#2980B9;color:white;font-weight:bold;border-radius:6px;")
        btn_new.setVisible(False)

        btn_row.addWidget(btn_search)
        btn_row.addWidget(btn_new)
        btn_row.addWidget(btn_link)
        btn_row.addWidget(btn_unlink)
        btn_row.addWidget(btn_close)
        dv.addLayout(btn_row)

        # Nếu đang có KH liên kết → điền sẵn SĐT
        if self._linked_kh:
            txt_sdt.setText(self._linked_kh["sdt"])

        _found_kh: dict | None = None   # KH tìm được tạm thời

        def _do_search():
            nonlocal _found_kh
            sdt = txt_sdt.text().strip()
            if not sdt:
                lbl_result.setText("<span style='color:#E74C3C;'>Vui lòng nhập SĐT!</span>")
                return
            s = get_session()
            try:
                kh = s.query(KhachHang).filter_by(so_dien_thoai=sdt).first()
                if kh:
                    hang_color = {
                        "Kim cương": "#00BCD4", "Vàng": "#F1C40F",
                        "Bạc": "#BDC3C7", "Đồng": "#CD7F32",
                    }.get(kh.hang_thanh_vien or "Đồng", "#C39BD3")
                    _found_kh = {
                        "id":   kh.id,
                        "ten":  kh.ten_kh,
                        "sdt":  kh.so_dien_thoai,
                        "hang": kh.hang_thanh_vien or "Đồng",
                        "diem": kh.diem_tich_luy or 0,
                    }
                    lbl_result.setText(
                        f"<b style='color:{hang_color};'>{kh.ten_kh}</b>"
                        f"  <span style='color:#606770;'>({kh.hang_thanh_vien or 'Đồng'})</span><br>"
                        f"<span style='color:#BDC3C7;'>SĐT: {kh.so_dien_thoai}"
                        f"  |  Điểm: <b style='color:#F1C40F;'>{kh.diem_tich_luy or 0:,}</b></span>"
                    )
                    btn_link.setEnabled(True)
                    btn_new.setVisible(False)
                else:
                    _found_kh = None
                    lbl_result.setText(
                        f"<span style='color:#E74C3C;'>⚠️  Chưa có thành viên với SĐT <b>{sdt}</b></span>"
                    )
                    btn_link.setEnabled(False)
                    btn_new.setVisible(True)
            finally:
                s.close()

        def _do_link():
            if _found_kh:
                self._linked_kh = _found_kh
                self._update_loyalty_label()
                _log(self.user.id, "Liên kết thành viên",
                     f"Liên kết KH '{_found_kh['ten']}' ({_found_kh['sdt']}) vào bill",
                     o_dau="POS - Thanh toán")
                dlg.accept()

        def _do_unlink():
            old = self._linked_kh["ten"] if self._linked_kh else "—"
            self._linked_kh = None
            self._update_loyalty_label()
            _log(self.user.id, "Bỏ liên kết thành viên",
                 f"Gỡ KH '{old}' khỏi bill", o_dau="POS - Thanh toán")
            dlg.accept()

        def _do_new():
            """Mở thẳng CustomerForm để tạo KH mới ngay, điền sẵn SĐT."""
            sdt = txt_sdt.text().strip()
            from views.customer_manager import CustomerForm
            f = CustomerForm(sdt_mac_dinh=sdt, parent=dlg)
            if f.exec():
                # Tạo thành công thì tự động tìm và hiển thị luôn
                sdt_moi = f.txt_sdt.text().strip()
                if sdt_moi:
                    txt_sdt.setText(sdt_moi)
                    _do_search()

        txt_sdt.returnPressed.connect(_do_search)
        btn_search.clicked.connect(_do_search)
        btn_link.clicked.connect(_do_link)
        btn_unlink.clicked.connect(_do_unlink)
        btn_new.clicked.connect(_do_new)
        btn_close.clicked.connect(dlg.reject)
        dlg.exec()

    # ----------------------------------------------------------------
    # THANH TOÁN
    # ----------------------------------------------------------------
    def handle_checkout(self):
        import random
        if not self.order_table.get_items():
            QMessageBox.warning(self, "Cảnh báo", "Hóa đơn đang trống!")
            return

        raw_items   = self.order_table.get_items()
        order_items = []
        grand_total = 0
        for it in raw_items:
            if it.get("is_gift"):
                # Dòng quà tặng MuaXTangY — price=0, không tính vào tổng
                order_items.append({
                    'name': it['name'], 'qty': it['qty'],
                    'price': 0, 'note': '🎁 Quà tặng KM',
                })
                continue
            parts = []
            if it.get("topping") and it["topping"] != "Không topping":
                parts.append(it["topping"])
            if it.get("da") and it["da"] != "Bình thường":
                parts.append(it["da"])
            if it.get("duong") and it["duong"] != "Vừa":
                parts.append(it["duong"])
            if it.get("note"):
                parts.append(it["note"])
            note = " | ".join(parts)
            grand_total += it["qty"] * it["price"]
            order_items.append({
                'name': it['name'], 'qty': it['qty'],
                'price': it['price'], 'note': note,
            })

        vat_tax      = grand_total * 0.10
        subtotal     = grand_total + vat_tax
        total_to_pay = max(0, subtotal - self._km_discount)

        # ── POPUP THANH TOÁN NÂNG CẤP ───────────────────────────────
        import random as _rnd
        order_code = f"CF{_rnd.randint(1000, 9999)}"

        # Biến lưu phương thức thanh toán được chọn (mặc định QR)
        _pay_method = ["qr"]   # dùng list để closure có thể ghi

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Thanh toán  ·  {order_code}")
        dialog.setFixedSize(440, 600)
        dialog.setStyleSheet("""
            QDialog { background-color: #F8FAFC; color: #0F172A; }
            QLabel  { border: none; background: transparent; }
            * { font-family: 'Segoe UI', 'Inter', sans-serif; }
        """)

        dlg_layout = QVBoxLayout(dialog)
        dlg_layout.setContentsMargins(18, 16, 18, 14)
        dlg_layout.setSpacing(10)

        # ── A. Header ───────────────────────────────────────────────────
        hdr = QFrame(dialog)
        hdr.setStyleSheet(
            "QFrame { background: #FFFFFF; border-radius: 16px; border: 1px solid #E2E8F0; }"
        )
        # Drop shadow for header card
        shadow_hdr = QGraphicsDropShadowEffect(dialog)
        shadow_hdr.setBlurRadius(10)
        shadow_hdr.setXOffset(0)
        shadow_hdr.setYOffset(2)
        shadow_hdr.setColor(QColor(0, 0, 0, 15))
        hdr.setGraphicsEffect(shadow_hdr)

        hdr_lay = QVBoxLayout(hdr)
        hdr_lay.setContentsMargins(18, 14, 18, 14)
        hdr_lay.setSpacing(4)

        # Mã đơn nhỏ gọn
        lbl_code = QLabel(f"🧾  {order_code}")
        lbl_code.setAlignment(Qt.AlignCenter)
        lbl_code.setStyleSheet(
            "font-size: 11px; color: #64748B; letter-spacing: 2px;"
            " font-weight: 600; text-transform: uppercase;"
        )
        hdr_lay.addWidget(lbl_code)

        # Tổng tiền lớn
        lbl_total = QLabel(f"{int(total_to_pay):,} đ")
        lbl_total.setAlignment(Qt.AlignCenter)
        lbl_total.setStyleSheet(
            "font-size: 32px; font-weight: 800; color: #2563EB;"
            " letter-spacing: -0.5px;"
        )
        hdr_lay.addWidget(lbl_total)

        # Chi tiết: Tạm tính · VAT · Giảm giá
        detail_parts = [f"Tạm tính: {int(grand_total):,}đ", "VAT: 10%"]
        if self._applied_km and self._km_discount > 0:
            detail_parts.append(
                f"KM: -{int(self._km_discount):,}đ"
            )
        lbl_sub = QLabel("  •  ".join(detail_parts))
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet(
            "font-size: 11px; color: #64748B; font-weight: 500;"
        )
        hdr_lay.addWidget(lbl_sub)

        dlg_layout.addWidget(hdr)

        # ── B. Tabs phương thức ─────────────────────────────────────────
        tab_frame = QFrame(dialog)
        tab_frame.setStyleSheet(
            "QFrame { background: #F1F5F9; border-radius: 10px; border: 1px solid #E2E8F0; }"
        )
        tab_frame.setFixedHeight(40)
        tab_lay = QHBoxLayout(tab_frame)
        tab_lay.setContentsMargins(4, 4, 4, 4)
        tab_lay.setSpacing(4)

        _STYLE_TAB_ON = (
            "QPushButton { background: #FFFFFF; color: #2563EB; font-weight: 700;"
            " border-radius: 6px; font-size: 13px; padding: 6px 0; border: none; }"
        )
        _STYLE_TAB_OFF = (
            "QPushButton { background: transparent; color: #64748B; font-weight: 600;"
            " border-radius: 6px; font-size: 13px; padding: 6px 0; border: none; }"
            "QPushButton:hover { background: rgba(255, 255, 255, 0.4); color: #0F172A; }"
        )

        btn_tab_qr   = QPushButton("📱  QR / Chuyển khoản")
        btn_tab_cash = QPushButton("💵  Tiền mặt")
        for b in (btn_tab_qr, btn_tab_cash):
            b.setCursor(Qt.PointingHandCursor)
            tab_lay.addWidget(b)
        dlg_layout.addWidget(tab_frame)

        # ── C. Stack ────────────────────────────────────────────────────
        from PySide6.QtWidgets import QStackedWidget
        stack = QStackedWidget(dialog)
        stack.setStyleSheet("QStackedWidget { border: none; background: transparent; }")

        # ── Panel QR ────────────────────────────────────────────────────
        pg_qr = QWidget(); pg_qr.setStyleSheet("background: transparent;")
        qr_vlay = QVBoxLayout(pg_qr)
        qr_vlay.setContentsMargins(0, 4, 0, 0)
        qr_vlay.setSpacing(8)

        # Card nền sáng cho QR
        qr_card = QFrame()
        qr_card.setStyleSheet(
            "QFrame { background: #FFFFFF; border-radius: 16px;"
            " border: 1px solid #CBD5E1; }"
        )
        shadow_qr = QGraphicsDropShadowEffect(dialog)
        shadow_qr.setBlurRadius(12)
        shadow_qr.setXOffset(0)
        shadow_qr.setYOffset(3)
        shadow_qr.setColor(QColor(0, 0, 0, 15))
        qr_card.setGraphicsEffect(shadow_qr)

        qr_card_lay = QVBoxLayout(qr_card)
        qr_card_lay.setContentsMargins(10, 10, 10, 10)

        qr_label = QLabel("Đang tải mã QR…")
        qr_label.setAlignment(Qt.AlignCenter)
        qr_label.setStyleSheet("color: #64748B; font-size: 13px; background: transparent;")
        qr_label.setFixedSize(222, 222)   # 270 × 0.82 ≈ 222
        qr_card_lay.addWidget(qr_label, 0, Qt.AlignCenter)
        qr_vlay.addWidget(qr_card, 0, Qt.AlignCenter)

        try:
            from utils.qr_generator import generate_vietqr_pixmap
            pixmap = generate_vietqr_pixmap(total_to_pay, f"Thanh toan don {order_code}")
            if pixmap:
                qr_label.setPixmap(
                    pixmap.scaled(222, 222, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
        except Exception:
            qr_label.setText("(Không tải được mã QR)")

        hint_qr = QLabel("💡 Quét mã QR bằng ứng dụng Ngân hàng để thanh toán nhanh")
        hint_qr.setAlignment(Qt.AlignCenter)
        hint_qr.setWordWrap(True)
        hint_qr.setStyleSheet("font-size: 11px; color: #475569; font-weight: 500;")
        qr_vlay.addWidget(hint_qr)
        qr_vlay.addStretch()
        stack.addWidget(pg_qr)

        # ── Panel Tiền mặt ───────────────────────────────────────────────
        pg_cash = QWidget(); pg_cash.setStyleSheet("background: transparent;")
        cash_vlay = QVBoxLayout(pg_cash)
        cash_vlay.setContentsMargins(0, 4, 0, 0)
        cash_vlay.setSpacing(8)

        lbl_need = QLabel(f"Cần thu:  {int(total_to_pay):,} đ")
        lbl_need.setAlignment(Qt.AlignCenter)
        lbl_need.setStyleSheet(
            "font-size: 15px; font-weight: 700; color: #1E293B;"
            " background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 8px 0;"
        )
        shadow_need = QGraphicsDropShadowEffect(dialog)
        shadow_need.setBlurRadius(8)
        shadow_need.setXOffset(0)
        shadow_need.setYOffset(2)
        shadow_need.setColor(QColor(0, 0, 0, 10))
        lbl_need.setGraphicsEffect(shadow_need)
        cash_vlay.addWidget(lbl_need)

        # Ô nhập tiền khách
        row_cash = QHBoxLayout()
        lbl_given = QLabel("Khách đưa:")
        lbl_given.setStyleSheet("font-size: 13px; color: #475569; font-weight: 600; min-width: 80px;")
        txt_given = QLineEdit()
        txt_given.setPlaceholderText(f"{int(total_to_pay):,}")
        txt_given.setAlignment(Qt.AlignRight)
        txt_given.setStyleSheet(
            "QLineEdit { background: #FFFFFF; border: 1px solid #CBD5E1;"
            " border-radius: 10px; padding: 10px 14px;"
            " color: #0F172A; font-size: 16px; font-weight: 700; }"
            "QLineEdit:focus { border: 2px solid #3B82F6; }"
        )
        row_cash.addWidget(lbl_given)
        row_cash.addWidget(txt_given)
        cash_vlay.addLayout(row_cash)

        # Card tiền thối nổi bật
        change_card = QFrame()
        change_card.setStyleSheet(
            "QFrame { background: #FFFFFF; border-radius: 12px;"
            " border: 1px solid #E2E8F0; }"
        )
        shadow_change = QGraphicsDropShadowEffect(dialog)
        shadow_change.setBlurRadius(8)
        shadow_change.setXOffset(0)
        shadow_change.setYOffset(2)
        shadow_change.setColor(QColor(0, 0, 0, 10))
        change_card.setGraphicsEffect(shadow_change)

        change_card_lay = QHBoxLayout(change_card)
        change_card_lay.setContentsMargins(14, 10, 14, 10)
        lbl_change_title = QLabel("Tiền thối")
        lbl_change_title.setStyleSheet("font-size: 13px; color: #475569; font-weight: 600;")
        lbl_change = QLabel("—")
        lbl_change.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_change.setStyleSheet("font-size: 24px; font-weight: 700; color: #64748B;")
        change_card_lay.addWidget(lbl_change_title)
        change_card_lay.addStretch()
        change_card_lay.addWidget(lbl_change)
        cash_vlay.addWidget(change_card)

        # Quick-cash thông minh: gợi ý số tiền gần nhất + các nút tiện
        def _smart_amounts():
            """Tạo danh sách gợi ý: làm tròn gần nhất + cố định + đúng tiền."""
            candidates = set()
            # Làm tròn lên
            for unit in [10_000, 20_000, 50_000, 100_000, 200_000, 500_000]:
                rounded = ((int(total_to_pay) + unit - 1) // unit) * unit
                candidates.add(rounded)
            # Loại bỏ những số bằng tổng tiền chính xác
            final = sorted([a for a in candidates if a >= total_to_pay])[:3]
            return final

        quick_lay = QGridLayout()
        quick_lay.setSpacing(5)

        smart = _smart_amounts()
        all_btns = []

        # Dòng 1: gợi ý thông minh
        for i, amt in enumerate(smart[:3]):
            label = f"{amt//1000}k" if amt < 1_000_000 else f"{amt/1_000_000:.1f}M"
            bq = QPushButton(label)
            bq.setMinimumHeight(32)
            bq.setCursor(Qt.PointingHandCursor)
            bq.setStyleSheet(
                "QPushButton { background: #EFF6FF; color: #1D4ED8;"
                " border: 1px solid #BFDBFE; border-radius: 8px;"
                " font-size: 12px; font-weight: 600; }"
                "QPushButton:hover { background: #3B82F6; color: #FFFFFF; border-color: #3B82F6; }"
                "QPushButton:pressed { background: #2563EB; color: #FFFFFF; }"
            )
            bq.clicked.connect(lambda checked=False, a=amt: txt_given.setText(f"{a:,}"))
            quick_lay.addWidget(bq, 0, i)
            all_btns.append(bq)

        # Dòng 2: đúng tiền, +10k, +50k
        btn_exact = QPushButton("◎ Đúng tiền")
        btn_p10   = QPushButton("+10k")
        btn_p50   = QPushButton("+50k")
        for i, b in enumerate([btn_exact, btn_p10, btn_p50]):
            b.setMinimumHeight(32)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(
                "QPushButton { background: #FFFFFF; color: #475569;"
                " border: 1px solid #CBD5E1; border-radius: 8px;"
                " font-size: 12px; font-weight: 600; }"
                "QPushButton:hover { background: #F1F5F9; color: #0F172A; border-color: #94A3B8; }"
                "QPushButton:pressed { background: #E2E8F0; }"
            )
            quick_lay.addWidget(b, 1, i)

        btn_exact.clicked.connect(lambda: txt_given.setText(f"{int(total_to_pay):,}"))
        btn_p10.clicked.connect(lambda: _add_to_given(10_000))
        btn_p50.clicked.connect(lambda: _add_to_given(50_000))

        def _add_to_given(delta: int):
            try:
                cur = float(txt_given.text().replace(",", "") or 0)
            except ValueError:
                cur = 0
            txt_given.setText(f"{int(cur + delta):,}")

        cash_vlay.addLayout(quick_lay)
        cash_vlay.addStretch()

        def _calc_change():
            try:
                given  = float(txt_given.text().replace(",", "").replace(".", "") or 0)
                change = given - total_to_pay
                if given <= 0:
                    lbl_change.setText("—")
                    lbl_change.setStyleSheet(
                        "font-size: 24px; font-weight: 700; color: #64748B;"
                    )
                    change_card.setStyleSheet(
                        "QFrame { background: #FFFFFF; border-radius: 12px;"
                        " border: 1px solid #E2E8F0; }"
                    )
                    btn_confirm.setEnabled(True)
                elif change < 0:
                    lbl_change.setText(f"⚠ Thiếu  {abs(int(change)):,} đ")
                    lbl_change.setStyleSheet(
                        "font-size: 16px; font-weight: 700; color: #EF4444;"
                    )
                    change_card.setStyleSheet(
                        "QFrame { background: #FEF2F2; border-radius: 12px;"
                        " border: 1px solid #FCA5A5; }"
                    )
                    btn_confirm.setEnabled(False)
                else:
                    lbl_change.setText(f"{int(change):,} đ")
                    lbl_change.setStyleSheet(
                        "font-size: 24px; font-weight: 700; color: #10B981;"
                    )
                    change_card.setStyleSheet(
                        "QFrame { background: #ECFDF5; border-radius: 12px;"
                        " border: 1px solid #A7F3D0; }"
                    )
                    btn_confirm.setEnabled(True)
            except Exception:
                lbl_change.setText("—")

        txt_given.textChanged.connect(_calc_change)
        stack.addWidget(pg_cash)
        dlg_layout.addWidget(stack, 1)

        # ── D. Nút xác nhận ─────────────────────────────────────────────
        btn_confirm = QPushButton("⬡  ĐÃ NHẬN TIỀN  —  CHỐT ĐƠN")
        btn_confirm.setMinimumHeight(48)
        btn_confirm.setCursor(Qt.PointingHandCursor)

        shadow_confirm = QGraphicsDropShadowEffect(dialog)
        shadow_confirm.setBlurRadius(8)
        shadow_confirm.setXOffset(0)
        shadow_confirm.setYOffset(3)
        shadow_confirm.setColor(QColor(0, 0, 0, 20))
        btn_confirm.setGraphicsEffect(shadow_confirm)

        def _reset_confirm_style():
            btn_confirm.setStyleSheet(
                "QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                "stop:0 #10B981, stop:1 #059669); "
                "color: #FFFFFF; font-weight: 700; font-size: 14px; "
                "border-radius: 12px; border: none; letter-spacing: 0.5px; }"
                "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                "stop:0 #059669, stop:1 #047857); }"
                "QPushButton:pressed { background: #047857; }"
                "QPushButton:disabled { background: #E2E8F0; color: #94A3B8; }"
            )

        _reset_confirm_style()

        def _on_confirm():
            btn_confirm.setEnabled(False)
            btn_confirm.setText("⟳  Đang xử lý…")
            dialog.accept()

        btn_confirm.clicked.connect(_on_confirm)
        dlg_layout.addWidget(btn_confirm)

        btn_cancel = QPushButton("Hủy")
        btn_cancel.setMinimumHeight(38)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet(
            "QPushButton { background: #F1F5F9; color: #475569;"
            " font-size: 13px; font-weight: 600; border: none; border-radius: 12px; }"
            "QPushButton:hover { background: #E2E8F0; color: #0F172A; }"
            "QPushButton:pressed { background: #CBD5E1; }"
        )
        btn_cancel.clicked.connect(dialog.reject)
        dlg_layout.addWidget(btn_cancel)

        # ── E. Tab switch ────────────────────────────────────────────────
        def _switch(method: str):
            _pay_method[0] = method
            if method == "qr":
                btn_tab_qr.setStyleSheet(_STYLE_TAB_ON)
                btn_tab_cash.setStyleSheet(_STYLE_TAB_OFF)
                stack.setCurrentIndex(0)
                btn_confirm.setText("⬡  ĐÃ NHẬN TIỀN  —  CHỐT ĐƠN")
                btn_confirm.setEnabled(True)
                _reset_confirm_style()
            else:
                btn_tab_qr.setStyleSheet(_STYLE_TAB_OFF)
                btn_tab_cash.setStyleSheet(_STYLE_TAB_ON)
                stack.setCurrentIndex(1)
                btn_confirm.setText("◈  THU TIỀN MẶT  —  CHỐT ĐƠN")
                _calc_change()   # cập nhật trạng thái nút ngay

        btn_tab_qr.clicked.connect(lambda: _switch("qr"))
        btn_tab_cash.clicked.connect(lambda: _switch("cash"))
        _switch("qr")

        if dialog.exec() == QDialog.Accepted:
            from controllers.pos_controller import process_checkout
            success, message = process_checkout(
                order_items, self.user.id,
                km_id=self._applied_km["id"] if self._applied_km else None,
                km_discount=int(self._km_discount),
                khach_hang_id=self._linked_kh["id"] if self._linked_kh else None,
            )
            if success:
                self.sound_cash.play()

                # ── Đánh dấu voucher đã dùng (nếu áp voucher) ──────────
                vc_id = getattr(self, '_applied_voucher_id', None)
                if vc_id:
                    try:
                        from database.db_config import get_session as _gs
                        from database.models import Voucher as _VC
                        _s = _gs()
                        try:
                            vc = _s.query(_VC).filter_by(id=vc_id).first()
                            if vc:
                                vc.trang_thai = "Đã dùng"
                                _s.commit()
                        finally:
                            _s.close()
                    except Exception:
                        pass
                self._applied_voucher_id = None

                # Tóm tắt đơn để ghi log
                mon_list = ", ".join(
                    f"{it['name']} x{it['qty']}" for it in order_items
                )
                km_info = f" | KM: {self._applied_km['ten']}" if self._applied_km else ""
                _log(self.user.id, "Chốt đơn hàng",
                     f"{message}{km_info} | Món: {mon_list}",
                     o_dau="POS - Thanh toán")

                # ── Reset hóa đơn ───────────────────────────────────
                # FIX: Reset KM TRƯỚC khi gọi update_grand_total
                self._applied_km  = None
                self._km_discount = 0
                self._linked_kh   = None
                self.order_table.clear_items()
                self.update_grand_total()
                self._update_loyalty_label()
                self.refresh_product_grid()

                # ── Cập nhật lịch sử nếu dialog đang mở ──────────────
                # (HistoryDialog là modal nên thường _history_dialog=None
                #  ở đây; đoạn này chỉ là safety-net)
                if self._history_dialog is not None:
                    try:
                        self._history_dialog.load_data()
                    except Exception:
                        pass

                QMessageBox.information(
                    self, "✅ Thành công",
                    f"ĐÃ CHỐT ĐƠN HÀNG!\n\n{message}\n\n"
                    "(Xem Lịch sử giao dịch để lấy mã hóa đơn nếu cần)"
                )
            else:
                _log(self.user.id, "Lỗi chốt đơn", message,
                     o_dau="POS - Thanh toán", ket_qua="Thất bại")
                QMessageBox.warning(self, "Lỗi Database", message)

    def show_shift_manager(self):
        if not yeu_cau_quyen(self.user.chuc_vu, "quan_ly_ca_lam", self):
            return
        _log(self.user.id, "Mở Phân công ca làm", o_dau="Phân công")
        from views.shift_manager import ShiftManagerDialog
        ShiftManagerDialog(self).exec()

    def show_attendance(self):
        if not yeu_cau_quyen(self.user.chuc_vu, "quan_ly_ca_lam", self):
            return
        _log(self.user.id, "Mở Điểm danh", o_dau="Điểm danh")
        from views.attendance_manager import AttendanceDialog
        AttendanceDialog(self).exec()

    def show_khuyen_mai(self):
        _log(self.user.id, "Mở Quản lý KM", o_dau="Khuyến mãi")
        from views.khuyen_mai_manager import KhuyenMaiManagerDialog
        KhuyenMaiManagerDialog(self).exec()

        # Kiểm tra xem KM đang áp dụng có bị xóa hoặc dừng chạy không
        if self._applied_km:
            from database.db_config import get_session
            from database.models import KhuyenMai
            session = get_session()
            try:
                # Chỉ kiểm tra nếu là KM thuộc bảng khuyến mãi (is_km_table=True hoặc mặc định)
                if self._applied_km.get("is_km_table", True):
                    km = session.query(KhuyenMai).filter_by(id=self._applied_km["id"]).first()
                    if not km or km.trang_thai != "Đang chạy":
                        self.order_table.remove_gifts()
                        self._applied_km = None
                        self._km_discount = 0.0
                        self._km_user_picked = False
                        self._applied_voucher_id = None
                        self.update_grand_total()
            except Exception:
                pass
            finally:
                session.close()
    def show_voucher_manager(self):
        from views.voucher_manager import VoucherManagerDialog
        VoucherManagerDialog(self, ma_nv=self.user.id).exec()
    def show_report(self):
        _log(self.user.id, "Mở Báo cáo", o_dau="Báo cáo")
        try:
            from views.report_window import ReportDialog
            ReportDialog(self).exec()
        except ImportError as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, "Lỗi mở Báo cáo",
                f"Không thể mở cửa sổ Báo cáo:\n{e}\n\n"
                "Kiểm tra file views/report_window.py có tồn tại không."
            )
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Lỗi Báo cáo", str(e))

    def show_product_manager(self):
        _log(self.user.id, "Mở Quản lý Menu", o_dau="Menu")
        from views.product_manager import ProductManager
        ProductManager(self).exec()
        self.refresh_product_grid()

    def show_category_manager(self):
        _log(self.user.id, "Mở Quản lý Phân Loại", o_dau="Phân Loại")
        from views.category_manager import CategoryManagerDialog
        CategoryManagerDialog(self).exec()
        self.refresh_product_grid()

    def show_history_dialog(self):
        _log(self.user.id, "Mở Lịch sử giao dịch", o_dau="Lịch sử")
        from views.history_window import HistoryDialog
        self._history_dialog = HistoryDialog(self)
        self._history_dialog.exec()
        # KHÔNG set về None ở đây — để handle_checkout vẫn giữ được reference
        # khi cửa sổ lịch sử vừa được đóng sau thanh toán
        self._history_dialog = None

    # ----------------------------------------------------------------
    # CHECK-OUT CA LÀM VIỆC
    # ----------------------------------------------------------------
    def handle_ca_checkout(self):
        """
        Kết thúc ca làm việc: lưu giờ ra, tính công, khoá nghiệp vụ.
        Nếu không có ca trong ngày (ma_phien=None) → bỏ qua hoàn toàn.
        """
        # Không có ca đang mở → không cần check-out
        # Hỏi DB thực tế thay vì chỉ dựa vào ma_phien (có thể stale)
        try:
            from controllers.auth_controller import lay_ca_dang_mo
            _co_ca_mo = bool(lay_ca_dang_mo(self.user.id))
        except Exception:
            _co_ca_mo = bool(self.ma_phien)   # fallback nếu import lỗi

        if not _co_ca_mo:
            self._da_checkout = True
            return

        if self._da_checkout:
            QMessageBox.information(
                self, "Đã check-out",
                "Bạn đã hoàn tất check-out rồi.\nHãy bấm Đăng xuất để thoát."
            )
            return

        confirm = QMessageBox.question(
            self, "Xác nhận Check-out Ca",
            f"Bạn có muốn kết thúc ca làm việc không?\n\n"
            f"Hệ thống sẽ:\n"
            f"  ✅ Ghi nhận giờ ra\n"
            f"  ✅ Tính tổng giờ làm & tăng ca\n"
            f"  ✅ Khoá các thao tác bán hàng\n"
            f"  ✅ Chuyển trạng thái sang 'Nghỉ ca'",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        # ── Thực hiện check-out qua auth_controller ──────────────
        # checkout_ca(ma_cham_cong: int) — chỉ nhận int ID của ChamCong.
        # Phải dùng lay_ca_dang_mo() để lấy danh sách, rồi loop từng ca.
        checkout_ok  = False
        checkout_msg = ""
        try:
            from controllers.auth_controller import checkout_ca, lay_ca_dang_mo
            cas_dang_mo = lay_ca_dang_mo(self.user.id)

            if not cas_dang_mo:
                # Không còn ca mở nào → coi như đã checkout
                checkout_ok  = True
                checkout_msg = "Không có ca đang mở"
            else:
                ok_list, err_list = [], []
                for ca_info in cas_dang_mo:
                    ok, msg = checkout_ca(ca_info["id"])   # truyền đúng int
                    (ok_list if ok else err_list).append(
                        f"  • {ca_info['ten_ca']}: {msg}"
                    )

                if err_list:
                    QMessageBox.warning(
                        self, "Lỗi Check-out",
                        "Một số ca không thể check-out:\n"
                        + "\n".join(err_list)
                        + "\n\nVui lòng liên hệ Admin hoặc thử lại."
                    )
                    if not ok_list:
                        return   # toàn bộ đều lỗi → dừng lại

                checkout_ok  = True
                checkout_msg = " | ".join(
                    m.strip("  •") for m in ok_list
                ) or "Đã check-out"

        except ImportError as e:
            # Controller chưa triển khai → bypass (backward-compat)
            checkout_ok  = True
            checkout_msg = f"(bỏ qua — {e})"
        except Exception as e:
            QMessageBox.warning(
                self, "Lỗi Check-out",
                f"Lỗi không mong đợi khi check-out:\n{e}\n\n"
                "Vui lòng liên hệ quản trị viên."
            )
            return

        if not checkout_ok:
            return

        # ── Cập nhật trạng thái UI ───────────────────────────────
        self._da_checkout = True

        _log(self.user.id, "Check-out ca làm",
             f"{self.user.ten_nv} kết thúc ca | phiên #{self.ma_phien} | {checkout_msg}",
             o_dau="Ca làm việc")

        # Khoá nút bán hàng
        self.checkout_btn.setEnabled(False)
        self.checkout_btn.setStyleSheet(
            "background-color: #555; color: #999; font-size: 18px;"
            " font-weight: bold; border-radius: 10px;"
        )
        self.checkout_btn.setText("🔒 ĐÃ KHOÁ (Ca đã kết thúc)")

        # Khoá luôn nút check-out và đổi màu
        self.btn_ca_checkout.setEnabled(False)
        self.btn_ca_checkout.setStyleSheet(
            "background-color: #27AE60; color: white; font-weight: bold;"
            " padding: 8px; border-radius: 6px;"
        )
        self.btn_ca_checkout.setText("✅ Đã Check-out")

        # Làm nổi bật nút Đăng xuất để hướng dẫn bước tiếp theo
        self.btn_logout.setStyleSheet(
            "background-color: #E74C3C; color: white; font-weight: bold;"
            " padding: 8px; border-radius: 6px;"
            " border: 2px solid #FF6B6B;"
        )
        self.btn_logout.setText(f"🚪 Đăng xuất ngay ←")

        QMessageBox.information(
            self, "✅ Check-out Thành Công",
            f"Ca làm việc đã được kết thúc!\n\n"
            f"Bạn có thể bấm 'Đăng xuất' để thoát khỏi hệ thống."
        )

    # ----------------------------------------------------------------
    # ĐĂNG XUẤT (thoát phiên ứng dụng)
    # ----------------------------------------------------------------
    def logout(self):
        """
        Thoát phiên đăng nhập.
        - Nếu nhân viên có ca đang mở mà chưa check-out thủ công:
            → Chỉ hiện thông báo nhắc nhở rồi cho phép đăng xuất.
        - Admin: bỏ qua kiểm tra ca, cho đăng xuất thẳng.
        """
        from utils.session_manager import clear_session

        role = getattr(self.user, 'chuc_vu', '') or ''

        # ── Kiểm tra ca đang mở (chỉ với nhân viên chưa tự check-out) ──
        co_ca_dang_mo = False
        if not self._da_checkout and role != "Admin":
            try:
                from controllers.auth_controller import lay_ca_dang_mo
                co_ca_dang_mo = bool(lay_ca_dang_mo(self.user.id))
            except Exception:
                co_ca_dang_mo = getattr(self, '_co_ca', False)

        if co_ca_dang_mo:
            QMessageBox.information(
                self, "⚠️ Nhắc nhở",
                "Bạn chưa check-out ca làm việc.\n"
                "Lưu ý: Bạn cần tự check-out thủ công để ghi nhận giờ ra chính xác."
            )

        # ── Xác nhận đăng xuất ───────────────────────────────────
        confirm = QMessageBox.question(
            self, "Đăng xuất",
            "Bạn có chắc chắn muốn đăng xuất?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        _log(self.user.id, "Đăng xuất POS",
             f"{self.user.ten_nv} đăng xuất khỏi màn hình bán hàng",
             o_dau="POS")

        # Gọi logout_user để đóng phiên (tự ghi giờ ra nếu còn ca chưa checkout)
        try:
            from controllers.auth_controller import logout_user
            logout_user(self.user, ma_phien=self.ma_phien)
        except Exception:
            pass

        clear_session()
        self.is_logged_out = True
        self.close()