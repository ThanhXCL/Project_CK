# app.py
import sys
import socket
from PyQt5 import QtWidgets
from ui.ui_remote import UiRemote
from socket_module.server import RemoteServer
from socket_module.client import RemoteClient


class AppLogic:
    def __init__(self, ui: UiRemote):
        self.ui = ui
        self.server = None
        self.client = None

        # Bind logic vào UI
        self.ui.bind_logic(self)

        # Hiển thị IP cục bộ
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            local_ip = "127.0.0.1"
        self.ui.txt_my_id.setText(local_ip)

    # -------------------------------
    # Server
    # -------------------------------
    def start_server(self):
        port = int(self.ui.txt_port.text())  # đọc port từ UI khi bấm nút
        password = self.ui.txt_pwd.text()
        self.server = RemoteServer(
            host="0.0.0.0",
            port_cmd=port,
            port_vid=port + 1,
            password=password
        )
        self.server.start()
        self.ui.lbl_status.setText("Server started...")
        self.ui.btn_start.setEnabled(False)
        self.ui.btn_stop.setEnabled(True)

    def stop_server(self):
        if self.server:
            try:
                self.server.stop()
            except Exception as e:
                print("[App] Stop server error:", e)
            self.server = None
            self.ui.lbl_status.setText("⏹ Server đã dừng")
            self.ui.btn_start.setEnabled(True)
            self.ui.btn_stop.setEnabled(False)

    # ✅ Ngắt luôn client nếu có
        if self.client:
            self.disconnect_from_server()

    # -------------------------------
    # Client
    # -------------------------------
    def connect_to_server(self):
        host = self.ui.in_host.text().strip()
        port = int(self.ui.in_port.text())
        password = self.ui.in_pwd.text()

        try:
            # tạo client, gán callback trước khi connect()
            self.client = RemoteClient(
                host,
                port_cmd=port,
                port_vid=port + 1,
                password=password,
                frame_callback=self.ui.frame_received,  # truyền signal của UI
                server_stop_callback=self.on_server_stopped
            )
            # Nếu UI dùng function thay vì signal, dùng: self.ui.update_frame
            # self.client.frame_callback = self.ui.update_frame

            # Thực sự mở kết nối (socket) và start recv thread
            self.client.connect()

            self.ui.lbl_status.setText("Đã kết nối tới server")
            self.ui.btn_connect.setEnabled(False)
            self.ui.btn_disconnect.setEnabled(True)
            # để UI gọi client khi thao tác
            self.ui.logic = self
        except Exception as e:
            self.ui.lbl_status.setText(f"Kết nối thất bại: {e}")
            print("[App] Connect error:", e)


    def on_server_stopped(self):
        self.disconnect_from_server()
        self.ui.viewer.setText("⚠️ Server đã dừng")
    
    def disconnect_from_server(self):
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                print("[App] Disconnect error:", e)
            self.client = None

        # reset UI
        self.ui.viewer.setText("❌ Chưa kết nối")
        self.ui.btn_connect.setEnabled(True)
        self.ui.btn_disconnect.setEnabled(False)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = UiRemote()
    logic = AppLogic(ui)
    ui.show()
    sys.exit(app.exec_())
