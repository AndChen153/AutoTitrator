  #!/usr/bin/python
# -*- coding: utf-8 -*-

'''
motor control using arduino
'''

from spidev import SpiDev
import Adafruit_ADS1x15
import Adafruit_AS726x
import RPi.GPIO as GPIO
from Queue import Empty
from multiprocessing import Process, Queue
import time
import datetime as dt
import sys
import os
import io         # used to create file streams
import fcntl      # used to access I2C parameters like addresses
import math
import string     # helps parse strings
import pickle

# GPIO setup-----------------------------------------------
# Motor 1
mot1_step = 11
mot1_Dir = 13
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(mot1_step, GPIO.OUT)
GPIO.setup(mot1_Dir, GPIO.OUT)
GPIO.setup(mot1_Dir, GPIO.HIGH)      # HIGH = inject; LOW = fill
p1_channel =  3
# Motor 2
mot2_step = 16
mot2_Dir = 18
GPIO.setup(mot2_step, GPIO.OUT)
GPIO.setup(mot2_Dir, GPIO.OUT)
GPIO.setup(mot2_Dir, GPIO.HIGH)  
p2_channel = 0


# AMIS 30543 setup and SPI communication --------------------
REG = {
            'WR':  0x00,
            'CR0': 0x01,
            'CR1': 0x02,
            'CR2': 0x03,
            'CR3': 0x09,
            'SR0': 0x04,
            'SR1': 0x05,
            'SR2': 0x06,
            'SR3': 0x07,
            'SR4': 0x0A
            }

CMD = {
        'READ': 0x00,
        'WRITE': 0x80
        }
        
# driver for motor1
spi_1 = SpiDev()
spi_1.open(0, 0)
spi_1.max_speed_hz = 1000000
# driver for motor 2
spi_2 = SpiDev()
spi_2.open(0, 1)
spi_2.max_speed_hz = 1000000
# End of AMIS driver setup---------------------------------------

class dispexeMotors:
  def pump2(volume, direction):
    steps = int((volume + 0.000785) / 0.0000502)
    proc_queue2.put(steps)
    if spi_2.xfer2([CMD['READ'] | REG['CR0'], 0])[1] != 0b10001000:    # compensated half step
      spi_2.writebytes([CMD['WRITE'] | REG['CR0'], 0b10001000])
      
    if spi_2.xfer2([CMD['READ'] | REG['CR2'], 0])[1] != 0b10000000:
      spi_2.writebytes([CMD['WRITE'] | REG['CR2'], 0b10000000])
      
    if direction == 1:		
      valve_control('Alkalinity', 'OFF')									  #direction--> 1 = dispense, 0 = refill/retract, 2 = prime/purge, 
      if spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b01000000:
        spi_2.writebytes([CMD['WRITE'] | REG['CR1'], 0b01000000])
    elif direction == 2:
      valve_control('Alkalinity', 'OFF')	
      if spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b01000000:
        spi_2.writebytes([CMD['WRITE'] | REG['CR1'], 0b01000000])
    else:
      valve_control('Alkalinity', 'ON')	
      if spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b11000000:
        spi_2.writebytes([CMD['WRITE'] | REG['CR1'], 0b11000000])
    start_process_p2()


  def THM_RR(volume, direction):
    steps = int((volume + 0.000785) / 0.0000502)
    p.put(steps)
    if spi_1.xfer2([CMD['READ'] | REG['CR0'], 0])[1] != 0b10001000:    # compensated half step
      spi_1.writebytes([CMD['WRITE'] | REG['CR0'], 0b10001000])
      
    if spi_1.xfer2([CMD['READ'] | REG['CR2'], 0])[1] != 0b10000000:
      spi_1.writebytes([CMD['WRITE'] | REG['CR2'], 0b10000000])
      
    if direction == 1:	
      valve_control('Hardness', 'OFF')											  #direction--> 1 = dispense, 0 = refill/retract, 2 = prime/purge, 
      if spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b01000000:
        spi_1.writebytes([CMD['WRITE'] | REG['CR1'], 0b01000000])
        std_stop()
    elif direction == 2:
      valve_control('Hardness', 'OFF')	
      if spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b01000000:
        spi_1.writebytes([CMD['WRITE'] | REG['CR1'], 0b01000000])
    else:
      valve_control('Hardness', 'ON')	
      if spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b11000000:
        spi_1.writebytes([CMD['WRITE'] | REG['CR1'], 0b11000000])
    start_process()	
    
    
  def Enable_p2(direction, prime):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(mot2_step, GPIO.OUT)
    
    if spi_2.xfer2([CMD['READ'] | REG['CR0'], 0])[1] != 0b10001000:    # compensated half step
      spi_2.writebytes([CMD['WRITE'] | REG['CR0'], 0b10001000])
      
    if spi_2.xfer2([CMD['READ'] | REG['CR2'], 0])[1] != 0b10000000:
      spi_2.writebytes([CMD['WRITE'] | REG['CR2'], 0b10000000])
      
    if direction == 1:
      if spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b01000000:
        spi_2.writebytes([CMD['WRITE'] | REG['CR1'], 0b01000000])
      
    else:
      if spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b11000000:
        spi_2.writebytes([CMD['WRITE'] | REG['CR1'], 0b11000000])


  def Enable(direction, prime):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(mot1_step, GPIO.OUT)
    
    if spi_1.xfer2([CMD['READ'] | REG['CR0'], 0])[1] != 0b10001000:    # compensated half step
      spi_1.writebytes([CMD['WRITE'] | REG['CR0'], 0b10001000])
      
    if spi_1.xfer2([CMD['READ'] | REG['CR2'], 0])[1] != 0b10000000:
      spi_1.writebytes([CMD['WRITE'] | REG['CR2'], 0b10000000])
      
    if direction == 1:
      if spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b01000000:
        spi_1.writebytes([CMD['WRITE'] | REG['CR1'], 0b01000000])
      
    else:
      if spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b11000000:
        spi_1.writebytes([CMD['WRITE'] | REG['CR1'], 0b11000000])			

          
  def prime():																		### v1 is not defined
    try:
      if volume_check(v1, check = True):
        if tkMessageBox.askyesno('proceed', 'Do you want to Prime pump#1'):
          if spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b01000000:
            THM_RR(0.125, 2)
          else:
            THM_RR(0.075, 2)
          empty_queue()
      else:
        tkMessageBox.showwarning('warning', "Not Enough Volume.")
    except Exception:
      if tkMessageBox.askyesno('proceed', 'Do you want to Prime pump#1'):
        THM_RR(0.075, 2)
        empty_queue()


  def prime_p2():
    try:
      if volume_check_p2(v1, check = True):
        if tkMessageBox.askyesno('proceed', 'Do you want to Prime pump#2'):
          if spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b01000000:
            pump2(0.25, 2)
          else:
            pump2(0.075, 2)
          empty_queue()
      else:
        tkMessageBox.showwarning('warning', "Not Enough Volume.")
    except Exception:
      if tkMessageBox.askyesno('proceed', 'Do you want to Prime pump#2'):
        pump2(0.075, 2)
        empty_queue_p2()
    
        
  def Retract():
    if tkMessageBox.askyesno('proceed', 'Do you want to Retract syringe#1'):
      THM_RR(0.075, 0)
      valve_control('Hardness', 'OFF')	
      empty_queue()
          
  def Retract_p2():
    if tkMessageBox.askyesno('proceed', 'Do you want to Retract syringe#2'):
      pump2(0.075, 0)
      valve_control('Alkalinity', 'OFF')
      empty_queue_p2()

  def Output():
    if tkMessageBox.askyesno('proceed', 'Do you want to Output syringe#1'):
      THM_RR(0.075, 1)
      valve_control('Hardness', 'OFF')	
      empty_queue()

  def Output_p2():
    if tkMessageBox.askyesno('proceed', 'Do you want to Output syringe#1'):
      pump2(0.075, 1)
      valve_control('Hardness', 'OFF')	
      empty_queue()

  def Retract5ml():
    if tkMessageBox.askyesno('proceed', 'Do you want to Retract syringe#1'):
      THM_RR(5, 0)
      valve_control('Hardness', 'OFF')	
      empty_queue()

  def Retract5ml_p2():
    if tkMessageBox.askyesno('proceed', 'Do you want to Retract syringe#2'):
      pump2(5, 0)
      valve_control('Hardness', 'OFF')	
      empty_queue()

      
  def Rf_start():
    if tkMessageBox.askyesno('proceed', 'Do you want to Refill the syringe#1'):
      fill_volume = volume_check(0, check = False)
      if fill_volume > 0:
        #valve_control('Hardness', 'ON')
        if spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b11000000:
          THM_RR(fill_volume, 0)
        else:
          THM_RR((fill_volume+0.05), 0)
        popup_window(0, "p1")
      else:
        tkMessageBox.showinfo('Full', 'Syringe#1 filled to 5 mL')


  def Rf_start_p2():
    if tkMessageBox.askyesno('proceed', 'Do you want to Refill the syringe#2'):
      fill_volume = volume_check_p2(0, check = False)
      if fill_volume > 0:
        #valve_control('Alkalinity', 'ON')
        if spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b11000000:
          pump2(fill_volume, 0)
        else:
          pump2((fill_volume+0.05), 0)
        popup_window(0, "p2")
      else:
        tkMessageBox.showinfo('Full', 'Syringe#2 filled to 5 mL')		

  def Rf_start_both():
    if tkMessageBox.askyesno('proceed', 'Do you want to Refill both Syringes'):
      fill_volume1 = volume_check(0, check = False)
      fill_volume2 = volume_check_p2(0, check = False)
      if fill_volume1 > 0 and fill_volume2 > 0:
        if (spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b11000000) and (spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b11000000):
          THM_RR(fill_volume1, 0)
          pump2(fill_volume2, 0)
        else:
          THM_RR((fill_volume1+0.05), 0)
          pump2((fill_volume2+0.05), 0)
        popup_window(0, "p1")
      else:
        tkMessageBox.showinfo('Full', 'Both Syringes filled to 5 mL')

        
  def purge():
    if tkMessageBox.askyesno('proceed', 'Do you want to empty the syringe#1'):
      purge_volume = 4.99 - (volume_check(0, check = False))	
      if purge_volume != 0:
        if spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b01000000:
          THM_RR(purge_volume, 2)
        else:
          THM_RR((purge_volume+0.05), 2)
        popup_window(1, "p1")
      else:
        tkMessageBox.showinfo('Empty', 'Syringe#1 is Empty. Please Refill')

        
  def purge_p2():
    if tkMessageBox.askyesno('proceed', 'Do you want to empty the syringe#2'):
      purge_volume = 4.99 - (volume_check_p2(0, check = False))	
      if purge_volume != 0:
        if spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b01000000:
          pump2(purge_volume, 2)
        else:
          pump2((purge_volume + 0.15), 2)
        popup_window(1, "p2")
      else:
        tkMessageBox.showinfo('Empty', 'Syringe#2 is Empty. Please Refill')

  def purge_both():
    if tkMessageBox.askyesno('proceed', 'Do you want to empty both syringes'):
      purge_volume1 = 4.99 - (volume_check(0, check = False))	
      purge_volume2 = 4.99 - (volume_check_p2(0, check = False))

      if purge_volume1 != 0 and purge_volume2 != 0:
        if (spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b01000000) and (spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b01000000):
          THM_RR(purge_volume1, 2)
          pump2(purge_volume2, 2)
        else:
          THM_RR((purge_volume1+0.05), 2)
          pump2((purge_volume2 + 0.15), 2)
          
        popup_window(1, "p1")
      else:
        tkMessageBox.showinfo('Empty', 'Both Syringes are Empty. Please Refill')

              
        
  def dispense_loop():
    step = 11
    Dir = 13
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(step, GPIO.OUT)
    GPIO.setup(Dir, GPIO.OUT)
    #pid1 = os.getpid()
    #q.put(pid1)Dispense_step_volume
    steps = p.get()
    for x in range (0, steps):
        GPIO.output(step, GPIO.LOW)
        time.sleep(0.0005)
        GPIO.output(step, GPIO.HIGH)
        time.sleep(0.0005)
    GPIO.cleanup()	
    r.put(1)   
    time.sleep(1)
    sys.exit(1)

      
  def dispense_loop_p2():
    step = 16
    Dir = 18
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(step, GPIO.OUT)
    GPIO.setup(Dir, GPIO.OUT)
    #pid1 = os.getpid()
    #q2.put(pid1)
    steps = proc_queue2.get()
    for x in range (0, steps):
        GPIO.output(step, GPIO.LOW)
        time.sleep(0.0005)
        GPIO.output(step, GPIO.HIGH)
        time.sleep(0.0005)
    GPIO.cleanup()	
    r2.put(1)   
    time.sleep(1)
    sys.exit(1)	
