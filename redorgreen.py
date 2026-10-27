#code for the red and green lights
from machine import Pin

#create pin outs
red_led = Pin(18, Pin.OUT)
green_led = Pin(19, Pin.OUT)

#for north go red
def show_north():
    # red on, green off
    red_led.value(1)
    green_led.value(0)

#south go green
def show_south():
    # Green on, red off
    red_led.value(0)
    green_led.value(1)

#turn off leds
def pole_leds_off():
    # Turn both off
    red_led.value(0)
    green_led.value(0)