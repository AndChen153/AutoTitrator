import RPi.GPIO as GPIO
import time
Alkalinity_valve = 35
Hardness_valve = 37
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(Alkalinity_valve, GPIO.OUT, initial=True)
GPIO.setup(Hardness_valve, GPIO.OUT, initial=True)
# End of GPIO setup------------------------------------------------

def valve_control(valve, mode):
	GPIO.setup(Alkalinity_valve, GPIO.OUT, initial=True)
	GPIO.setup(Hardness_valve, GPIO.OUT,initial=True)
	if valve == 'Hardness':
		if mode == 'ON':
			GPIO.output(Hardness_valve, False)
		elif mode == 'OFF':
			GPIO.output(Hardness_valve, True)
		else:
			print 'ERROR Hardness valve Mode not selected'          
	elif valve == 'Alkalinity':
		if mode == 'ON':
			GPIO.output(Alkalinity_valve, False)
		elif mode == 'OFF':
			GPIO.output(Alkalinity_valve, True)
		else:
			print 'ERROR Alkalinity valve Mode not selected'
	else:
		print 'ERROR Valve type not selected'

valve_control('Hardness', 'ON')

