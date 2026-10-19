
import time
import movement
import linesensor
import led
from machine import Pin


#set a power pin for sensors and led
power = Pin(28, Pin.OUT)

#BUTTON CODE
#set button pin to be an input, the pin pull up mean the button is high normally, and when pressed it will be 
button = Pin(15, Pin.IN, Pin.PULL_UP)

#running variable to keep track of if robot is on or off, start with off
running = False

#previous state variable to keep track of the button state, start with high because button is not pressed
previous_state = 1

#the button value is 1 when not pressed, and 0 when pressed
#set loop that runs always using while True:

######NORMAL CODE
#while True:
    #set that current_state is equal to the button value
#    current_state = button.value()
    
    # detect a new press: released (1) to pressed (0)
#    if previous_state == 1 and current_state == 0:
#        # change running to the opposite of what it was before
#        running = not running

        #set conditions for what happens if not running, versus running
#        if not running:
#            led.led_off()
#            movement.stop()
#        else:
#            led.flash_led(1, 0.1) 

    #update previous_state to be equal to current_state for the next loop
#    previous_state = current_state

    #set condition for if running
#    if running:
#        led.flash_led(1, 0.1)  # flash LED many times with a 0.1 second interval
#        linesensor.follow_line()


#######FOR THE LINE TEST
while True:
    #set that current_state is equal to the button value
    current_state = button.value()
    
    # detect a new press: released (1) to pressed (0)
    if previous_state == 1 and current_state == 0:
        # change running to the opposite of what it was before
        running = not running

        #set conditions for what happens if not running, versus running
        if running:
            linesensor.reset_route()  #start from the first instruction
            print("Starting route")
        else:
            movement.stop()
            led.led_off()
            print("Stopped by button")

        time.sleep(0.2)  #debounce delay

    #update previous_state to be equal to current_state for the next loop
    previous_state = current_state

    #set condition for if running
    if running:
        led.update_flash()  #flash LED without blocking the rest of the code
        keep_going = linesensor.follow_line()  #one step of the line following code, returns True if we should keep going, False if we have finished the route
        
        if not keep_going:
            running = False
            movement.stop()
            led.led_off()
            time.sleep(0.01) #short pause so the loop runs about 100 times per second, which is a good speed for the line following code to run at