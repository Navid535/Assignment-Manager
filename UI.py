import sys, re, os
from core import *
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QColor, QTransform, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return str(os.path.join(base_path, relative_path))


class AddDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("New Assignment")
        self.setMinimumSize(QSize(500, 300))

        layout = QVBoxLayout(self)

        # -------- Name --------
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Course name:"))
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # -------- Deadline (Jalali) --------
        deadline_layout = QHBoxLayout()
        deadline_layout.addWidget(QLabel("Deadline (Jalali YYYY-MM-DD):"))
        self.deadline_input = QLineEdit()
        self.deadline_input.setPlaceholderText("1404-02-03")
        self.deadline_input.setInputMask("9999-99-99")
        deadline_layout.addWidget(self.deadline_input)
        layout.addLayout(deadline_layout)

        # -------- Stars --------
        stars_layout = QHBoxLayout()
        stars_layout.addWidget(QLabel("Difficulty (stars):"))
        self.stars_input = QSpinBox()
        self.stars_input.setRange(1, 7)
        stars_layout.addWidget(self.stars_input)
        layout.addLayout(stars_layout)

        # -------- Buttons --------
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_ok = QPushButton("OK")
        self.btn_ok.setEnabled(False)
        self.btn_cancel = QPushButton("Cancel")

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.name_input.textChanged.connect(self.validate)
        self.deadline_input.textChanged.connect(self.validate)

    def validate(self):
        name_ok = len(self.name_input.text().strip()) > 0

        date_text = self.deadline_input.text().strip()
        date_pattern = r"^\d{4}-\d{2}-\d{2}$"
        date_ok = re.match(date_pattern, date_text) is not None

        self.btn_ok.setEnabled(name_ok and date_ok)

    def get_data(self):
        return (
            self.name_input.text().strip(),
            self.deadline_input.text().strip(),
            self.stars_input.value(),
        )


class EditDialog(QDialog):
    def __init__(self, name, deadline_jalali, stars, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Edit Assignment")
        self.setMinimumSize(QSize(500, 300))

        layout = QVBoxLayout(self)

        # -------- Name --------
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Course name:"))
        self.name_input = QLineEdit(name)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # -------- Deadline --------
        deadline_layout = QHBoxLayout()
        deadline_layout.addWidget(QLabel("Deadline (Jalali):"))
        self.deadline_input = QLineEdit(deadline_jalali)
        self.deadline_input.setInputMask("9999-99-99")
        deadline_layout.addWidget(self.deadline_input)
        layout.addLayout(deadline_layout)

        # -------- Stars --------
        stars_layout = QHBoxLayout()
        stars_layout.addWidget(QLabel("Difficulty:"))
        self.stars_input = QSpinBox()
        self.stars_input.setRange(1, 7)
        self.stars_input.setValue(stars)
        stars_layout.addWidget(self.stars_input)
        layout.addLayout(stars_layout)

        # -------- Buttons --------
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_ok = QPushButton("Save")
        btn_cancel = QPushButton("Cancel")

        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def get_data(self):
        return (
            self.name_input.text().strip(),
            self.deadline_input.text().strip(),
            self.stars_input.value(),
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Assignment Manager")
        self.setMinimumSize(QSize(1000, 700))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # ---------- Buttons ----------
        button_layout = QHBoxLayout()

        self.btn_add = QPushButton("Add")
        self.btn_edit = QPushButton("Edit")
        self.btn_edit.setEnabled(False)
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setEnabled(False)
        self.btn_refresh = QPushButton("Refresh")

        button_layout.addWidget(self.btn_add)
        button_layout.addWidget(self.btn_edit)
        button_layout.addWidget(self.btn_delete)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_refresh)

        self.btn_add.clicked.connect(self.add_clicked)
        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_edit.clicked.connect(self.edit_clicked)
        self.btn_delete.clicked.connect(self.delete_clicked)

        self.btn_add.setIcon(QIcon(resource_path("icons/add.svg")))
        self.btn_add.setIconSize(QSize(20, 20))
        self.btn_edit.setIcon(QIcon(resource_path("icons/edit.svg")))
        self.btn_edit.setIconSize(QSize(20, 20))
        self.btn_delete.setIcon(QIcon(resource_path("icons/delete.svg")))
        self.btn_delete.setIconSize(QSize(20, 20))
        self.btn_refresh.setIcon(QIcon(resource_path("icons/refresh.svg")))
        self.btn_refresh.setIconSize(QSize(20, 20))
        self.refresh_icon = QPixmap(resource_path("icons/refresh.png"))
        self._rotation_angle = 0

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.rotate_refresh_icon)

        main_layout.addLayout(button_layout)

        # ---------- Table ----------
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Deadline", "Difficulty"])

        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        # no assignment
        self.placeholder = QLabel(
            "Unbelievable, No assignment found. congratulation!", self.table
        )
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.hide()

        # ----------------- today ---------
        today_jalali = JalaliDate.today().isoformat()
        self.lbl_today = QLabel()
        self.lbl_today.setAlignment(Qt.AlignLeft)
        self.lbl_today.setText(f"Today: {today_jalali}")

        # button showing
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

        # deselection
        self.table.cellClicked.connect(self.on_cell_clicked)
        self._last_selected_row = None

        self.refresh(first_time=True)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        for col in range(self.table.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.Stretch)
        header.setDefaultAlignment(Qt.AlignLeft)
        main_layout.addWidget(self.lbl_today)
        main_layout.addWidget(self.table)
        # self.placeholder.resize(self.table.size())

    def rotate_refresh_icon(self):
        transform = QTransform().rotate(self._rotation_angle)
        rotated = self.refresh_icon.transformed(transform, Qt.SmoothTransformation)

        self.btn_refresh.setIcon(QIcon(rotated))
        self._rotation_angle = (self._rotation_angle + 90) % 360

    def start_refresh_animation(self):
        self._rotation_angle = 0
        self.refresh_timer.start(120)

    def stop_refresh_animation(self):
        self.refresh_timer.stop()
        self.btn_refresh.setIcon(QIcon(self.refresh_icon))

    def on_cell_clicked(self, row, column):
        if self._last_selected_row == row:
            self.table.clearSelection()
            self._last_selected_row = None
        else:
            self._last_selected_row = row

    def on_selection_changed(self):
        has_selection = self.table.currentRow() >= 0

        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)

    def showEvent(self, event):
        super().showEvent(event)
        self.placeholder.resize(self.table.size())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.placeholder.resize(self.table.size())

    def add_clicked(self, s):
        dlg = AddDialog(self)
        if dlg.exec() == QDialog.Accepted:
            name, deadline, stars = dlg.get_data()
            try:
                with AssignmentManager("assignments.db") as mgr:
                    mgr.add(name, deadline, stars)
                    self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def refresh(self, first_time=False):
        self.start_refresh_animation()
        try:
            with AssignmentManager("assignments.db") as mgr:
                all_assignments = mgr.get_all()
                number_of_all = len(all_assignments)

                self.table.setRowCount(number_of_all)

                if number_of_all == 0:
                    self.placeholder.show()
                    self.statusBar().showMessage(
                        "Go waste your time on ridiculous things, engineer.", 2500
                    )

                if number_of_all > 0:
                    self.placeholder.hide()
                    self.statusBar().showMessage("Data refreshed, engineer.", 1500)
                    if number_of_all > 3:
                        self.statusBar().showMessage(
                            "It seems like you're cooked, engineer.", 2500
                        )

                for idx, ass in enumerate(all_assignments):
                    iname = QTableWidgetItem(str(ass["name"]).upper())
                    iname.setData(Qt.UserRole, ass["id"])
                    self.table.setItem(idx, 0, iname)
                    # self.table.setItem(idx, 1, QTableWidgetItem(ass['deadline']))
                    self.table.setItem(idx, 1, QTableWidgetItem(ass["deadline_jalali"]))
                    self.table.setItem(
                        idx, 2, QTableWidgetItem("★" * int(ass["stars"]))
                    )

                    jalali_deadline = JalaliDate.fromisoformat(ass["deadline_jalali"])
                    greg_deadline = jalali_deadline.to_gregorian()
                    today = datetime.date.today()

                    remaining = (greg_deadline - today).days
                    if remaining <= 3:
                        fcolor = QColor("#e60909")
                        bcolor = QColor("#360101")
                    elif remaining <= 7:
                        fcolor = QColor("#f7c705")
                        bcolor = QColor("#403301")
                    else:
                        fcolor = None
                        bcolor = None
                    if fcolor:
                        for col in range(self.table.columnCount()):
                            self.table.item(idx, col).setForeground(fcolor)
                            self.table.item(idx, col).setBackground(bcolor)
                            if remaining < 3:
                                self.table.item(idx, col).setToolTip(
                                    f"Deadline in {remaining} day(s). Wake up engineer!"
                                )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        QTimer.singleShot(900, self.stop_refresh_animation)

    def edit_clicked(self):
        selected = self.table.currentRow()

        if selected < 0:
            QMessageBox.warning(
                self, "Warning", "No assignments found, Please select an assignment."
            )
            return

        iname = self.table.item(selected, 0)
        ideadline = self.table.item(selected, 1)
        stars = self.table.item(selected, 2)
        id = iname.data(Qt.UserRole)
        name = iname.text()
        dl = ideadline.text()
        stars = stars.text().count("★")

        dlg = EditDialog(name, dl, stars, self)

        if dlg.exec() == QDialog.Accepted:
            new_name, new_dl, new_strs = dlg.get_data()
            try:
                with AssignmentManager("assignments.db") as mgr:
                    mgr.update_by_id(id, new_name, new_dl, new_strs)
                self.table.clearSelection()
                self._last_selected_row = None
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def delete_clicked(self):
        selected = self.table.currentRow()

        if selected < 0:
            QMessageBox.warning(
                self, "Warning", "No assignments found, Please select an assignment."
            )
            return

        iname = self.table.item(selected, 0)
        ass_id = iname.data(Qt.UserRole)
        name = iname.text()

        reply = QMessageBox.question(
            self,
            "Delete Assignment",
            f"Are you sure you want to delete {name}?",
        )

        if reply == QMessageBox.Yes:
            with AssignmentManager("assignments.db") as mgr:
                mgr.delete_by_id(ass_id)
            self.refresh()
            self._last_selected_row = None
            self.table.clearSelection()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyleSheet(
        """
        QMainWindow {
            background-color: #171219;
        }
        
        QTableWidget {
            background-color: #000F08;
            color: #ffffff;
            text-align: center;
            gridline-color: #0A3F36;
            border: 1px solid #0A3F36;
        }
        
        QHeaderView::section {
            background-color: #136F63;
            color: white;
            padding: 4px;
            border: none;
        }
        
        QPushButton {
            background-color: #136F63;
            color: #ffffff;
            padding: 6px 12px;
            border-radius: 4px;
        }
        
        QPushButton:disabled {
        background-color: #1e3a37;
        color: #7f9a97;
        }
        
        QPushButton:hover {
            background-color: #47865A;
        }
        
        QPushButton:pressed {
            background-color: #86A660;
        }
        
        QDialog {
            background-color: #000F08;
            
        }
        
        QLabel {
                color: #aaa;
                font-size: 14px;
        }
    """
    )

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
