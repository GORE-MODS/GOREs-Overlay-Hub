import psutil, time, json, os, sys, keyboard
from tkinter import Tk, Label, Canvas
from ctypes import windll
from ping3 import ping

# ─── Music Metadata ───────────────────────────────────────────
from pycaw.pycaw import AudioUtilities
from comtypes import CoInitialize

# ─── System Tray ──────────────────────────────────────────────
import pystray
from PIL import Image, ImageDraw

# ─── Paths ────────────────────────────────────────────────────
_appdata = os.getenv("APPDATA") or os.path.expanduser("~")
CONFIG_PATH = os.path.join(_appdata, "OverlayHub_Config.json")

# =====================================================================
# SAFE TEMP READING
# =====================================================================
def get_temps_safe():
    cpu_temp = gpu_temp = "N/A"
    try:
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if "coretemp" in temps:
                cpu_temp = f"{temps['coretemp'][0].current:.0f}°C"
            if "cpu_thermal" in temps:
                cpu_temp = f"{temps['cpu_thermal'][0].current:.0f}°C"
            if "amdgpu" in temps:
                gpu_temp = f"{temps['amdgpu'][0].current:.0f}°C"
            if "gpu" in temps:
                gpu_temp = f"{temps['gpu'][0].current:.0f}°C"
    except:
        pass
    return cpu_temp, gpu_temp


def get_ping_ms(host="8.8.8.8"):
    try:
        r = ping(host, timeout=1)
        return f"{int(r * 1000)} ms" if r else "N/A"
    except:
        return "N/A"


# =====================================================================
# MUSIC NOW PLAYING
# =====================================================================
def get_song():
    try:
        CoInitialize()
        sessions = AudioUtilities.GetAllSessions()
        for s in sessions:
            if s.SimpleAudioVolume.GetMute() is False:
                disp = s.DisplayName
                if disp and "System Sounds" not in disp:
                    return disp
    except:
        pass
    return "None"


# =====================================================================
# SAVE / LOAD WINDOW POSITION
# =====================================================================
def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except:
            pass
    return {"x": 20, "y": 40}


def save_config(x, y):
    with open(CONFIG_PATH, "w") as f:
        json.dump({"x": x, "y": y}, f)


# =====================================================================
# TK OVERLAY SETTINGS
# =====================================================================
root = Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-alpha", 0.90)

# Rounded Corner Background Canvas
canvas = Canvas(root, width=260, height=150, bg="#000000", highlightthickness=0)
canvas.pack(fill="both", expand=True)

# Draw rounded rectangle
def draw_round():
    canvas.delete("all")
    r = 20
    w = 260
    h = 150
    canvas.create_rectangle(
        r, 0, w - r, h, fill="#0a0a0a", outline="#0a0a0a"
    )
    canvas.create_oval(0, 0, r * 2, r * 2, fill="#0a0a0a", outline="")
    canvas.create_oval(w - r * 2, 0, w, r * 2, fill="#0a0a0a", outline="")
    canvas.create_oval(0, h - r * 2, r * 2, h, fill="#0a0a0a", outline="")
    canvas.create_oval(w - r * 2, h - r * 2, w, h, fill="#0a0a0a", outline="")

draw_round()

lbl = Label(
    root,
    bg="#0a0a0a",
    fg="lime",
    font=("Consolas", 11),
    justify="left"
)
lbl.place(x=15, y=15)

# Restore position
config = load_config()
root.geometry(f"260x150+{config['x']}+{config['y']}")

# =====================================================================
# DRAGGING
# =====================================================================
drag = {"x": 0, "y": 0}

def click(e):
    drag["x"] = e.x
    drag["y"] = e.y

def drag_move(e):
    x = root.winfo_x() + (e.x - drag["x"])
    y = root.winfo_y() + (e.y - drag["y"])
    root.geometry(f"+{x}+{y}")

def drag_stop(e):
    save_config(root.winfo_x(), root.winfo_y())

root.bind("<Button-1>", click)
root.bind("<B1-Motion>", drag_move)
root.bind("<ButtonRelease-1>", drag_stop)


# =====================================================================
# TOGGLE VISIBILITY (F2)
# =====================================================================
visible = True

def toggle():
    global visible
    visible = not visible
    root.withdraw() if not visible else root.deiconify()

keyboard.add_hotkey("F2", toggle)


# =====================================================================
# TRAY ICON
# =====================================================================
def icon_image():
    img = Image.new("RGB", (64, 64), "black")
    draw = ImageDraw.Draw(img)
    draw.rectangle((10, 25, 54, 40), fill="lime")
    draw.text((18, 10), "HUD", fill="white")
    return img

def tray_exit(icon):
    icon.stop()
    root.destroy()
    sys.exit()

def tray_reload(icon):
    os.execv(sys.executable, ["python"] + sys.argv)

def tray_toggle(icon):
    toggle()

tray = pystray.Icon(
    "OverlayHub",
    icon_image(),
    "Overlay Hub",
    menu=pystray.Menu(
        pystray.MenuItem("Toggle Overlay", tray_toggle),
        pystray.MenuItem("Reload", tray_reload),
        pystray.MenuItem("Exit", tray_exit),
    )
)
tray.run_detached()


# =====================================================================
# UPDATE LOOP
# =====================================================================
def update():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    cpu_temp, gpu_temp = get_temps_safe()
    ping = get_ping_ms()
    song = get_song()

    lbl.config(
        text=(
            f"⚡ CPU: {cpu:.1f}% ({cpu_temp})\n"
            f"🎮 GPU: {gpu_temp}\n"
            f"💾 RAM: {ram:.1f}%\n"
            f"🌐 Ping: {ping}\n"
            f"🎵 Music: {song}\n"
            f"[F2 Hide/Show]"
        )
    )

    root.after(1000, update)

update()
root.mainloop()
