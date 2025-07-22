import serial.tools.list_ports

def list_serial_ports():
    """Return a list of (device, description) tuples."""
    return [(port.device, port.description) for port in serial.tools.list_ports.comports()]

def find_colorimeter_port():
    """Return the device path of the ESP32 if found."""
    for port in serial.tools.list_ports.comports():
        desc = port.description.lower()
        if "esp32" in desc or "usb serial" in desc or "silicon labs" in desc or "Silicon Labs" in desc or "CP210x" in desc:
            return port.device
    return None
