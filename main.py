#runs automatically when the pico powers on
#waits for the button to be pressed
#while running, it flashes the amber LED, calls navigation.update() to update the agv's journey, and calls the function for the current state in states.py
#order of states: collecting -> checking_spaces -> delivering -> return_start

import time
import movement
import led
from machine import Pin
import linefollowing
import states
import navigation
import grabber

#if the program was stopped while driving, make sure everything is off
movement.stop()
led.led_off()

#start/stop button on GP27 - PULL_UP means it reads 1 normally and 0 when pressed
button = Pin(27, Pin.IN, Pin.PULL_UP)

running = False         #is the robot on? starts off until the button is pressed
previous_state = 1      #keeps track of the button state, start with high because button is not pressed
state = "collecting"    #the current state of the robot

while True:
    current_state = button.value()
    
    #detect a new press: not pressed (1) to pressed (0)
    if previous_state == 1 and current_state == 0:
        running = not running   #toggle the running state

        #put everything back to the start state
        led.pole_leds_off()
        grabber.reset_grabber()
        led.led_off()
        
        if not running:
            #agv was just turned off
            movement.stop()

        else:
            #robot was just turned on - it starts at node 0 (start box) facing north
            navigation.current_node = 0
            navigation.facing = "N"
            navigation.stage = "idle"

        #clear any old journey data
            navigation.target = None
            navigation.next_node = None
            navigation.wanted = None

        #clear any interrupted turn
            linefollowing.turning = None
            linefollowing.turn_stage = None
            linefollowing.turn_started = 0
            linefollowing.lost_since = None

        #clear what the states remember from any earlier run
            states.step = None
            states.next_bay = 0
            states.occupied_slots = []
            states.delivered_count = 0

        #start from beginning
            state = "collecting"

        time.sleep(0.2)  #debounce

    previous_state = current_state

    if running:
        led.update_flash()  #amber LED flashes while the robot is running

        #update journey
        navigation.update()

        #stop agv if theres an error
        if navigation.stage == "error":
            movement.stop()
            led.led_off()
            running=False

        else:
         #run the current state - each one returns a result telling us when to move to the next state
            if state == "collecting":
                result = states.collecting()

                #got a package - choose a slot for it
                if result is True:
                    state = "checking_spaces"

                #bay was empty - stay in "collecting", so it goes to the next bay
                elif result == "empty":
                    state = "collecting"

            elif state == "checking_spaces":
                if states.checking_spaces():
                    state = "delivering"

                #if no free slots left on this rack level - stop
                else:
                    movement.stop()
                    led.led_off()
                    running = False

            elif state == "delivering":
                result = states.delivering()
                
                if result == "delivered":
                    #delivered enough boxes? go back to the start, otherwise collect the next one
                    if states.delivered_count >= states.boxes_to_deliver:
                        state = "return_start"
                    else:
                        state = "collecting"

                #if the slot was occupied, choose another slot
                elif result == "occupied":
                    state = "checking_spaces"

                elif result == "error":
                    movement.stop()
                    led.led_off()
                    running = False

            elif state == "return_start":
                #back in the start box - stop and finish
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