import pyray as pr
from vex_link import VexConnection
from network_engine import FlightNetworkServer
import math
import random

class FlightSimulator:
    def __init__(self):
        self.backend = VexConnection(port="COM5") 
        self.backend.connect()
        self.network = FlightNetworkServer()

        pr.init_window(1280, 720, "Flight Simulator - PILOT (Laptop 1)")
        pr.set_target_fps(60)

        try:
            self.plane_model = pr.load_model("plane/plane.glb")
        except: self.plane_model = None

        # --- SYNCHRONIZED WORLD GENERATION ---
        self.world_size = 8000.0
        self.structures = []
        random.seed(42) # The Secret Key
        for _ in range(400):
            x = random.uniform(-4000, 4000)
            z = random.uniform(-4000, 4000)
            h = random.uniform(50, 250)
            w = random.uniform(15, 40)
            c = pr.GRAY if h > 100 else pr.DARKGREEN
            self.structures.append({"pos": pr.Vector3(x, 0.0, z), "width": w, "height": h, "color": c})

        self.plane_pos = pr.Vector3(0.0, 300.0, 0.0) 
        self.yaw = self.pitch = self.roll = 0.0
        self.speed = 50.0 
        self.cam_follow_dist = 3.5   
        self.cam_height = 1.5            
        self.camera = pr.Camera3D([0,0,0], [0,0,0], [0,1,0], 70.0, pr.CAMERA_PERSPECTIVE)

    def update_logic(self):
        state = self.backend.state
        dt = pr.get_frame_time()
        target_pitch = 0.0
        target_roll = 0.0

        if state[1]["type"] == "Motor":
            try: self.speed = max(20.0, float(state[1]["value"]) * 0.1) 
            except ValueError: pass
        if state[2]["type"] == "Motor":
            try: target_roll = max(-1.0, min(1.0, float(state[2]["value"]) * 0.005))
            except ValueError: pass

        if pr.is_key_down(pr.KEY_A): target_roll = -0.8      
        elif pr.is_key_down(pr.KEY_D): target_roll = 0.8   
        if pr.is_key_down(pr.KEY_W): target_pitch = 0.5    
        elif pr.is_key_down(pr.KEY_S): target_pitch = -0.5   

        self.pitch += (target_pitch - self.pitch) * 3.0 * dt
        self.roll += (target_roll - self.roll) * 4.0 * dt
        self.yaw -= (self.roll * 1.2) * dt # TRUE AERODYNAMIC TURNING

        fwd_x = math.cos(self.pitch) * math.sin(self.yaw)
        fwd_z = math.cos(self.pitch) * math.cos(self.yaw)
        fwd_y = math.sin(self.pitch)

        self.plane_pos.x += fwd_x * self.speed * dt
        self.plane_pos.y += fwd_y * self.speed * dt
        self.plane_pos.z += fwd_z * self.speed * dt

        if self.plane_pos.y <= 10.0:
            self.plane_pos.y = 10.0
            self.pitch = max(0.0, self.pitch) 

        # BROADCAST
        self.network.broadcast({"px": self.plane_pos.x, "py": self.plane_pos.y, "pz": self.plane_pos.z, "y": self.yaw, "p": self.pitch, "r": self.roll})

        cam_x, cam_z = math.sin(self.yaw), math.cos(self.yaw)
        self.camera.position = pr.Vector3(self.plane_pos.x - (cam_x * self.cam_follow_dist), self.plane_pos.y + self.cam_height, self.plane_pos.z - (cam_z * self.cam_follow_dist))
        self.camera.target = pr.Vector3(self.plane_pos.x + (cam_x * 100.0), self.plane_pos.y, self.plane_pos.z + (cam_z * 100.0))

    def draw_frame(self):
        pr.begin_drawing()
        pr.clear_background(pr.SKYBLUE)
        pr.begin_mode_3d(self.camera)
        pr.draw_cube(pr.Vector3(0,0,0), 8000, 1, 8000, pr.DARKGREEN)
        for s in self.structures: 
            pr.draw_cube(pr.Vector3(s["pos"].x, s["height"]/2, s["pos"].z), s["width"], s["height"], s["width"], s["color"])
            pr.draw_cube_wires(pr.Vector3(s["pos"].x, s["height"]/2, s["pos"].z), s["width"], s["height"], s["width"], pr.BLACK)

        if self.plane_model:
            mat = pr.matrix_multiply(pr.matrix_rotate_y(-1.5708), pr.matrix_rotate_z(self.roll))
            mat = pr.matrix_multiply(mat, pr.matrix_rotate_x(-self.pitch))
            self.plane_model.transform = pr.matrix_multiply(mat, pr.matrix_rotate_y(self.yaw))
            pr.draw_model(self.plane_model, self.plane_pos, 1.0, pr.WHITE)
        pr.end_mode_3d()
        
        pr.draw_rectangle(10, 10, 280, 100, pr.Color(0,0,0,160))
        pr.draw_text(f"IP: 192.168.1.224", 20, 20, 20, pr.SKYBLUE)
        pr.draw_text(f"NET: {self.network.status_msg}", 20, 50, 18, pr.LIME if self.network.client_conn else pr.WHITE)
        
        btn = pr.Rectangle(1000, 20, 260, 60)
        pr.draw_rectangle_rec(btn, pr.SKYBLUE if not self.network.is_hosting else pr.GRAY)
        label = "WAITING FOR LAPTOP 2" if self.network.is_hosting else "START SERVER"
        pr.draw_text(label, 1015, 40, 16, pr.BLACK)
        if pr.is_mouse_button_pressed(0) and pr.check_collision_point_rec(pr.get_mouse_position(), btn):
            if not self.network.is_hosting: self.network.start()
        pr.end_drawing()

    def run(self):
        while not pr.window_should_close():
            self.update_logic()
            self.draw_frame()
        self.network.stop()
        self.backend.disconnect()
        pr.close_window()

if __name__ == "__main__":
    FlightSimulator().run()