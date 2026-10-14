from machine import Pin
import time

led = Pin(14, Pin.OUT)  # Assign GPIO 14 to the LED
button = Pin(6, Pin.IN, Pin.PULL_DOWN)  # Assign GPIO 6 to the button with pull-up resistor



runtime = 5000
while runtime > 0:
    led.value(button.value())  # Set LED state based on button state
    time.sleep(0.1)  # Add a small delay to debounce the button
    print("Button state:", button.value())  # Print the button state for debugging
    runtime -= 1  # Decrease the runtime counter


led.value(0)  # Turn off the LED after the loop ends
print("Runtime ended. LED turned off.")  # Print a message indicating the end of the runtime
