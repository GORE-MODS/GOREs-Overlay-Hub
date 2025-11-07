import psutil, time, json, os, sys, threading
from tkinter import Tk, Label
from ctypes import windll
import win32gui, win32con
from ping3 import ping
import keyboard
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

_appdata = os.getenv("APPDATA") or os.path.expanduser("~")
CONFIG_PATH = os.path.join(_appdata, "OverlayHub_Config.json")

# ──────────────────────────────────────────────
# Safe temperature fetch
def get_temps_safe():
    cpu_temp = gpu_temp = "N/A"
    try:
        temps = getattr(psutil, "sensors_temperatures", lambda: {})()
        if temps:
            if "coretemp" in temps and temps["coretemp"]:
                cpu_temp = f"{temps['coretemp'][0].current:.0f}°C"
            elif "cpu_thermal" in temps and temps["cpu_thermal"]:
                cpu_temp = f"{temps['cpu_thermal'][0].current:.0f}°C"
            if "amdgpu" in temps and temps["amdgpu"]:
                gpu_temp = f"{temps['amdgpu'][0].current:.0f}°C"
            elif "gpu" in temps and temps["gpu"]:
                gpu_temp = f"{temps['gpu'][0].current:.0f}°C"
    except Exception:
        pass
    return cpu_temp, gpu_temp

# ──────────────────────────────────────────────
def get_ping_ms(host="8.8.8.8"):
    try:
        result = ping(host, timeout=1)
        if result is None:
            return "N/A"
        return f"{int(result * 1000)} ms"
    except Exception:
        return "N/A"

# ──────────────────────────────────────────────
def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except:
            return {"x": 20, "y": 40}
    return {"x": 20, "y": 40}

def save_config(x, y):
    with open(CONFIG_PATH, "w") as f:
        json.dump({"x": x, "y": y}, f)

# ──────────────────────────────────────────────
# Tkinter overlay setup
root = Tk()
root.attributes("-topmost", True)
root.attributes("-alpha", 0.9)
root.overrideredirect(True)

lbl = Label(
    root,
    justify="left",
    font=("Consolas", 11),
    fg="lime",
    bg="#101010",
    padx=10,
    pady=6,
)
lbl.pack(fill="both", expand=True)

config = load_config()
root.geometry(f"250x120+{config['x']}+{config['y']}")

# Click-through
hwnd = windll.user32.GetParent(root.winfo_id())
ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_LAYERED)

# ──────────────────────────────────────────────
# Drag to move
drag_data = {"x": 0, "y": 0}
def on_press(event):
    drag_data["x"] = event.x
    drag_data["y"] = event.y
def on_drag(event):
    x = root.winfo_x() + (event.x - drag_data["x"])
    y = root.winfo_y() + (event.y - drag_data["y"])
    root.geometry(f"+{x}+{y}")
def on_release(event):
    save_config(root.winfo_x(), root.winfo_y())

root.bind("<Button-1>", on_press)
root.bind("<B1-Motion>", on_drag)
root.bind("<ButtonRelease-1>", on_release)

# ──────────────────────────────────────────────
visible = True

def toggle_overlay():
    global visible
    visible = not visible
    if visible:
        root.deiconify()
    else:
        root.withdraw()

keyboard.add_hotkey("F2", toggle_overlay)

# ──────────────────────────────────────────────
# System tray
def create_image():
    # simple green circle icon
    image = Image.new("RGB", (64, 64), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 56, 56), fill=(0, 255, 0))
    return image

def on_exit(icon, item):
    icon.stop()
    root.destroy()
    os._exit(0)

def on_reload(icon, item):
    os.execl(sys.executable, sys.executable, *sys.argv)

def on_toggle(icon, item):
    toggle_overlay()

menu = (
    item("Toggle Overlay (F2)", on_toggle),
    item("Reload", on_reload),
    item("Exit", on_exit),
)
icon = pystray.Icon("OverlayHub", create_image(), "OverlayHub", menu)

def run_tray():
    icon.run()

threading.Thread(target=run_tray, daemon=True).start()

# ──────────────────────────────────────────────
def update():
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    cpu_temp, gpu_temp = get_temps_safe()
    ping_time = get_ping_ms()

    lbl.config(
        text=(
            f"⚡ CPU: {cpu_usage:.1f}%  ({cpu_temp})\n"
            f"🎮 GPU: {gpu_temp}\n"
            f"💾 RAM: {ram_usage:.1f}%\n"
            f"🌐 Ping: {ping_time}\n"
            f"[F2 to toggle]"
        )
    )
    root.after(1000, update)

update()
root.mainloop()
