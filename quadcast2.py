#!/usr/bin/env python3
import sys
import threading
import time
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QComboBox, QSystemTrayIcon, QMenu, QSpacerItem, QSizePolicy
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
import usb.core
import usb.util
import os

# ---------------- USB CONFIG ----------------
VENDOR_ID = 0x03F0
PRODUCT_ID = 0x09AF
INTERFACE = 0

# ---------------- STATE ----------------
running = True
led_enabled = True
led_mode = "bottom"   # bottom | top | both
led_effect = "static" # static | blink | wave
brightness_raw = 24
wave_speed = 1.0
wave_phase = 0.0

# ---------------- USB FUNCTIONS ----------------
def usb_loop():
    global wave_phase
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if dev is None:
        print("QuadCast 2 not found.")
        return

    try:
        if dev.is_kernel_driver_active(INTERFACE):
            dev.detach_kernel_driver(INTERFACE)
    except usb.core.USBError:
        pass

    last_effect = None

    while running:
        try:
            usb.util.claim_interface(dev, INTERFACE)

            global led_effect, led_mode, brightness_raw, wave_speed, led_enabled

            if led_effect != last_effect:
                wave_phase = 0.0
                last_effect = led_effect

            lower = 0
            upper = 0
            if led_enabled:
                if led_mode == "bottom":
                    lower = brightness_raw
                    upper = 0
                elif led_mode == "top":
                    lower = 0
                    upper = brightness_raw
                elif led_mode == "both":
                    lower = brightness_raw
                    upper = brightness_raw

                t = time.time()
                if led_effect == "blink":
                    state = int(t*2)%2
                    lower *= state
                    upper *= state
                elif led_effect == "wave":
                    wave_phase += 0.05 * wave_speed
                    factor = (np.sin(wave_phase)+1)/2
                    lower = int(lower*factor)
                    upper = int(upper*factor)

            cmd = bytearray(64)
            cmd[0] = 0x81
            cmd[1] = lower
            cmd[4] = 0x81
            cmd[5] = upper
            dev.ctrl_transfer(0x21, 0x09, 0x0300, INTERFACE, cmd)

            hb = bytearray(64)
            hb[0] = 0x04
            hb[1] = max(lower, upper)
            hb[8] = 0x01
            dev.ctrl_transfer(0x21, 0x09, 0x0300, INTERFACE, hb)

            usb.util.release_interface(dev, INTERFACE)
            time.sleep(0.05)
        except usb.core.USBError:
            time.sleep(0.5)

# ---------------- GUI ----------------
class QuadCastApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QuadCast 2 Control")
        self.setFixedSize(500, 400)
        self.init_ui()

        # Start USB thread
        threading.Thread(target=usb_loop, daemon=True).start()

        # Create system tray
        self.tray = QSystemTrayIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons/mic.svg")))
        self.tray.setToolTip("QuadCast 2 Control")
        menu = QMenu()
        open_action = menu.addAction("Open")
        quit_action = menu.addAction("Quit")
        open_action.triggered.connect(self.show_window)
        quit_action.triggered.connect(self.quit_app)
        self.tray.setContextMenu(menu)
        self.tray.show()
        self.tray.activated.connect(lambda reason: self.show_window() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20,20,20,20)

        # Brightness
        main_layout.addWidget(QLabel("Brightness"))
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(0,100)
        self.brightness_slider.setValue(10)
        self.brightness_slider.valueChanged.connect(self.change_brightness)
        main_layout.addWidget(self.brightness_slider)

        # LED Mode
        main_layout.addWidget(QLabel("LED Mode"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["bottom","top","both"])
        self.mode_combo.currentTextChanged.connect(self.change_mode)
        main_layout.addWidget(self.mode_combo)

        # LED Effect
        main_layout.addWidget(QLabel("LED Effect"))
        self.effect_combo = QComboBox()
        self.effect_combo.addItems(["static","blink","wave"])
        self.effect_combo.currentTextChanged.connect(self.change_effect)
        main_layout.addWidget(self.effect_combo)

        # Wave speed
        main_layout.addWidget(QLabel("Wave Speed"))
        self.wave_slider = QSlider(Qt.Orientation.Horizontal)
        self.wave_slider.setRange(1,50)
        self.wave_slider.setValue(10)
        self.wave_slider.valueChanged.connect(self.change_wave)
        main_layout.addWidget(self.wave_slider)

        # LED ON/OFF
        self.toggle_btn = QPushButton("LED ON")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(True)
        self.toggle_btn.clicked.connect(self.toggle_led)
        main_layout.addWidget(self.toggle_btn)

        main_layout.addItem(QSpacerItem(10,10,QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding))

    # ---------------- CALLBACKS ----------------
    def change_brightness(self,value):
        global brightness_raw
        brightness_raw = int(value*242/100)

    def change_mode(self,value):
        global led_mode
        led_mode = value

    def change_effect(self,value):
        global led_effect
        led_effect = value

    def change_wave(self,value):
        global wave_speed
        wave_speed = value/10

    def toggle_led(self,checked):
        global led_enabled
        led_enabled = checked
        self.toggle_btn.setText("LED ON" if checked else "LED OFF")

    # ---------------- TRAY FUNCTIONS ----------------
    def show_window(self):
        self.show()
        self.activateWindow()
        self.raise_()

    def quit_app(self):
        global running
        running = False
        self.tray.hide()
        QApplication.quit()

    # Minimize to tray on close
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray.showMessage("QuadCast 2 Control","App minimized to tray","Information",2000)

# ---------------- MAIN ----------------
def main():
    app = QApplication(sys.argv)
    win = QuadCastApp()
    win.show()
    sys.exit(app.exec())

if __name__=="__main__":
    main()
