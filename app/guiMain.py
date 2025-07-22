#!/usr/bin/env python
from config import *
from serial_utils import find_colorimeter_port
import threading, time, subprocess, sys, json
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QDialog
from PySide6.QtCore    import QTimer, Qt
#import pyqtgraph as pg
from serialReader import SerialReader
#import Matrix

class MainWindow(QWidget):
    COLOR_NAMES=["115 82 68", "194 150 130", "98 122 157", "87 108 67", "133 128 177", "103 189 170", "214 126 44", "80 91 166", "193, 90, 99", "94 60 108", "157 188 64", "224 163 46", "56 61 150", "70 148 73", "175 54 60", "231 199 31", "187 86 149", "8 133 161", "243 243 242", "200 200 200", "160 160 160", "122 122 121", "85 85 85", "52 52 52"]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Colorimeter Interface")
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(screen.width()/5,screen.height()/5,400,200)
        self.overlay=None
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.loading_dots = 0

        # Widgets
        self.status_label = QLabel("Idle")
        self.start_btn    = QPushButton("Start Reading")
        self.calibrateBase_btn = QPushButton("Calibrate Spectrometer Baseline")
        self.calibrateMonitor_btn = QPushButton("Calibrate Monitor")
        self.createProfile_btn = QPushButton("Generate ICC Profile")

        self.start_btn.clicked.connect(self.on_start_clicked)
        self.calibrateBase_btn.clicked.connect(self.on_calibrateBase_clicked)
        self.calibrateBase_btn.setEnabled(False)
        self.calibrateMonitor_btn.clicked.connect(self.on_calibrateMonitor_clicked)
        self.calibrateMonitor_btn.setEnabled(False)
        self.createProfile_btn.clicked.connect(self.on_createProfile_clicked)

        # self.plot_widget = pg.PlotWidget()
        # self.curve       = self.plot_widget.plot()

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.status_label)
        layout.addWidget(self.start_btn)
        # layout.addWidget(self.plot_widget)
        layout.addWidget(self.calibrateMonitor_btn)
        layout.addWidget(self.calibrateBase_btn)
        layout.addWidget(self.createProfile_btn)

        # Plot refresh timer
        # self.plot_timer = QTimer(self)
        # self.plot_timer.timeout.connect(self.update_plot)
        # self.plot_timer.start(100)

        # Placeholders
        self.reader = None

        self.calibrating = False
        self.calibration_index = 0
        self.calibration_data = []

        self.monitor_calibrating = False
        self.monitor_calibration_index=0
        self.monitor_calibration_data=[]
        self.COLOR_NAMES = ["115 82 68", "194 150 130", "98 122 157", "87 108 67", "133 128 177", "103 189 170", "214 126 44", "80 91 166", "193, 90, 99", "94 60 108", "157 188 64", "224 163 46", "56 61 150", "70 148 73", "175 54 60", "231 199 31", "187 86 149", "8 133 161", "255 255 255", "243 243 242", "200 200 200", "160 160 160", "122 122 121", "85 85 85", "52 52 52", "0 0 0"]
        self.PATCH_HEX = ["#735244", "#c29682", "#627a9d", "#576c43", "#8580b1", "#67bdaa", "#d67e2c", "#505ba6", "#c15a63", "#5e3c6c", "#9dbc40", "#e0a32e", "#383d96", "#469449", "#af262c", "#e7c71f", "#bb5695", "#0885a1", "#ffffff","#f3f3f3", "#c8c8c8", "#a0a0a0", "#7a7a7a", "#555555", "#343434", "#000000"]
        
        # Ensure we close the JSON file on exit
        QApplication.instance().aboutToQuit.connect(self.cleanup)

    def on_start_clicked(self):
        self.start_btn.setEnabled(False)
        self.status_label.setText("Waiting 2 s before start…")
        QTimer.singleShot(2000, self.start_reading)

    def start_reading(self):
        try:
            port = find_colorimeter_port()
            if not port:
                self.status_label.setText("❌ Could not find colorimeter (ESP32).")
                self.start_btn.setEnabled(True)
                return

            self.reader = SerialReader(
                port=port,
                baud=115200,
                timeout=1,
                output_file=COLOR_DATA)
            self.reader.start()
            self.status_label.setText("Reading data…")
            self.calibrateBase_btn.setEnabled(True)
            self.calibrateMonitor_btn.setEnabled(True)
        except Exception as e:
            self.status_label.setText(f"Serial error: {e}")

    def on_calibrateMonitor_clicked(self):
        if not self.monitor_calibrating:
            #begin calibration
            self.monitor_calibrating = True
            self.monitor_calibration_index = 0
            self.monitor_calibration_data = []
            self.calibrateBase_btn.setEnabled(False)
            self.calibrateMonitor_btn.setText("Capture")
            self.calibrateMonitor_btn.setEnabled(True)
            self.status_label.setText( f"Cal: {self.COLOR_NAMES[0]} (1/26) - press “Capture”")
            self._show_monitor_patch(0)
        else:
            # → schedule a delayed capture (8 readings @50 ms → ~400 ms)
            self.calibrateMonitor_btn.setEnabled(False)
            self.status_label.setText("Capturing monitor patch…")
            QTimer.singleShot(450, self._finish_monitor_capture)

    def _show_monitor_patch(self, idx: int):
        """Display full-screen color patch idx."""
        if self.overlay:
            self.overlay.close()

        hexcol=self.PATCH_HEX[idx]
        self.overlay=ColorOverlay(hexcol)
    
    def _finish_monitor_capture(self):
        if self.overlay:
            self.overlay.close()
            self.overlay = None

        # if we don’t yet have 8 samples, retry shortly
        if not self.reader or len(self.reader.data) < 8:
            return QTimer.singleShot(100, self._finish_monitor_capture)

        # grab the last 8 readings
        cycle = self.reader.data[-8:].copy()

        # record and advance
        self.monitor_calibration_data.append(cycle)
        self.monitor_calibration_index += 1

        # close this patch
        if self.overlay:
            self.overlay.close()
            self.overlay = None

        if self.monitor_calibration_index < len(self.COLOR_NAMES):
            idx = self.monitor_calibration_index
            self._show_monitor_patch(idx)
            self.overlay=ColorOverlay(self.PATCH_HEX[idx])
            self.status_label.setText(
                f"Monitor Cal: {self.COLOR_NAMES[idx]} ({idx+1}/26) – press “Capture”"
            )
            self.calibrateMonitor_btn.setEnabled(True)
        else:
            self.finish_monitor_calibration()

    def finish_monitor_calibration(self):
        """Save and reset after monitor calibration"""
        with open(MONITOR_RAW_JSON, "w") as f:
            json.dump(self.monitor_calibration_data, f, indent=2)

        if self.overlay:
            self.overlay.close()
            self.overlay= None
        self.monitor_calibrating=False
        self.calibrateMonitor_btn.setText("Calibrate Monitor")
        self.calibrateBase_btn.setEnabled(True)
        self.calibrateMonitor_btn.setEnabled(True)
        self.status_label.setText("Monitor Calibration Complete ✔️")

    def on_calibrateBase_clicked(self):
        if not self.calibrating:
            #begin calibration
            self.calibrating = True
            self.calibration_index = 0
            self.calibration_data = []
            self.start_btn.setEnabled(False)
            self.status_label.setText( f"Cal: {self.COLOR_NAMES[0]} (1/26) – press “Capture”")
            self.status_label.setText("Capture")

            #ensure the reading is running
            if not self.reader:
                self.start_reading()
        else:
            self.calibrateBase_btn.setEnabled(False)
            self.status_label.setText("Capturing…")
            QTimer.singleShot(450, self._finish_buffer_cycle)

    def _finish_buffer_cycle(self):
        if not self.reader or len(self.reader.data)<8:
            QTimer.singleShot(100, self._finish_buffer_cycle)
            return
        cycle = self.reader.data[-8:]
        self.calibration_data.append(cycle)
        self.calibration_index +=1
        if self.calibration_index<len(self.COLOR_NAMES):
            name=self.COLOR_NAMES[self.calibration_index]
            self.status_label.setText(f"Cal: {name} ({self.calibration_index+1}/{len(self.COLOR_NAMES)}) – press “Capture”")
            self.calibrateBase_btn.setEnabled(True)
        else:
            self.finish_calibration()

    def _capture_cycle(self):
        """Runs in background; reads one full cycle then posts result back on GUI thread."""
        try:
            cycle = self.reader.read_cycle()
        except Exception as e:
            # forward errors to GUI
            QTimer.singleShot(0, lambda: self.status_label.setText(f"Error: {e}"))
            QTimer.singleShot(0, lambda: self.calibrateBase_btn.setEnabled(True))
            return
        QTimer.singleShot(0, lambda: self._finish_calibration_cycle(cycle))

    # This callback runs on the main thread:
    def _finish_calibration_cycle(self, cycle):
        # append and bump the index
        self.calibration_data.append(cycle)
        self.calibration_index += 1

        if self.calibration_index < len(self.COLOR_NAMES):
            name = self.COLOR_NAMES[self.calibration_index]
            self.status_label.setText(f"Cal: {name} ({self.calibration_index+1}/26) – press “Capture”")
            self.calibrateBase_btn.setEnabled(True)
        else:
            self.finish_calibration()


    def finish_calibration(self):
        #dump calibration into baseline.json
        with open(BASELINE_RAW_JSON, "w") as f:
            json.dump(self.calibration_data, f, indent=2)
        self.status_label.setText("Calibration Complete ✔️")
        self.calibrateBase_btn.setText("calibrateBase")
        self.calibrateBase_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.calibrating = False

    # def update_plot(self):
    #     if self.reader and self.reader.data:
    #         self.curve.setData(self.reader.data)

    def cleanup(self):
        # Called when the app is closing
        if self.reader:
            self.reader.close()

    def on_createProfile_clicked(self):
        """Generate the ICC profile and color matrix."""
        if file_exists(MONITOR_RAW_JSON) and file_exists(BASELINE_RAW_JSON):
            self.loading_dots = 0
            self.status_label.setText("Generating ICC profile")
            self.createProfile_btn.setEnabled(False)
            # Run the Matrix script and store the process
            self.matrix_process = subprocess.Popen(["python", MATRIX_PATH])
            
            # Create a timer to check the process status
            self.check_timer = QTimer(self)  # Add parent to prevent garbage collection
            self.check_timer.timeout.connect(self.check_matrix_process)
            self.check_timer.start(500)  # Check every 500ms for smoother animation
        else:
            self.status_label.setText("❌ Missing calibration data files. Please calibrate first.")

    def check_matrix_process(self):
        """Check if the Matrix process is still running"""
        if hasattr(self, 'matrix_process'):
            # Update loading animation
            self.loading_dots = (self.loading_dots + 1) % 4
            dots = "." * self.loading_dots
            self.status_label.setText(f"Generating ICC profile{dots}")
            
            return_code = self.matrix_process.poll()
            if return_code is not None:  # Process has finished
                self.check_timer.stop()
                if return_code == 0:
                    self.status_label.setText("ICC profile generated successfully ✔️")
                else:
                    self.status_label.setText("❌ Error generating ICC profile")
                self.createProfile_btn.setEnabled(True)
                del self.matrix_process
        
class ColorOverlay(QDialog):
    def __init__(self, color_hex: str):
        super().__init__(None, Qt.FramelessWindowHint)
        self.setStyleSheet(f"background-color: {color_hex};")
        self.showFullScreen()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    w   = MainWindow()
    w.show()
    sys.exit(app.exec())
