import RPi.GPIO as GPIO
import time

#Pins
stop = 16
go = 1
pause = 14
GPIO.setmode(GPIO.BCM)
GPIO.setup(stop, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(go, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pause, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    while True:
        stop_state = GPIO.input(stop)
        go_state = GPIO.input(go)
        pause_state = GPIO.input(pause)
        
        if stop_state == GPIO.LOW:
            print("Stop button pressed")
        if go_state == GPIO.LOW:
            print("Go button pressed")
        if pause_state == GPIO.LOW:
            print("Pause button pressed")
        
        time.sleep(0.01)
except KeyboardInterrupt:
    GPIO.cleanup()
    print("Program terminated.")
