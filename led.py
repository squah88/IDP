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

#runtime = 5000
#while runtime > 0:
 #   led.value(button.value())  # Set LED state based on button state
  #  time.sleep(0.1)  # Add a small delay to debounce the button
   # print("Button state:", button.value())  # Print the button state for debugging
    #runtime -= 1  # Decrease the runtime counter

#led.value(0)  # Turn off the LED after the loop ends
#print("Runtime ended. LED turned off.")  # Print a message indicating the end of the runtime


