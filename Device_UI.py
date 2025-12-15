#Display After prototype 2, but before final prototype
import tkinter as tk
from tkinter import ttk
import RPi.GPIO as GPIO
import time
import threading

# --- Motor pins and PWM setup ---
IN1 = 12
IN2 = 13
GPIO.setmode(GPIO.BCM)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
pwm_in1 = GPIO.PWM(IN1, 1000)
pwm_in2 = GPIO.PWM(IN2, 1000)
pwm_in1.start(0)
pwm_in2.start(0)

# --- Motor timing configuration ---
INITIAL_WAIT = 1
MOTOR_DOWN_DURATION = 0.5
MOTOR_UP_DURATION = 0.5
MIN_CYCLE_RATE = int(INITIAL_WAIT + MOTOR_DOWN_DURATION + MOTOR_UP_DURATION + 1)  # = 3

def spin_motor(direction, speed=80, duration=1):
    """Spins the motor in a given direction for a specified duration."""
    if direction == 'forward':
        pwm_in1.ChangeDutyCycle(speed)
        pwm_in2.ChangeDutyCycle(0)
    elif direction == 'backward':
        pwm_in1.ChangeDutyCycle(0)
        pwm_in2.ChangeDutyCycle(speed)
    else:
        pwm_in1.ChangeDutyCycle(0)
        pwm_in2.ChangeDutyCycle(0)
    time.sleep(duration)
    pwm_in1.ChangeDutyCycle(0)
    pwm_in2.ChangeDutyCycle(0)

# --- UI States ---
STATE_SETUP = "setup"
STATE_RUNNING = "running"
STATE_PAUSED = "paused"
SCALE = 1.2

class DeviceUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Device UI")
        self.root.geometry("800x480+0+0")
        self.root.configure(bg="white")

        # --- State variables ---
        self.total_minutes = 10
        self.cycle_rate = MIN_CYCLE_RATE
        self.elapsed = 0
        self.cycle_count = 0
        self.state = STATE_SETUP
        self.motor_active = False

        self._run_flag = threading.Event()
        self._pause_flag = threading.Event()
        self._run_thread = None

        # --- Style ---
        style = ttk.Style()
        style.configure("TScale", sliderlength=int(30 * SCALE))

        self._build_ui()
        self._update_ui_from_values()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        top = tk.Frame(self.root, bg="white")
        top.pack(side="top", fill="x", pady=10)
        left = tk.Frame(self.root, bg="white")
        left.pack(side="left", fill="y", padx=20)
        right = tk.Frame(self.root, bg="white")
        right.pack(side="right", fill="both", expand=True)

        # --- Timer and cycles display ---
        tk.Label(top, text="Timer (hh:mm):", bg="white", font=("Arial", 18, "bold")).grid(row=0, column=0, sticky="w", padx=20)
        self.time_display = tk.Label(top, text="00:00", bg="white", font=("Arial", 24))
        self.time_display.grid(row=0, column=1, sticky="w")
        tk.Label(top, text="Cycles:", bg="white", font=("Arial", 18, "bold")).grid(row=1, column=0, sticky="w", padx=20)
        self.count_display = tk.Label(top, text="0", bg="white", font=("Arial", 24))
        self.count_display.grid(row=1, column=1, sticky="w")

        # --- State and motor activity labels ---
        self.state_label = tk.Label(top, text="State: SETUP", bg="white", fg="gray", font=("Arial", 14))
        self.state_label.grid(row=2, column=0, sticky="w", padx=20, pady=(5, 0))
        self.motor_label = tk.Label(top, text="○ Idle", bg="white", fg="gray", font=("Arial", 14))
        self.motor_label.grid(row=2, column=1, sticky="w", padx=20)

        # --- Close Button ---
        tk.Button(top, text="X", command=self._on_close, bg="red", fg="white", font=("Arial", 12, "bold")).grid(row=0, column=3, sticky="e", padx=10)

        # --- Timer Slider ---
        self.timer_value_label = tk.Label(left, text="Timer 00:10", bg="white", font=("Arial", 12))
        self.timer_value_label.pack(pady=(0, 10))
        tk.Label(left, text="Timer Duration (hours)", bg="white", font=("Arial", 14)).pack()
        self.timer_scale = ttk.Scale(left, from_=0, to=720, orient="horizontal", length=300, command=self._on_timer_scale)
        self.timer_scale.set(self.total_minutes)
        self.timer_scale.pack(pady=10)
        self._draw_timer_ticks(left)

        # --- Cycle Slider ---
        self.cycle_value_label = tk.Label(left, text=f"Cycles every {self.cycle_rate}s", bg="white", font=("Arial", 12))
        self.cycle_value_label.pack(pady=(20, 5))
        tk.Label(left, text="Cycle Interval (seconds)", bg="white", font=("Arial", 14)).pack()
        self.cycle_scale = ttk.Scale(left, from_=MIN_CYCLE_RATE, to=30, orient="horizontal", length=300, command=self._on_cycle_scale)
        self.cycle_scale.set(self.cycle_rate)
        self.cycle_scale.pack(pady=10)

        # --- Hold Time Display ---
        self.hold_time_label = tk.Label(left, text=f"Hold Time: {self._calculate_hold_time(self.cycle_rate)}s", bg="white", font=("Arial", 12, "italic"), fg="gray")
        self.hold_time_label.pack(pady=(5, 10))

        # --- Buttons in Triangle ---
        btn_size = int(100 * SCALE)
        # Start
        self.start_btn = tk.Canvas(right, width=btn_size, height=btn_size, bg="white", highlightthickness=0)
        self.start_circle = self.start_btn.create_oval(0, 0, btn_size, btn_size, fill="#00AA00", outline="")
        self.start_btn.place(relx=0.5, rely=0.15, anchor="center")
        tk.Label(right, text="Start", bg="white", font=("Arial", 12, "bold")).place(relx=0.5, rely=0.32, anchor="center")
        self.start_btn.bind("<ButtonRelease-1>", lambda e: self.start())

        # Pause
        self.pause_btn = tk.Canvas(right, width=btn_size, height=btn_size, bg="white", highlightthickness=0)
        self.pause_circle = self.pause_btn.create_oval(0, 0, btn_size, btn_size, fill="#FFD700", outline="")
        self.pause_btn.place(relx=0.25, rely=0.55, anchor="center")
        tk.Label(right, text="Pause", bg="white", font=("Arial", 12, "bold")).place(relx=0.25, rely=0.72, anchor="center")
        self.pause_btn.bind("<ButtonRelease-1>", lambda e: self.pause())

        # Stop
        self.stop_btn = tk.Canvas(right, width=btn_size, height=btn_size, bg="white", highlightthickness=0)
        self.stop_circle = self.stop_btn.create_oval(0, 0, btn_size, btn_size, fill="#FF0000", outline="")
        self.stop_btn.place(relx=0.75, rely=0.55, anchor="center")
        tk.Label(right, text="Stop", bg="white", font=("Arial", 12, "bold")).place(relx=0.75, rely=0.72, anchor="center")
        self.stop_btn.bind("<ButtonRelease-1>", lambda e: self.stop(True))

    def _draw_timer_ticks(self, frame):
        canvas = tk.Canvas(frame, width=300, height=35, bg="white", highlightthickness=0)
        canvas.pack()
        offset = 10
        for hour in range(13):
            x = offset + (hour / 12) * (300 - 2 * offset)
            canvas.create_line(x, 0, x, 10)
            if hour % 2 == 0:
                canvas.create_text(x, 25, text=f"{hour}:00", font=("Arial", 9))

    def _calculate_hold_time(self, cycle_rate):
        return max(round(cycle_rate - (INITIAL_WAIT + MOTOR_DOWN_DURATION + MOTOR_UP_DURATION), 2), 0)

    def _on_timer_scale(self, v):
        self.total_minutes = int(float(v))
        h = self.total_minutes // 60
        m = self.total_minutes % 60
        self.timer_value_label.config(text=f"Timer {h:02}:{m:02}")

    def _on_cycle_scale(self, v):
        val = max(MIN_CYCLE_RATE, float(v))
        self.cycle_rate = val
        self.cycle_value_label.config(text=f"Cycles every {self.cycle_rate:.1f}s")
        self.hold_time_label.config(text=f"Hold Time: {self._calculate_hold_time(self.cycle_rate)}s")

    def _update_ui_from_values(self):
        h = self.elapsed // 60
        m = self.elapsed % 60
        self.time_display.config(text=f"{h:02}:{m:02}")
        self.count_display.config(text=str(self.cycle_count))
        self.state_label.config(text=f"State: {self.state.upper()}")

        if self.motor_active:
            self.motor_label.config(text="● Motor Active", fg="green")
        else:
            self.motor_label.config(text="○ Idle", fg="gray")

        self.root.after(200, self._update_ui_from_values)

    def start(self):
        if self.state == STATE_RUNNING:
            return
        self.state = STATE_RUNNING
        self._run_flag.set()
        self._pause_flag.clear()
        if not (self._run_thread and self._run_thread.is_alive()):
            self._run_thread = threading.Thread(target=self._run_loop, daemon=True)
            self._run_thread.start()

    def pause(self):
        if self.state != STATE_RUNNING:
            return
        self.state = STATE_PAUSED
        self._pause_flag.set()

    def stop(self, reset=False):
        self._run_flag.clear()
        self._pause_flag.clear()
        self.state = STATE_SETUP
        if reset:
            self.elapsed = 0
            self.cycle_count = 0

    def _run_loop(self):
        last_cycle_time = time.time()
        start_time = time.time()

        while self._run_flag.is_set():
            if self._pause_flag.is_set():
                time.sleep(0.1)
                continue

            self.elapsed = int(time.time() - start_time)

            if time.time() - last_cycle_time >= self.cycle_rate:
                last_cycle_time = time.time()
                threading.Thread(target=self._motor_cycle, daemon=True).start()
                self.cycle_count += 1

            time.sleep(0.1)

    def _motor_cycle(self):
        """Motor cycle with dynamic timing."""
        time.sleep(INITIAL_WAIT)
        self.motor_active = True
        spin_motor("forward", duration=MOTOR_DOWN_DURATION)
        hold_time = self._calculate_hold_time(self.cycle_rate)
        if hold_time > 0:
            time.sleep(hold_time)
        spin_motor("backward", duration=MOTOR_UP_DURATION)
        self.motor_active = False

    def _on_close(self):
        self._run_flag.clear()
        self._pause_flag.clear()
        pwm_in1.stop()
        pwm_in2.stop()
        GPIO.cleanup()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DeviceUI(root)
    root.mainloop()
