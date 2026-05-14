"""
views/attendance_manager.py
─────────────────────────────────────────────────────────────────
Dialog Điểm Danh — Quản lý chấm công nhân viên theo ngày.

Bảng DB cần có (thêm vào models.py nếu chưa có):

    class ChamCong(Base):
        __tablename__ = "cham_cong"
        id           = Column(Integer, primary_key=True)
        nhan_vien_id = Column(Integer, ForeignKey("nhan_vien.id"))
        ngay         = Column(Date, nullable=False)
        gio_vao      = Column(Time, nullable=True)
        gio_ra       = Column(Time, nullable=True)
        trang_thai   = Column(String, default="Co_mat")  # Co_mat / Vang / Tre
        ghi_chu      = Column(String, nullable=True)
        nhan_vien    = relationship("NhanVien", back_populates="cham_congs")
"""

from datetime import date, time as dtime, datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QMessageBox, QWidget, QDateEdit, QTimeEdit, QLineEdit,
    QFormLayout, QFrame,
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QColor

from database.db_config import get_session

# ── Import model an toàn ──────────────────────────────────────
try:
    from database.models import ChamCong, NhanVien
    _MODELS_OK = True
except ImportError:
    _MODELS_OK = False


STYLE = """
QDialog, QWidget { background-color: #1E1E2E; color: white; }
QTableWidget {
    background-color: #2D2D3F; border: none; border-radius: 8px;
    gridline-color: #3E3E55; color: white; font-size: 13px;
}
QTableWidget::item { padding: 6px; border-bottom: 1px solid #3E3E55; }
QTableWidget::item:selected { background: #2980B9; }
QHeaderView::section {
    background-color: #2C3E50; color: #A1A1AA; padding: 8px;
    border: none; font-weight: bold;
}
QPushButton { border-radius: 6px; padding: 6px 12px; font-weight: bold; }
QComboBox, QDateEdit, QTimeEdit, QLineEdit {
    background-color: #2D2D3F; border: 1px solid #3E3E55;
    border-radius: 6px; padding: 6px; color: white;
}
QLabel { color: #BDC3C7; }
"""

TT_COLOR = {
    "Co_mat": "#2ECC71",
    "Vang":   "#E74C3C",
    "Tre":    "#F39C12",
}


def _btn(text, color, h=36):
    b = QPushButton(text)
    b.setMinimumHeight(h)
    b.setStyleSheet(f"background-color:{color}; color:white; font-weight:bold; border-radius:6px;")
    return b


def _lbl(text, color="#BDC3C7", size=13, bold=False):
    l = QLabel(text)
    w = "bold" if bold else "normal"
    l.setStyleSheet(f"color:{color}; font-size:{size}px; font-weight:{w}; background:transparent;")
    return l


# ═══════════════════════════════════════════════════════════════
# FORM ĐIỂM DANH / SỬA CHẤM CÔNG
# ═══════════════════════════════════════════════════════════════
class ChamCongForm(QDialog):
    def __init__(self, cc_id=None, default_nv_id=None, default_ngay=None, parent=None):
        super().__init__(parent)
        self.cc_id = cc_id
        self.setWindowTitle("Điểm Danh" if not cc_id else "Sửa Chấm Công")
        self.resize(420, 380)
        self.setStyleSheet(STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        root.addWidget(_lbl("CHẤM CÔNG NHÂN VIÊN", "#3498DB", 15, True))

        form = QFormLayout(); form.setSpacing(10)

        def _fl(t):
            l = QLabel(t); l.setStyleSheet("color:#A1A1AA;"); return l

        # Nhân viên
        self.cb_nv = QComboBox()
        self._nv_map = {}
        s = get_session()
        try:
            nvs = s.query(NhanVien).order_by(NhanVien.ten_nv).all()
            for nv in nvs:
                self.cb_nv.addItem(f"{nv.ten_nv} ({nv.chuc_vu})", nv.id)
                self._nv_map[nv.id] = nv.ten_nv
        finally:
            s.close()
        if default_nv_id:
            idx = self.cb_nv.findData(default_nv_id)
            if idx >= 0: self.cb_nv.setCurrentIndex(idx)

        # Ngày
        self.de_ngay = QDateEdit(QDate.currentDate())
        self.de_ngay.setCalendarPopup(True)
        self.de_ngay.setDisplayFormat("dd/MM/yyyy")
        if default_ngay:
            self.de_ngay.setDate(QDate(default_ngay.year, default_ngay.month, default_ngay.day))

        # Giờ vào / ra
        self.te_vao = QTimeEdit(QTime(7, 0))
        self.te_vao.setDisplayFormat("HH:mm")
        self.te_ra  = QTimeEdit(QTime(17, 0))
        self.te_ra.setDisplayFormat("HH:mm")

        # Trạng thái
        self.cb_tt = QComboBox()
        self.cb_tt.addItems(["Co_mat", "Vang", "Tre"])

        # Ghi chú
        self.txt_note = QLineEdit()
        self.txt_note.setPlaceholderText("Lý do vắng, ghi chú thêm...")

        form.addRow(_fl("Nhân viên:"),   self.cb_nv)
        form.addRow(_fl("Ngày:"),        self.de_ngay)
        form.addRow(_fl("Giờ vào:"),     self.te_vao)
        form.addRow(_fl("Giờ ra:"),      self.te_ra)
        form.addRow(_fl("Trạng thái:"),  self.cb_tt)
        form.addRow(_fl("Ghi chú:"),     self.txt_note)
        root.addLayout(form)

        # Kết nối: khi chọn Vắng → ẩn giờ
        self.cb_tt.currentTextChanged.connect(self._on_tt_changed)

        btn_save = _btn("💾 Lưu Chấm Công", "#27AE60", 44)
        btn_save.clicked.connect(self._save)
        root.addWidget(btn_save)

        if cc_id:
            self._load()

    def _on_tt_changed(self, tt):
        vang = (tt == "Vang")
        self.te_vao.setEnabled(not vang)
        self.te_ra.setEnabled(not vang)

    def _load(self):
        s = get_session()
        cc = s.query(ChamCong).get(self.cc_id); s.close()
        if not cc: return
        idx = self.cb_nv.findData(cc.nhan_vien_id)
        if idx >= 0: self.cb_nv.setCurrentIndex(idx)
        self.de_ngay.setDate(QDate(cc.ngay.year, cc.ngay.month, cc.ngay.day))
        if cc.gio_vao:
            self.te_vao.setTime(QTime(cc.gio_vao.hour, cc.gio_vao.minute))
        if cc.gio_ra:
            self.te_ra.setTime(QTime(cc.gio_ra.hour, cc.gio_ra.minute))
        self.cb_tt.setCurrentText(cc.trang_thai or "Co_mat")
        self.txt_note.setText(cc.ghi_chu or "")

    def _save(self):
        nv_id = self.cb_nv.currentData()
        qd    = self.de_ngay.date()
        ngay  = date(qd.year(), qd.month(), qd.day())
        tt    = self.cb_tt.currentText()

        qvao = self.te_vao.time()
        qra  = self.te_ra.time()
        gio_vao = dtime(qvao.hour(), qvao.minute()) if tt != "Vang" else None
        gio_ra  = dtime(qra.hour(),  qra.minute())  if tt != "Vang" else None

        s = get_session()
        try:
            if self.cc_id:
                cc = s.query(ChamCong).get(self.cc_id)
            else:
                # Kiểm tra đã chấm hôm nay chưa
                exists = s.query(ChamCong).filter_by(
                    nhan_vien_id=nv_id, ngay=ngay
                ).first()
                if exists:
                    QMessageBox.warning(
                        self, "Đã chấm",
                        "Nhân viên này đã được chấm công ngày này!\n"
                        "Hãy chọn bản ghi có sẵn để sửa."
                    )
                    return
                cc = ChamCong(); s.add(cc)

            cc.nhan_vien_id = nv_id
            cc.ngay         = ngay
            cc.gio_vao      = gio_vao
            cc.gio_ra       = gio_ra
            cc.trang_thai   = tt
            cc.ghi_chu      = self.txt_note.text().strip() or None
            s.commit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi DB", str(e))
        finally:
            s.close()


# ═══════════════════════════════════════════════════════════════
# DIALOG CHÍNH — QUẢN LÝ ĐIỂM DANH
# ═══════════════════════════════════════════════════════════════
class AttendanceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✅ Điểm Danh & Chấm Công")
        self.resize(880, 580)
        self.setStyleSheet(STYLE)

        if not _MODELS_OK:
            QVBoxLayout(self).addWidget(
                _lbl("⚠️ Chưa có model ChamCong trong database/models.py.\n"
                     "Hãy thêm bảng ChamCong và chạy lại migrate.", "#E74C3C", 14)
            )
            return

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 16)
        root.setSpacing(10)

        # ── Tiêu đề ──────────────────────────────────────────────
        root.addWidget(_lbl("✅ ĐIỂM DANH & CHẤM CÔNG", "#2ECC71", 17, True))

        # ── Thanh lọc ────────────────────────────────────────────
        bar = QHBoxLayout(); bar.setSpacing(10)

        bar.addWidget(_lbl("Ngày:"))
        self.de_filter = QDateEdit(QDate.currentDate())
        self.de_filter.setCalendarPopup(True)
        self.de_filter.setDisplayFormat("dd/MM/yyyy")
        self.de_filter.setFixedWidth(140)
        self.de_filter.dateChanged.connect(self.load_data)
        bar.addWidget(self.de_filter)

        bar.addWidget(_lbl("Nhân viên:"))
        self.cb_nv_filter = QComboBox()
        self.cb_nv_filter.setFixedWidth(200)
        self.cb_nv_filter.addItem("-- Tất cả --", None)
        self._load_nv_filter()
        self.cb_nv_filter.currentIndexChanged.connect(self.load_data)
        bar.addWidget(self.cb_nv_filter)

        bar.addStretch()

        btn_add   = _btn("➕ Chấm công", "#27AE60")
        btn_edit  = _btn("✏️ Sửa",      "#2980B9")
        btn_del   = _btn("🗑 Xóa",      "#C0392B")
        btn_today = _btn("📅 Chấm nhanh hôm nay", "#8E44AD")

        for b in [btn_add, btn_edit, btn_del, btn_today]:
            b.setDefault(False); b.setAutoDefault(False)
            bar.addWidget(b)

        root.addLayout(bar)

        # ── Bảng chấm công ───────────────────────────────────────
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Nhân Viên", "Chức Vụ", "Ngày", "Giờ Vào", "Giờ Ra", "Trạng Thái", "Ghi Chú"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 90)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        root.addWidget(self.table)

        # ── Thanh thống kê ───────────────────────────────────────
        self.lbl_stat = _lbl("", "#A1A1AA", 12)
        root.addWidget(self.lbl_stat)

        # Kết nối nút
        btn_add.clicked.connect(self._add)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_today.clicked.connect(self._quick_checkin_today)

        self.load_data()

    def _load_nv_filter(self):
        s = get_session()
        try:
            nvs = s.query(NhanVien).order_by(NhanVien.ten_nv).all()
            for nv in nvs:
                self.cb_nv_filter.addItem(nv.ten_nv, nv.id)
        finally:
            s.close()

    def load_data(self):
        qd   = self.de_filter.date()
        ngay = date(qd.year(), qd.month(), qd.day())
        nv_id = self.cb_nv_filter.currentData()

        s = get_session()
        try:
            q = s.query(ChamCong).filter(ChamCong.ngay == ngay)
            if nv_id:
                q = q.filter(ChamCong.nhan_vien_id == nv_id)
            records = q.join(NhanVien).order_by(NhanVien.ten_nv).all()

            self.table.setRowCount(0)
            co_mat = vang = tre = 0
            for cc in records:
                r = self.table.rowCount()
                self.table.insertRow(r)
                nv = cc.nhan_vien

                def _item(text, color=None):
                    it = QTableWidgetItem(text)
                    it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    if color:
                        it.setForeground(QColor(color))
                    return it

                self.table.setItem(r, 0, _item(nv.ten_nv if nv else "?"))
                self.table.setItem(r, 1, _item(nv.chuc_vu if nv else ""))
                self.table.setItem(r, 2, _item(cc.ngay.strftime("%d/%m/%Y")))
                self.table.setItem(r, 3, _item(cc.gio_vao.strftime("%H:%M") if cc.gio_vao else "--"))
                self.table.setItem(r, 4, _item(cc.gio_ra.strftime("%H:%M")  if cc.gio_ra  else "--"))

                tt_color = TT_COLOR.get(cc.trang_thai, "#BDC3C7")
                tt_text  = {"Co_mat": "Có mặt", "Vang": "Vắng", "Tre": "Đi trễ"}.get(
                    cc.trang_thai, cc.trang_thai
                )
                tt_item = _item(tt_text, tt_color)
                tt_item.setData(Qt.UserRole, cc.id)
                self.table.setItem(r, 5, tt_item)
                self.table.setItem(r, 6, _item(cc.ghi_chu or ""))

                if cc.trang_thai == "Co_mat": co_mat += 1
                elif cc.trang_thai == "Vang":  vang  += 1
                elif cc.trang_thai == "Tre":   tre   += 1

            total = co_mat + vang + tre
            self.lbl_stat.setText(
                f"Tổng: {total} nhân viên  |  "
                f"✅ Có mặt: {co_mat}  |  ❌ Vắng: {vang}  |  ⏰ Trễ: {tre}"
            )
        finally:
            s.close()

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0: return None
        it = self.table.item(row, 5)
        return it.data(Qt.UserRole) if it else None

    def _add(self):
        qd = self.de_filter.date()
        ngay = date(qd.year(), qd.month(), qd.day())
        if ChamCongForm(default_ngay=ngay, parent=self).exec():
            self.load_data()

    def _edit(self):
        cc_id = self._selected_id()
        if not cc_id:
            QMessageBox.warning(self, "Chưa chọn", "Hãy chọn một bản ghi để sửa!"); return
        if ChamCongForm(cc_id=cc_id, parent=self).exec():
            self.load_data()

    def _delete(self):
        cc_id = self._selected_id()
        if not cc_id:
            QMessageBox.warning(self, "Chưa chọn", "Hãy chọn một bản ghi để xóa!"); return
        if QMessageBox.question(
            self, "Xác nhận", "Xóa bản ghi chấm công này?",
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return
        s = get_session()
        try:
            cc = s.query(ChamCong).get(cc_id)
            if cc: s.delete(cc); s.commit()
        finally:
            s.close()
        self.load_data()

    def _quick_checkin_today(self):
        """Chấm nhanh toàn bộ nhân viên chưa có record hôm nay với mặc định Có mặt."""
        qd   = self.de_filter.date()
        ngay = date(qd.year(), qd.month(), qd.day())
        s = get_session()
        added = 0
        try:
            nvs = s.query(NhanVien).all()
            for nv in nvs:
                exists = s.query(ChamCong).filter_by(nhan_vien_id=nv.id, ngay=ngay).first()
                if not exists:
                    cc = ChamCong()
                    cc.nhan_vien_id = nv.id
                    cc.ngay         = ngay
                    cc.gio_vao      = dtime(7, 0)
                    cc.gio_ra       = dtime(17, 0)
                    cc.trang_thai   = "Co_mat"
                    s.add(cc)
                    added += 1
            s.commit()
        finally:
            s.close()

        QMessageBox.information(
            self, "Hoàn tất",
            f"Đã chấm nhanh {added} nhân viên chưa có dữ liệu hôm nay.\n"
            "Hãy sửa lại những ai vắng hoặc đến trễ."
        )
        self.load_data()