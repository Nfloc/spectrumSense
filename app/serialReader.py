import serial
import threading
import json
from PySide6.QtCore import QTimer

class SerialReader:
    def __init__(self, port: str, baud: int = 115200, timeout: float = 1.0, output_file: str = None):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.output_file = output_file
        self.serial = None
        self._thread = None
        self.data = []  # rolling buffer of floats

        # If we’re writing JSON, open and start the array
        if self.output_file:
            self._fh    = open(self.output_file, "w")
            self._fh.write("[\n")
            self._first = True

    def read_cycle(self):
        """
        Block until one full set of 8 channel readings has been read.
        Returns a list of 8 values in channel order [ch0, ch1, …, ch7].
        """
        buf = [None] * 8
        while True:
            raw_line = self.serial.readline().decode(errors="ignore").strip()
            if not raw_line:
                continue
            # Quickly skip anything that can't be a JSON object
            if not (raw_line.startswith("{") and raw_line.endswith("}")):
                continue
            # Now parse it
            try:
                obj = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            # Ensure it's a dict before using .get()
            if not isinstance(obj, dict):
                continue
            # Detect end-of-cycle marker
            if obj.get("cycle"):
                return buf
            # Fill the buffer
            ch = obj.get("ch")
            val = obj.get("val")
            if isinstance(ch, int) and 0 <= ch < 8:
                buf[ch] = val

    def start(self):
        """Open the port and launch the background read thread."""
        self.serial = serial.Serial(self.port, self.baud, timeout=self.timeout)
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self):
        """Continuously read lines, parse JSON or float, append to buffer."""
        while True:
            raw_line = self.serial.readline().decode(errors="ignore").strip()
            if not raw_line:
                continue

            # Try to parse JSON
            try:
                obj = json.loads(raw_line)
            except json.JSONDecodeError:
                # Not valid JSON at all → try plain float
                try:
                    val = float(raw_line)
                except ValueError:
                    # neither JSON nor float, skip
                    continue
                else:
                    # got a float, append and continue
                    self._append(val)
                    continue

            # If parsing JSON gave you something other than a dict, skip
            if not isinstance(obj, dict):
                continue

            # Look for a 'val' field
            if "val" in obj:
                try:
                    val = float(obj["val"])
                except (TypeError, ValueError):
                    continue
                self._append(val)

    def _append(self, val: float):
        """Common logic to buffer & truncate, and optionally write to file."""
        self.data.append(val)
        if len(self.data) > 200:
            self.data.pop(0)

        if self.output_file:
            if not self._first:
                self._fh.write(",\n")
            self._first = False
            self._fh.write(json.dumps({"val": val}))
            self._fh.flush()
    
    def close(self):
        """Call this on exit to finish the JSON array."""
        if self.output_file:
            self._fh.write("\n]\n")
            self._fh.close()
                