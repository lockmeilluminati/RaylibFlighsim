import serial
import serial.tools.list_ports
import threading
import time

class VexConnection:
    def __init__(self, port="COM5", baudrate=115200):
        self.port_name = port
        self.baudrate = baudrate
        self.serial_port = None
        self.is_reading = False
        
        # ERROR FIX: Expanded dictionary to support up to 30 ports for Virtual Controllers
        self.state = {i: {"type": "Empty", "value": "N/A"} for i in range(1, 30)}

    def connect(self):
        available_ports = [p.device for p in serial.tools.list_ports.comports()]
        
        if not available_ports:
            print("[ERROR] No USB COM ports found. Plug in the Brain and turn it on.")
            return False
            
        if self.port_name not in available_ports:
            print(f"Auto-switching from {self.port_name} to {available_ports[0]}...")
            self.port_name = available_ports[0]

        try:
            self.serial_port = serial.Serial(self.port_name, self.baudrate, timeout=0.1)
            self.is_reading = True
            
            thread = threading.Thread(target=self._read_serial, daemon=True)
            thread.start()
            
            print(f"[SUCCESS] Link established on {self.port_name}")
            return True
            
        except serial.SerialException:
            print(f"[ERROR] Port {self.port_name} is locked by another program!")
            print(">>> FIX: Close the VEXcode app completely so Python can use the USB.")
            return False

    def _read_serial(self):
        while self.is_reading:
            if self.serial_port and self.serial_port.is_open:
                try:
                    line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self._parse_line(line)
                except Exception:
                    pass
            time.sleep(0.01)

    def _parse_line(self, line):
        if not line or ":" not in line:
            return
            
        port_entries = line.split(',')
        for entry in port_entries:
            parts = entry.split(':')
            if len(parts) >= 3:
                try:
                    p_id = int(parts[0])
                    # Safety check to ensure we don't crash if the Brain sends a massive port number
                    if p_id in self.state:
                        self.state[p_id]["type"] = parts[1]
                        self.state[p_id]["value"] = ":".join(parts[2:]) 
                except (ValueError, IndexError):
                    continue

    def disconnect(self):
        self.is_reading = False
        if self.serial_port:
            self.serial_port.close()
            print(f"[DISCONNECTED] Released {self.port_name}")

if __name__ == "__main__":
    link = VexConnection()
    if link.connect():
        print("Listening for Brain data... Press CTRL+C to stop.")
        try:
            while True:
                aim_data = link.state[7]['value']
                trigger_data = link.state[10]['value']
                joy_data = link.state[20]['value']
                print(f"Brain Aim: {aim_data} | Trigger 10: {trigger_data} | Controller Joy: {joy_data}", end='\r')
                time.sleep(0.1)
        except KeyboardInterrupt:
            link.disconnect()