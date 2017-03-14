# Betabot
# Code: https://github.com/tjacobs/betabot
# by Tom Jacobs

# Neural Network: LSTM.
# 

# Inputs are:
# IMU X, Y angles (2) ( 0 - 1, 0.5, 0.5 is flat level )
# CurrentAngles (8) ( 0 - 1, from 20 to 160 degrees, 0 being knees all straight up in the air, flipped for backwards motors )
# Resistances (8) ( 0 - 1, amount of resistance each motor is currently experiencing )
# MotorSpeeds (8) ( 0 - 1, current motor speeds from calculated from PID loop from output params )
# Sin(t) (1) ( 0 - 1, sin of t, where t is increasing with time )
# Cos(t) (1) ( 0 - 1, cos of t, where t is increasing with time )

# Outputs are:
# TargetAngles (8) ( 0 - 1, from 20 to 160 degrees. Flipped for every backwards motor, so 0 is always up. )
# P_rate (8) (0 - 1, from off to max_p_rate) (add later, fix to resonable default to start with)

# How it works
# Robot starts standing, all legs almost knees sraight up.
# CurrentAngles = [ 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1 ]

# 1. Train the network to stay like that.
# Loss function = difference of targetAngles to [ 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1 ]



from ams import AMS
from time import sleep
import time
import math
import array
#import tensorflow as tf

hit = False
armTime = time.time()*1000

n_legs = 1
n_params = 6

def clamp(n, smallest, largest): return max(smallest, min(n, largest))

#~ sess = tf.Session()
#~ def network(x):
#~ 
	#~ # Fully Connected.
    #~ fc_W  = tf.Variable(tf.truncated_normal(shape=(n_legs, n_params), mean = 0, stddev = 0.1))
    #~ fc_b  = tf.Variable(tf.zeros(n_params))
    #~ output = tf.matmul(x, fc_W) + fc_b
    #~ return tf.sigmoid( output )


# Go
test = 0.0
testa = 0.0
def main():
	try:
		# Talk to motor angle sensors via I2C
		sensors = AMS()
		connected = sensors.connect(1)
		if connected < 0:
			print( "Warning: Can not read all motor sensors" )

		# Talk to motor controller via serial UART SBUS
		sbus = openSBUS()

		# What speed is each motor at, and one step back, two steps back?
		motorSpeeds = [0] * 8
		lastMotorSpeeds = [0] * 8
		lastLastMotorSpeeds = [0] * 8

		# Last loop values
		lastAngles = [0] * 8
		lastCheck = time.time()*1000

		#~ x_in = [[1]]
		#~ x = tf.placeholder(tf.float32, (1, 1))
		#~ input = network(x)
		#~ sess.run(tf.global_variables_initializer())

		# Loop
		global hit, testa
		while True:
			
			# Arm after a second
			arm = 500
			if time.time()*1000 > armTime + 1000:
				arm = 1000
    
			#~ x_in[0][0] = x_in[0][0] + 0.1
		    #~ # What does our brain say to do?
			#~ output = sess.run(input, feed_dict={x:x_in})
			#~ print( output )
			testa = testa + 1.0
			
			height = 0.9# math.sin(testa/50.0) /2  + 0.5

			# Slow if leg hit something			
			#if hit == True:
		#		height = 1
			
			speed = 5.0
			leftLeg = {}
			leftLeg['a_offset'] =     clamp( height, 0.0, 1.0) * 5000.0
			leftLeg['a_timeOffset'] = clamp( 0,      0.0, 1.0) * 1.0
			leftLeg['a_scale'] =      clamp( 0.8,      0.0, 1.0) * 5000.0
			leftLeg['b_offset'] =     clamp( height, 0.0, 1.0) * 5000.0
			leftLeg['b_timeOffset'] = clamp( 0.5,      0.0, 1.0) * 1.0
			leftLeg['b_scale'] =      clamp( 0.8,      0.0, 1.0) * 5000.0
			rightLeg = {}
			rightLeg['a_offset'] =    clamp( height, 0.0, 1.0) * 5000.0
			rightLeg['a_timeOffset'] =clamp( 0,      0.0, 1.0) * 1.0
			rightLeg['a_scale'] =     clamp( 0.8,      0.0, 1.0) * 5000.0
			rightLeg['b_offset'] =    clamp( height, 0.0, 1.0) * 5000.0
			rightLeg['b_timeOffset'] =clamp( 0.5,      0.0, 1.0) * 1.0
			rightLeg['b_scale'] =     clamp( 0.1,      0.0, 1.0) * 5000.0

			# Main loop
			targetAngles = updateTargetAngles(speed, leftLeg, rightLeg)
			currentAngles = readCurrentAngles(sensors)
			Ps = calculatePs(currentAngles, targetAngles)
			motorSpeeds = clampMotorSpeeds(Ps)
			print( currentAngles[0] / 100, currentAngles[1] / 100, currentAngles[2] / 100, currentAngles[3]/100 )
			
			motorSpeeds[2] = 0
			#motorSpeeds[3] = 0
			
			# Calculate how much the motor has moved in the last 100ms
			if time.time()*1000 > lastCheck + 100:
				lastCheck = time.time()*1000
				moved = currentAngles[0] - lastAngles[0]
				if( moved > 16384 - 5000 ):
					moved = moved - 16384
				if( moved < -(16384 - 5000) ):
					moved = moved + 16384
				percentageMoved = abs( moved / 30.0 )				
				percentagePower = abs(lastLastMotorSpeeds[0])
				
				# Record values for next check
				lastAngles[0] = currentAngles[0]
				lastLastMotorSpeeds[0] = lastMotorSpeeds[0]
				lastMotorSpeeds[0] = motorSpeeds[0]

				# Did we hit something?
				percentageExpectedMoved = percentagePower
				#print "MOVED " + str( int( percentageMoved)) + "   POWER " + str( int(percentageExpectedMoved))
#				if( percentagePower > 30 and motorSpeeds[0] > 30 and percentageMoved < percentageExpectedMoved * 0.6 and hit == False):
#					print( "OW!" )
#					hit = True

			# Move
			sendMotorSpeeds(sbus, motorSpeeds, arm)
				

	except:
		
	 	print( "DONE" )
	 	arm = 500
	 	sendMotorSpeeds(sbus, motorSpeeds, arm)
	 	sleep(0.5)
	 	sendMotorSpeeds(sbus, motorSpeeds, arm)

# -------------
# Functions

t = 0
targetAngles = [0] * 8
def updateTargetAngles( speed, left, right ):
	global targetAngles, t, hit
	targetAngles[0] = int( math.sin( speed * t * math.pi / 500.0 + (left['a_timeOffset']*math.pi)) * left['a_scale'] + 3000 + left['a_offset'] )
	targetAngles[1] = int( math.sin( speed * t * math.pi / 500.0 + (left['b_timeOffset']*math.pi)) * left['b_scale'] + 7000 + left['b_offset'] )
	targetAngles[2] = int( math.sin( speed * t * math.pi / 500.0 + (right['a_timeOffset']*math.pi)) * right['a_scale'] + 1000 + right['a_offset'] )
	targetAngles[3] = int( math.sin( speed * t * math.pi / 500.0 + (right['b_timeOffset']*math.pi)) * right['b_scale'] + 7000 + right['b_offset'] )
	t += 1
#	if( t > 500 * 2 / speed ):
#		t = 0
#		if hit == True:
#			hit = False
#			print "OK again"
	return targetAngles

def readCurrentAngles(sensors):
	currentAngles = [0] * 8
	try:
		for i in range(4):
			currentAngles[i] = sensors.getAngle(i+1)
	except:
		return currentAngles
	return currentAngles

def clampMotorSpeeds( motorSpeeds ):
	minSpeed = -100
	maxSpeed = 100
	for i in range(len(motorSpeeds)):
		motorSpeeds[i] = max(min(motorSpeeds[i], maxSpeed), minSpeed)
	return motorSpeeds

def calculatePs( currentAngles, targetAngles ):
	Ps = [0] * len( targetAngles )
	P_rate = 0.05
	for i in range(len(targetAngles)):
		Ps[i] = P_rate * (targetAngles[i] - currentAngles[i])
	return Ps

def sendMotorSpeeds( sbus, motorSpeedsIn, arm ):
	motorSpeeds = [0] * 8
	for i in range(len(motorSpeedsIn)):
		motorSpeeds[i] = int(motorSpeedsIn[i])
	middle = 995
	sendSBUSPacket( sbus, [motorSpeeds[0]*6+middle, motorSpeeds[1]*6+middle, motorSpeeds[2]*6+middle, motorSpeeds[3]*6+middle, arm] )

# ----------
# SBUS

def openSBUS():
	try:
		import serial
		return serial.Serial(
			port='/dev/serial0',
			baudrate = 115200, # Must rebuild and flash betaflight to listen at this rate, not 100,000 as per normal SBUS.
			parity=serial.PARITY_EVEN,
			stopbits=serial.STOPBITS_TWO,
			bytesize=serial.EIGHTBITS,
			timeout=10)
	except:
		print( "Serial not available" )


def sendSBUSPacket(sbus, channelValues):

	# 16 blank channels, copy as many channels as given
	channels = [100]*16
	for j in range(len(channelValues)):
		channels[j] = int(channelValues[j])

	# SBUS start byte
	sbus_data = [0]*25
	sbus_data[0] = 0x0F

	# SBUS channel bytes. 11 bits per channel.
	ch = 0
	bit_in_channel = 0
	byte_in_sbus = 1
	bit_in_sbus = 0
   
	# For 16ch * 11bits = 176 bits 
	for i in range(1, 176):
		if channels[ch] & (1<<bit_in_channel):
			sbus_data[byte_in_sbus] |= (1<<bit_in_sbus)
		bit_in_sbus = bit_in_sbus + 1
		bit_in_channel = bit_in_channel + 1
		if bit_in_sbus == 8:
			bit_in_sbus = 0
			byte_in_sbus = byte_in_sbus + 1
		if bit_in_channel == 11:
			bit_in_channel = 0
			ch = ch + 1

	# Send
	try:
		sbus.write( array.array('B', sbus_data).tostring() )
	except:
		pass


if __name__=="__main__":
   main()
