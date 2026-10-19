from machine import Pin
import time


led = Pin(14, Pin.OUT)  # Assign GPIO 14 to the LED

def led_on():
    led.value(1)  # turn on the LED

def led_off():
    led.value(0)  # turn off the LED

def flash_led(times, interval):
    #create a function to flash the led a certain number of times (times) with a certain interval (interval)
    #classic loop to just repeat on and off, with sleep in the middle to create the interval
    for i in range(times):
        led_on()
        time.sleep(interval)
        led_off()
        time.sleep(interval)

#a better way to flash the led is to use a timer so we don't have to wait for the sleep to finish before doing other things
last_toggle = 0
def update_flash():
    global last_toggle    #global ensures we can access the variable outside of this function
    now = time.ticks_ms()   #current time in milliseconds
    if time.ticks_diff(now, last_toggle) >= 250:  #has 250 ms passed?
        led.toggle()        #flips on or off
        last_toggle = now   #remember when we flipped

#function to wait for a certain number of ms but also update the led flash so it doesn't stop flashing
#basically a better version of time.sleep
def wait_ms(ms):
    #wait for a certain number of milliseconds but also update the led flash so it doesn't stop flashing
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < ms:
        update_flash()  #update the led flash while waiting
        time.sleep_ms(10)  #sleep for a short time to avoid busy waiting


#runtime = 5000
#while runtime > 0:
 #   led.value(button.value())  # Set LED state based on button state
  #  time.sleep(0.1)  # Add a small delay to debounce the button
   # print("Button state:", button.value())  # Print the button state for debugging
    #runtime -= 1  # Decrease the runtime counter

#led.value(0)  # Turn off the LED after the loop ends
#print("Runtime ended. LED turned off.")  # Print a message indicating the end of the runtime


