import tkinter as tk
from tkinter import ttk, messagebox
import serial
from PIL import Image, ImageTk  # Import necessary modules from PIL
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

    def stop_laser(self):
        send_command(self.serial_port, "M5")

    def home_machine(self):
        # Command to home the machine
        send_command(self.serial_port, "G28 F2000 S30")  # Common G-code command for homing

if __name__ == "__main__":
    root = tk.Tk()
    app = LaserDrillPressApp(root)
    root.mainloop()
