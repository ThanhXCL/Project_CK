import socket, threading

from control.control_server import normalize_key
from .common import recv_with_len, send_json, recv_json
from pynput import mouse, keyboard

class RemoteClient:
    def __init__(self, host='0.0.0.0', port_cmd=8888, port_vid=8889, password='123456', frame_callback=None, server_stop_callback=None):
        self.host = host
        self.port_cmd = port_cmd
        self.port_vid = port_vid
        self.password = password
        self.frame_callback = frame_callback
        self.server_stop_callback = server_stop_callback
        self.cmd = None
        self.vid = None
        self._stop = threading.Event()

    # ===================== Vòng client =====================
    def connect(self):
        # Kết nối server
        self.cmd = socket.create_connection((self.host, self.port_cmd), timeout=5)
        self.cmd.settimeout(None)
        send_json(self.cmd, {"type": "auth", "password": self.password})
        auth = recv_json(self.cmd)
        if not auth.get("ok"):
            raise RuntimeError("Auth failed")
        self.remote_w = auth.get("w")
        self.remote_h = auth.get("h")
        threading.Thread(target=self._recv_cmd, daemon=True).start()

        # Kết nối video socket
        try:
            self.vid = socket.create_connection((self.host, self.port_vid), timeout=5)
            self.vid.settimeout(None)  
            threading.Thread(target=self._recv_video, daemon=True).start()
        except Exception as e:
            print("[Client] Could not connect video:", e)
            self.vid = None

    def close(self):
        # Đóng kết nối
        for s in (self.cmd, self.vid):
            if s:
                try: s.shutdown(socket.SHUT_RDWR)
                except: pass
                try: s.close()
                except: pass
        self.cmd = None
        self.vid = None

    # ===================== Nhận dữ liệu từ server =====================
    def _recv_cmd(self):
        try:
            while not self._stop.is_set() and self.cmd:
                msg = recv_json(self.cmd)
                if not msg:
                    break
                if msg.get("type") == "server_stop":
                    print("[Client] Server đã ngắt kết nối.")
                    if self.server_stop_callback:
                        self.server_stop_callback()
                    self.close()
                    break
        except Exception as e:
            if not self._stop.is_set():
                print("[Client] CMD nghe loi", e)
        finally:
            self.close()

    def _recv_video(self):
        # Nhận dữ liệu video từ server
        try:
            while not self._stop.is_set() and self.vid:
                data = recv_with_len(self.vid)
                if not data:
                    break
                if self.frame_callback:
                    try:
                        self.frame_callback.emit(data)
                    except AttributeError:
                        # Nếu chỉ là function bình thường
                        self.frame_callback(data)
        except Exception as e:
            print('[Client] Video error:', e)

    # ===================== Gửi dữ liệu đến server =====================
    def _send(self, data):
        if not self.cmd:
            print("[Client] Not connected")
            return
        try:
            send_json(self.cmd, data)
        except (ConnectionResetError, BrokenPipeError):
            print("[Client] Connection lost, cannot send:", data)
            self.cmd = None

    # ===== API public cho UI gọi =====
    def mouse_move_norm(self, nx, ny):
        self._send({"type": "mouse_move_norm", "x": nx, "y": ny})

    def mouse_down(self, button="left"):
        self._send({"type": "mouse_down", "button": button})

    def mouse_up(self, button="left"):
        self._send({"type": "mouse_up", "button": button})

    def mouse_click(self, nx, ny, button="left", clicks=1):
        """Click tại vị trí chuẩn hóa."""
        self._send({
            "type": "mouse_click",
            "x": nx, "y": ny,
            "button": button,
            "clicks": clicks
        })

    def scroll(self, dy):
        self._send({"type": "scroll", "amount": dy})

    def key_down(self, key):
        self._send({"type": "key_down", "key": key})

    def key_up(self, key):
        self._send({"type": "key_up", "key": key})

    def type_text(self, text):
        self._send({"type": "type_text", "text": text})

    
    # ===================== Bàn phím =====================
    def _listen_keyboard(self):
        pressed_specials = set()

        def _normalize_key(k):
            if hasattr(k, "char") and k.char:
                if ord(k.char) >= 32:
                    return k.char
                return None
            return normalize_key(str(k))

        def on_press(key):
            norm = _normalize_key(key)
            if not norm:
                return
            specials_once = {"enter", "backspace", "delete", "tab", "esc"}
            
            # Nếu là chữ/số bình thường
            if len(norm) == 1 and norm.isprintable():
                if not pressed_specials:
                    self._send({"type": "type_text", "text": norm})
                else:
                    self._send({"type": "key_down", "key": norm})
            else:
                if norm in specials_once:
                    self._send({"type": "key", "key": norm})
                else:
                    if norm not in pressed_specials:
                        pressed_specials.add(norm)
                        self._send({"type": "key_down", "key": norm})

        def on_release(key):
            norm = _normalize_key(key)
            if not norm:
                return

            if len(norm) == 1 and norm.isprintable():
                if pressed_specials:  # nếu đang trong tổ hợp
                    self._send({"type": "key_up", "key": norm})
            else:
                if norm in pressed_specials:
                    pressed_specials.remove(norm)
                    self._send({"type": "key_up", "key": norm})

        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()


    def _listen_mouse(self):
        def on_click(x, y, button, pressed):
            try:
                bth = "left" if button == mouse.Button.left else "right"
                if pressed:
                    self.mouse_down(bth)
                else:
                    self.mouse_up(bth)
            except Exception as e:
                print("[Client] Mouse listener error:", e)

        def on_scroll(x, y, dx, dy):
            self.scroll(dy)

        def on_move(x, y):
            nx, ny = x / self.remote_w, y / self.remote_h
            self.mouse_move_norm(nx, ny)

        with mouse.Listener(
            on_click=on_click,
            on_scroll=on_scroll,
            on_move=on_move
        ) as listener:
            listener.join()
