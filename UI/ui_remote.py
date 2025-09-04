from PyQt5 import QtWidgets, QtCore, QtGui
from control.control_client import ClientControl
import random
import string


class UiRemote(QtWidgets.QMainWindow):
    frame_received = QtCore.pyqtSignal(bytes)
    def __init__(self):
        super().__init__()
        self.frame_received.connect(self.update_frame)
        self.setWindowTitle('REMOTE DESKTOP')
        self.setMinimumSize(800, 600)
        self.resize(1000, 600)

        # ================== Giao diện chính ==================
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QHBoxLayout(central)



        # ================== Panel trái: Server ==================
        server_box = QtWidgets.QGroupBox('Máy bị điều khiển (Server)')
        server_box.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        server_layout = QtWidgets.QFormLayout(server_box)

        self.txt_my_id = QtWidgets.QLineEdit("0.0.0.0")
        self.txt_my_id.setReadOnly(True)
        self.txt_port = QtWidgets.QLineEdit('8888')
        self.txt_pwd = QtWidgets.QLineEdit("123456")
        self.txt_pwd.setEchoMode(QtWidgets.QLineEdit.Normal)

        # đổi thành btn_change_pass
        self.btn_change_pass = QtWidgets.QPushButton('🔄 Đổi mật khẩu')
        self.btn_start = QtWidgets.QPushButton('▶️ Start Server')
        self.btn_stop = QtWidgets.QPushButton('⏹ Stop Server')
        self.btn_stop.setEnabled(False)
        self.btn_change_pass.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_start.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_stop.setFocusPolicy(QtCore.Qt.NoFocus)

        self.lbl_status = QtWidgets.QLabel('Chưa khởi động')
        self.lbl_status.setStyleSheet("color: gray; font-style: italic;")

        

        # add row
        server_layout.addRow('ID (IP):', self.txt_my_id)
        server_layout.addRow('Port:', self.txt_port)
        row_pwd = QtWidgets.QHBoxLayout()
        row_pwd.addWidget(self.txt_pwd)
        row_pwd.addWidget(self.btn_change_pass)
        server_layout.addRow('Mật khẩu:', row_pwd)

        row_btns = QtWidgets.QHBoxLayout()
        row_btns.addWidget(self.btn_start)
        row_btns.addWidget(self.btn_stop)
        server_layout.addRow(row_btns)
        server_layout.addRow('Trạng thái:', self.lbl_status)

        # ================== Panel phải: Client ==================
        client_box = QtWidgets.QGroupBox('Điều khiển máy khác (Client)')
        client_box.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        client_layout = QtWidgets.QFormLayout(client_box)

        self.in_host = QtWidgets.QLineEdit()
        self.in_port = QtWidgets.QLineEdit('8888')
        self.in_pwd = QtWidgets.QLineEdit()
        self.in_pwd.setEchoMode(QtWidgets.QLineEdit.Password)

        self.btn_connect = QtWidgets.QPushButton('🔗 Kết nối')
        self.btn_disconnect = QtWidgets.QPushButton('❌ Ngắt kết nối')
        self.btn_disconnect.setEnabled(False)
        self.btn_connect.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_disconnect.setFocusPolicy(QtCore.Qt.NoFocus)

        client_layout.addRow('ID đối tác (IP):', self.in_host)
        client_layout.addRow('Port:', self.in_port)
        client_layout.addRow('Mật khẩu:', self.in_pwd)
        row_client_btns = QtWidgets.QHBoxLayout()
        row_client_btns.addWidget(self.btn_connect)
        row_client_btns.addWidget(self.btn_disconnect)
        client_layout.addRow(row_client_btns)

        # ================== Viewer ==================
        viewer_box = QtWidgets.QGroupBox('Xem màn hình đối tác')
        vlayout = QtWidgets.QVBoxLayout(viewer_box)

        self.viewer = QtWidgets.QLabel("Chưa kết nối") 
        self.viewer.setAlignment(QtCore.Qt.AlignCenter)
        self.viewer.setStyleSheet("""
            background: #111;
            color: #bbb;
            border: 2px dashed #555;
            font-size: 14px;
        """)
        vlayout.addWidget(self.viewer)

        # Combine layout
        side_layout = QtWidgets.QVBoxLayout()
        side_layout.addWidget(server_box)
        side_layout.addWidget(client_box)
        main_layout.addLayout(side_layout, 0)
        main_layout.addWidget(viewer_box, 1)

        # ======= Kết nối sự kiện =======
        self.btn_change_pass.clicked.connect(self.change_password)
        self.logic = None  # sẽ bind sau




    # ================== Đổi mật khẩu ==================
    def change_password(self):
        # Sinh mật khẩu random 6 ký tự
        new_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        self.txt_pwd.setText(new_pass)
        self.lbl_status.setText(f"Password da duoc doi ✅ ({new_pass})")
        self.lbl_status.setStyleSheet("color: green;")

    # ================== Gán logic vào UI ==================
    def bind_logic(self, logic):
        self.logic = logic
        self.btn_connect.clicked.connect(logic.connect_to_server)
        self.btn_disconnect.clicked.connect(logic.disconnect_from_server)
        self.btn_start.clicked.connect(logic.start_server)
        self.btn_stop.clicked.connect(logic.stop_server)
        self.control = ClientControl(logic, self.viewer)
        # Gán callback video
        if hasattr(logic, "client") and logic.client:
            logic.client.frame_callback = self.update_frame
            

   # ================== Cập nhật khung hình ==================
    def update_frame(self, data: bytes):
        try:
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(data)  # load ảnh từ bytes
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.viewer.size(),
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation
                )
                self.viewer.setPixmap(scaled)
                self.viewer.setFocus() 
        except Exception as e:
            print("[UI] Error frame:", e)
