#amber LED flashes while the robot is running
#red LED on when the package is north (goes to a top rack)
#green LED on when the package is south (goes to a bottom rack)

from machine import Pin
import time

#pins
amber_led = Pin(8, Pin.OUT)
red_led = Pin(9, Pin.OUT)
green_led = Pin(10, Pin.OUT)

def led_on():
    amber_led.value(1)  #turn on the amber LED

def led_off():
    amber_led.value(0)  #turn off the amber LED

last_toggle = 0         #when the amber LED was last toggled

def update_flash():
    #if 250 ms has passed since last toggle, toggle led again
    global last_toggle
    now = time.ticks_ms()
    if time.ticks_diff(now, last_toggle) >= 250:
        amber_led.toggle()
        last_toggle = now

def wait_ms(ms):
    #better version of time.sleep() as it keeps the amber LED flashing while waiting
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < ms:
        update_flash()
        time.sleep_ms(10)

def show_north():
    #for north show red
    red_led.value(1)
    green_led.value(0)

def show_south():
    #for south show green
    red_led.value(0)
    green_led.value(1)

def pole_leds_off():
    #turn off pole LEDs
    red_led.value(0)
    green_led.value(0)