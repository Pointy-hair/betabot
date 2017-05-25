# Betabot
# https://github.com/tjacobs/betabot
# by Tom Jacobs

print( "Starting Betabot." )

# Imports
import sys
import time
import math
import array
import datetime
import functions
import motors as motorsModule
import walk
import sensors

# What shall we enable?
ENABLE_KEYS 		= True
ENABLE_MOUSE 		= False
ENABLE_BRAIN 		= False
ENABLE_SIMULATOR 	= False

# Import Betabot parts
keys 		= None
mouse 		= None
brain 		= None
simulator 	= None
if ENABLE_KEYS:
	import keys
if ENABLE_MOUSE:
	import mouse
if ENABLE_BRAIN:
	import brain
if ENABLE_SIMULATOR:
	sys.path.append( 'simulator' )
	import simulator

# Go
def main():
	# Flush output for file logging
	sys.stdout.flush()

	# Init motor angle sensors via I2C
	magneticSensors = sensors.AMS()
	magneticSensors.connect(1)
	
	# Init motors via USB
	motorsModule.initMotors()
	motors = [0.0] * 9 # Motor outputs 1 to 8, ignore 0
	
	# Init balance trim
	trim = 0.0

	# Read initial angles
	offsetPitch = motorsModule.readIMU()
	currentAngles = functions.readCurrentAngles(magneticSensors)
	offsetAngle = currentAngles[1]
	
	# Loop
	while not keys or not keys.esc_key_pressed:

		# Read current IMU accelerometer values to see which way we're leaning
		pitch = motorsModule.readIMU()
		
		# Update from keyboard
		if( keys ):
			if( keys.up_key_pressed == True ):
				trim += 1
			if( keys.down_key_pressed == True ):
				trim -= 1

		# Read current angles of motors
		currentAngles = functions.readCurrentAngles(magneticSensors)
		
		# Compensate for the angle seen at startup
#		currentAngles[1] += offsetAngle
#		currentAngles[3] += offsetAngle

		# Figure out what our angles should be now to walk
		targetAngles = walk.updateTargetAngles(4.0)

		# Compensate for our current body angle to always stand up straight
		#targetAngles[1] += pitch

		# Allow ourselves to lean forward back manually
		#targetAngles[3] += trim

		# Move mouse up, raise up
		#targetAngles[1] += 255 #mouse_y/3 # Right hip goes CW
		#targetAngles[2] += mouse_y/3 # Left hip goes CW
		#targetAngles[3] += 280 #mouse_x/3 # Right knee goes CCW
		#targetAngles[4] -= mouse_y/3 # Left knee goes CCW
		#targetAngles[5] -= mouse_y/3 # Right foot goes CCW
		#targetAngles[6] -= mouse_y/3 # Left foot goes CCW

		# Restrict movement. Hip and knee should only ever try to go 90 degrees
		targetAngles[1] = functions.clamp(targetAngles[1], -100, 150) #210, 300)
		targetAngles[2] = functions.clamp(targetAngles[2], -100, 150) #210, 300)
		targetAngles[3] = functions.clamp(targetAngles[3], -100, 100)
		targetAngles[4] = functions.clamp(targetAngles[4], -100, 100)
		targetAngles[5] = functions.clamp(targetAngles[5], -100, 100)
		targetAngles[6] = functions.clamp(targetAngles[6], -100, 100)

		# Set servo angles directly
		rightKneeServoAngle = targetAngles[3]
		leftKneeServoAngle = targetAngles[4]
		rightFootServoAngle = targetAngles[5]
		leftFootServoAngle = targetAngles[6]

		# Run our movement controller to see how fast we should set our motor speeds to get to targets
		movement = walk.calculateMovement(currentAngles, targetAngles)

		if movement[1] > 3:
			movement[1] = 3
		if movement[2] < -3:
			movement[2] = -3

		# Send motor speeds
		motors[1] = movement[1] 		  # Right hip
		motors[2] = movement[2] 		  # Left hip
		motors[3] = rightKneeServoAngle  # Right knee servo
		motors[4] = leftKneeServoAngle   # Left knee servo
		motors[5] = rightFootServoAngle  # Right foot servo
		motors[6] = leftFootServoAngle   # Left foot servo
		motorsModule.sendMotorCommands(motors, simulator, False, False)
		
		# Display balance, angles, target angles and speeds
		functions.display( "Pitch: %3d. R Hip, R Knee: %3d, %3d, Target: %3d, %3d, Speeds: %3d, %3d" % (pitch, currentAngles[1], currentAngles[2], targetAngles[1], targetAngles[2], motors[1], motors[2] ) )

	# Finish up
	try:
		import RPi.GPIO as GPIO
		GPIO.cleanup()
	except:
		pass

	# Close
	motors[0] = 0
	motors[1] = 0
	motorsModule.sendMotorCommands(motors)
	motorsModule.board.close()

# Go
if __name__=="__main__":
   main()
