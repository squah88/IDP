#grabber test - open this file in Thonny and press Run (press Stop first if main.py is running)
#change the numbers below, Run again, and watch - when they look right, copy them into grabber.py

import grabber
import time

#---------- try different angles here ----------
grabber.UP_ANGLE = 0
grabber.DOWN_ANGLE = 90
grabber.OPEN_ANGLE = 0
grabber.CLOSED_ANGLE = 90

#---------- what to test - put a # in front of the lines you DON'T want ----------
print("lift DOWN")
grabber.lift.move_to(grabber.DOWN_ANGLE)
time.sleep(1)

print("lift UP")
grabber.lift.move_to(grabber.UP_ANGLE)
time.sleep(1)

print("arm CLOSED")
grabber.arm.move_to(grabber.CLOSED_ANGLE)
time.sleep(1)

print("arm OPEN")
grabber.arm.move_to(grabber.OPEN_ANGLE)
time.sleep(1)

#once the four angles are right, hold a package under the grabber and test the full thing:
#print("GRAB")
#grabber.grab()
#time.sleep(2)
#print("RELEASE")
#grabber.release()

print("Done")