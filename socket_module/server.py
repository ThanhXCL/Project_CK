import socket, threading, time, io
from networkx import draw
from .common import send_with_len, recv_json, send_json
from control.control_server import (
    screenshot_bytes,
    click, mouse_down, mouse_up, scroll, press, type_text, key_down, key_up,
    move_mouse_norm, move_click_norm
)
import pyautogui
from PIL import Image, ImageDraw


class RemoteServer:
    # ===================== Khởi tạo =====================
    def __init__(self, host="0.0.0.0", port_cmd=8888, port_vid=8889, password="123456"):
        self.host = host
        self.port_cmd = port_cmd
        self.port_vid = port_vid
        self.password = password
        self.cmd_socket = None
        self.vid_socket = None
        self._stop = threading.Event()
        self._threads = []
        self._cmd_conns = []   # lưu tất cả client CMD kết nối

    def start(self):
        self._stop.clear()
        t1 = threading.Thread(target=self._serve_cmd, daemon=True)
        t2 = threading.Thread(target=self._serve_vid, daemon=True)
        t1.start()
        t2.start()
        self._threads.extend([t1, t2])
        print(f"[Server] Listening at {self.host}:{self.port_cmd} (CMD), {self.port_vid} (VID)")

    def stop(self):
        print("[Server] Stopping...")
        self._stop.set()

        # gửi tín hiệu server_stop cho tất cả client
        for c in list(self._cmd_conns):
            try:
                send_json(c, {"type": "server_stop"})
                c.close()
            except:
                pass
        self._cmd_conns.clear()

        # đóng socket gốc
        for s in (self.cmd_socket, self.vid_socket):
            if s:
                try:
                    s.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                try:
                    s.close()
                except:
                    pass
        self.cmd_socket = None
        self.vid_socket = None

    # ===================== CMD =====================
    def _serve_cmd(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port_cmd))
        s.listen(5)
        self.cmd_socket = s
        print("[Server] CMD socket listening...")

        while not self._stop.is_set():
            try:
                conn, addr = s.accept()
            except OSError:
                break
            if self._stop.is_set():
                conn.close()
                break
            print("[Server] CMD client from", addr)
            self._cmd_conns.append(conn)
            threading.Thread(target=self._handle_cmd, args=(conn,), daemon=True).start()

    def _handle_cmd(self, conn: socket.socket):
        # Xử lý kết nối CMD
        try:
            auth = recv_json(conn)
            if not auth or auth.get("password") != self.password:
                send_json(conn, {"ok": False})
                conn.close()
                return
            # Gửi độ phân giải cho màng hình
            w, h = pyautogui.size   ()
            send_json(conn, {"ok": True, "w": w, "h": h})

            while not self._stop.is_set():
                cmd = recv_json(conn)
                if not cmd:
                    break
                print("[Server] CMD:", cmd)
                self._execute_cmd(cmd)
        except Exception as e:
            if not self._stop.is_set():
                print("[Server] CMD error:", e)
        finally:
            try:
                self._cmd_conns.remove(conn)
            except:
                pass
            conn.close()

    # ===================== VID =====================
    def _serve_vid(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port_vid))
        s.listen(5)
        self.vid_socket = s
        print("[Server] Video socket listening...")

        while not self._stop.is_set():
            try:
                conn, addr = s.accept()
            except OSError:
                break
            if self._stop.is_set():
                conn.close()
                break
            print("[Server] VID client from", addr)
            threading.Thread(target=self._handle_vid, args=(conn,), daemon=True).start()

    def _handle_vid(self, conn: socket.socket):
        # Gửi hình ảnh màng hình liên tục cho clent
        try:
            while not self._stop.is_set():
                frame = screenshot_bytes()
                img = Image.open(io.BytesIO(frame))

                # Vẽ con trỏ
                #mx, my = pyautogui.position()
                #draw = ImageDraw.Draw(img)
                #cursor_size = 12
                #draw.polygon(
                    #[(mx, my), (mx + cursor_size, my + cursor_size//2), (mx, my + cursor_size)],
                    #fill="white", outline="black")
            
                # Nén ảnh JPEG
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=50)
                send_with_len(conn, buf.getvalue())
                time.sleep(0.05)
        except Exception as e:
            if not self._stop.is_set():
                print("[Server] VID error:", e)
        finally:
            conn.close()

    # ===================== EXEC CMD =====================
    def _execute_cmd(self, cmd: dict):
        # Thực thi lệnh CMD từ client
        try:
            t = cmd["type"]
            if t == "mouse_move_norm":
                move_mouse_norm(cmd["x"], cmd["y"])
            elif t == "mouse_down":
                mouse_down(cmd.get("button", "left"))
            elif t == "mouse_up":
                mouse_up(cmd.get("button", "left"))
            elif t == "scroll":
                scroll(cmd.get("amount", 0))
            elif t == "key":
                press(cmd["key"])
            elif t == "key_down":
                key_down(cmd["key"])
            elif t == "key_up":
                key_up(cmd["key"])
            elif t == "type_text":
                text = cmd.get("text", "")
                if text and all(ord(c) >= 32 for c in text):
                    type_text(text)
            elif t == "click_norm":
                move_click_norm(
                    cmd["x"], cmd["y"],
                    cmd.get("button", "left"),
                    cmd.get("clicks", 1)
                )
            elif t == "click":
                click(cmd.get("button", "left"), cmd.get("clicks", 1))
        except Exception as e:
            print("[Server] Exec error:", e)
