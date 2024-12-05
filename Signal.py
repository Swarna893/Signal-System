import tkinter as tk
import time
import firebase_admin
from firebase_admin import credentials, db
from threading import Thread

# Initialize Firebase Admin
cred = credentials.Certificate(
    'C:/Users/HP/PycharmProjects/Algorithm/credentials/sihbytebenders2-firebase-adminsdk-2tnhf-f6ee56795c.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://sihbytebenders2-default-rtdb.asia-southeast1.firebasedatabase.app/'
})


# Function to get car count from a specific node
def get_car_count(node):
    ref = db.reference(f'data/{node}/car_count')
    return ref.get()


# Function to update car count in a specific node
def update_car_count(node, count):
    ref = db.reference(f'data/{node}/car_count')
    ref.set(count)


# Function to fetch car counts from all four nodes
def fetch_traffic_data():
    return {
        "Reno": get_car_count('Reno'),
        "Swarna": get_car_count('Swarna'),
        "Harsh": get_car_count('Harshendu'),
        "Ani": get_car_count('anirban'),
    }


# Function to release traffic on a selected lane
def release_lane(lane_counts, selected_lane):
    lane_counts[selected_lane] = max(0, lane_counts[selected_lane] - 10)
    node_mapping = {
        "Reno": "Reno",
        "Swarna": "Swarna",
        "Harsh": "Harshendu",
        "Ani": "anirban",
    }
    update_car_count(node_mapping[selected_lane], lane_counts[selected_lane])
    return lane_counts


# GUI Class
class TrafficControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Traffic Light Simulation with Firebase")
        self.frames = {}
        self.car_counts = {}
        self.lights = {}
        self.init_gui()

    def init_gui(self):
        lanes = ["Reno", "Swarna", "Harsh", "Ani"]
        for index, lane in enumerate(lanes):
            frame = tk.Frame(self.root, relief=tk.RAISED, borderwidth=2, padx=10, pady=10)
            frame.grid(row=0, column=index, padx=10, pady=10)

            tk.Label(frame, text=lane, font=("Arial", 14)).pack(pady=5)

            # Traffic light representation
            canvas = tk.Canvas(frame, width=80, height=220, bg="white")  # Transparent canvas
            canvas.pack(pady=10)

            # Draw a rounded rectangle for the traffic light box
            self.draw_rounded_rectangle(canvas, 10, 10, 70, 210, 20, fill="black", outline="black")

            # Draw the lights inside the box
            red_light = canvas.create_oval(20, 20, 60, 60, fill="gray")
            yellow_light = canvas.create_oval(20, 80, 60, 120, fill="gray")
            green_light = canvas.create_oval(20, 140, 60, 180, fill="gray")

            self.lights[lane] = {
                "canvas": canvas,
                "ovals": {"red": red_light, "yellow": yellow_light, "green": green_light},
            }

            # Car count
            tk.Label(frame, text="Car Count:", font=("Arial", 12)).pack()
            count_label = tk.Label(frame, text="0", font=("Arial", 14), fg="blue")
            count_label.pack()
            self.car_counts[lane] = count_label

    def draw_rounded_rectangle(self, canvas, x1, y1, x2, y2, radius, **kwargs):
        """Draw a rounded rectangle on the canvas."""
        points = [
            (x1 + radius, y1),
            (x2 - radius, y1),
            (x2 - radius, y1 + radius),
            (x2, y1 + radius),
            (x2, y2 - radius),
            (x2 - radius, y2 - radius),
            (x2 - radius, y2),
            (x1 + radius, y2),
            (x1 + radius, y2 - radius),
            (x1, y2 - radius),
            (x1, y1 + radius),
            (x1 + radius, y1 + radius),
        ]
        canvas.create_polygon(points, smooth=True, **kwargs)

    def update_gui(self, traffic_data, lights_state):
        for lane, count in traffic_data.items():
            self.car_counts[lane].config(text=str(count))
            for color in ["red", "yellow", "green"]:
                color_fill = "gray"
                if color.lower() == lights_state[lane].lower():
                    color_fill = color
                self.lights[lane]["canvas"].itemconfig(self.lights[lane]["ovals"][color], fill=color_fill)


# Traffic control logic in a separate thread
def traffic_control(gui):
    lane_priority = ["Reno", "Swarna", "Harsh", "Ani"]  # Round-robin priority
    wait_times = {lane: 0 for lane in lane_priority}  # Tracks wait times for fairness
    index = 0  # Current lane index for round-robin scheduling

    while True:
        lane_counts = fetch_traffic_data()

        # Select the current lane in a round-robin fashion
        selected_lane = lane_priority[index]
        index = (index + 1) % len(lane_priority)  # Move to the next lane

        # Transition to yellow before green
        lights_state = {lane: "Red" for lane in lane_priority}
        gui.update_gui(lane_counts, lights_state)  # All red
        time.sleep(1)  # Short pause

        # Set yellow for the selected lane (Red to Green transition)
        lights_state[selected_lane] = "Yellow"
        gui.update_gui(lane_counts, lights_state)
        time.sleep(1)  # Yellow light duration

        # Set green for the selected lane
        lights_state[selected_lane] = "Green"
        gui.update_gui(lane_counts, lights_state)
        lane_counts = release_lane(lane_counts, selected_lane)
        time.sleep(3)  # Green light duration

        # Transition back to yellow (Green to Red transition)
        lights_state[selected_lane] = "Yellow"
        gui.update_gui(lane_counts, lights_state)
        time.sleep(1)  # Yellow light duration

        # Set red for the selected lane
        lights_state[selected_lane] = "Red"
        gui.update_gui(lane_counts, lights_state)

        # Increment wait times for all other lanes
        for lane in lane_priority:
            if lane != selected_lane:
                wait_times[lane] += 1
            else:
                wait_times[lane] = 0


# Run the GUI and traffic control system
if __name__ == "__main__":
    root = tk.Tk()
    gui = TrafficControlGUI(root)
    Thread(target=traffic_control, args=(gui,), daemon=True).start()
    root.mainloop()
