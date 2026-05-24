import socket
import threading
import json

class FlightNetworkServer:
    def __init__(self, port=5555):
        self.port = port
        self.host_ip = "0.0.0.0"
        self.server_socket = None
        self.client_conn = None
        self.is_hosting = False
        self.active = True
        self.status_msg = "OFFLINE"

    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host_ip, self.port))
            self.server_socket.listen(1)
            self.is_hosting = True
            self.status_msg = "WAITING FOR LAPTOP 2..."
            threading.Thread(target=self._listen_loop, daemon=True).start()
            return True
        except Exception as e:
            self.status_msg = f"ERR: {str(e)[:15]}"
            return False

    def _listen_loop(self):
        while self.active:
            try:
                conn, addr = self.server_socket.accept()
                self.client_conn = conn
                self.status_msg = f"CONNECTED: {addr[0]}"
            except: break

    def broadcast(self, data):
        if self.client_conn:
            try:
                self.client_conn.sendall((json.dumps(data) + "\n").encode())
            except:
                self.client_conn = None
                self.status_msg = "LAPTOP 2 DISCONNECTED"

    def stop(self):
        self.active = False
        if self.client_conn: self.client_conn.close()
        if self.server_socket: self.server_socket.close()