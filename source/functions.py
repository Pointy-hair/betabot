# -------------
# Betabot functions
import time

def clamp(n, smallest, largest):
	return max(smallest, min(n, largest))

# Read angles from sensors
def readCurrentAngles( sensors ):
	currentAngles = [0] * 4
	try:
		for i in range(len(currentAngles)):
			currentAngles[i] = 360.0 * sensors.getAngle(i+1) / 16384.0
	except:
		return currentAngles
	return currentAngles

# Motor speeds can go from -100 to 100
def clampMotorSpeeds( motorSpeeds ):
	minSpeed = -100
	maxSpeed = 100
	for i in range(len(motorSpeeds)):
		motorSpeeds[i] = clamp(motorSpeeds[i], minSpeed, maxSpeed)
	return motorSpeeds

# Send the motor speeds to the motors
# And enable the motors if any have any speed
motorEnablePin = 18 # Broadcom 18 = pin 12, 6 from the top corner on the outside of the Pi
goTime = 0

def sendMotorSpeeds( sbus, motorSpeedsIn, arm ):
	global goTime
	motorSpeeds = [0] * 4
	
	# Any motor speeds?
	for i in range(len(motorSpeedsIn)):
		motorSpeeds[i] = int(motorSpeedsIn[i])
		if( (i != 2 ) and (motorSpeeds[i] > 1 or motorSpeeds[i] < -1 ) ):
			# Set used time as now
			go = True
			goTime = time.time()*1000
			
	# Motors been on for five seconds unused?
	if time.time()*1000 > goTime + 5000:
		go = False

	# Send
	middle = 992
	sbus.sendSBUSPacket( [motorSpeeds[0]*6+middle, motorSpeeds[1]*6+middle, motorSpeeds[2]*6+middle, motorSpeeds[3]*6+middle, arm] )
	try:
		import RPi.GPIO as GPIO
		global motorEnablePin
		if( go ):
			GPIO.output(motorEnablePin, GPIO.HIGH)
		else:
			GPIO.output(motorEnablePin, GPIO.LOW)
	except:
		pass

