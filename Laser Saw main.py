import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog
import serial  # Import the serial module
import tempfile
import os
from PIL import Image, ImageTk  # Import from PIL

# Declare global variables
canvas = None
serial_port = None
def setup_serial():
    global serial_port
    serial_port = serial.Serial('COM3', 115200, timeout=1)
    print("Serial port opened on COM3 with baud rate 115200.")
setup_serial()  # Call the setup_serial function to initialize the serial port

def send_lines_to_engraver():
    global canvas
    lines = canvas.find_withtag("line")  # Get all items tagged with 'line'
    gcode_commands = []
    for line in lines:
        x1, y1, x2, y2 = canvas.coords(line)  # Get coordinates of each line
        gcode_commands.append(f"G1 X{x1} Y{y1} S100")  # Assuming laser power is set to 100 (adjust as needed)
        gcode_commands.append(f"G1 X{x2} Y{y2} S0")    # Turn off laser at the end of the line
    send_command(gcode_commands)
def send_command(gcode_commands):
    global serial_port
    for command in gcode_commands:
        serial_port.write((command + "\n").encode())
        serial_port.flush()

def save_gcode():
    global canvas
    lines = canvas.find_withtag("line")
   
    machine_height = 860  # Assuming the machine's height is 860mm, adjust as needed
    gcode_lines = []
    for line in lines:
        x1, y1, x2, y2 = canvas.coords(line)
        # Adjust coordinates to match desired position relative to bottom-left corner
        # Subtract x-coordinate from machine width and y-coordinate from machine height
        # to move the origin to the bottom-left corner
        y1 = machine_height - y1
        y2 = machine_height - y2
        # Add feedrate (speed) and laser power (S1000 for full power, S0 for off)
        gcode_lines.append(f"G1 X{x1} Y{y1} F2000")  # Move to starting position
        gcode_lines.append("M3 S1000")  # Turn laser on
        gcode_lines.append(f"G1 X{x1} Y{y1} F2000")  # Move to starting position (redundant)
        gcode_lines.append(f"G1 X{x2} Y{y2} F2000")    # Move to ending position
        gcode_lines.append("M5")  # Turn laser off
    file_path = filedialog.asksaveasfilename(defaultextension=".gcode",
                                              filetypes=[("G-code Files", "*.gcode")])
    if file_path:
        with open(file_path, 'w') as f:
            f.write("\n".join(gcode_lines))
        messagebox.showinfo("G-code Export", "G-code saved successfully.")

import tempfile




def Engrave():
    global canvas, speed_entry, power_entry
    
    # Get the values from the speed and power entries
    speed = speed_entry.get()
    power = power_entry.get()

    # Convert speed and power to integers (assuming they are entered as integers)
    speed = int(speed)
    power = int(power)

    # Define the traveling speed when the laser is off
    travel_speed = 2000

    lines = canvas.find_withtag("line")
    machine_height = 860  # Assuming the machine's height is 860mm, adjust as needed
    gcode_lines = []

    for line in lines:
        x1, y1, x2, y2 = canvas.coords(line)

        # Adjust coordinates to match desired position relative to bottom-left corner
        y1 = machine_height - y1
        y2 = machine_height - y2

        # Move to starting position
        gcode_lines.append(f"G1 X{x1} Y{y1} F{travel_speed} S{power}")

        # Turn laser on
        gcode_lines.append(f"M3 S{power}")

        # Move to starting position (redundant)
        gcode_lines.append(f"G1 X{x1} Y{y1} F{travel_speed}")

        # Move to ending position
        gcode_lines.append(f"G1 X{x2} Y{y2} F{speed if power > 0 else travel_speed}")

        # Turn laser off
        gcode_lines.append("M5")

    # Create a temporary file to store the G-code
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write("\n".join(gcode_lines))

    # Send the G-code from the temporary file to the laser engraver
    with open(temp_file.name, 'r') as f:
        gcode_commands = f.readlines()
        send_command([command.strip() for command in gcode_commands])

    # Delete the temporary file after sending the G-code
    os.unlink(temp_file.name)

    messagebox.showinfo("Engraving", "G-code sent to the laser engraver.")


def cut():
    global serial_port
    file_path = filedialog.askopenfilename(filetypes=[("G-code Files", "*.gcode")])
    if file_path:
        print("Reading G-code file:", file_path)
        with open(file_path, 'r') as f:
            gcode_commands = f.readlines()
            print("Sending G-code commands:")
            for command in gcode_commands:
                print(command.strip())
            send_command([command.strip() for command in gcode_commands])  # Sending each command individually

def home_laser():
    global serial_port
    print("Sending homing command...")
    # Send homing command along with the current position as 0,0
    send_command(["G28 F2000 "])  
    print("Homing command sent.")
    Set_Zero()

def Set_Zero():
    global serial_port
    print("Sending Zero homing command...")
    # Send homing command along with the current position as 0,0
    send_command([" G90 G28 X0 Y0 Z0"])  
    print("Zero homing command sent.")


def main():
    global canvas, speed_entry, power_entry  # Declare these variables globally here



    root = tk.Tk()
    root.title("Draw Cut Application")
    root.geometry("1600x1200")  # Adjusted window size for better layout
    # Load the background image
    try:
        bg_image = Image.open("background_1.jpg")
        bg_photo = ImageTk.PhotoImage(bg_image)
        bg_label = tk.Label(root, image=bg_photo)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        bg_label.image = bg_photo  # Keep a reference to avoid garbage collection
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load background image: {e}")
        return
    # Menu frame for inputs at the top of the window
    menu_frame = tk.Frame(root)
    menu_frame.pack(side='left', fill='y', expand=False)  # Packed to the left side

    # Variables for machine and material dimensions with default values
    machine_width = tk.IntVar(value=410)
    machine_height = tk.IntVar(value=860)

    # Canvas setup; dimensions will be updated via a function
    canvas = tk.Canvas(root, bg='white')
    canvas.pack(fill='both', expand=True)

    # Function to update canvas size based on machine dimensions
    def update_canvas():
        mw, mh = machine_width.get(), machine_height.get()
        canvas.config(width=mw, height=mh)
        canvas.delete("all")  # Clear previous drawings
        # Draw the maximum cutting area
        canvas.create_rectangle(2.5, 2.5, mw - 2.5, mh - 2.5, outline="blue", width=1)

    # Function to clear all lines from the canvas
    def clear_lines():
        canvas.delete("line")  # Assumes all lines are tagged with 'line' when created

    # Machine width and height entries
    machine_width_label = ttk.Label(menu_frame, text="Machine Width (mm):")
    machine_width_label.pack(padx=5, pady=2)
    machine_width_entry = ttk.Entry(menu_frame, textvariable=machine_width, width=7)
    machine_width_entry.pack(padx=5, pady=2)

    machine_height_label = ttk.Label(menu_frame, text="Machine Height (mm):")
    machine_height_label.pack(padx=5, pady=2)
    machine_height_entry = ttk.Entry(menu_frame, textvariable=machine_height, width=7)
    machine_height_entry.pack(padx=5, pady=2)

    confirm_machine_button = ttk.Button(menu_frame, text="Set Machine Size", command=update_canvas)
    confirm_machine_button.pack(padx=5, pady=2)

    material_x_label = ttk.Label(menu_frame, text="Material Width (mm):")
    material_x_label.pack(padx=5, pady=2)
    material_x_entry = ttk.Entry(menu_frame, width=7)
    material_x_entry.pack(padx=5, pady=2)

    material_y_label = ttk.Label(menu_frame, text="Material Height (mm):")
    material_y_label.pack(padx=5, pady=2)
    material_y_entry = ttk.Entry(menu_frame, width=7)
    material_y_entry.pack(padx=5, pady=2)

    confirm_button = ttk.Button(menu_frame, text="Set Material", command=lambda: draw_material())
    confirm_button.pack(padx=5, pady=2)

    draw_line_button = ttk.Button(menu_frame, text="Enable Draw Line", command=lambda: toggle_line_drawing())
    draw_line_button.pack(padx=5, pady=2)

    clear_lines_button = ttk.Button(menu_frame, text="Clear Lines", command=clear_lines)
    clear_lines_button.pack(padx=5, pady=2)

    gcode_button = ttk.Button(menu_frame, text="Save G-code", command=save_gcode)
    gcode_button.pack(padx=5, pady=2)

    cut_button = ttk.Button(menu_frame, text="Cut", command=cut)
    cut_button.pack(padx=5, pady=2)

    home_button = ttk.Button(menu_frame, text="Home", command=home_laser)
    home_button.pack(padx=5, pady=2)

    zero_button = ttk.Button(menu_frame, text="Set Zero", command=Set_Zero)
    zero_button.pack(padx=5, pady=2)

    engrave_button = ttk.Button(menu_frame, text="Engrave", command=Engrave)
    engrave_button.pack(padx=5, pady=2)

    speed_label = ttk.Label(menu_frame, text="Speed (F):")
    speed_label.pack(padx=5, pady=2)

    speed_entry = ttk.Entry(menu_frame, width=7)
    speed_entry.pack(padx=5, pady=2)

    power_label = ttk.Label(menu_frame, text="Power (S):")
    power_label.pack(padx=5, pady=2)

    power_entry = ttk.Entry(menu_frame, width=7)
    power_entry.pack(padx=5, pady=2)




    # Functions to handle drawing and material settings
    line_start = None
    line_drawing_enabled = False  # To track if line drawing mode is enabled

    def handle_left_click(event):
        nonlocal line_start
        if line_drawing_enabled:
            if line_start is None:
                line_start = (event.x, event.y)
                canvas.create_oval(event.x-2, event.y-2, event.x+2, event.y+2, fill="green")
            else:
                # Tagging lines with 'line' for easy removal
                canvas.create_line(line_start[0], line_start[1], event.x, event.y, fill="green", width=2, tags="line")
                line_start = (event.x, event.y)

    def handle_right_click(event):
        nonlocal line_start
        line_start = None

    def draw_material():
        canvas.delete("material_area")
        try:
            material_width = int(material_x_entry.get())
            material_height = int(material_y_entry.get())
            if 0 < material_width <= machine_width.get() and 0 < material_height <= machine_height.get():
                x1 = 2.5
                y1 = machine_height.get() - material_height - 2.5
                canvas.create_rectangle(x1, y1, x1 + material_width, y1 + material_height, outline="red", width=2, fill="light grey", tags="material_area")
            else:
                messagebox.showerror("Error", "Material dimensions must fit within the specified machine dimensions.")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid integer dimensions.")

    def toggle_line_drawing():
        nonlocal line_drawing_enabled
        if line_drawing_enabled:
            canvas.unbind("<Button-1>")
            canvas.unbind("<Button-3>")
            draw_line_button.config(text="Enable Draw Line")
        else:
            canvas.bind("<Button-1>", handle_left_click)
            canvas.bind("<Button-3>", handle_right_click)
            draw_line_button.config(text="Disable Draw Line")
        line_drawing_enabled = not line_drawing_enabled



    # Initialize the canvas with the default machine size
    update_canvas()




    root.mainloop()

if __name__ == "__main__":
    main()
