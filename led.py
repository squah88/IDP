#amber LED flashes while the robot is running
#red LED flashes when the package is north (goes to a top rack)
#green LED flashes when the package is south (goes to a bottom rack)

from machine import Pin
import time

#pins
amber_led = Pin(8, Pin.OUT)
red_led = Pin(9, Pin.OUT)
green_led = Pin(10, Pin.OUT)

#amber led
def led_on():
    amber_led.value(1)  #turn on the amber LED

def led_off():
    amber_led.value(0)  #turn off the amber LED

#checks if 250 ms has passed since last toggle, if so, toggles led and updates last_toggle
last_toggle = 0
def update_flash():
    global last_toggle      #global ensures we can access the variable outside of this function
    now = time.ticks_ms()   #current time in milliseconds
    if time.ticks_diff(now, last_toggle) >= 250:  #has 250 ms passed?
        amber_led.toggle()  #flips on or off
        last_toggle = now   #remember when we flipped

def wait_ms(ms):
    #better version of time.sleep()
    #wait for a certain number of milliseconds but also update the led flash so it doesn't stop flashing
    start = time.ticks_ms()
    #while loop that keeps checking the difference between current time and start time
    while time.ticks_diff(time.ticks_ms(), start) < ms:
        update_flash()  #update the led flash while waiting
        time.sleep_ms(10)  #sleep for a short time to avoid using too much computing power

#for north go red
def show_north():
    # red on, green off
    red_led.value(1)
    green_led.value(0)

#south go green
def show_south():
    # green on, red off
    red_led.value(0)
    green_led.value(1)

#turn off both pole leds
def pole_leds_off():
    red_led.value(0)
    green_led.value(0)

