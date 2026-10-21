#grabber - picks up and puts down the package
#servo   = the claw (opens / closes to grip the package)
#actuator = the lift (moves the claw down / up)
#tune the numbers below on the real robot

from machine import Pin, PWM
import led

#---------- actuator = the lift (motor driver 1 = GP0 direction, GP1 speed) ----------
ACT_SPEED = 100           # 0-100
DOWN = 0                  # direction value that LOWERS the claw (swap to 1 if it goes up instead)
LIFT_TIME_MS = 2000       # how long the actuator takes to go fully down or up

#---------- servo = the claw ----------
OPEN_ANGLE = 0            # claw open
CLOSED_ANGLE = 90         # claw gripping
SERVO_TIME_MS = 500       # time to let the servo get there

#set up the actuator
act_dir = Pin(0, Pin.OUT) # actuator direction on GP0
act_pwm = PWM(Pin(1))  # actuator speed on GP1
act_pwm.freq(1000)
act_pwm.duty_u16(0)

#set up the servo
servo = PWM(Pin(16))  # servo on GP16
servo.freq(50)            # servos need 50 Hz


def lift(direction):
    #run the actuator one way for LIFT_TIME_MS, then stop
    #(it can't tell where it is, so it's timed)
    act_dir.value(direction)
    act_pwm.duty_u16(int(65535 * ACT_SPEED / 100))
    led.wait_ms(LIFT_TIME_MS)
    act_pwm.duty_u16(0)


def lower():
    lift(DOWN)


def raise_up():
    lift(1 - DOWN)            # the opposite direction (1 - 0 = 1, 1 - 1 = 0)


def claw(angle):
    #move the servo to an angle (same maths as the course's test_servo.py: 0 deg = 1638, 270 deg = 8192)
    servo.duty_u16(int(1638 + (angle / 270) * (8192 - 1638)))
    led.wait_ms(SERVO_TIME_MS)


def grab():
    #pick up the package
    claw(OPEN_ANGLE)          # make sure the claw is open
    lower()                   # claw down around the package
    claw(CLOSED_ANGLE)        # grip it
    raise_up()                # lift it off the table


def release():
    #put the package down
    lower()                   # lower it onto the rack
    claw(OPEN_ANGLE)          # let go
    raise_up()                # lift the empty claw clear