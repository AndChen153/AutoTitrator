#!/usr/bin/python
# -*- coding: utf-8 -*-
from matplotlib.figure import Figure
from matplotlib import style
from spidev import SpiDev
import matplotlib.pyplot as plt
from numpy import diff
from Tkinter import *
from PIL import ImageTk, Image
import Tkinter as tk
import tkFileDialog
import Adafruit_ADS1x15
import Adafruit_AS726x
from tkFont import Font
import tkMessageBox
import RPi.GPIO as GPIO
from Queue import Empty
from multiprocessing import Process, Queue
import csv
import ttk
import matplotlib
import time
import pytz
import datetime as dt
import sys
import os
import io         # used to create file streams
import fcntl      # used to access I2C parameters like addresses
import math
import string     # helps parse strings
from functools import partial
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.ticker import FormatStrFormatter
import pandas as pd
from pandastable import Table, TableModel
matplotlib.use("TkAgg")
import pickle
from w1thermsensor import W1ThermSensor
from dispexe_pHmeter import AtlasI2C
#from sklearn.neighbors import KNeighborsClassifier



# GPIO setup-----------------------------------------------
# Motor 1
mot1_step = 11						# set up motor 1 gpio pin
mot1_Dir = 13
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(mot1_step, GPIO.OUT)
GPIO.setup(mot1_Dir, GPIO.OUT)
GPIO.setup(mot1_Dir, GPIO.HIGH)		# HIGH = inject; LOW = fill
p1_channel =  3
# Motor 2
mot2_step = 16						# set up motor 2 gpio pin
mot2_Dir = 18
GPIO.setup(mot2_step, GPIO.OUT)
GPIO.setup(mot2_Dir, GPIO.OUT)
GPIO.setup(mot2_Dir, GPIO.HIGH)  
p2_channel = 0



## Valve setup---------------------------------------------------
Syringe_2 = 35						# sets up gpio pins for relays that control three way valves
Syringe_1 = 37
GPIO.setup(Syringe_2, GPIO.OUT, initial=True)
GPIO.setup(Syringe_1, GPIO.OUT, initial=True)
# End of GPIO setup------------------------------------------------



def valve_control(valve, mode):
	# switching 3 way valve that controls input and output direction
	# refilling syringe is "ON", dispensing is "OFF"
	GPIO.setup(Syringe_2, GPIO.OUT, initial=True)
	GPIO.setup(Syringe_1, GPIO.OUT, initial=True)
	if valve == 'Hardness':
		if mode == 'ON':
			GPIO.output(Syringe_1, False)
		elif mode == 'OFF':
			GPIO.output(Syringe_1, True)
		else:
			tkMessagebox.Showwarning('ERROR', 'Hardness valve Mode not selected')           
	elif valve == 'Alkalinity':
		if mode == 'ON':
			GPIO.output(Syringe_2, False)
		elif mode == 'OFF':
			GPIO.output(Syringe_2, True)
		else:
			tkMessagebox.Showwarning('ERROR', 'Alkalinity valve Mode not selected')
	else:
		tkMessagebox.Showwarning('ERROR', 'Valve type not selected')



# AMIS 30543 setup and SPI communication --------------------
# setup for Arduino communication for PI, pH meter, and temp probe
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



# numpad setup--------------------------------------------
# creates numpad for typing on touchscreen
num_run = 0
btn_funcid = 0
entry = 0

global variable_list
global entry_list
entry_list = []
def click(btn):
	global num_run
	global entry_list
	global var_entry_list
	text = "%s" % btn
	#entry_list1 = [entrym1, entrym2, entryv2]
	widget = root.focus_get()

	if not text == "Del" and not text == "Close":
		if widget in entry_list1 or entry_list or variable_list:
			widget.insert("insert", text)

	if text == 'Del':
		if widget in entry_list1 or entry_list or variable_list:
			widget.delete("0", END)

	if text == 'Close':
		boot.destroy()
		num_run = 0
		root.unbind('<Button-1>', btn_funcid)

def numpad():
    global num_run, boot
    boot = tk.Tk()
    boot.overrideredirect(True)
    boot['bg'] = 'RoyalBlue1'
    useFactor = True
    width = 0.7
    height = 0.2
    ws = boot.winfo_screenwidth()
    hs = boot.winfo_screenheight()
    w = (useFactor and ws*width) or width
    h = (useFactor and ws*height) or height
    # calculate position x, y
    x = (ws/2) - (w/2)
    y = (hs/0.95) - (h/0.95)
    boot.geometry('%dx%d+%d+%d' % (w, h, x, y))
    lf = tk.LabelFrame(boot)
    lf.pack(padx=15, pady=10)

    btn_list = [
        '0',  '1',  '2', '3', '4',  '5',
        '6', '7', '8', '9', '.', 'Del', 'Close']
    r = 1
    c = 0
    n = 0
    btn = list(range(len(btn_list)))

    for label in btn_list:
        cmd = partial(click, label)
        btn[n] = tk.Button(lf, text=label, width=5, height=2, font=myfont, command=cmd)
        btn[n].grid(row=r, column=c)
        n += 1
        c += 1
        if c == 7:
            c = 0
            r += 1

def close(event):
    global num_run, btn_funcid
    if num_run == 1:
        boot.destroy()
        num_run = 0
        root.unbind('<Button-1>', btn_funcid)
        
def Topfocus(event):
	run(event)

def run(event):
    global num_run, btn_funcid
    if num_run == 0:
        num_run = 1
        numpad()
        btn_funcid = root.bind('<Button-1>', close)
        
# end of numpad---------------------------------------------



# GUI PROGRAMME ----------------------------------------------------
root = Tk()								# initialize Tkinter
root.configure(bg="RoyalBlue1")			# sets background color
# root.title('FI-EZ-PIPETTE')
tool_frame = Frame(root, bd=1, relief="raised")		# creates a container for other widgets
tool_frame.pack(side=TOP, fill=X)		# makes window as small as possible while still encompassing the "frame"
ws = root.winfo_screenwidth()
hs = root.winfo_screenheight()
root.geometry('%dx%d' % (ws, hs))
root.attributes("-fullscreen", True)
img = PhotoImage(file ='/home/pi/icons/play.gif')
img2 = img.subsample(2, 2)

# img3 = PhotoImage(file = '/home/pi/icons/stop.gif')
# img4 = img3.subsample(2,2) 
img5 = PhotoImage(file ='/home/pi/icons/FI.gif')
img7 = ImageTk.PhotoImage(Image.open('/home/pi/icons/check.jpg'))
tool_frame = Frame(root, bd=1, relief="raised")
tool_frame.pack(side=TOP, fill=X)
myfont = Font(family ='Times New Roman', size=16)
titlefont = Font(family ='Gentium basic', size=16, 
				weight='bold', slant='italic')
container = Frame(root)
container.pack(side=TOP, fill="both", expand=True)



# Progress bar----------------------------------------------
# use linear potentiometer to sense position of syringes
pot = Adafruit_ADS1x15.ADS1115()
GAIN = 1
s = ttk.Style()
s2 = ttk.Style()
s.theme_use("alt")
s2.theme_use("alt")
s.configure("pump1.Vertical.TProgressbar",foreground='red', 
			background='green', thickness=30)
s2.configure("pump2.Vertical.TProgressbar",foreground='red', 
			background='green', thickness=30)
#progress_frame = Frame(container, bg = 'red')
#progress_frame.place(x=10)
progress_mot2 = ttk.Progressbar(root, style="pump2.Vertical.TProgressbar", 
								orient="vertical", length=105, maximum=5, 
								mode="determinate")
progress_mot2.place(x=10, y=200)
progress = ttk.Progressbar(root, style="pump1.Vertical.TProgressbar", 
						   orient="vertical", length=105, maximum=5, 
						   mode="determinate")
progress.place(x=50, y=200)
p1bar_label = Label(root, text="P2", 
					bg="RoyalBlue1", foreground="white", 
					font=myfont)
p1bar_label.place(x=15, y=305)
p2bar_label = Label(root, text="P1", 
					bg="RoyalBlue1", foreground="white", 
					font=myfont)
p2bar_label.place(x=55, y=305)
progress_frame = Frame(root, bg = 'red')
progress_frame.place(x=85, y=193)

w = Canvas(progress_frame, bg='royalblue1', 
		   bd='0', highlightthickness='0', 
		   width='50', height='115')
w.pack()

line50 = w.create_line(0, 10, 20, 10,fill='red', width='2')
line45 = w.create_line(0, 20, 10, 20, fill='red', width='2')
line40 = w.create_line(0, 30, 10, 30, fill='red', width='2')
line35 = w.create_line(0, 40, 10, 40, fill='red', width='2')
line30 = w.create_line(0, 50, 10, 50, fill='red', width='2')
line25 = w.create_line(0, 60, 20, 60, fill='red', width='2')
line20 = w.create_line(0, 70, 10, 70, fill='red', width='2')
line15 = w.create_line(0, 80, 10, 80, fill ='red', width='2')
line10 = w.create_line(0, 90, 10, 90, fill='red', width='2')
line5 = w.create_line(0, 100, 10, 100, fill ='red', width='2')
line0 = w.create_line(0, 110, 20, 110, fill='red', width='2')
text50 = w.create_text(35, 10, text='5 mL')
text25 = w.create_text(35, 60, text='2.5')
text0 = w.create_text(30, 110, text='0')

def lift_widget():
	# brings container forwards
	progress.lift(aboveThis=container)
	progress_mot2.lift(aboveThis=container)
	p1bar_label.lift(aboveThis=container)
	p2bar_label.lift(aboveThis=container)
	progress_frame.lift()

def lower_widget():
	# sends container to the back
	progress.lower(belowThis=container)
	progress_mot2.lower(belowThis=container)
	p1bar_label.lower(belowThis=container)
	p2bar_label.lower(belowThis=container)
	progress_frame.lower()

def calibrate_calc1(distance):
	# calibration calcuation to align potentiometer and graph
	return ((distance - 8269.81) / 3170)

def calibrate_calc2(distance):
	# calibration calcuation to align potentiometer2 and graph
	return ((distance - 8013.36) / 3163.13)

def initial_bar():
	# creates initial settings for progress bar for amount dispensed/refilled in syringe 1
	distance = pot.read_adc_difference(p1_channel, gain=GAIN)
	calib_volume = 	5.0 - calibrate_calc1(distance)
	if 0 < calib_volume and calib_volume <= 1:
		s.configure("pump1.Vertical.TProgressbar", background='red')
	elif 1 < calib_volume and calib_volume <= 2:
		s.configure("pump1.Vertical.TProgressbar", background='yellow')	
	elif 2 < calib_volume and calib_volume <= 5:
		s.configure("pump1.Vertical.TProgressbar", background='green')
	progress['value'] = calib_volume
	root.update_idletasks()
	#if (volume + 0.02) < calib_volume:
		#tkMessageBox.showwarning('warning', 'Calibration is off')
		#return False
	return True

def initial_bar2():
	# creates initial settings for progress bar for amount dispensed/refilled in syringe 2
	distance = pot.read_adc_difference(p2_channel, gain=GAIN)
	calib_volume = 	5.0 - calibrate_calc2(distance)
	if 0 < calib_volume and calib_volume <= 1:
		s2.configure("pump2.Vertical.TProgressbar", background='red')
	elif 1 < calib_volume and calib_volume <= 2:
		s2.configure("pump2.Vertical.TProgressbar", background='yellow')	
	elif 2 < calib_volume and calib_volume <= 5:
		s2.configure("pump2.Vertical.TProgressbar", background='green')
	progress_mot2['value'] = calib_volume
	root.update_idletasks()
	return True

def bar_update():
	# updates progress bar 1 to reflect how much is filled/dispensed
	global barupdate_id
	distance = pot.read_adc_difference(p1_channel, gain=GAIN)
	calib_volume = 	5.0 - calibrate_calc1(distance)
	if 0 < calib_volume and calib_volume <= 1:
		s.configure("pump1.Vertical.TProgressbar", background='red')
	elif 1 < calib_volume and calib_volume <= 2:
		s.configure("pump1.Vertical.TProgressbar", background='yellow')	
	elif 2 < calib_volume and calib_volume <= 5:
		s.configure("pump1.Vertical.TProgressbar", background='green')
	progress['value'] = calib_volume
	root.update_idletasks()
	barupdate_id = root.after(1000, bar_update)

def bar_update_p2():
	# updates progress bar 1 to reflect how much is filled/dispensed
	global barupdate_id_p2
	distance = pot.read_adc_difference(p2_channel, gain=GAIN)
	calib_volume = 	5.0 - calibrate_calc2(distance)
	if 0 < calib_volume and calib_volume <= 1:
		s2.configure("pump2.Vertical.TProgressbar", background='red')
	elif 1 < calib_volume and calib_volume <= 2:
		s2.configure("pump2.Vertical.TProgressbar", background='yellow')	
	elif 2 < calib_volume and calib_volume <= 5:
		s2.configure("pump2.Vertical.TProgressbar", background='green')
	progress_mot2['value'] = calib_volume
	root.update_idletasks()
	barupdate_id_p2 = root.after(1000, bar_update_p2)
	


# Edit, load and save Method ------------------------------------------------
global vol_array
vol_array = []
global file_name
file_name = '/home/pi/Dispenser_gui/Methods/Method1.Met'
with open(file_name, "r") as f:
	vol_array = f.read().splitlines()
f.close()
ftypes = [('Method files', '*.Met'), ('All files', '*')]		
def load_method(opt):
	global file_name
	global entry_list
	global vol_array
	if opt == 'editor':
		file_name = tkFileDialog.askopenfilename(filetypes=ftypes, 
												initialdir='/home/pi/Dispenser_gui/Methods')
		if file_name != '':
			try:
				vol_array = []
				with open(file_name, "r") as f:
						vol_array = f.read().splitlines()
				f.close()
				cnt = 0
				edit_window()
				for entry in entry_list:
						entry.delete(0, END)
						entry.insert(0, vol_array[cnt])
						cnt = cnt+1
			except Exception as ex:
				tkMessageBox.showwarning('Error', ex)	         
	if opt == 'loader':
		file_name = tkFileDialog.askopenfilename(filetypes=ftypes, 
												initialdir='/home/pi/Dispenser_gui/Methods')
		if file_name != '':
			try:
				vol_array = []
				with open(file_name, "r") as f:
					vol_array = f.read().splitlines()
				f.close()
				std1_button.config(text='%s mL(S1)' % vol_array[0])
				std2_button.config(text='%s mL(S2)' % vol_array[1])
				std3_button.config(text='%s mL(S3)' % vol_array[2])
				std4_button.config(text='%s mL(S4)' % vol_array[3])
				std5_button.config(text='%s mL(S5)' % vol_array[4])
				chk_button.config(text='%s mL(chk)' % vol_array[5])
				status_label.config(text='%s' % (file_name.split('/')[5]))
			except Exception as ex:
				tkMessageBox.showwarning('Error', ex)	
			
				
def save_method():
	global mtop	
	global file_name
	if file_name != "":
		with open(file_name, "w") as f:
			for entry in entry_list:
				f.write("%s\n" % entry.get())
		f.close()
		mtop.grab_release()
		mtop.destroy()			
	


# Method Top-Level window-----------------------------------------------------

mtop = None
def edit_window():
	global mtop
	global entry_list

	entry_list = []
	mtop = Toplevel(root)
	mtop.transient(master=root)
	mtop.grab_set()
	mtop.geometry('250x220+150+60')
	mtop.title('Edit')

	l1 = Label(mtop, text="mL", font=myfont)
	l2 = Label(mtop, text="mL", font=myfont)
	l3 = Label(mtop, text="mL", font=myfont)
	l4 = Label(mtop, text="mL", font=myfont)
	l5 = Label(mtop, text="mL", font=myfont)
	l6 = Label(mtop, text="mL", font=myfont)

	label1 = Label(mtop, text="std 1", font=myfont)
	label2 = Label(mtop, text="std 2", font=myfont)
	label3 = Label(mtop, text="std 3", font=myfont)
	label4 = Label(mtop, text="std 4", font=myfont)
	label5 = Label(mtop, text="std 5", font=myfont)
	label6 = Label(mtop, text="chk std", font=myfont)

	e1 = Entry(mtop, width =10, relief ="raised", font=myfont)
	e2 = Entry(mtop, width =10, relief ="raised", font=myfont)
	e3 = Entry(mtop, width =10, relief ="raised", font=myfont)
	e4 = Entry(mtop, width =10, relief ="raised", font=myfont)
	e5 = Entry(mtop, width =10, relief ="raised", font=myfont)
	e6 = Entry(mtop, width =10, relief ="raised", font=myfont)

	l1.grid(row=0, column=2, sticky='W')
	l2.grid(row=1, column=2, sticky='W')
	l3.grid(row=2, column=2, sticky='W')
	l4.grid(row=3, column=2, sticky='W')
	l5.grid(row=4, column=2, sticky='W')
	l6.grid(row=5, column=2, sticky='W')

	label1.grid(row=0, column=0, padx=5)
	label2.grid(row=1, column=0, padx=5)
	label3.grid(row=2, column=0, padx=5)
	label4.grid(row=3, column=0, padx=5)
	label5.grid(row=4, column=0, padx=5)
	label6.grid(row=5, column=0, padx=5)

	e1.grid(row=0, column=1)
	e2.grid(row=1, column=1)
	e3.grid(row=2, column=1)
	e4.grid(row=3, column=1)
	e5.grid(row=4, column=1)
	e6.grid(row=5, column=1)

	entry_list = [e1,e2,e3,e4,e5,e6]

	for entry in entry_list:
		entry.bind('<Button-1>', Topfocus)
	sav_button = Button(mtop, text="Save Method", 
						font=myfont, relief="raised", command=save_method)
	sav_button.grid(row=6, column=0, 
					columnspan=2, pady=5)
	return



# dispenser start--------------------------------------------------------------

conc_mainframe = Frame(container, bg="RoyalBlue1")
THM_mainframe = Frame(container, bg="RoyalBlue1")
titer_mainframe = Frame(container, bg="RoyalBlue1")
Hardness_mainframe = Frame(container, bg="RoyalBlue1")
Alkalinity_mainframe = Frame(container, bg="RoyalBlue1")
conc_mainframe.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
THM_mainframe.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
titer_mainframe.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
Hardness_mainframe.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
Alkalinity_mainframe.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
THM_mainframe.lift()
#progress_frame.lift()
conc_frame = Frame(conc_mainframe, bg="RoyalBlue1")
THM_frame = Frame(THM_mainframe, bg="RoyalBlue1")

conc_frame.place(x=20, y=20)
THM_frame.place(x=150, y=20)

# create the 5 different tabs for different processes
def pageone():
	conc_mainframe.lift()
	#progress_frame.lift()
	lift_widget()

def pagetwo():
	THM_mainframe.lift()
	lift_widget()

def pagethree():
	titer_mainframe.lift()
	lift_widget()
	
def pagefour():
	Hardness_mainframe.lift()	
	lower_widget()
	
def pagefive():
	Alkalinity_mainframe.lift()
	lower_widget()

sy_button = Button(tool_frame, text = "MANUAL", command=pageone, font=myfont)
sy_button.pack(side=LEFT, padx=2, pady=2)

dis_button = Button(tool_frame, text =" THM-RR ", command=pagetwo, font=myfont)
dis_button.pack(side=LEFT, padx=2, pady=2)

titer_button = Button(tool_frame, text=" TITRATOR ", command=pagethree, font=myfont)
titer_button.pack(side=LEFT, padx=2, pady=2)

Hardness_button = Button(tool_frame, text="HARDNESS", command=pagefour, font=myfont)
Hardness_button.pack(side=LEFT, padx=2, pady=2)

Alkalinity_button = Button(tool_frame, text="ALKALINITY", command=pagefive, font=myfont)
Alkalinity_button.pack(side=LEFT, padx=2, pady=2)

bigfont = Font(family='Times New Roman', size=16)

root.option_add("*TCombobox*Listbox*Font", bigfont)
m1var = StringVar()
m1 = {' ppb(ug/L) ':0.001, ' ppt(ng/L) ':0.000001,'   g/L   ':1000, 'ppm(mg/L)': 1}
combovalues1 = m1.keys()
m1units = ttk.Combobox(conc_frame, textvariable=m1var, 
					   values=combovalues1, state="readonly", 
					   width=10, height=5)
m1units.config(font=myfont)
m1var.set('-- units --')
global unit1
unit1 = IntVar()

# unit conversion between ppb, ppt, g/L,and ppm
def change_unit1(*args):
    global unit1
    unit1 = m1[m1var.get()]

m1var.trace('w', change_unit1)
m2var = StringVar()
m2 = {
	' ppb(ug/L) ':0.001, ' ppt(ng/L) ':0.000001, 
	'   g/L   ':1000, 'ppm(mg/L)':1
	}
combovalues2 = m2.keys()
m2units = ttk.Combobox(conc_frame, textvariable=m2var, 
					   values=combovalues2, state="readonly", 
					   width=10, height=5)
m2units.config(font=myfont)
m2var.set('-- units --')

global unit2
unit2 = IntVar()


def change_unit2(*args):
    global unit2
    unit2 = m2[m2var.get()]
	
m2var.trace('w', change_unit2)
labelm1 = Label(conc_frame, text="M1", font=myfont, bg='white')
labelm2 = Label(conc_frame, text="M2", font=myfont, bg='white')
labelv1 = Label(conc_frame, text="V1 (mL)",font=myfont, bg='white')
labelv2 = Label(conc_frame, text="V2 (mL)", font=myfont, bg='white')

entrym1 = Entry(conc_frame, width=15, font=myfont, relief ="raised")
entrym2 = Entry(conc_frame, width=15, font=myfont, relief="raised")
entryv1 = Entry(conc_frame, width=15, font=myfont, relief="raised")
entryv2 = Entry(conc_frame, width=15, font=myfont, relief="raised")

entrym1.bind('<Button-1>', Topfocus)
entrym2.bind('<Button-1>', Topfocus)
entryv2.bind('<Button-1>', Topfocus)

labelm1.grid (row=0, column=1)
labelm2.grid(row=0, column=2, padx=5)
m1units.grid(row=1, sticky='nsew')
entrym1.grid(row=1, column=1, pady=2, padx=7, ipady=6)
entrym2.grid(row=1, column=2, padx=7, ipady=6)
m2units.grid(row=1, column=3, sticky='nsew')
labelv1.grid (row=2, column=1, pady=2)
labelv2.grid(row=2, column=2, padx=5)
entryv1.grid(row=3, column=1, ipady=6)
entryv2.grid(row=3, column=2, padx=5, ipady=6)

path = '/home/pi/Dispenser_gui/python/volume.csv'

entry_list1 = [
	entrym1, entrym2, 
	entryv2
	]

global p1
global p2
def start_process():
	global p1
	bar_update()
	p1 = Process(target=dispense_loop)
	p1.deamon = True
	p1.start()


def start_process_p2():
	global p2
	bar_update_p2()
	p2 = Process(target=dispense_loop_p2)
	p2.deamon = True
	p2.start()
	
	
def volume_check(dispense_volume, check = True):
	distance = pot.read_adc_difference(p1_channel, gain=GAIN)
	calib_volume = calibrate_calc1(distance)
	tot_volume = calib_volume + dispense_volume
	Rem_volume = 5.0 - tot_volume
	if check:
		if Rem_volume > 0.01:
			return True
		elif Rem_volume <= 0:
			return False
	else:
		return calib_volume

def volume_check_p2(dispense_volume, check = True):
	distance = pot.read_adc_difference(p2_channel, gain=GAIN)
	calib_volume = calibrate_calc2(distance)
	tot_volume = calib_volume + dispense_volume
	Rem_volume = 5.0 - tot_volume
	if check:
		if Rem_volume > 0.01:
			return True
		elif Rem_volume <= 0:
			return False
	else:
		return calib_volume
		
def volume1():
	try:
		global unit1
		global unit2
		m1 = float(entrym1.get())
		m2 = float(entrym2.get())
		v2 = float(entryv2.get())
		v1 = (m2*float(unit2)*v2)/(m1*float(unit1))
		entryv1.delete(0,"end")
		entryv1.insert(0, v1)
		if volume_check(v1, check = True):
			if tkMessageBox.askyesno('proceed',
									 'V1 is %s mL, do you really want to proceed' % (v1)):
				steps = int((v1 + 0.000785)/0.0000502)
				p.put(steps)
				Enable(1, 0)
				start_process()
			else:
				Manbar.state(['!selected'])
				s.configure("Manbar.Horizontal.TProgressbar", background='RoyalBlue1')
				Manbar.stop()
		else:
			tkMessageBox.showwarning('warning', "Not Enough Volume. Refill ")
			Manbar.state(['!selected'])
			s.configure("Manbar.Horizontal.TProgressbar", background='RoyalBlue1')
			Manbar.stop()
	except (AttributeError, ValueError):
		Manbar.state(['!selected'])
		s.configure("Manbar.Horizontal.TProgressbar", background='RoyalBlue1')
		Manbar.stop()
		tkMessageBox.showwarning('warning', "Check Your values/units")
		
def syringe_motor_1(volume, direction):
	# controls motor for syringe 1
	steps = int((volume + 0.000785) / 0.0000502)
	p.put(steps)
	if spi_1.xfer2([CMD['READ'] | REG['CR0'], 0])[1] != 0b10001000:    # compensated half step
		spi_1.writebytes([CMD['WRITE'] | REG['CR0'], 0b10001000])
		
	if spi_1.xfer2([CMD['READ'] | REG['CR2'], 0])[1] != 0b10000000:
		spi_1.writebytes([CMD['WRITE'] | REG['CR2'], 0b10000000])

	# 0 = refill/retract
	# 1 = dispense
	# 2 = prime/Empty
	if direction == 1:	
		valve_control('Hardness', 'OFF')											  
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

def syringe_motor_2(volume, direction):
	# controls motor for syringe 2
	steps = int((volume + 0.000785) / 0.0000502)
	proc_queue2.put(steps)
	if spi_2.xfer2([CMD['READ'] | REG['CR0'], 0])[1] != 0b10001000:    # compensated half step
		spi_2.writebytes([CMD['WRITE'] | REG['CR0'], 0b10001000])
		
	if spi_2.xfer2([CMD['READ'] | REG['CR2'], 0])[1] != 0b10000000:
		spi_2.writebytes([CMD['WRITE'] | REG['CR2'], 0b10000000])
		
	# 0 = refill/retract
	# 1 = dispense
	# 2 = prime/Empty
	if direction == 1:		
		valve_control('Alkalinity', 'OFF')
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
				
def prime():																		### v1 is not defined
	try:
		if volume_check(v1, check = True):
			if tkMessageBox.askyesno('proceed', 'Do you want to Prime pump#1'):
				if spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b01000000:		# checks if syringe is full??
					syringe_motor_1(0.125, 2)
				else:
					syringe_motor_1(0.075, 2)
				empty_queue()
		else:
			tkMessageBox.showwarning('warning', "Not Enough Volume.")
	except Exception:
		if tkMessageBox.askyesno('proceed', 'Do you want to Prime pump#1'):
			syringe_motor_1(0.075, 2)
			empty_queue()


def prime_p2():
	try:
		if volume_check_p2(v1, check = True):
			if tkMessageBox.askyesno('proceed', 'Do you want to Prime pump#2'):	
				if spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b01000000:		# checks if syringe is full??
					syringe_motor_2(0.25, 2)
				else:
					syringe_motor_2(0.075, 2)
				empty_queue()
		else:
			tkMessageBox.showwarning('warning', "Not Enough Volume.")
	except Exception:
		if tkMessageBox.askyesno('proceed', 'Do you want to Prime pump#2'):
			syringe_motor_2(0.075, 2)
			empty_queue_p2()
	
			
def Retract():
	if tkMessageBox.askyesno('proceed', 'Do you want to Retract syringe#1'):
		syringe_motor_1(0.075, 0)
		valve_control('Hardness', 'OFF')	
		empty_queue()
				
def Retract_p2():
	if tkMessageBox.askyesno('proceed', 'Do you want to Retract syringe#2'):
		syringe_motor_2(0.075, 0)
		valve_control('Alkalinity', 'OFF')
		empty_queue_p2()

def Output():
	if tkMessageBox.askyesno('proceed', 'Do you want to Output syringe#1'):
		syringe_motor_1(0.075, 1)
		valve_control('Hardness', 'OFF')	
		empty_queue()

def Output_p2():
	if tkMessageBox.askyesno('proceed', 'Do you want to Output syringe#1'):
		syringe_motor_2(0.075, 1)
		valve_control('Hardness', 'OFF')	
		empty_queue()

def Retract5ml():
	if tkMessageBox.askyesno('proceed', 'Do you want to Retract syringe#1'):
		syringe_motor_1(5, 0)
		valve_control('Hardness', 'OFF')	
		empty_queue()

def Retract5ml_p2():
	if tkMessageBox.askyesno('proceed', 'Do you want to Retract syringe#2'):
		syringe_motor_2(5, 0)
		valve_control('Hardness', 'OFF')	
		empty_queue()

		
def Refill():
	if tkMessageBox.askyesno('proceed', 'Do you want to Refill the syringe#1'):
		fill_volume = volume_check(0, check = False)
		if fill_volume > 0:
			#valve_control('Hardness', 'ON')
			if spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b11000000:
				syringe_motor_1(fill_volume, 0)
			else:
				syringe_motor_1((fill_volume+0.05), 0)
			popup_window(0, "p1")
		else:
			tkMessageBox.showinfo('Full', 'Syringe#1 filled to 5 mL')

def Refill_p2():
	if tkMessageBox.askyesno('proceed', 'Do you want to Refill the syringe#2'):
		fill_volume = volume_check_p2(0, check = False)
		if fill_volume > 0:
			#valve_control('Alkalinity', 'ON')
			if spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b11000000:
				syringe_motor_2(fill_volume, 0)
			else:
				syringe_motor_2((fill_volume+0.05), 0)
			popup_window(0, "p2")
		else:
			tkMessageBox.showinfo('Full', 'Syringe#2 filled to 5 mL')		

def Refill_both():
	if tkMessageBox.askyesno('proceed', 'Do you want to Refill both Syringes'):
		fill_volume1 = volume_check(0, check = False)
		fill_volume2 = volume_check_p2(0, check = False)
		if fill_volume1 > 0 and fill_volume2 > 0:
			if ((spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b11000000) and 
			   (spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b11000000)):
				syringe_motor_1(fill_volume1, 0)
				syringe_motor_2(fill_volume2, 0)
			else:
				syringe_motor_1((fill_volume1+0.05), 0)
				syringe_motor_2((fill_volume2+0.05), 0)
			popup_window(0, "p1")
		else:
			tkMessageBox.showinfo('Full', 'Both Syringes filled to 5 mL')

			
def Empty():
	if tkMessageBox.askyesno('proceed', 'Do you want to empty the syringe#1'):
		Empty_volume = 4.99 - (volume_check(0, check = False))	
		if Empty_volume != 0:
			if spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b01000000:
				syringe_motor_1(Empty_volume, 2)
			else:
				syringe_motor_1((Empty_volume+0.05), 2)
			popup_window(1, "p1")
		else:
			tkMessageBox.showinfo('Empty', 'Syringe#1 is Empty. Please Refill')
	
def Empty_p2():
	if tkMessageBox.askyesno('proceed', 'Do you want to empty the syringe#2'):
		Empty_volume = 4.99 - (volume_check_p2(0, check = False))	
		if Empty_volume != 0:
			if spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b01000000:
				syringe_motor_2(Empty_volume, 2)
			else:
				syringe_motor_2((Empty_volume + 0.15), 2)
			popup_window(1, "p2")
		else:
			tkMessageBox.showinfo('Empty', 'Syringe#2 is Empty. Please Refill')

def Empty_both():
	if tkMessageBox.askyesno('proceed', 'Do you want to empty both syringes'):
		Empty_volume1 = 4.99 - (volume_check(0, check = False))	
		Empty_volume2 = 4.99 - (volume_check_p2(0, check = False))

		if Empty_volume1 != 0 and Empty_volume2 != 0:
			if ((spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b01000000) and 
				(spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] == 0b01000000)):
				syringe_motor_1(Empty_volume1, 2)
				syringe_motor_2(Empty_volume2, 2)
			else:
				syringe_motor_1((Empty_volume1+0.05), 2)
				syringe_motor_2((Empty_volume2 + 0.15), 2)
				
			popup_window(1, "p1")
		else:
			tkMessageBox.showinfo('Empty', 'Both Syringes are Empty. Please Refill')				
			
def dispense_loop():
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(mot1_step, GPIO.OUT)
	GPIO.setup(mot1_Dir, GPIO.OUT)
	#pid1 = os.getpid()
	#q.put(pid1)Dispense_step_volume
	steps = p.get()
	for x in range (0, steps):
			GPIO.output(mot1_step, GPIO.LOW)
			time.sleep(0.0005)
			GPIO.output(mot1_step, GPIO.HIGH)
			time.sleep(0.0005)
	GPIO.cleanup()	
	r.put(1)   
	time.sleep(1)
	sys.exit(1)
	
def dispense_loop_p2():
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(mot2_step, GPIO.OUT)
	GPIO.setup(mot2_Dir, GPIO.OUT)
	#pid1 = os.getpid()
	#q2.put(pid1)
	steps = proc_queue2.get()
	for x in range (0, steps):
			GPIO.output(mot2_step, GPIO.LOW)
			time.sleep(0.0005)
			GPIO.output(mot2_step, GPIO.HIGH)
			time.sleep(0.0005)
	GPIO.cleanup()	
	r2.put(1)   
	time.sleep(1)
	sys.exit(1)	
	
def empty_queue():
	global barupdate_id
	global p1
	qid = root.after(500, empty_queue)
	try:
		fork = r.get(False)
		if fork ==1:
			root.after_cancel(qid)
			root.after_cancel(barupdate_id)
			#r.task_done()
			p1.join()
			tkMessageBox.showinfo("DONE", "Prime/Retract Completed.")
			initial_bar()
	except Empty:
		pass

def empty_queue_p2():
	global barupdate_id_p2
	global p2
	qid = root.after(500, empty_queue_p2)
	try:
		fork = r2.get(False)
		if fork ==1:
			root.after_cancel(qid)
			root.after_cancel(barupdate_id_p2)
			#r.task_done()
			p2.join()
			tkMessageBox.showinfo("DONE", "Prime/Retract Completed.")
			initial_bar2()
	except Empty:
		pass
				
def top_close():
	global barupdate_id
	global p1
	tid = root.after(500, top_close)
	try:
		fork = r.get(False)
		if fork == 1:
			top.destroy()
			root.after_cancel(tid)
			root.after_cancel(barupdate_id)
			#r.task_done()
			p1.join()
			tkMessageBox.showinfo("DONE", "Refill/Purging Completed.")
			initial_bar()
			top.grab_release()
	except Empty:
		pass

def top_close_p2():
	global barupdate_id_p2
	global p2
	tid = root.after(500, top_close_p2)
	try:
		fork = r2.get(False)
		if fork == 1:
			top.destroy()
			root.after_cancel(tid)
			root.after_cancel(barupdate_id_p2)
			#r.task_done()
			p2.join()
			tkMessageBox.showinfo("DONE", "Refill/Purging Completed.")
			initial_bar2()
			top.grab_release()
	except Empty:
		pass
			
def popup_window(dmsg, pump):
	# creates popup window for waiting messages
	global top,msg
	top = Toplevel()
	top.config(bg='royalblue1', relief='raised')
	top.geometry('160x160+300+280')
	top.overrideredirect(True)
	msg = Message(top, relief='raised', bg='white', font=myfont)
	msg.pack()
	top.grab_set()
	if pump == "p1":
		top_close()
		if dmsg == 1:
			msg.config(text='Please wait until system Empty syringe#1')
		else:
			msg.config(text="Please wait until system Refill's syringe#1")
	elif pump == "p2":
		top_close_p2()
		if dmsg == 1:
			msg.config(text='Please wait until system Empty syringe#2')
		else:
			msg.config(text="Please wait until system Refill's syringe#2")	
		
def button_call():
	if (Titration_loop.running_titration == False and Manbar.instate(['selected']) == False and 
		bar1.instate(['selected']) == False and bar2.instate(['selected']) == False and 
		bar3.instate(['selected']) == False and bar4.instate(['selected']) == False and 
		bar5.instate(['selected']) == False and chk.instate(['selected']) == False):
		s.configure("Manbar.Horizontal.TProgressbar", background='red')
		Manbar.start(10)
		Manbar.state(['!selected', 'selected'])
		std_stop()
		volume1()
	else:
		tkMessageBox.showwarning('warning', "Please wait untill current process is done")
	
Dispense_button = Button(conc_frame, image=img2, 
						width=100, height=60, 
						bg='white', command=button_call)
Dispense_button.grid(row=5, column=1, pady=10, columnspan=2)

def sys_shut():
	# closes out of the program but does not shutdown the pi
	if tkMessageBox.askyesno('SHUTDOWN', 'Do you want to shutdown the system?'):
		root.destroy()
		sys.exit()
		#os.system("sudo shutdown now -P")

def sys_reboot():
	# reboots the entire pi
	if tkMessageBox.askyesno('REBOOT', 'Do you want to reboot the system?'):
		root.destroy()
		os.system("sudo shutdown -r now")

	

## Menu widget--------------------------------------------------
# creates buttons for dropdown menu
menu=Menu(root, bg = 'floral white')
root.config(menu=menu)
optionmenu = Menu(menu, tearoff=0)
optionmenu.config(font = myfont)
menu.add_cascade(label="Options", menu=optionmenu, font=titlefont)		
menu.add_cascade(label="                         ",  font=titlefont)
menu.add_cascade(label="",image=img5, font=myfont)
menu.add_cascade(label="EZ-AutoTitrator",  font=titlefont)

primemenu = Menu(optionmenu)
primemenu.add_command(label="Pump-1..", command=prime, font=titlefont)		# creates submenu for dropdown
primemenu.add_separator()
primemenu.add_command(label= "Pump-2..", command=prime_p2, font=titlefont)
primemenu.add_separator()
optionmenu.add_cascade(label="Prime", menu=primemenu, font=titlefont)		# creates submenu title
optionmenu.add_separator()

retractmenu = Menu(optionmenu)
retractmenu.add_command(label="Pump-1..", command=Retract,font=titlefont) 
retractmenu.add_separator()
retractmenu.add_command(label="Pump-2..", command=Retract_p2,font=titlefont) 
retractmenu.add_separator()
retractmenu.add_command(label="Pump-1out..", command=Output,font=titlefont) 
retractmenu.add_separator()
retractmenu.add_command(label="Pump-2out..", command=Output_p2,font=titlefont) 
retractmenu.add_separator()
optionmenu.add_cascade(label="Incremental", menu=retractmenu,font=titlefont) 
optionmenu.add_separator()

retractmenu5ml = Menu(optionmenu)
retractmenu5ml.add_command(label="Pump-1..", command=Retract5ml,font=titlefont) 
retractmenu5ml.add_separator()
retractmenu5ml.add_command(label="Pump-2..", command=Retract5ml_p2,font=titlefont) 
retractmenu5ml.add_separator()
optionmenu.add_cascade(label="Retract5ml", menu=retractmenu5ml,font=titlefont) 
optionmenu.add_separator()

refillmenu = Menu(optionmenu)
refillmenu.add_separator()
refillmenu.add_command(label="Syringe-1..", command=Refill,font=titlefont)
refillmenu.add_separator()
refillmenu.add_command(label="Syringe_2..", command=Refill_p2,font=titlefont)
refillmenu.add_separator()
refillmenu.add_command(label="Both Syringes..", command=Refill_both,font=titlefont)
refillmenu.add_separator()
optionmenu.add_cascade(label="Refill", menu=refillmenu,font=titlefont) 
optionmenu.add_separator()

emptymenu = Menu(optionmenu)
emptymenu.add_command(label="Syringe-1..", command=Empty,font=titlefont)
emptymenu.add_separator()
emptymenu.add_command(label="Syringe-2..", command=Empty_p2,font=titlefont)
emptymenu.add_separator()
emptymenu.add_command(label="Both Syringes..", command=Empty_both,font=titlefont)
emptymenu.add_separator()
optionmenu.add_cascade(label="Empty", menu=emptymenu,font=titlefont) 
optionmenu.add_separator()

optionmenu.add_command(label="Reboot", command=sys_reboot,font=titlefont)
optionmenu.add_separator()
optionmenu.add_command(label="Quit", command=sys_shut,font=titlefont)
# end of menu widget-------------------------------------------



# THM standard ------------------------------------------------
def std_stop():
	global barupdate_id
	global p1
	std_id = root.after(500, std_stop)
	try:
		fork = r.get(False)
		if fork == 1:
			root.after_cancel(barupdate_id)
			root.after_cancel(std_id)
			p1.join()
			if bar1.instate(['selected']) == True:
				bar1.stop()
				bar1.state(['!selected'])
				s.configure("bar1.Horizontal.TProgressbar", background='RoyalBlue1')
				std1_label.config(image=img7)
			elif bar2.instate(['selected']) == True:
				bar2.state(['!selected'])
				s.configure("bar2.Horizontal.TProgressbar", background='RoyalBlue1')
				bar2.stop()
				std2_label.config(image=img7)
			elif bar3.instate(['selected']) == True:
				bar3.state(['!selected'])
				s.configure("bar3.Horizontal.TProgressbar", background='RoyalBlue1')
				bar3.stop()
				std3_label.config(image=img7)	
			elif bar4.instate(['selected']) == True:
				bar4.state(['!selected'])
				s.configure("bar4.Horizontal.TProgressbar", background='RoyalBlue1')
				bar4.stop()
				std4_label.config(image=img7)	
			elif bar5.instate(['selected']) == True:
				bar5.state(['!selected'])
				s.configure("bar5.Horizontal.TProgressbar", background='RoyalBlue1')
				bar5.stop()
				std5_label.config(image=img7)
			elif chk.instate(['selected']) == True:
				chk.state(['!selected'])
				s.configure("chk.Horizontal.TProgressbar", background='RoyalBlue1')
				chk.stop()
				chk_label.config(image=img7)
			elif Manbar.instate(['selected']) == True:
				Manbar.state(['!selected'])
				s.configure("Manbar.Horizontal.TProgressbar", background='RoyalBlue1')
				Manbar.stop()
			initial_bar()					
	except Empty:
		pass

def std1_vol():
	global vol_array
	if (Titration_loop.running_titration == False and bar1.instate(['selected']) == False and 
		bar2.instate(['selected']) == False and bar3.instate(['selected']) == False and 
		bar4.instate(['selected']) == False and bar5.instate(['selected']) == False and 
		chk.instate(['selected']) == False and Manbar.instate(['selected']) == False):
		try:
			if volume_check(float(vol_array[0]), check = True):
				if tkMessageBox.askyesno('proceed', 'Do you want to do std1'):
					syringe_motor_1(float(vol_array[0]), 1)
					s.configure("bar1.Horizontal.TProgressbar", background='red')
					bar1.start(10)
					bar1.state(['!selected', 'selected'])
			else:
				tkMessageBox.showwarning('warning', "Not Enough Volume. Refill ")
		except Exception as e:
			tkMessageBox.showwarning("ERROR", message=e)
			
	else:
		tkMessageBox.showwarning('warning', "Please wait untill current process is done")
		
def std2_vol():
	global vol_array
	if (Titration_loop.running_titration == False and bar2.instate(['selected']) == False and 
		bar1.instate(['selected']) == False and bar3.instate(['selected']) == False and 
		bar4.instate(['selected']) == False and bar5.instate(['selected']) == False and 
		chk.instate(['selected']) == False and Manbar.instate(['selected']) == False):	
		try:
			if volume_check(float(vol_array[1]), check = True):
				if tkMessageBox.askyesno('proceed', 'Do you want to do std2'):
					syringe_motor_1(float(vol_array[1]), 1)
					s.configure("bar2.Horizontal.TProgressbar", background='red')
					bar2.start(10)
					bar2.state(['!selected', 'selected'])
			else:
				tkMessageBox.showwarning('warning', "Not Enough Volume. Refill ")
		except Exception as e:
			tkMessageBox.showwarning("ERROR", message=e)	
	else:
		tkMessageBox.showwarning('warning', "Please wait untill current process is done")
		
def std3_vol():
	global vol_array
	if (Titration_loop.running_titration == False and bar3.instate(['selected']) == False and 
		bar1.instate(['selected']) == False and bar2.instate(['selected']) == False and 
		bar4.instate(['selected']) == False and bar5.instate(['selected']) == False and 
		chk.instate(['selected']) == False and Manbar.instate(['selected']) == False):
		try:
			if volume_check(float(vol_array[2]), check = True):
				if tkMessageBox.askyesno('proceed', 'Do you want to do std3'):
					syringe_motor_1(float(vol_array[2]), 1)
					s.configure("bar3.Horizontal.TProgressbar", background='red')
					bar3.start(10)
					bar3.state(['!selected', 'selected'])
			else:
				tkMessageBox.showwarning('warning', "Not Enough Volume. Refill ")
		except Exception as e:
			tkMessageBox.showwarning("ERROR", message=e)	
	else:
		tkMessageBox.showwarning('warning', "Please wait untill current process is done")
		
def std4_vol():
	global vol_array
	if (Titration_loop.running_titration == False and bar4.instate(['selected']) == False and 
		bar1.instate(['selected']) == False and bar2.instate(['selected']) == False and 
		bar3.instate(['selected']) == False and bar5.instate(['selected']) == False and 
		chk.instate(['selected']) == False and Manbar.instate(['selected']) == False):
		try:
			if volume_check(float(vol_array[3]), check = True):
				if tkMessageBox.askyesno('proceed', 'Do you want to do std4'):
					syringe_motor_1(float(vol_array[3]), 1)
					s.configure("bar4.Horizontal.TProgressbar", background='red')
					bar4.start(10)
					bar4.state(['!selected', 'selected'])
			else:
				tkMessageBox.showwarning('warning', "Not Enough Volume. Refill ")
		except Exception as e:
			tkMessageBox.showwarning("ERROR", message=e)
	else:
		tkMessageBox.showwarning('warning', "Please wait untill current process is done")
		
def std5_vol():
	global vol_array
	if (Titration_loop.running_titration == False and bar5.instate(['selected']) == False and 
		bar1.instate(['selected']) == False and bar2.instate(['selected']) == False and 
		bar3.instate(['selected']) == False and bar4.instate(['selected']) == False and 
		chk.instate(['selected']) == False and Manbar.instate(['selected']) == False):
		try:
			if volume_check(float(vol_array[4]), check = True):
				if tkMessageBox.askyesno('proceed', 'Do you want to do std5'):
					syringe_motor_1(float(vol_array[4]), 1)
					s.configure("bar5.Horizontal.TProgressbar", background='red')
					bar5.start(10)
					bar5.state(['!selected', 'selected'])
			else:
				tkMessageBox.showwarning('warning', "Not Enough Volume. Refill ")
		except Exception as e:
			tkMessageBox.showwarning("ERROR", message=e)			
	else:
		tkMessageBox.showwarning('warning', "Please wait untill current process is done")
		
def chk_vol():
	global vol_array
	if (Titration_loop.running_titration == False and chk.instate(['selected']) == False and 
	bar1.instate(['selected']) == False and bar2.instate(['selected']) == False and 
	bar3.instate(['selected']) == False and bar4.instate(['selected']) == False and 
	bar5.instate(['selected']) == False and Manbar.instate(['selected']) == False):
		try:
			if volume_check(float(vol_array[5]), check = True):
				if tkMessageBox.askyesno('proceed', 'Do you want to do check std'):
					syringe_motor_1(float(vol_array[5]), 1)
					s.configure("chk.Horizontal.TProgressbar", background='red')
					chk.start(10)
					chk.state(['!selected', 'selected'])
			else:
				tkMessageBox.showwarning('warning', "Not Enough Volume. Refill ")
		except Exception as e:
			tkMessageBox.showwarning("ERROR", message=e)			
	else:
		tkMessageBox.showwarning('warning', "Please wait untill current process is done")

def reset_label():
	std1_label.config(image='') 
	std2_label.config(image='') 
	std3_label.config(image='') 
	std4_label.config(image='') 
	std5_label.config(image='') 
	chk_label.config(image='')

THM_frame.columnconfigure(1, minsize=250)
std1_button = Button(THM_frame, width=10, 
					 text='%s mL(S1)' %vol_array[0], 
					 font=myfont, command=std1_vol)
std2_button = Button(THM_frame, width=10, 
					 text='%s mL(S2)' %vol_array[1], 
					 font=myfont, command=std2_vol)
std3_button = Button(THM_frame, width=10, 
					 text='%s mL(S3)' %vol_array[2], 
					 font=myfont, command=std3_vol)
std4_button = Button(THM_frame, width=10, 
					 text='%s mL(S4)' %vol_array[3], 
					 font=myfont, command=std4_vol)
std5_button = Button(THM_frame, width=10, 
					 text='%s mL(S5)' %vol_array[4], 
					 font=myfont, command=std5_vol)
chk_button = Button(THM_frame, width=10, 
					text='%s mL(chk)' %vol_array[5], 
					font=myfont, command=chk_vol)
reset_button = Button(THM_frame, width=10,  
					  text='CLEAR', font=myfont, 
					  command=reset_label)

s.configure("bar1.Horizontal.TProgressbar", troughcolor='RoyalBlue1', 
			background='RoyalBlue1', thickness=2)
s.configure("bar2.Horizontal.TProgressbar", troughcolor='RoyalBlue1', 
			background='RoyalBlue1', thickness=2)
s.configure("bar3.Horizontal.TProgressbar", troughcolor='RoyalBlue1', 
			background='RoyalBlue1', thickness=2)
s.configure("bar4.Horizontal.TProgressbar", troughcolor='RoyalBlue1', 
			background='RoyalBlue1', thickness=2)
s.configure("bar5.Horizontal.TProgressbar", troughcolor='RoyalBlue1', 
			background='RoyalBlue1', thickness=2)
s.configure("chk.Horizontal.TProgressbar", troughcolor='RoyalBlue1', 
			background='RoyalBlue1', thickness=2)
s.configure("Manbar.Horizontal.TProgressbar", troughcolor='RoyalBlue1', 
			background='RoyalBlue1', thickness=2)

bar1 = ttk.Progressbar(THM_frame, style="bar1.Horizontal.TProgressbar", 
					   orient="horizontal", length=137, mode="indeterminate")
bar2 = ttk.Progressbar(THM_frame, style="bar2.Horizontal.TProgressbar", 
					   orient="horizontal", length=137, mode="indeterminate")
bar3 = ttk.Progressbar(THM_frame, style="bar3.Horizontal.TProgressbar", 
					   orient="horizontal", length=137, mode="indeterminate")
bar4 = ttk.Progressbar(THM_frame, style="bar4.Horizontal.TProgressbar", 
	    			   orient="horizontal", length=137, mode="indeterminate")
bar5 = ttk.Progressbar(THM_frame, style="bar5.Horizontal.TProgressbar", 
					   orient="horizontal", length=137, mode="indeterminate")
chk = ttk.Progressbar(THM_frame, style="chk.Horizontal.TProgressbar", 
					  orient="horizontal", length=137, mode="indeterminate")
Manbar = ttk.Progressbar(conc_frame, style="Manbar.Horizontal.TProgressbar", 
					     orient="horizontal", length=107, mode="indeterminate")

bar1.place(y=47)
bar2.place(y=105)
bar3.place(y=161)
bar4.place(y=219)
bar5.place(y=275)
chk.place(y=332)
Manbar.place(x=261, y=219)

std1_label = Label(THM_frame, width=25, bg='RoyalBlue1')
std2_label = Label(THM_frame, width=25, bg='RoyalBlue1')
std3_label = Label(THM_frame, width=25, bg='RoyalBlue1')
std4_label = Label(THM_frame, width=25, bg='RoyalBlue1')
std5_label = Label(THM_frame, width=25, bg='RoyalBlue1')
chk_label = Label(THM_frame, width=25, bg='RoyalBlue1')

status_label = Label(THM_frame, width=12, bg='White', text=' ', font=myfont)
status_label.config(text='%s' % (file_name.split('/')[5]))

std1_button.grid(row=0, pady=10)
std2_button.grid(row=1, pady=10)
std3_button.grid(row=2, pady=10)
std4_button.grid(row=3, pady=10)
std5_button.grid(row=4, pady=10)

chk_button.grid(row=5, pady=10)
reset_button.grid(row=3, column =2, sticky='W')

std1_label.grid(row=0, column=1, pady=10, sticky='NSW')
std2_label.grid(row=1, column=1, pady=10, sticky='NSW') 
std3_label.grid(row=2, column=1, pady=10, sticky='NSW')
std4_label.grid(row=3, column=1, pady=10, sticky='NSW')
std5_label.grid(row=4, column=1, pady=10, sticky='NSW')
chk_label.grid(row=5, column=1, pady=10, sticky='NSW')
status_label.grid(row=1, column=2, sticky='W')

sel_button = Button(THM_frame, text="Load Method", 
					width=10, command=lambda: load_method('loader'), 
					font=myfont)
sel_button.grid(row=0, column=2, sticky='W')
edit_button = Button(THM_frame, text="Edit Method", 
					 width=10, command=lambda: load_method('editor'), 
					 font=myfont)
edit_button.grid(row=2, column=2, sticky='W')
# dispenser end----------------------------------------------------------------------------------------------------------------



# Titrator start----------------------------------------------------------------------------------------------------------------	
device = AtlasI2C()
#device.query("Sleep")
spectra = Adafruit_AS726x.Adafruit_AS726x()

def calibrate():
	#device.query('cal,clear')
	if tkMessageBox.askyesno('7.00', 'Is pH 7.00 reading stabilized?'):
		temp = sensor.get_temperature()
		device.query("T"+str(temp))
		device.query('cal,mid, 7.00')																
		if tkMessageBox.askyesno('4.00', 'Is pH 4.00 reading stabilized?'):
			temp = sensor.get_temperature()
			device.query("T"+str(temp))	
			device.query('cal,low, 4.00')
			if tkMessageBox.askyesno('10.00', 'Is pH 10.00 reading stabilized?'):	
				temp = sensor.get_temperature()
				device.query("T"+str(temp))
				device.query('cal,high, 10.00')
				tkMessageBox.showinfo('Done', 
									  'Calibration Updated with new three point calibration')
			else:
				tkMessageBox.showinfo('Done', 
									  'Calibration Updated with new two point calibration')
		else:
			tkMessageBox.showinfo('Done', 
								  'Calibration Updated with new single point calibration')
	else:
		tkMessageBox.showinfo('Info', 'Previous Calibration restored')
	pH_slope_update()	

def pH_slope_update():
	try:
		reading = device.query('slope,?')
		slope = string.split(reading, ",")
		slope_label.config(text='{}/{}'.format(slope[1],slope[2]))
	except Exception as e:
		tkMessageBox.showwarning('ERROR', message=str(e)+'\n pH circuit not workiing properly')

sensor = W1ThermSensor()
def temperature_update():
	try:
		temperature_celsius = sensor.get_temperature()
		return '{:.4s}'.format(str(temperature_celsius))
	except Exception as e:
			tkMessageBox.showerror('Error', message=e)
			return str(25.0)
		
pH_array = []
volume_array = [0]
average_volume = []
RGB = []
red_array = []
norm_red_array = []
units = ['M','N', 'mg/L', u'\u03BC'+'g/L' ]
unitvar = StringVar()  
Analyte_vol = StringVar()
blank_vol = StringVar(value='0.0')
predose_vol = StringVar(value='0.0')
titrant_conc= StringVar()
endpoint_pH = StringVar()		# check if int variable can assigned
threshold = StringVar()
Sample_ID_Var = StringVar()
filename = "/home/pi/Dispenser_gui/finalized_model_knn_extended.sav"
model = pickle.load(open(filename, 'rb'))

global conc_top
conc_top = None
class Titration_loop:
	titration_type = None
	acid_base_type = None
	p3 = None
	rf = False
	color = False
	running_titration = False
	predose = False
	prev_temp = 0
	prev_pH = 0
	stop_vol = 1.8
	set_val = 0.4
	
	def read_volume(self, step_volume):
		try:
			rem_volume = volume_check(step_volume, check = True)
				#tkMessageBox.showwarning('warning', "Not Enough Volume. Refill the syringe#1")
			return rem_volume
		except Exception as e:
			tkMessageBox.showwarning("ERROR", message=e)
			
	def read_volume_p2(self, step_volume):
		try:
			rem_volume = volume_check_p2(step_volume, check = True)
				#tkMessageBox.showwarning('warning', "Not Enough Volume. Refill the syringe#2")
			return rem_volume
		except Exception as e:
			tkMessageBox.showwarning("ERROR", message=e)
			
	def Read_pH(self):
		current_temp = temperature_update()
		f.current_temp  = float(current_temp)
		if f.current_temp >= Titration_loop.prev_temp+1 or f.current_temp <= Titration_loop.prev_temp+1:
			device.query("T," + current_temp)
			Titration_loop.prev_temp = f.current_temp
		reading = device.query("R")
		pH = string.split(reading, " ")[1]
		f_pH = float(pH)
		pH_rate = abs(f_pH - Titration_loop.prev_pH)/5      ## Change in pH over time (5s).
		Titration_loop.prev_pH = f_pH
		if pH_rate <= 0.0025:
			pH_label.config(
				text='{0:.4} pH/{1}{2}'.format(pH, current_temp,(u"\u2103").encode('utf-8')), 
				bg='SeaGreen1')
		else:
			pH_label.config(
				text='{0:.4} pH/{1}{2}'.format(pH, current_temp,(u"\u2103").encode('utf-8')), 
				bg='brown1')
		return f_pH
		
	def Dispense_step_volume(self, volume, Refill = None):
		steps = int((volume + 0.000785)/0.0000502)
		bar_update()
		p.put(steps)
		if Refill == 'go':
			#valve_control('Hardness', 'ON')
			if spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b11000000:
				spi_1.writebytes([CMD['WRITE'] | REG['CR1'], 0b11000000])	
		else: 								# Dispense
			if spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b01000000:
				spi_1.writebytes([CMD['WRITE'] | REG['CR1'], 0b01000000])
			
		self.p3 = Process(target=dispense_loop)
		self.p3.deamon = True
		self.p3.start()	
		
	def Dispense_step_volume_p2(self, volume, Refill = None):
		steps = int((volume + 0.000785)/0.0000502)
		bar_update_p2()
		proc_queue2.put(steps)
		if Refill == 'go':
			#valve_control('Alkalinity', 'ON')
			if spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b11000000:
				spi_2.writebytes([CMD['WRITE'] | REG['CR1'], 0b11000000])	
		else: 								# Dispense
			if spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b01000000:
				spi_2.writebytes([CMD['WRITE'] | REG['CR1'], 0b01000000])
			
		self.p3 = Process(target=dispense_loop_p2)
		self.p3.deamon = True
		self.p3.start()	
		
	def var_window(self):
		global conc_top
		global variable_list
		variable_list = []
		conc_top = Toplevel()
		conc_top.title('Variable Window')
		conc_top.geometry('+160+60')

		var_frame = Frame(conc_top)
		var_frame.grid(row=0, sticky='nsew')

		conc_label = Label(var_frame, text='Titrant Concentration:')
		conc_label.grid(row=0, column=0,sticky = 'nsew')
		conc_entry = Entry(var_frame, width = 10,textvariable = titrant_conc)
		conc_entry.grid(row=0, column=1, sticky ='nsew')

		unitvar.set('-UNITS-')                     # define it as class/instance variable
		unitbox = ttk.Combobox(var_frame, textvariable = unitvar, 
							   values = units, state="readonly", 
							   width =10)#,font =myfont)
		unitbox.grid(row=0, column=2)

		vol_label = Label(var_frame, text='Sample Volume:')
		vol_label.grid(row=1, column=0, pady=1, sticky = 'nsew')
		vol_entry = Entry(var_frame, width =10, textvariable = Analyte_vol)
		vol_entry.grid(row=1, column=1, pady=1, sticky = 'nsew')

		blank_vol_label = Label(var_frame, text='Blank Volume:')
		blank_vol_label.grid(row=2, column=0, pady=1, sticky = 'nsew')
		blank_vol_entry = Entry(var_frame, width =10, 
							    textvariable=blank_vol, text=0.0)
		blank_vol_entry.grid(row=2, column=1, pady=1, sticky = 'nsew')

		ml_label = Label(var_frame, text='mL')
		ml_label.grid(row=1, column=2, pady=1,sticky = 'w')

		blank_ml_label = Label(var_frame, text='mL')
		blank_ml_label.grid(row=2, column=2, pady=1,sticky = 'w')

		predose_vol_label = Label(var_frame, text='Predose:')
		predose_vol_label.grid(row=3, column=0, pady=1, sticky = 'nsew')
		predose_vol_entry = Entry(var_frame, width =10, 
								  textvariable=predose_vol, text=0.0)
		predose_vol_entry.grid(row=3, column=1, pady=1, sticky = 'nsew')
		predose_ml_label = Label(var_frame, text='mL')
		predose_ml_label.grid(row=3, column=2, pady=1,sticky = 'w')

		endpoint_label= Label(var_frame, text= "Endpoint pH:")
		endpoint_label.grid(row=4,column=0, sticky='nsew')
		endpoint_bar = Scale(var_frame, from_=0, to=14, 
							 length = 200, resolution = 0.01, 
							 variable = endpoint_pH, orient = HORIZONTAL)
		endpoint_bar.grid(row=4, column=1,columnspan =3)

		threshold_label = Label(var_frame, text= "Threshold:")
		threshold_label.grid(row=5, column = 0,sticky = 'nsew')
		threshold_bar = Scale(var_frame, from_=200, to=2000, 
							  length = 200, resolution = 50, 
							  variable=threshold, orient = HORIZONTAL)
		threshold_bar.grid(row=5, column=1,columnspan =3)

		Sample_type = Label(var_frame, text = 'Sample_ID')
		Sample_type.grid(row=6,sticky = 'nsew')

		R1 = Radiobutton(var_frame, text="Raw", 
						 variable=Sample_ID_Var, value='Raw')  
		R1.grid(row=6, column = 1)         
		R2 = Radiobutton(var_frame, text="Finished", 
						 variable=Sample_ID_Var, value='Finished')
		R2.grid(row=6, column = 2) 
		R1.select()

		close_button = Button(var_frame, text= "Ok", 
							  width = 10, command = self.titration_go)
		close_button.grid(row=7, column=1, pady=5)
		variable_list = [
			vol_entry, conc_entry, 
			blank_vol_entry, predose_vol_entry
			]

		for entry in variable_list:
			entry.bind('<Button-1>', Topfocus)
		
		titre_type = methodvar.get()
		if titre_type == 'Alkalinity':
			unitvar.set('M')
			predose_vol.set('0.9')
			Analyte_vol.set('15')
			titrant_conc.set('0.02')
		elif titre_type == 'Hardness':
			unitvar.set('M')
			predose_vol.set('0.9')
			Analyte_vol.set('15')
			titrant_conc.set('0.01')
			
	def titration_go(self):
		global conc_top
		conc_top.destroy()
		titration_type = methodvar.get()
		Titration_loop.running_titration = True
		reading = device.query("R")
		initpH = float(string.split(reading, " ")[1])
		pH_label.config(text='{:.4} pH'.format(initpH))
		if titration_type == "Acid-Base":
			if tkMessageBox.askyesno(
					'start', 
					'Is beaker with analyte ready?\n' '\n' 'Is syringe filled with titrant?'):
				valve_control('Alkalinity', 'OFF')
				Enable(1, 0)
				pH_array.append(initpH)
				if initpH < 7:
					if endpoint_pH.get() == '0.00':
						endpoint_pH.set('12')
						Titration_loop.acid_base_type = "fullscale"
					else:
						Titration_loop.acid_base_type = "setpoint"
					if float(predose_vol.get()) == 0.0:
						Titration_loop.predose = False
					elif float(predose_vol.get()) > 0.0:
						Titration_loop.predose = True
					Titration.acid()
				elif initpH > 7:
					if endpoint_pH.get() == '0.00':
						endpoint_pH.set('2')
						Titration_loop.acid_base_type = "fullscale"
					else:
						Titration_loop.acid_base_type = "setpoint"
					if float(predose_vol.get()) == 0.0:
						Titration_loop.predose = False
					elif float(predose_vol.get()) > 0.0:
						Titration_loop.predose = True
					Titration.base()
		elif titration_type == "Alkalinity":
			if tkMessageBox.askyesno(
					'start', 
					'Is beaker with sample ready?\n''\n' 'Is syringe filled with Acid?'):
				if initpH >= 4.3:
					Enable_p2(1, 0)
					valve_control('Alkalinity', 'OFF')
					pH_array.append(initpH)
					if float(predose_vol.get()) == 0.0:
						Titration_loop.predose = False
					elif float(predose_vol.get()) > 0.0:
						Titration_loop.predose = True
					Titration.alkalinity()
				elif initpH < 4.3:
					tkMessageBox.showinfo('DONE', 'pH Already Below 4.3')
					titration_button.config(text = "START")	
		elif titration_type =="Colorimetry":
			if tkMessageBox.askyesno(
					'start', 
					'Is beaker with analyte ready?\n''\n' 'Is syringe filled with Base?'):
				Enable(1, 0)
				valve_control('Alkalinity', 'OFF')
				try:
					spectra.setup()
					spectra.setDrvCurrent(0b10)	
					spectra.drvOn()
				except Exception as err:
					tkMessageBox.showwarning("ERROR", err)
					titration_button.config(text = "START")	
				if float(predose_vol.get()) == 0.0:
					Titration_loop.predose = False
				elif float(predose_vol.get()) > 0.0:
					Titration_loop.predose = True
				root.after(100, lambda:get_baseline('General'))
		elif titration_type =="Hardness":
			if tkMessageBox.askyesno(
					'start', 
					'Is beaker with analyte ready?\n''\n' 'Is syringe filled with Titrant?'):
				Enable(1, 0)
				valve_control('Hardness', 'OFF')
				Titration_loop.set_val = 0.4
				#threshold.set("1150")
				try:
					spectra.setup()
					spectra.setDrvCurrent(0b10)	
					spectra.drvOn()
				except Exception as err:
					tkMessageBox.showwarning("ERROR", err)
					titration_button.config(text = "START")
				if float(predose_vol.get()) == 0.0:
					Titration_loop.predose = False
				elif float(predose_vol.get()) > 0.0:
					Titration_loop.predose = True	
				root.after(100, lambda:get_baseline('Hardness'))	
		elif titration_type =="   -Method-":	
			tkMessageBox.showwarning(
				'Method', 
				'select a method from dropdown to proceed')
			titration_button.config(text = "START")				
		
	def Refill(self):
		#if tkMessageBox.askyesno("Refill", "Place the refill solution under the pump#1 dispense line "):
		valve_control('Hardness', 'ON')
		distance = pot.read_adc_difference(p1_channel, gain=GAIN)
		calib_volume = 	float(calibrate_calc1(distance))
		self.Dispense_step_volume((calib_volume + 0.05), Refill = 'go')
		Titration_loop.rf=True
		self.initiate_hardness()
			
	def Refill_p2(self):
		#if tkMessageBox.askyesno("Refill", "Place the refill solution under the pump#2 dispense line"):
		valve_control('Alkalinity', 'ON')
		distance = pot.read_adc_difference(p2_channel, gain=GAIN)
		calib_volume = 	float(calibrate_calc2(distance))
		self.Dispense_step_volume_p2((calib_volume + 0.15), Refill = 'go')
		Titration_loop.rf=True
		self.initiate()					
		
	def acid(self):
		Titration_loop.titration_type = "acid"
		pH = self.Read_pH()
		if pH >= float(endpoint_pH.get()):
			if Titration_loop.acid_base_type == "fullscale":
				Titration_loop.titration_type = None
				Titration_loop.acid_base_type = None
				self.graph_update()
				#if len(pH_array) == len(volume_array):
				if True == True:
					firs_derivative = diff(pH_array)/diff(volume_array)
				else:
					tkMessageBox.showerror('value error', 'Values missing, redo Titration')
				end_volume = average_volume[firs_derivative[:].argmax()] - float(blank_vol.get())
				end_vol_update.config(text = '{}'.format(end_volume))
				ax1.axvline(x=average_volume[firs_derivative[:].argmax()], color='blue')
				ax2.axvline(x=average_volume[firs_derivative[:].argmax()], color='blue')
				del volume_array[1:]
				del pH_array[:]
				del average_volume[:]
				#titration_button.config(text = "START")	
				Titration_loop.running_titration = False
				tkMessageBox.showinfo('Done', 'Titration Completed')
				try:
					analyte_conc = (float(titrant_conc.get())*end_volume)/float(Analyte_vol.get())  
					conc_update.config(text = '{0}{1}'.format(analyte_conc, unitvar.get()))
				except:
					conc_update.config(text = '0.0')
				return

			elif Titration_loop.acid_base_type == "setpoint":
				Titration_loop.titration_type = None
				Titration_loop.acid_base_type = None
				self.graph_update()
				final_vol = volume_array[-1] - volume_array[-2]
				Interpol_vol = ((final_vol/(float(pH)) - pH_array[-2])*(float(endpoint_pH.get()) - pH_array[-2]) + volume_array[-2]) - float(blank_vol.get())
				end_vol_update.config(text ='{:.4}'.format(Interpol_vol))
				del volume_array[1:]
				del pH_array[:]
				del average_volume[:]
				#titration_button.config(text = "START")	
				Titration_loop.running_titration = False
				try:
					analyte_conc = (float(titrant_conc.get())*Interpol_vol)/float(Analyte_vol.get())  
					conc_update.config(text = '{0}{1}'.format(analyte_conc, unitvar.get()))
				except:
					conc_update.config(text = '0.0')
				self.Refill()
				tkMessageBox.showinfo('Done', 'Titration Completed')
				return					

		elif pH < float(endpoint_pH.get()):
			if abs(pH -pH_array[len(pH_array) - 1]) > 0.1:
				if Titration_loop.predose == True:
					step_volume = float(predose_vol.get())
				else:
					step_volume = 0.05
				if self.read_volume(step_volume) != False:
					self.Dispense_step_volume(step_volume)
					Titration_loop.predose = False
					self.initiate()
					volume_array.append(volume_array[len(volume_array)-1] + step_volume)
					if len(volume_array) > 1:
						average_volume.append((volume_array[-1]+volume_array[-2])/2)								
				else:
					self.Refill()
			elif abs(pH - pH_array[len(pH_array) - 1]) < 0.1:
				if Titration_loop.predose == True:
					step_volume = float(predose_vol.get())
				else:
					step_volume = 0.1
				if self.read_volume(step_volume) != False:
					self.Dispense_step_volume(step_volume)
					Titration_loop.predose = False
					self.initiate()
					volume_array.append(volume_array[len(volume_array)-1] + step_volume)
					if len(volume_array) > 1:
						average_volume.append((volume_array[-1]+volume_array[-2])/2)								
				else:
					self.Refill()	
					  
	def base(self):
		Titration_loop.titration_type = "base"
		pH = self.Read_pH()
		if pH <= float(endpoint_pH.get()):
			if Titration_loop.acid_base_type == "fullscale":
				Titration_loop.titration_type = None
				Titration_loop.acid_base_type = None
				self.graph_update()
				if len(pH_array) == len(volume_array):
					firs_derivative = diff(pH_array)/diff(volume_array)
				else:
					tkMessageBox.showerror('value error', 'Values missing, redo Titration')
				end_volume = average_volume[firs_derivative[:].argmin()] - float(blank_vol.get())
				end_vol_update.config(text ='{}'.format(end_volume))
				ax1.axvline(x=average_volume[firs_derivative[:].argmin()], color='blue')
				ax2.axvline(x=average_volume[firs_derivative[:].argmin()], color='blue')
				del volume_array[1:]
				del pH_array[:]
				del average_volume[:]
				#titration_button.config(text = "START")	
				Titration_loop.running_titration = False
				try:
					analyte_conc = (float(titrant_conc.get())*end_volume)/float(Analyte_vol.get())  
					conc_update.config(text = '{0}{1}'.format(analyte_conc, unitvar.get()))
				except:
					conc_update.config(text = '0.0')
				self.Refill()
				tkMessageBox.showinfo('Done', 'Titration Completed')
				return
			elif Titration_loop.acid_base_type == "setpoint":
				Titration_loop.titration_type = None
				Titration_loop.acid_base_type = None
				self.graph_update()
				final_vol = volume_array[-1] - volume_array[-2]
				Interpol_vol = ((final_vol/(pH_array[-2] - float(pH)))*(pH_array[-2] - float(endpoint_pH.get())) + volume_array[-2]) - float(blank_vol.get())
				end_vol_update.config(text ='{:.4}'.format(Interpol_vol))
				del volume_array[1:]
				del pH_array[:]
				del average_volume[:]
				#titration_button.config(text = "START")	
				Titration_loop.running_titration = False
				tkMessageBox.showinfo('Done', 'Titration Completed')
				try:
					analyte_conc = (float(titrant_conc.get())*Interpol_vol)/float(Analyte_vol.get())  
					conc_update.config(text = '{0}{1}'.format(analyte_conc, unitvar.get()))
				except:
					conc_update.config(text = '0.0')
				return	
		elif pH > float(endpoint_pH.get()):
			if abs(pH -pH_array[len(pH_array) - 1]) > 0.1:
				if Titration_loop.predose == True:
					step_volume = float(predose_vol.get())
				else:
					step_volume = 0.05
				if self.read_volume(step_volume) != False:
					self.Dispense_step_volume(step_volume)
					Titration_loop.predose = False
					self.initiate()
					volume_array.append(volume_array[len(volume_array)-1] + step_volume)
					if len(volume_array) > 1:
						average_volume.append((volume_array[-1]+volume_array[-2])/2)							
				else:
					self.Refill()				
			elif abs(pH -pH_array[len(pH_array) - 1]) < 0.1:
				if Titration_loop.predose == True:
					step_volume = float(predose_vol.get())
				else:
					step_volume = 0.1
				if self.read_volume(step_volume) != False:
					self.Dispense_step_volume(step_volume)
					Titration_loop.predose = Falses
					self.initiate()	
					volume_array.append(volume_array[len(volume_array)-1] + step_volume)
					if len(volume_array) > 1:
						average_volume.append((volume_array[-1]+volume_array[-2])/2)								
				else:
					self.Refill()		
			
	def alkalinity(self):
		Titration_loop.titration_type = "alkalinity"
		pH = self.Read_pH()
		if pH < 4.3:   
			Titration_loop.titration_type = None
			self.graph_update()
			final_vol = volume_array[-1] - volume_array[-2]
			Interpol_vol = ((final_vol/(pH_array[-2] - float(pH)))*(pH_array[-2] - 4.3) + volume_array[-2]) - float(blank_vol.get())
			end_vol_update.config(text ='{:.4}'.format(Interpol_vol))
			del volume_array[1:]
			del pH_array[:]
			del average_volume[:]
			Titration_loop.running_titration = False

			try:
				analyte_conc = (float(titrant_conc.get())*Interpol_vol*50000)/float(Analyte_vol.get())  
				conc_update.config(text = '{0:.5} mg CaCO{1}/L'.format(analyte_conc, (u'\u2083').encode('utf-8')))
				Alkalinity_file_exist = os.path.isfile('/home/pi/Dispenser_gui/Alkalinity_Result_log.csv')
				utc_time = dt.datetime.utcnow()
				tz = pytz.timezone('America/Chicago')
				local_time = pytz.utc.localize(utc_time, is_dst=None).astimezone(tz)
				formatted_localtime = local_time.strftime('%Y-%m-%d')
				with open('/home/pi/Dispenser_gui/Alkalinity_Result_log.csv', 'a') as csvfile:
					fieldnames_alkalinity = ['Date/Time','Sample_ID(A)', 'Alkalinity (mg/L CaCO3)']
					Alkalinity_result = csv.DictWriter(csvfile, fieldnames=fieldnames_alkalinity)
					if not Alkalinity_file_exist:
						Alkalinity_result.writeheader()
					Alkalinity_result.writerow(
						{'Date/Time': formatted_localtime, 'Sample_ID(A)':Sample_ID_Var.get(), 
						'Alkalinity (mg/L CaCO3)': '{0:.5}'.format(analyte_conc)
						})
			except Exception as e:
				conc_update.config(text = '0.0')
				tkMessageBox.showwarning("ERROR", message=e)
			Report.update_Alkalinity()
			self.Refill_p2()
			tkMessageBox.showinfo('Done', 'Titration Completed')
			return

		elif pH > 6:
			if Titration_loop.predose == True:
				step_volume = float(predose_vol.get())
			else:
				step_volume = 0.1
			if self.read_volume_p2(step_volume) != False:					
				Titration_loop.predose = False
				Total_dispensed = volume_array[len(volume_array) - 1] + step_volume
				if Total_dispensed < Titration_loop.stop_vol:
					self.Dispense_step_volume_p2(step_volume)
					self.initiate()
					volume_array.append(volume_array[len(volume_array)-1] + step_volume)	
					if len(volume_array) > 1:
						average_volume.append((volume_array[-1]+volume_array[-2])/2)	
				else:
					Titration_loop.titration_type = None
					del volume_array[1:]
					del pH_array[:]
					del average_volume[:]
					Titration_loop.running_titration = False
					self.Refill_p2()
					tkMessageBox.showinfo(
						'No Endpoint', 
						'Endpoint not detected even after {}mL'.format(Titration_loop.stop_vol))								
					return
			else:
				self.Refill_p2()		
		elif pH <= 6:
			if Titration_loop.predose == True:
				step_volume = float(predose_vol.get())
			else:
				step_volume = 0.05
			if self.read_volume_p2(step_volume) != False:
				Titration_loop.predose = False
				Total_dispensed = volume_array[len(volume_array) - 1] 
				if Total_dispensed < Titration_loop.stop_vol:
					self.Dispense_step_volume_p2(step_volume)
					self.initiate()
					volume_array.append(volume_array[len(volume_array)-1] + step_volume)	
					if len(volume_array) > 1:
						average_volume.append((volume_array[-1]+volume_array[-2])/2)				
				else:
					Titration_loop.titration_type = None
					del volume_array[1:]
					del pH_array[:]
					del average_volume[:]
					Titration_loop.running_titration = False
					self.Refill_p2()
					tkMessageBox.showinfo(
						'No Endpoint', 
						'Endpoint not detected even after {}mL'.format(Titration_loop.stop_vol))
					return	
			else:
				self.Refill_p2()		
	
	def Hardness(self, refill = False):
		Titration_loop.color = True
		Titration_loop.titration_type = 'Hardness'
		condition = []	
		spectra.startMeasurement()
		rdy = False
		while not rdy:
			time.sleep(.005)
			rdy = spectra.dataAvailable()
		new_RGB = spectra.readRawValues()
		if refill == False:
			red_array.append(new_RGB[5])
			norm_red = (float(new_RGB[5]/float(sum(new_RGB))))*100
			norm_red_array.append(norm_red)
		self.hardness_graph_update()
		result = model.predict([new_RGB])
		if result[0] == 'blue':
		#if len(norm_red_array) > 1:
			if abs(norm_red_array[len(norm_red_array) - 2] - norm_red) < Titration_loop.set_val:
			#if abs(firs_derivative[-2]-firs_derivative[-1]) < Titration_loop.set_val:
		#if norm_red < 6:
			#titration_type = None
			#color = False
			#end_volume = volume_array[len(volume_array) - 1]
			#end_vol_update.config(text='{}'.format(end_volume))
			#del volume_array[1:]
			#del RGB[:]
			#del condition[:]
			#spectra.drvOff()
			#titration_button.config(text = "START")	
			#Titration_loop.running_titration = False
			#tkMessageBox.showinfo('Done', 'Titration Completed')
			#if len(red_array) == len(volume_array):
				#firs_derivative = diff(red_array)/diff(volume_array)
			#else:
				#tkMessageBox.showerror('value error', 'Values missing, redo Titration')
			#end_volume = average_volume[firs_derivative[:].argmin()]
			#end_vol_update.config(text ='{}'.format(end_volume))
			#ax1.axvline(x=average_volume[firs_derivative[:].argmin()], color='blue')
			#ax2.axvline(x=average_volume[firs_derivative[:].argmin()], color='blue')
				#final_vol = volume_array[-1] - volume_array[-2]
				#end_volume = (final_vol/(norm_red_array[-2] - norm_red))*(norm_red_array[-2] - 6) + volume_array[-2]
				Titration_loop.titration_type = None
				Titration_loop.color = False
				self.hardness_graph_update()
				if len(red_array) == len(volume_array):
					firs_derivative = diff(red_array)/diff(volume_array)
				else:
					tkMessageBox.showerror('value error', 'Values missing, redo Titration')
				end_volume = average_volume[firs_derivative[:].argmin()]
				ax1.axvline(x=average_volume[firs_derivative[:].argmin()], color='blue')
				ax2.axvline(x=average_volume[firs_derivative[:].argmin()], color='blue')
				end_vol_update.config(text ='{}'.format(end_volume))
				del volume_array[1:]
				del red_array[:]
				del norm_red_array[:]
				del average_volume[:]
				spectra.drvOff()	
				Titration_loop.running_titration = False
				result = model.predict([new_RGB])
				try:
					analyte_conc = (float(titrant_conc.get())*end_volume*100000)/float(Analyte_vol.get())  
					conc_update.config(text = '{0:.5} mg CaCO{1}/L'.format(analyte_conc, (u'\u2083').encode('utf-8')))
					Hardness_file_exist = os.path.isfile('/home/pi/Dispenser_gui/Hardness_Result_log.csv')
					utc_time = dt.datetime.utcnow()
					tz = pytz.timezone('America/Chicago')
					local_time = pytz.utc.localize(utc_time, is_dst=None).astimezone(tz)
					formatted_localtime = local_time.strftime('%Y-%m-%d')
					with open('/home/pi/Dispenser_gui/Hardness_Result_log.csv', 'a') as csvfile:
						fieldnames_hardness = ['Date/Time(H)', 'Sample_ID', 'Hardness (mg/L CaCO3)'] 
						Hardness_result = csv.DictWriter(csvfile, fieldnames=fieldnames_hardness)
						if not Hardness_file_exist:
							Hardness_result.writeheader()
						Hardness_result.writerow(
							{'Date/Time(H)': formatted_localtime, 'Sample_ID': Sample_ID_Var.get(), 
							'Hardness (mg/L CaCO3)':'{0:.5}'.format(analyte_conc)
							})
				except Exception as e:
					conc_update.config(text = '0.0')
					tkMessageBox.showwarning("ERROR", message=e)
				Report.update_Hardness()		
				self.Refill()
				#titration_button.config(text = "START")
				tkMessageBox.showinfo('Done', 'Titration Completed.')
				return
			else:
				step_volume = 0.05
				if self.read_volume(step_volume) != False:
					self.Dispense_step_volume(step_volume)
					Total_dispensed = volume_array[len(volume_array) - 1] + step_volume
					if Total_dispensed >= Titration_loop.stop_vol:
						Titration_loop.set_val = 1
					self.initiate_hardness()
					volume_array.append(volume_array[len(volume_array) - 1] + step_volume)
					if len(volume_array) > 1:
						average_volume.append((volume_array[-1]+volume_array[-2])/2)					 
				else:
					self.Refill()
		else:
			if Titration_loop.predose == True:
				step_volume = float(predose_vol.get())				
			else:
				step_volume = 0.05
			if self.read_volume(step_volume) != False:
				Titration_loop.predose = False
				Total_dispensed = volume_array[len(volume_array) - 1]
				if Total_dispensed <= Titration_loop.stop_vol:
					self.Dispense_step_volume(step_volume)
					self.initiate_hardness()
					volume_array.append(volume_array[len(volume_array)-1] + step_volume)	
					if len(volume_array) > 1:
						average_volume.append((volume_array[-1]+volume_array[-2])/2)
				else:
					Titration_loop.titration_type = None
					Titration_loop.color = False
					del volume_array[1:]
					del red_array[:]
					del norm_red_array[:]
					del average_volume[:]
					spectra.drvOff()	
					Titration_loop.running_titration = False
					self.Refill()
					tkMessageBox.showerror(
						'No Endpoint', 
						'Endpoint not detected even after {}mL'.format(Titration_loop.stop_vol))
					return
			else:
				self.Refill()		
		
	def Colorimetry(self):
		Titration_loop.color = True
		Titration_loop.titration_type = 'Colorimetry'
		condition = []	
		spectra.startMeasurement()
		rdy = False
		while not rdy:
			time.sleep(.005)
			rdy = spectra.dataAvailable()
		new_RGB = spectra.readRawValues()
		thresh =  float(threshold.get())
		for count, value in enumerate(new_RGB):
			if RGB[count] - thresh > value or value > RGB[count] + thresh:
				condition.append(1)
			else:
				condition.append(0)
		if condition.count(1) >= 2:
			titration_type = None
			color = False
			end_volume = volume_array[len(volume_array) - 1] - float(blank_vol.get())
			end_vol_update.config(text='{}'.format(end_volume))
			del volume_array[1:]
			del RGB[:]
			del condition[:]
			spectra.drvOff()
			#titration_button.config(text = "START")	
			Titration_loop.running_titration = False
	
			try:
				analyte_conc = (float(titrant_conc.get())*end_volume)/float(Analyte_vol.get())  
				conc_label.config(text = '{0}{1}'.format(analyte_conc, unitvar.get()))
			except:
				conc_label.config(text = '0.0')
			self.Refill()
			tkMessageBox.showinfo('Done', 'Titration Completed')
			return
		else:
			step_volume = 0.05
			if self.read_volume(step_volume) != False:
				self.Dispense_step_volume(step_volume)
				self.initiate()
				volume_array.append(volume_array[len(volume_array) - 1] + step_volume)						 
			else:
				self.Refill()		
		
	def graph_update(self):
		if len(pH_array) == len(volume_array):
			firs_derivative = diff(pH_array) / diff(volume_array)
		else:
			tkMessageBox.showerror('value error', 'Values missing, Stop and redo Titration')
		ax1.clear()
		ax2.clear()
		ax1.set_ylabel('pH')
		ax1.set_xlabel('Volume (mL)')
		ax1.xaxis.set_label_coords(0.5, 1.2)
		ax1.xaxis.set_label_coords(0.5, 1.2)
		ax1.set_ylim(0,14.5)         
		ax1.grid(b=True, which='major', color='green', linestyle='-')
		ax1.grid(b=True, which='minor', color='black', linestyle=':', alpha=0.2)
		ax1.minorticks_on()
		ax2.set_ylabel(r'$\Delta$''pH/'r'$\Delta$''v')
		ax2.grid(b=True, which='major', color='green', linestyle='-')
		ax2.grid(b=True, which='minor', color='black', linestyle=':', alpha=0.2)
		ax2.minorticks_on()
		#ax2.yaxis.set_major_formatter(FormatStrFormatter('%0.2f'))
		ax1.plot(volume_array, pH_array)
		ax2.plot(average_volume, firs_derivative)
		f.canvas.draw_idle()
		
	def hardness_graph_update(self):
		if len(red_array) == len(volume_array):
			Hardness_firs_derivative = diff(red_array) / diff(volume_array)
		else:
			tkMessageBox.showerror('value error', 'Values missing, Stop and redo Titration')
		ax1.clear()
		ax2.clear()
		ax1.set_ylabel('I')
		ax1.set_xlabel('Volume (mL)')
		ax1.xaxis.set_label_coords(0.5, 1.2)
		ax1.xaxis.set_label_coords(0.5, 1.2)
		#ax1.set_ylim(0,14)         
		ax1.grid(b=True, which='major', color='green', linestyle='-')
		ax1.grid(b=True, which='minor', color='black', linestyle=':', alpha=0.2)
		ax1.minorticks_on()
		ax2.set_ylabel(r'$\Delta$''I/'r'$\Delta$''v')
		ax2.grid(b=True, which='major', color='green', linestyle='-')
		ax2.grid(b=True, which='minor', color='black', linestyle=':', alpha=0.2)
		ax2.minorticks_on()
		#ax2.yaxis.set_major_formatter(FormatStrFormatter('%0.2f'))
		ax1.plot(volume_array, red_array)
		ax2.plot(average_volume, Hardness_firs_derivative)
		f.canvas.draw_idle()

	def check_stop(self):
		if titration_button['text'] == "STOP":
			return False
		else:
			return True
			
	def initiate(self):
			global barupdate_id_p2
			titre_type = Titration_loop.titration_type
			iid = root.after(500, self.initiate)
			try:
				fork = r2.get(False)
				if fork == 1:
					root.after_cancel(iid)	
					self.p3.join()
					self.p3 = None
					if self.check_stop() == False:
						if Titration_loop.color == False and Titration_loop.rf == False:
							pH = self.Read_pH()
							pH_array.append(pH)
							self.graph_update()
						if Titration_loop.rf == True:
							root.after_cancel(barupdate_id_p2)
							Titration_loop.rf = False
							#valve_control('Alkalinity', 'ON')
							self.Dispense_step_volume_p2(0.2)
							time.sleep(10)
							r2.get(False)
							root.after_cancel(barupdate_id_p2)
							#if tkMessageBox.askyesno('Ready', 'Refill Completed.\n''\n' 'Place the analyte beaker back under the dispensing tube.'): 
							if titre_type == "acid":
								root.after(5000, self.acid)
							elif titre_type == "base":
								root.after(5000, self.base)
							elif titre_type == "alkalinity":
								root.after(5000, self.alkalinity)
							elif titre_type == "Colorimetry":
								root.after(5000, self.Colorimetry)
							elif titre_type == None:
								titration_button.config(text = "START")	
								return
																
						else:
							root.after_cancel(barupdate_id_p2)
							if titre_type == "acid":
								root.after(5000, self.acid)
							elif titre_type == "base":
								root.after(5000, self.base)
							elif titre_type == "alkalinity":
								root.after(5000, self.alkalinity)
							elif titre_type == "Colorimetry":
								root.after(5000, self.Colorimetry)
					else:
						Titration_loop.titration_type = None
						Titration_loop.color = False
						del volume_array[1:]
						del red_array[:]
						del norm_red_array[:]
						del pH_array[:]
						del average_volume[:]
						spectra.drvOff()
						root.after_cancel(barupdate_id_p2)	
						Titration_loop.running_titration = False
						tkMessageBox.showinfo('Done', 'Titration Aborted')
			except Empty:
				pass	
				
	def initiate_hardness(self):
			global barupdate_id
			titre_type = Titration_loop.titration_type
			iid = root.after(500, self.initiate_hardness)
			try:
				fork = r.get(False)
				if fork == 1:
					root.after_cancel(iid)	
					self.p3.join()
					self.p3 = None
					if self.check_stop() == False:
						if Titration_loop.rf == True:
							root.after_cancel(barupdate_id)
							Titration_loop.rf = False
							#valve_control('Hardness', 'ON')
							self.Dispense_step_volume(0.25)
							time.sleep(10)
							r.get(False)
							root.after_cancel(barupdate_id)
							#if tkMessageBox.askyesno('Ready', 'Refill Completed.\n''\n' 'Place the analyte beaker back under the dispensing tube.'): 
							if titre_type == "Hardness":
								root.after(10000, lambda:self.Hardness(refill = True))
							elif titre_type == None:
								titration_button.config(text = "START")
								return								
						else:
							root.after_cancel(barupdate_id)
							if titre_type == "Hardness":
								root.after(10000, self.Hardness)
					else:
						Titration_loop.titration_type = None
						Titration_loop.color = False
						del volume_array[1:]
						del red_array[:]
						del norm_red_array[:]
						del average_volume[:]
						spectra.drvOff()
						root.after_cancel(barupdate_id)	
						Titration_loop.running_titration = False
						tkMessageBox.showinfo('Done', 'Titration Aborted')					
			except Empty:
				pass	
				
		
def start_titration():
	if titration_button['text'] == "START":
		end_vol_update.config(text = '0.0')
		conc_update.config(text = ' ')
		titration_button.config(text = "STOP")
		Titration.var_window()
		
	else:
		titration_button.config(text = "START")	
		Titration_loop.running_titration = False
		Titration_loop.titration_type = None
		Titration_loop.color = False
		del volume_array[1:]
		del red_array[:]
		del norm_red_array[:]
		del average_volume[:]
		del pH_array[:]
		spectra.drvOff()		

def get_baseline(type_of_titration):
	#for channel in (spectra.readViolet, spectra.readBlue, spectra.readGreen, spectra.readYellow, spectra.readOrange, spectra.readRed):
		#channel_data = []
		#for x in range(0, 5):
			#spectra.startMeasurement()
			#rdy = False
			#while not rdy:
				#time.sleep(.005)
				#rdy = spectra.dataAvailable()
			#channel_data.append(channel())
		#channel_average = sum(channel_data) / len(channel_data)
		#RGB.append(channel_average)
	##print RGB
	#if type_of_titration == 'Hardness':
		#Titration.Hardness()
	#elif type_of_titration == 'General':
		#Titration.Colorimetry()
	spectra.startMeasurement()
	rdy = False
	while not rdy:
			time.sleep(.005)
			rdy = spectra.dataAvailable()
	new_RGB = spectra.readRawValues()
	result = model.predict([new_RGB])
	tkMessageBox.showinfo('Color', '{} color detected'.format(result[0]))
	if result[0] == 'red':
		Titration.Hardness()
	else:
		tkMessageBox.showinfo('END', 'Titration stopped as solution already in blue')
	

def get_pH():
	def pH_loop():
		global get_id
		Titration.Read_pH()
		get_id = root.after(5000, pH_loop)
	state = pbutton['text']
	if state == 'Read':
		pbutton.config(text='Stop')
		pH_loop()
	else:
		pbutton.config(text='Read')
		root.after_cancel(get_id)


Titration = Titration_loop()

class Create_table:
	def __init__(self):
		report_subframe_Hardness = Frame(Hardness_mainframe)
		report_subframe_Hardness.pack(fill=BOTH, expand=1)
		report_subframe_Alkalinity = Frame(Alkalinity_mainframe)
		report_subframe_Alkalinity.pack(fill=BOTH, expand=1)
		Alkalinity = pd.read_csv('/home/pi/Dispenser_gui/Alkalinity_Result_log.csv', delimiter=',')
		Hardness = pd.read_csv('/home/pi/Dispenser_gui/Hardness_Result_log.csv', delimiter=',')
		#df = pd.concat([Hardness,Alkalinity], axis=1)
		self.table_Hardness = pt_H = Table(report_subframe_Hardness, dataframe=Hardness.sort_values(by=['Date/Time(H)'], ascending=False),
								showtoolbar=False, showstatusbar=False) 
		self.table_Alkalinity = pt_A = Table(report_subframe_Alkalinity, dataframe=Alkalinity.sort_values(by=['Date/Time'], ascending=False),
								showtoolbar=False, showstatusbar=False)                                         
		pt_H.show()
		pt_A.show()
		return
		
	def update_Hardness(self):
		Hardness = pd.read_csv('/home/pi/Dispenser_gui/Hardness_Result_log.csv')
		df = Hardness.sort_values(by='Date/Time(H)', ascending=False)
		self.table_Hardness.model.df = df
		self.table_Hardness.redraw()
		return
		
	def update_Alkalinity(self):
		Alkalinity = pd.read_csv('/home/pi/Dispenser_gui/Alkalinity_Result_log.csv')
		df = Alkalinity.sort_values(by='Date/Time', ascending=False)
		self.table_Alkalinity.model.df = df
		self.table_Alkalinity.redraw()
		return
		
Report = Create_table()	

Report = Create_table()	

style.use("ggplot")
controlframe = Frame(titer_mainframe, bg='RoyalBlue1')
controlframe.place(x=10, y=10)

pbutton = Button(controlframe, width=10, text='Read', font=myfont, command=get_pH)
pbutton.grid(row=0, column=0, pady=10)
pH_label = Label(controlframe, background='white', width=14, font=myfont)
pH_label.grid(row=0, column=1,columnspan=2)

methods = ['Acid-Base', 'Alkalinity', 'Colorimetry', 'Hardness']
methodvar = StringVar()
methodbox = ttk.Combobox(controlframe, textvariable=methodvar, 
						 values=methods, state="readonly", 
						 width=10, font=myfont)
methodvar.set('   -Method-')
methodbox.grid(row=2, column=0, pady=10)

calib_button = Button(controlframe, text="Calibrate", 
					  width=10, font=myfont, command=calibrate)
calib_button.grid(row=1, column=0)
slope_label = Label(controlframe, background='white', 
					width=14, font=myfont)
slope_label.grid(row=1, column=1)
titration_button = Button(controlframe, text="START", 
						  width=10, font=myfont, 
						  command=start_titration)
titration_button.grid(row=2, column=1, pady=10)

end_vol_label = Label(controlframe, text='End Volume( mL)', width=15)
end_vol_label.grid(row=3, column=1)
end_vol_update =Label(controlframe, text='0.0', 
					  width=10, bg='white', 
					  font=myfont)
end_vol_update.grid(row=4, column=1)

spacer_label =Label(controlframe, text = '', 
					width=10, bg='RoyalBlue1', 
					font=myfont)
spacer_label.grid(row=5, column=1)

conc_label = Label(controlframe, text='Concentration', width=15)
conc_label.grid(row=6, column=1)
conc_update = Label(controlframe, text='0.0', 
					width=10, bg='white', font=myfont, 
					wraplength=80)
conc_update.grid(row=7, column=1)

gframe= Frame(titer_mainframe)
gframe.place(x=310)
plt.ion()	
f = Figure(figsize=(5.5, 3.5))

ax1 = f.add_subplot(211)
ax1.set_ylabel('pH')
ax1.set_xlabel('Volume (mL)')   #, labelpad =-140) # negative padding to move the label to top
ax1.xaxis.set_label_coords(0.5, 1.2)         
ax1.grid(b=True, which='major', color='green', linestyle='-')
ax1.grid(b=True, which='minor', color='black', linestyle=':', alpha=0.2)
ax1.minorticks_on()
ax1.set_ylim(0, 14)
ax1.plot([], [])
ax2 = f.add_subplot(212, sharex=ax1)
ax2.set_ylabel(r'$\Delta$''pH/'r'$\Delta$''v')
ax2.grid(b=True, which='major', color='green', linestyle='-')
ax2.grid(b=True, which='minor', color='black', linestyle=':', alpha =0.2)
ax2.set_ylim(0, 14)
ax2.minorticks_on()
ax2.plot([], [])

canvas = FigureCanvasTkAgg(f, gframe)
canvas.show()
canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)
toolbar = NavigationToolbar2TkAgg(canvas, gframe)
toolbar.update()
canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=True)

def sys_check():
	chk_top = Toplevel()
	chk_top.title("Status Check")
	chk_top.config(bg="white")
	chk_top.geometry('260x100+200+260')
	chk_msg = Message(chk_top, bg="white", 
					  text="Initial system check..Please wait", 
					  font=myfont, aspect=200)
	chk_msg.pack(fill=BOTH)
	time.sleep(0.5)
	ready = True
	spi_2.writebytes([CMD['WRITE'] | REG['CR2'], 0b10000000])

	if spi_2.xfer2([CMD['READ'] | REG['CR2'], 0])[1] != 0b10000000:
		tkMessageBox.showwarning(
			'warning', 
			"Registry failure. Power might be off or pump #1 stepper driver not communicating with Pi")
		for x in (
				std1_button, std2_button, std3_button, 
				std4_button, std5_button, chk_button, 
				Dispense_button):
			x.config(state="disabled")
		optionmenu.entryconfigure(0, state="disabled")
		optionmenu.entryconfigure(2, state="disabled")
		optionmenu.entryconfigure(4, state="disabled")
		optionmenu.entryconfigure(6, state="disabled")
		chk_top.destroy()
		ready = False
	spi_1.writebytes([CMD['WRITE'] | REG['CR2'], 0b10000000])

	if spi_1.xfer2([CMD['READ'] | REG['CR2'], 0])[1] != 0b10000000:
		tkMessageBox.showwarning(
			'warning', 
			"Registry failure. Power might be off or pump #2 stepper driver not communicating with Pi")
		#titration_button.configure(state='disabled')    modified

	calib_check1 = initial_bar()
	calib_check2 = initial_bar2()

	if (not calib_check1 or not calib_check2):
		chk_top.destroy()
		ready = False
	time.sleep(3)

	try:
		pump1 = pot.read_adc_difference(p1_channel, gain=GAIN)
		calib_volume1 = calibrate_calc1(pump1)
		if not -0.3 < calib_volume1 < 5.1:
			tkMessageBox.showwarning('warning', "Pump#1 Position Sensor Fault or Calibration is off")
			chk_top.destroy()	
			ready = False	
	except:
			tkMessageBox.showwarning('warning', "Pump#1 Position Sensor Fault or Calibration is off")
			chk_top.destroy()	
			ready = False

	try:
		pump2 = pot.read_adc_difference(p2_channel, gain=GAIN)
		calib_volume2 = calibrate_calc2(pump2)
		if not -0.3 < calib_volume2 < 5.1:
			tkMessageBox.showwarning('warning', "Pump#2 Position Sensor Fault or Calibration is off")
			chk_top.destroy()
			ready = False
	except:
			tkMessageBox.showwarning('warning', "Pump#2 Position Sensor Fault or Calibration is off")
			chk_top.destroy()
			ready = False
	chk_top.destroy()

	if ready == True:
		tkMessageBox.showinfo("READY", "CHECK COMPLETED.SYSTEM READY TO USE")
	else:
		tkMessageBox.showinfo("Error", "Some modules are not working correctly, system can not operate as intended")


###########################################################

if __name__ == '__main__':
	p = Queue()
	q = Queue()
	proc_queue2 = Queue()
	r = Queue()
	r2 = Queue()
	root.after(1000, sys_check)
	root.after(200, pH_slope_update)
	#Create_table()
	root.mainloop()
