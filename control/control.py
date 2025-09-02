import pyautogui
from PIL import ImageGrab
import io

# Tắt failsafe để không bị thoát khi chạm góc màn hình
pyautogui.FAILSAFE = False


def handle_command(cmd: dict):
    action = cmd.get("action")

    if action == "mouse_click":
        x, y = cmd["x"], cmd["y"]
        pyautogui.click(x, y, button="left" if "left" in cmd["button"] else "right")

    elif action == "key_press":
        key = cmd["key"].replace("'", "")  # dọn string
        pyautogui.press(key)
        
def screen_size():
    w, h = pyautogui.size()
    return int(w), int(h)


def screenshot_bytes():
    """Chụp màn hình và trả về bytes (JPEG)."""
    img = ImageGrab.grab()
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=50)
    return buf.getvalue()


def move_mouse_abs(x, y, duration=0):
    """Di chuyển chuột tới tọa độ tuyệt đối (pixel trên máy server)."""
    pyautogui.moveTo(int(x), int(y), duration=duration)


def move_mouse_norm(nx, ny):
    w, h = screen_size()
    x = max(0, min(int(nx * w), w-1))
    y = max(0, min(int(ny * h), h-1))
    move_mouse_abs(x, y)


def click(button="left", clicks=1):
    """Click chuột."""
    pyautogui.click(button=button, clicks=clicks)


def mouse_down(button="left"):
    pyautogui.mouseDown(button=button)


def mouse_up(button="left"):
    pyautogui.mouseUp(button=button)


def scroll(dy):
    """Cuộn theo trục dọc (+ lên, - xuống)."""
    pyautogui.scroll(int(dy))


def press(key):
    """Nhấn 1 phím (nhấn và nhả)."""
    pyautogui.press(key)

def key_down(key):
    """Giữ phím."""
    pyautogui.keyDown(key)


def key_up(key):
    """Nhả phím."""
    pyautogui.keyUp(key)


def type_text(text):
    """Gõ 1 đoạn văn bản."""
    pyautogui.typewrite(text)


def move_click_norm(nx, ny, button="left", clicks=1):
    """Nhận tọa độ chuẩn hóa (0..1) -> đổi sang pixel và click."""
    w, h = screen_size()
    x = max(0, min(int(nx * w), w - 1))
    y = max(0, min(int(ny * h), h - 1))
    move_mouse_abs(x, y)
    click(button=button, clicks=clicks)
