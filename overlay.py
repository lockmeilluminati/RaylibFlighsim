import tkinter as tk
from vex_link import VexConnection

class FeedbackOverlay(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VEX Live Feedback Overlay")
        self.geometry("900x400")
        self.configure(bg="#0f172a") # Dark background
        
        # Initialize and auto-connect the backend
        self.backend = VexConnection(port="COM5")
        self.backend.connect()
        
        self.port_boxes = {}
        self.create_overlay_grid()
        
        # Start the visual update loop
        self.update_visuals()

    def create_overlay_grid(self):
        # Create a simple 2-row, 6-column grid for the 12 ports
        for i in range(1, 13):
            col, row = (i - 1) % 6, (i - 1) // 6
            
            frame = tk.Frame(self, bg='#1e293b', bd=2, relief='flat', highlightbackground="#334155", highlightthickness=1)
            frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            lbl_num = tk.Label(frame, text="PORT {}".format(i), bg='#1e293b', fg='#94a3b8', font=('Arial', 10, 'bold'))
            lbl_num.pack(pady=(15, 5))
            
            lbl_type = tk.Label(frame, text="Waiting...", bg='#1e293b', fg='#cbd5e1', font=('Arial', 12))
            lbl_type.pack()
            
            lbl_val = tk.Label(frame, text="N/A", bg='#1e293b', fg='#64748b', font=('Arial', 16, 'bold'))
            lbl_val.pack(pady=(5, 15))
            
            self.port_boxes[i] = {"frame": frame, "type": lbl_type, "value": lbl_val}
            self.grid_columnconfigure(col, weight=1)
            self.grid_rowconfigure(row, weight=1)

    def update_visuals(self):
        # Pull the latest data directly from the backend dictionary
        current_data = self.backend.state
        
        for p_id, data in current_data.items():
            box = self.port_boxes[p_id]
            val = data["value"]
            
            # Update the text
            box["type"].config(text=data["type"])
            box["value"].config(text=val)
            
            # Change colors dynamically if a button is pressed
            if val == "Pressed":
                box["frame"].config(bg="#10b981") # Bright Green
                box["type"].config(bg="#10b981", fg="black")
                box["value"].config(bg="#10b981", fg="black")
                box["num_lbl"] = box["frame"].winfo_children()[0]
                box["num_lbl"].config(bg="#10b981", fg="black")
            elif "Vel" in val:
                box["frame"].config(bg="#3b82f6") # Blue for motors
                box["type"].config(bg="#3b82f6", fg="white")
                box["value"].config(bg="#3b82f6", fg="white")
                box["num_lbl"] = box["frame"].winfo_children()[0]
                box["num_lbl"].config(bg="#3b82f6", fg="white")
            else:
                box["frame"].config(bg="#1e293b") # Default dark gray
                box["type"].config(bg="#1e293b", fg="#cbd5e1")
                box["value"].config(bg="#1e293b", fg="#34d399")
                box["num_lbl"] = box["frame"].winfo_children()[0]
                box["num_lbl"].config(bg="#1e293b", fg="#94a3b8")

        # Re-run this update function every 50 milliseconds
        self.after(50, self.update_visuals)

    def on_closing(self):
        self.backend.disconnect()
        self.destroy()

if __name__ == "__main__":
    app = FeedbackOverlay()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()