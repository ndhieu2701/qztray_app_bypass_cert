# App: Public Key Tray App (Optimized)
# Description: App cho phép chọn file chứa public key (.txt) và private key (.key), lưu vào config, cung cấp API /public-key và /sign, chạy Flask + icon tray

import tkinter as tk
from tkinter import filedialog, messagebox
from ttkbootstrap import Style
from ttkbootstrap.constants import *
import ttkbootstrap as ttk
import threading
import os
import json
from flask import Flask, jsonify, request
import sys
import winreg
import atexit
from PIL import Image
import pystray

import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
from flask_cors import CORS

# --- Constants ---
APP_NAME = "PublicKeyTrayApp"
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
PORT = 5000


# --- Icon Path ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = BASE_DIR
    return os.path.join(base_path, relative_path)


ICON_PATH = resource_path("ReadFile.ico")
TRAY_ICON_PATH = resource_path("ReadFile.ico")  # Use ICO for better performance

# --- Flask App ---
app = Flask(__name__)
CORS(app)


def read_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


@app.route("/public-key", methods=["GET"])
def get_public_key():
    config = read_config()
    pem_path = config.get("pem_path")
    if pem_path and os.path.exists(pem_path):
        try:
            with open(pem_path, "r") as f:
                content = f.read()
                return jsonify(
                    {
                        "status": "OK",
                        "message": "Lấy public key thành công",
                        "publicKey": content,
                    }
                )
        except Exception as e:
            return (
                jsonify({"status": "ERR", "message": f"Không thể đọc file: {e}"}),
                500,
            )
    return (
        jsonify(
            {"status": "ERR", "message": "Public key không tồn tại hoặc chưa được chọn"}
        ),
        404,
    )


@app.route("/sign", methods=["POST"])
def sign_data():
    try:
        data = request.json.get("data")
        if not data:
            return jsonify({"status": "ERR", "message": "Thiếu dữ liệu cần ký"}), 400

        config = read_config()
        private_key_path = config.get("private_key")
        if not private_key_path or not os.path.exists(private_key_path):
            return (
                jsonify({"status": "ERR", "message": "Không tìm thấy private key"}),
                500,
            )

        with open(private_key_path, "rb") as f:
            private_key = load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )

        signature = private_key.sign(
            data.encode("utf-8"), padding.PKCS1v15(), hashes.SHA1()
        )
        signature_b64 = base64.b64encode(signature).decode("utf-8")
        return jsonify({"status": "OK", "signature": signature_b64})
    except Exception as e:
        return jsonify({"status": "ERR", "message": str(e)}), 500


def run_flask():
    app.run(port=PORT, debug=False, use_reloader=False)


# --- Registry ---
def set_startup(name, exe_path):
    key = winreg.HKEY_CURRENT_USER
    subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
        winreg.SetValueEx(reg_key, name, 0, winreg.REG_SZ, f'"{exe_path}"')


def remove_startup(name):
    key = winreg.HKEY_CURRENT_USER
    subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
            winreg.DeleteValue(reg_key, name)
    except FileNotFoundError:
        pass


def is_autostart_enabled(name):
    key = winreg.HKEY_CURRENT_USER
    subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(key, subkey, 0, winreg.KEY_READ) as reg_key:
            value, _ = winreg.QueryValueEx(reg_key, name)
            return bool(value)
    except FileNotFoundError:
        return False


# --- Tray ---
def create_icon_image():
    try:
        return Image.open(TRAY_ICON_PATH)
    except Exception as e:
        print(f"\u26a0\ufe0f Không thể tải icon tray: {e}")
        return Image.new("RGB", (32, 32), "gray")


def setup_tray():
    def on_restore(icon, item):
        root.after(0, root.deiconify)
        icon.stop()

    def on_exit(icon, item):
        icon.stop()
        root.after(0, root.destroy)

    image = create_icon_image()
    menu = pystray.Menu(
        pystray.MenuItem("Hiện cửa sổ", on_restore), pystray.MenuItem("Thoát", on_exit)
    )
    icon = pystray.Icon(APP_NAME, image, "PublicKey App", menu)
    threading.Thread(target=icon.run, daemon=True).start()


# --- Main Window ---
def build_main_gui():
    root = tk.Tk()
    root.title("Public Key Tray App")
    root.geometry("520x240")
    root.resizable(False, False)
    try:
        root.iconbitmap(default=ICON_PATH)
    except Exception as e:
        print(f"\u26a0\ufe0f Không thể đặt icon: {e}")

    style = Style("flatly")
    style.master = root

    config = read_config()
    pem_path_var = tk.StringVar(value=config.get("pem_path", ""))
    key_path_var = tk.StringVar(value=config.get("private_key", ""))
    autostart_var = tk.BooleanVar(value=is_autostart_enabled(APP_NAME))

    def browse_pem():
        path = filedialog.askopenfilename(
            title="Chọn file public key (.txt)", filetypes=[("Text files", "*.txt")]
        )
        if path:
            pem_path_var.set(path)

    def browse_key():
        path = filedialog.askopenfilename(
            title="Chọn file private key (.key)",
            filetypes=[("Key files", "*.key"), ("All files", "*.*")],
        )
        if path:
            key_path_var.set(path)

    def on_save():
        pem = pem_path_var.get()
        key = key_path_var.get()
        if not (pem and os.path.exists(pem) and key and os.path.exists(key)):
            messagebox.showerror(
                "Lỗi", "Vui lòng chọn đủ file public key và private key"
            )
            return

        try:
            with open(pem, "r") as f:
                if "-----BEGIN CERTIFICATE-----" not in f.read():
                    raise ValueError("Public key không hợp lệ")
            with open(key, "rb") as f:
                load_pem_private_key(f.read(), password=None, backend=default_backend())
        except Exception as e:
            messagebox.showerror("Lỗi", f"File không hợp lệ: {e}")
            return

        save_config({"pem_path": pem, "private_key": key})
        exe_path = sys.executable
        if autostart_var.get():
            set_startup(APP_NAME, exe_path)
        else:
            remove_startup(APP_NAME)
        messagebox.showinfo("Đã lưu", "Đã lưu cấu hình thành công")
        root.withdraw()
        setup_tray()

    def on_minimize():
        root.withdraw()
        setup_tray()

    root.protocol("WM_DELETE_WINDOW", on_minimize)

    form = ttk.Frame(root)
    form.pack(padx=10, pady=10, fill="x")

    ttk.Label(form, text="Public key (.txt):").grid(row=0, column=0, sticky="w")
    ttk.Entry(form, textvariable=pem_path_var, width=50).grid(row=0, column=1, padx=5)
    ttk.Button(form, text="Chọn", command=browse_pem).grid(row=0, column=2)

    ttk.Label(form, text="Private key (.key):").grid(
        row=1, column=0, sticky="w", pady=(10, 0)
    )
    ttk.Entry(form, textvariable=key_path_var, width=50).grid(
        row=1, column=1, padx=5, pady=(10, 0)
    )
    ttk.Button(form, text="Chọn", command=browse_key).grid(
        row=1, column=2, pady=(10, 0)
    )

    ttk.Checkbutton(
        form,
        text="Khởi động cùng Windows",
        variable=autostart_var,
        bootstyle="info-round-toggle",
    ).grid(row=2, column=0, columnspan=3, pady=10, sticky="w")

    ttk.Button(form, text="Lưu cấu hình", command=on_save).grid(
        row=3, column=0, columnspan=3
    )

    return root


# --- Start ---
def start_app():
    global root
    root = build_main_gui()

    config = read_config()
    if (
        config.get("pem_path")
        and os.path.exists(config.get("pem_path"))
        and config.get("private_key")
        and os.path.exists(config.get("private_key"))
    ):
        root.after(300, lambda: [root.withdraw(), setup_tray()])
        root.after(
            1000, lambda: threading.Thread(target=run_flask, daemon=True).start()
        )
    else:
        threading.Thread(target=run_flask, daemon=True).start()

    root.mainloop()


if __name__ == "__main__":
    atexit.register(lambda: print("App thoát"))
    start_app()
