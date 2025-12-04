#This is the UI from Prototype 2

import tkinter as tk
from tkinter import ttk
import threading
import time
import RPi.GPIO as GPIO

# --- Motor timing ---
INITIAL_WAIT = 1
MOTOR_DOWN_DURATION = 0.5
MOTOR_UP_DURATION = 0.5
MIN_CYCLE_RATE = int(INITIAL_WAIT + MOTOR_DOWN_DURATION + MOTOR_UP_DURATION + 1)

STATE_SETUP = "setup"
STATE_RUNNING = "running"
STATE_PAUSED = "paused"
SCALE = 1.2

# Pump & motor variables
PUMP_RUN_TIME = 1.0  # seconds, changeable
MOTOR_SPEED_UP = 80  # changeable
MOTOR_SPEED_DOWN = 80  # changeable
DEVICE_SWITCH_DELAY = 0.1  # seconds between device activations
HOLD_PWM = 20  # small duty cycle for holding motor

# --- GPIO pins (external buttons) ---
STOP_PIN = 16
GO_PIN = 1
PAUSE_PIN = 14
GPIO.setmode(GPIO.BCM)
GPIO.setup(STOP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PAUSE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# --- Pump 1 GPIO pins ---
ENA = 18
ENB = 15
IN1 = 17
IN2 = 27
IN3 = 22
IN4 = 23
for pin in [ENA, ENB, IN1, IN2, IN3, IN4]:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)

# --- Pump 2 GPIO pins ---
P2_ENA = 8
P2_ENB = 11
P2_IN1 = 25
P2_IN2 = 24
P2_IN3 = 9
P2_IN4 = 10
for pin in [P2_ENA, P2_ENB, P2_IN1, P2_IN2, P2_IN3, P2_IN4]:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)

# --- Motor GPIO pins using PWM on IN1/IN2 ---
MOTOR_IN1 = 12
MOTOR_IN2 = 13
GPIO.setup(MOTOR_IN1, GPIO.OUT)
GPIO.setup(MOTOR_IN2, GPIO.OUT)
pwm_in1 = GPIO.PWM(MOTOR_IN1, 1000)
pwm_in2 = GPIO.PWM(MOTOR_IN2, 1000)
pwm_in1.start(0)
pwm_in2.start(0)

class DeviceUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Device UI")
        self.root.geometry("800x480+0+0")
        self.root.configure(bg="white")

        # --- Initial slider values ---
        self.total_seconds = 60       # 1 minute
        self.chews = 2                # 2 chews
        self.fluid_cycle = 10.0       # 10 seconds per cycle

        self.cycle_rate = float(MIN_CYCLE_RATE)
        self.elapsed = 0.0
        self.cycle_count = 0
        self.state = STATE_SETUP
        self.motor_active = False

        self._run_flag = threading.Event()
        self._pause_flag = threading.Event()
        self._run_thread = None

        style = ttk.Style()
        style.configure("TScale", sliderlength=int(30 * SCALE))

        self._build_ui()
        self._update_ui_from_values()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Start thread to monitor external buttons
        threading.Thread(target=self._external_buttons_loop, daemon=True).start()

    # --- UI building ---
    def _build_ui(self):
        top = tk.Frame(self.root, bg="white")
        top.pack(side="top", fill="x", pady=10)
        left = tk.Frame(self.root, bg="white")
        left.pack(side="left", fill="y", padx=20)
        right = tk.Frame(self.root, bg="white")
        right.pack(side="right", fill="both", expand=True)

        tk.Label(top, text="Timer (hh:mm:ss):", bg="white", font=("Arial", 18, "bold")).grid(row=0, column=0, sticky="w", padx=20)
        self.time_display = tk.Label(top, text="00:01:00", bg="white", font=("Arial", 24))
        self.time_display.grid(row=0, column=1, sticky="w")

        tk.Label(top, text="Cycles:", bg="white", font=("Arial", 18, "bold")).grid(row=1, column=0, sticky="w", padx=20)
        self.count_display = tk.Label(top, text="0", bg="white", font=("Arial", 24))
        self.count_display.grid(row=1, column=1, sticky="w")

        self.state_label = tk.Label(top, text="State: SETUP", bg="white", fg="gray", font=("Arial", 14))
        self.state_label.grid(row=2, column=0, sticky="w", padx=20, pady=(5,0))
        self.motor_label = tk.Label(top, text="○ Idle", bg="white", fg="gray", font=("Arial", 14))
        self.motor_label.grid(row=2, column=1, sticky="w", padx=20)

        self.hold_time_label = tk.Label(top, text="Hold time per chew: 0.0s", bg="white", font=("Arial", 12, "italic"), fg="gray")
        self.hold_time_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=20)

        # Timer slider
        self.timer_value_label = tk.Label(left, text="Timer 01:00", bg="white", font=("Arial", 12))
        self.timer_value_label.pack(pady=(0,10))
        tk.Label(left, text="Timer Duration (minutes)", bg="white", font=("Arial", 14)).pack()
        self.timer_scale = ttk.Scale(left, from_=0, to=720, orient="horizontal", length=300, command=self._on_timer_scale)
        self.timer_scale.set(self.total_seconds // 60)
        self.timer_scale.pack(pady=10)
        self._draw_timer_ticks(left)

        # Chews slider
        self.chews_value_label = tk.Label(left, text=f"Chews: {self.chews}", bg="white", font=("Arial", 12))
        self.chews_value_label.pack(pady=(20,5))
        tk.Label(left, text="Number of Chews", bg="white", font=("Arial", 14)).pack()
        self.chews_scale = ttk.Scale(left, from_=0, to=10, orient="horizontal", length=300, command=self._on_chews_scale)
        self.chews_scale.set(self.chews)
        self.chews_scale.pack(pady=10)
        self._draw_chews_ticks(left)

        # Fluid cycle slider
        self.fluid_value_label = tk.Label(right, text=f"Fluid Cycle: {self.fluid_cycle:.1f}s", bg="white", font=("Arial", 12))
        self.fluid_value_label.place(relx=0.5, rely=0.08, anchor="center")
        tk.Label(right, text="Fluid Cycle (s)", bg="white", font=("Arial", 14)).place(relx=0.5, rely=0.03, anchor="center")
        self.fluid_scale = ttk.Scale(right, from_=self._calculate_min_fluid_cycle(), to=120, orient="horizontal", length=300, command=self._on_fluid_scale)
        self.fluid_scale.set(self.fluid_cycle)
        self.fluid_scale.place(relx=0.5, rely=0.13, anchor="center")
        self._draw_fluid_ticks(right)

    # --- Tick drawing and helpers ---
    def _draw_timer_ticks(self, frame):
        canvas = tk.Canvas(frame, width=300, height=35, bg="white", highlightthickness=0)
        canvas.pack()
        offset = 10
        for hour in range(13):
            x = offset + (hour / 12) * (300 - 2 * offset)
            canvas.create_line(x, 0, x, 10)
            if hour % 2 == 0:
                canvas.create_text(x, 25, text=f"{hour}:00", font=("Arial", 9))

    def _draw_chews_ticks(self, frame):
        canvas = tk.Canvas(frame, width=300, height=20, bg="white", highlightthickness=0)
        canvas.pack()
        for i in range(0, 11, 2):
            x = (i / 10) * 300
            canvas.create_line(x, 0, x, 10)
            canvas.create_text(x, 15, text=f"{i}", font=("Arial", 9))

    def _draw_fluid_ticks(self, frame):
        canvas = tk.Canvas(frame, width=300, height=20, bg="white", highlightthickness=0)
        canvas.place(relx=0.5, rely=0.18, anchor="center")
        for i in range(int(self._calculate_min_fluid_cycle()), 121, 10):
            x = ((i - int(self._calculate_min_fluid_cycle())) / (120 - int(self._calculate_min_fluid_cycle()))) * 300
            canvas.create_line(x, 0, x, 10)
            canvas.create_text(x, 15, text=f"{i}", font=("Arial", 9))

    def _calculate_min_fluid_cycle(self):
        return INITIAL_WAIT + PUMP_RUN_TIME*2 + MOTOR_DOWN_DURATION*10 + MOTOR_UP_DURATION*10 + 2

    def _calculate_hold_time(self):
        if self.chews <= 0:
            return 0
        available_time = self.fluid_cycle - INITIAL_WAIT - PUMP_RUN_TIME*2 - MOTOR_DOWN_DURATION - MOTOR_UP_DURATION
        return max(round(available_time / (2 * self.chews), 2), 0)

    # --- Slider callbacks ---
    def _on_timer_scale(self, v):
        if self.state != STATE_SETUP:
            return
        minutes = int(float(v))
        self.total_seconds = minutes * 60
        h = self.total_seconds // 3600
        m = (self.total_seconds % 3600) // 60
        self.timer_value_label.config(text=f"Timer {h:02}:{m:02}")

    def _on_chews_scale(self, v):
        if self.state != STATE_SETUP:
            return
        self.chews = int(float(v))
        self.chews_value_label.config(text=f"Chews: {self.chews}")
        self.hold_time_label.config(text=f"Hold time per chew: {self._calculate_hold_time():.2f}s")

    def _on_fluid_scale(self, v):
        if self.state != STATE_SETUP:
            return
        self.fluid_cycle = int(float(v))
        self.fluid_value_label.config(text=f"Fluid Cycle: {self.fluid_cycle}s")
        self.hold_time_label.config(text=f"Hold time per chew: {self._calculate_hold_time():.2f}s")

    # --- UI update ---
    def _update_ui_from_values(self):
        secs = int(self.elapsed)
        h = secs // 3600
        m = (secs % 3600) // 60
        s = secs % 60
        self.time_display.config(text=f"{h:02}:{m:02}:{s:02}")
        self.count_display.config(text=str(self.cycle_count))
        self.state_label.config(text=f"State: {self.state.upper()}")
        self.motor_label.config(text="● Motor Active" if self.motor_active else "○ Idle",
                                fg="green" if self.motor_active else "gray")
        self.root.after(200, self._update_ui_from_values)

    # --- External buttons ---
    def _external_buttons_loop(self):
        while True:
            if GPIO.input(STOP_PIN) == GPIO.LOW:
                self.stop(True)
            if GPIO.input(GO_PIN) == GPIO.LOW:
                self.start()
            if GPIO.input(PAUSE_PIN) == GPIO.LOW:
                self.pause()
            time.sleep(0.01)

    # --- Control methods ---
    def start(self):
        if self.state == STATE_SETUP:
            self.elapsed = 0
            self.cycle_count = 0
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
        # Stop motor hold PWM when going to setup
        pwm_in1.ChangeDutyCycle(0)
        pwm_in2.ChangeDutyCycle(0)
        if reset:
            self.elapsed = 0
            self.cycle_count = 0

    # --- Run motor helper using PWM on IN1/IN2 with holding torque ---
    def _spin_motor(self, direction, speed, duration, hold=False):
        self.motor_active = True
        end_time = time.time() + duration

        if direction == 'down':
            pwm_in1.ChangeDutyCycle(speed)
            pwm_in2.ChangeDutyCycle(0)
            while time.time() < end_time and self._run_flag.is_set():
                time.sleep(0.05)
            pwm_in1.ChangeDutyCycle(0)
            pwm_in2.ChangeDutyCycle(0)

        elif direction == 'up':
            pwm_in1.ChangeDutyCycle(0)
            pwm_in2.ChangeDutyCycle(speed)
            while time.time() < end_time and self._run_flag.is_set():
                time.sleep(0.05)
            # Maintain holding torque if running or paused
            if hold and self.state in [STATE_RUNNING, STATE_PAUSED]:
                pwm_in1.ChangeDutyCycle(0)
                pwm_in2.ChangeDutyCycle(HOLD_PWM)
            else:
                pwm_in1.ChangeDutyCycle(0)
                pwm_in2.ChangeDutyCycle(0)

        self.motor_active = False

    # --- Main loop implementing cycle-by-cycle, finishing last cycle if timer reached ---
    def _run_loop(self):
        start_time = time.time() - self.elapsed
        next_cycle_time = start_time
        sequence = [[1,0,1,0],[0,1,1,0],[0,1,0,1],[1,0,0,1]]
        rev_sequence = [[1,0,0,1],[0,1,0,1],[0,1,1,0],[1,0,1,0]]  # Pump 2 forward
        step_delay = 0.001

        while self._run_flag.is_set():
            if self._pause_flag.is_set():
                time.sleep(0.05)
                continue

            now = time.time()
            self.elapsed = now - start_time

            # Stop if elapsed time exceeds total_seconds
            if self.elapsed >= self.total_seconds:
                break

            if now >= next_cycle_time:
                # --- INITIAL_WAIT ---
                wait_end = now + INITIAL_WAIT
                while time.time() < wait_end and self._run_flag.is_set():
                    time.sleep(0.05)

                # --- Pump 1 ---
                GPIO.output(ENA, 1)
                GPIO.output(ENB, 1)
                pump_end = time.time() + PUMP_RUN_TIME
                step_index = 0
                while time.time() < pump_end and self._run_flag.is_set():
                    step = sequence[step_index]
                    GPIO.output(IN1, step[0])
                    GPIO.output(IN2, step[1])
                    GPIO.output(IN3, step[2])
                    GPIO.output(IN4, step[3])
                    step_index = (step_index + 1) % len(sequence)
                    time.sleep(step_delay)
                GPIO.output(ENA, 0)
                GPIO.output(ENB, 0)
                for pin in [IN1, IN2, IN3, IN4]:
                    GPIO.output(pin, 0)

                # --- Chewing sequence (motor down/up) ---
                for chew in range(self.chews):
                    self._spin_motor('down', MOTOR_SPEED_DOWN, MOTOR_DOWN_DURATION)
                    hold_time = self._calculate_hold_time()
                    hold_end = time.time() + hold_time
                    while time.time() < hold_end and self._run_flag.is_set():
                        time.sleep(0.05)

                    self._spin_motor('up', MOTOR_SPEED_UP, MOTOR_UP_DURATION, hold=True)
                    hold_end = time.time() + hold_time
                    while time.time() < hold_end and self._run_flag.is_set():
                        time.sleep(0.05)

                # --- Pump 2 ---
                GPIO.output(P2_ENA, 1)
                GPIO.output(P2_ENB, 1)
                pump_end = time.time() + PUMP_RUN_TIME
                step_index = 0
                while time.time() < pump_end and self._run_flag.is_set():
                    step = rev_sequence[step_index]
                    GPIO.output(P2_IN1, step[0])
                    GPIO.output(P2_IN2, step[1])
                    GPIO.output(P2_IN3, step[2])
                    GPIO.output(P2_IN4, step[3])
                    step_index = (step_index + 1) % len(rev_sequence)
                    time.sleep(step_delay)
                GPIO.output(P2_ENA, 0)
                GPIO.output(P2_ENB, 0)
                for pin in [P2_IN1, P2_IN2, P2_IN3, P2_IN4]:
                    GPIO.output(pin, 0)

                # --- Increment cycle count ---
                self.cycle_count += 1

                # --- Prepare for next cycle ---
                next_cycle_time += self.fluid_cycle

            time.sleep(0.05)

        # After finishing loop, stop safely
        self._run_flag.clear()
        self.state = STATE_SETUP
        pwm_in1.ChangeDutyCycle(0)
        pwm_in2.ChangeDutyCycle(0)

    # --- Close handler ---
    def _on_close(self):
        self._run_flag.clear()
        self._pause_flag.clear()
        pwm_in1.stop()
        pwm_in2.stop()
        GPIO.cleanup()
        self.root.destroy()

# --- Main ---
if __name__ == "__main__":
    root = tk.Tk()
    app = DeviceUI(root)
    root.mainloop()
