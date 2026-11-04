import time
import movement
import led
from machine import Pin
import linefollowing
import states
import mapping
import navigation
import grabber

#if the program was stopped while driving, make sure everything is off
movement.stop()
led.led_off()

#set button pin to be an input, the pin pull up mean the button is high normally
button = Pin(27, Pin.IN, Pin.PULL_UP)

running = False #keeps track of if robot is on or off, start with off
previous_state = 1 #keeps track of the button state, start with high because button is not pressed

#1 = not pressed and 0 = pressed
#set loop that runs always using while True:
#set starting state of robot
state = "collecting"

while True:
    #set that current_state is equal to the button value
    current_state = button.value()
    
    #detect a new press: released (1) to pressed (0)
    if previous_state == 1 and current_state == 0:
        #change running to the opposite of what it was before
        #toggle if on or off based on if button was clicked
        running = not running
        led.pole_leds_off()
        grabber.reset_grabber()
        led.led_off()          #after the grabber moves, so amber is definitely off
        
        if not running:
            #if running and button pressed, then not running
            movement.stop()


        else:
            #if robot is on, then set robot to be at start node facing north
            #should be in idle state at start
            navigation.current_node = 0
            navigation.heading = "E"
            navigation.stage = "idle"

        #clear what the target destinations are
            navigation.target = None
            navigation.next_node = None
            navigation.wanted = None

        #clear any interrupted turn, ie. reset everything to start
            linefollowing.turning = None
            linefollowing.turn_stage = None
            linefollowing.turn_started = 0
            linefollowing.lost_since = None

        #clear what the states remember from any earlier run
            states.step = None
            states.next_bay = 0
            states.occupied_slots = []
            states.delivered_count = 0

        #restart
            state = "collecting"

        time.sleep(0.2)  #debounce

    #update previous_state to be equal to current_state for the next loop
    previous_state = current_state

    #set condition for if running
    if running:
        led.update_flash()  #update the led flash while running

        #update journery requested, depending on the state we are in 
        navigation.update()

        #make it stop if theres an error
        if navigation.stage == "error":
            movement.stop()
            led.led_off()
            running=False

        else:
         #this sets the order of states that needs to be followed, provided it has completed prior state
            if state == "collecting":
                result = states.collecting()

                #got a package - find a slot for it
                if result is True:
                    state = "checking_spaces"

                #bay was empty - stay in "collecting", so it goes to the next bay
                elif result == "empty":
                    state = "collecting"

            elif state == "checking_spaces":
                if states.checking_spaces():
                    state = "delivering"

                #if no availble slots in this rack
                else:
                    movement.stop()
                    led.led_off()
                    running = False

            elif state == "delivering":
                #keep track if package was delivered
                result = states.delivering()
                
                if result == "delivered":
                    #delivered enough boxes? go back to the start, otherwise collect the next one
                    if states.delivered_count >= states.boxes_to_deliver:
                        state = "return_start"
                    else:
                        state = "collecting"


                elif result == "occupied":
            # find another slot in the same rack
                    state = "checking_spaces"

                elif result == "error":
                    movement.stop()
                    led.led_off()
                    running = False

            elif state == "return_start":
                if states.return_start():
                    movement.stop()
                    led.led_off()
                    state = "finished"
                    running = False

            else:
                movement.stop()
                running = False
                led.led_off()

    time.sleep_ms(10)     #small pause between updates