import tkinter as tk
from tkinter import ttk, messagebox
import serial
from PIL import Image, ImageTk  # Import necessary modules from PIL
import math
def setup_serial():
    try:
        serial_port = serial.Serial('COM3', 115200, timeout=1)
        print("Serial port opened on COM3 with baud rate 115200.")
        return serial_port
    except serial.SerialException as e:
        messagebox.showerror("Error", f"Failed to open serial port: {e}")
        return None

def send_command(serial_port, command):
    if serial_port:
        try:
            serial_port.write((command + '\n').encode())
            print(f"Sent command: {command}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send command: {e}")

class LaserDrillPressApp:
    def __init__(self, root):
        self.root = root
        self.serial_port = setup_serial()

        # Load the background image
        self.background_image = Image.open("background_2.png")
        self.background_photo = ImageTk.PhotoImage(self.background_image)

        # Create a Label to put the background image
        self.background_label = tk.Label(root, image=self.background_photo)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.root.title("Laser Drill Press Application")
        self.root.geometry("500x500")  # Increased height to accommodate new input boxes

        # Diameter input
        ttk.Label(root, text="Diameter (mm):").pack(pady=(20, 5))
        self.diameter_entry = ttk.Entry(root)
        self.diameter_entry.pack()

        # Speed input
        ttk.Label(root, text="Cutting Speed (mm/min):").pack(pady=5)
        self.speed_entry = ttk.Entry(root)
        self.speed_entry.pack()

        # Power input
        ttk.Label(root, text="Laser Power (max 1000):").pack(pady=5)
        self.power_entry = ttk.Entry(root)
        self.power_entry.pack()

        # Action buttons
        ttk.Button(root, text="Move to Center and Mark", command=self.move_and_mark).pack(pady=10)
        ttk.Button(root, text="Cut Circle", command=self.cut_circle).pack(pady=10)
        ttk.Button(root, text="Cut Square", command=self.cut_square).pack(pady=10)
        ttk.Button(root, text="Cut Hexagon", command=self.cut_hexagon).pack(pady=10)
        ttk.Button(root, text="Stop Laser", command=self.stop_laser).pack(pady=10)
        ttk.Button(root, text="Home", command=self.home_machine).pack(pady=10)  # Home button
    def move_and_mark(self):
        # First, ensure the laser is off before starting a new operation
        send_command(self.serial_port, "M5")
        send_command(self.serial_port, "M3")
        # Move to the desired position (200, 200)
        send_command(self.serial_port, "G1 X200 Y200 F2000 S30")

    def cut_circle(self):
        diameter = float(self.diameter_entry.get())
        radius = diameter / 2
        speed = self.speed_entry.get()
        power = int(self.power_entry.get())

        commands = [
            f"G0 X{200 + radius} Y{200 }",
            "G17",  # XY plane selection
            f"G2 X{200 + radius} Y{200 } I-{radius} F{speed} S{power}",
            "M5",
            "G1 X200 Y200 F2000 S30"
        ]
        for cmd in commands:
            send_command(self.serial_port, cmd)

    def cut_square(self):
        side_length = float(self.diameter_entry.get())  # Reusing the diameter entry as the side length for simplicity
        half_side = side_length / 2
        speed = self.speed_entry.get()
        power = int(self.power_entry.get())

        # Calculate corner positions
        x_center = 200
        y_center = 200
        top_left = (x_center - half_side, y_center + half_side)
        top_right = (x_center + half_side, y_center + half_side)
        bottom_right = (x_center + half_side, y_center - half_side)
        bottom_left = (x_center - half_side, y_center - half_side)

        commands = [
            "M5",  # Ensure the laser is off before starting
            f"M3 S{power}",  # Turn on the laser
            f"G0 X{top_left[0]} Y{top_left[1]}",  # Move to the starting position (top-left corner)
            f"G1 X{top_right[0]} Y{top_right[1]} F{speed}",  # Draw to top-right
            f"G1 X{bottom_right[0]} Y{bottom_right[1]} F{speed}",  # Draw to bottom-right
            f"G1 X{bottom_left[0]} Y{bottom_left[1]} F{speed}",  # Draw to bottom-left
            f"G1 X{top_left[0]} Y{top_left[1]} F{speed}",  # Draw back to top-left to close the square
            "M5"  # Turn off the laser
        ]

        for cmd in commands:
            send_command(self.serial_port, cmd)


    def cut_hexagon(self):
        radius = float(self.diameter_entry.get())  # Assuming this entry now captures the radius for the hexagon
        speed = self.speed_entry.get()
        power = int(self.power_entry.get())

        # Central point (change these as necessary)
        x_center = 200
        y_center = 200

        # Calculate vertex coordinates
        vertices = []
        for i in range(6):
            angle_deg = 60 * i - 30  # Starts the hexagon flat on the top
            angle_rad = math.radians(angle_deg)
            x = x_center + radius * math.cos(angle_rad)
            y = y_center + radius * math.sin(angle_rad)
            vertices.append((x, y))

        commands = [
            "M5",  # Ensure the laser is off before starting
            f"M3 S{power}",  # Turn on the laser
            f"G0 X{vertices[0][0]} Y{vertices[0][1]}",  # Move to the first vertex
        ]

        # Draw lines between vertices
        for vertex in vertices[1:]:
            commands.append(f"G1 X{vertex[0]} Y{vertex[1]} F{speed}")
        # Close the hexagon by drawing a line back to the first vertex
        commands.append(f"G1 X{vertices[0][0]} Y{vertices[0][1]} F{speed}")

        commands.append("M5")  # Turn off the laser

        for cmd in commands:
            send_command(self.serial_port, cmd)


    def stop_laser(self):
        send_command(self.serial_port, "M5")

    def home_machine(self):
        # Command to home the machine
        send_command(self.serial_port, "G28 F2000 S30")  # Common G-code command for homing

if __name__ == "__main__":
    root = tk.Tk()
    app = LaserDrillPressApp(root)
    root.mainloop()
