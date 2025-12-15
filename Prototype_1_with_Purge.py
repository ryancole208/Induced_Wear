#Prototype 1 code with purge function
import RPi.GPIO as GPIO
import time
import board
from adafruit_ht16k33.segments import Seg14x4  # Correct library

# --------------------
# Rotary Encoder Setup
# --------------------
CLK = 17  # Pin 11
DT = 25   # Pin 22
SW = 27   # Pin 13

CLK2 = 22 # Pin 15
DT2 = 23 # Pin 16
SW2 = 24 # Pin 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(CLK2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SW2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# --------------------
# Display Setup
# --------------------
i2c = board.I2C()
display = Seg14x4(i2c, address=0x70)
# display.fill(1)  # original code commented out
display.fill(0)  # this is new code by ChatGPT
display.brightness = 0.5  # this is new code by ChatGPT

display_cycles = Seg14x4(i2c, address=0x71)  # this is new code by ChatGPT
display_cycles.fill(0)  # this is new code by ChatGPT
display_cycles.brightness = 0.5  # this is new code by ChatGPT

# --------------------
# Button Setup
# --------------------
stop = 26
go = 16
GPIO.setup(stop, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(go, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# --------------------
# Valve Set Up
# --------------------
VALVE_PIN = 6
GPIO.setup(VALVE_PIN, GPIO.OUT, initial=GPIO.LOW)  # this is new code by ChatGPT
#GPIO.setmode(GPIO.BCM)  # original code commented out
#GPIO.setup(VALVE_PIN, GPIO.OUT, initial=GPIO.LOW)  # original code commented out

# --------------------
# Global Variables
# --------------------
rotary_counter = 0
clk_last_state = GPIO.input(CLK)

rotary_counter2 = 0
clk_last_state2 = GPIO.input(CLK2)
#start_time = time.monotonic()
last_display_update = 0
button_state = 0
global_state = 0
elapsed = 0
stop_state = 0
go_state = 0

valve_cycles = 0  # this is new code by ChatGPT
start_time = 0  # this is new code by ChatGPT
last_valve_close = 0  # this is new code by ChatGPT

purge_mode = False  # this is new code by ChatGPT

# --------------------
# Mapping: ensure encoder 1 => timer, encoder 2 => cycles
# --------------------
# We'll compute timer_input and cycles_input each loop from the physical encoder counters.
# This makes the mapping explicit and easy to change later if you re-wire hardware.
# (No other logic is changed.)
# --------------------


# --------------------
# Functions
# --------------------
def handle_rotary_encoder():
    global clk_last_state, rotary_counter

    clk_state = GPIO.input(CLK)
    dt_state = GPIO.input(DT)

    if clk_state != clk_last_state:
        if dt_state != clk_state:
            rotary_counter += 1
        else:
            rotary_counter -= 1

        if rotary_counter == 40 or rotary_counter == -40:
            rotary_counter = 0
        print(f"Rotary Counter (encoder1): {rotary_counter}")  # this is new code by ChatGPT

    clk_last_state = clk_state

def handle_rotary_encoder2():
    global clk_last_state2, rotary_counter2

    clk_state2 = GPIO.input(CLK2)
    dt_state2 = GPIO.input(DT2)

    if clk_state2 != clk_last_state2:
        if dt_state2 != clk_state2:
            rotary_counter2 += 1
        else:
            rotary_counter2 -= 1

        if rotary_counter2 == 40 or rotary_counter2 == -40:
            rotary_counter2 = 0
        print(f"Rotary Counter2 (encoder2): {rotary_counter2}")  # this is new code by ChatGPT

    clk_last_state2 = clk_state2

def update_timer_display():
    global elapsed
    elapsed = int(time.monotonic() - start_time)
    minutes = elapsed // 60
    seconds = elapsed % 60
    display.print(f"{minutes:02d}{seconds:02d}")
    display.colon = True

def update_cycle_display():
    display_cycles.print(f"{valve_cycles:04d}")  # this is new code by ChatGPT

def stop_press():
    global stop_state
    stop_state = GPIO.input(stop)

def go_press():
    global go_state, global_state, start_time, valve_cycles, last_valve_close  # this is new code by ChatGPT
    go_state = GPIO.input(go)
    if go_state == 0:
        print('Starting Timer')
        start_time = time.monotonic()  # this is new code by ChatGPT
        valve_cycles = 0  # this is new code by ChatGPT
        last_valve_close = start_time  # this is new code by ChatGPT
        global_state = 1

def open_valve():
    GPIO.output(VALVE_PIN, GPIO.HIGH)

def close_valve():
    GPIO.output(VALVE_PIN, GPIO.LOW)

# --------------------
# Main Loop
# --------------------
try:
    print("Rotary encoders running. Rotate and press button to set timer.")
    while True:
        stop_press()
        go_press()
        handle_rotary_encoder()
        handle_rotary_encoder2()

        # map physical encoders to logical inputs (explicit mapping)  # this is new code by ChatGPT
        timer_input = rotary_counter2   # encoder 1 controls the timer  
        cycles_input = rotary_counter # encoder 2 controls the cycles  

        # -------------
        # PURGE MODE (both STOP+GO pressed) - minimal changes, doesn't touch cycle logic
        # -------------
        if GPIO.input(stop) == 0 and GPIO.input(go) == 0:  # both pressed
            if not purge_mode:
                purge_mode = True  # this is new code by ChatGPT
                print("PURGE MODE: ENTER")  # this is new code by ChatGPT
                open_valve()  # this is new code by ChatGPT
                display.print("   P")  # show ___P (P in 4th position)  # this is new code by ChatGPT
                display.colon = False  # this is new code by ChatGPT
                display_cycles.print("URGE")  # show URGE on second display  # this is new code by ChatGPT
            time.sleep(0.05)  # this is new code by ChatGPT
            continue  # this is new code by ChatGPT

        # Exit purge mode when any button is released
        if purge_mode and (GPIO.input(stop) == 1 or GPIO.input(go) == 1):  # this is new code by ChatGPT
            purge_mode = False  # this is new code by ChatGPT
            print("PURGE MODE: EXIT")  # this is new code by ChatGPT
            close_valve()  # this is new code by ChatGPT
            display.fill(0)  # this is new code by ChatGPT
            display_cycles.fill(0)  # this is new code by ChatGPT
            time.sleep(0.2)  # debounce  # this is new code by ChatGPT

        # Normal stop logic
        if stop_state == 0:
            display.fill(0)
            display_cycles.fill(0)
            close_valve()  # this is new code by ChatGPT
            print("Program terminated.")
            global_state = 0
            time.sleep(0.5)
            print("Rotary encoder running. Rotate and press button to set timer.")

        # Main logic when timer is running
        if global_state == 1:
            current_time = time.monotonic()
            elapsed = int(current_time - start_time)

            # --------------------
            # Determine timer duration from encoder 1 via timer_input  # this is new code by ChatGPT
            if timer_input <= -10:  # this is new code by ChatGPT
                timer_target = 120  # seconds  # this is new code by ChatGPT
            elif -10 < timer_input < 10:  # this is new code by ChatGPT
                timer_target = 60  # this is new code by ChatGPT
            else:  # this is new code by ChatGPT
                timer_target = 10  # this is new code by ChatGPT

            # --------------------
            # Determine valve interval from encoder 2 via cycles_input (unchanged behavior)  # this is new code by ChatGPT
            if cycles_input <= -10:  # this is new code by ChatGPT
                valve_interval = 1.0  # this is new code by ChatGPT
            elif -10 < cycles_input < 10:  # this is new code by ChatGPT
                valve_interval = 2.0  # this is new code by ChatGPT
            else:  # this is new code by ChatGPT
                valve_interval = 3.0  # this is new code by ChatGPT

            # --------------------
            # Update displays
            update_timer_display()
            update_cycle_display()

            # --------------------
            # Valve open/close logic (kept exactly as in your working code)
            if elapsed < timer_target:
                valve_phase = int((current_time - start_time) / (valve_interval / 2)) % 2
                if valve_phase == 0:
                    open_valve()
                else:
                    close_valve()
                    if current_time - last_valve_close >= valve_interval:
                        valve_cycles += 1
                        last_valve_close = current_time  # this is new code by ChatGPT
            else:
                # Timer complete
                global_state = 0
                display.fill(0)
                display_cycles.fill(0)
                close_valve()

        time.sleep(0.001)

except KeyboardInterrupt:
    display.fill(0)
    display_cycles.fill(0)
    close_valve()
    GPIO.cleanup()
    print("Program terminated.")
