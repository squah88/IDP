from machine import Pin
import time


led = Pin(20, Pin.OUT)  # Assign GPIO 14 to the LED

def led_on():
    led.value(1)  # turn on the LED

def led_off():
    led.value(0)  # turn off the LED

#led that toggles state on and off, to be used in a loop
#checks if 250 ms has passed since last toggle, if so, toggles led and updates last_toggle

last_toggle = 0
def update_flash():
    global last_toggle    #global ensures we can access the variable outside of this function
    now = time.ticks_ms()   #current time in milliseconds
    if time.ticks_diff(now, last_toggle) >= 250:  #has 250 ms passed?
        led.toggle()        #flips on or off
        last_toggle = now   #remember when we flipped

#function to wait for a certain number of ms but also update the led flash so it doesn't stop flashing
#basically a better version of time.sleep
#when fucntion called, starts a timer
#finds difference between current time and start time, if difference is less than ms, keeps looping
#ms is the amount we want to wait for
#difference contiunes increasing until it is greater than ms, then function ends and program continues
def wait_ms(ms):
    #wait for a certain number of milliseconds but also update the led flash so it doesn't stop flashing
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < ms:
        update_flash()  #update the led flash while waiting
        time.sleep_ms(10)  #sleep for a short time to avoid busy waiting
