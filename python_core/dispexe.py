#!/usr/bin/env python
from Tkinter import *
import ttk
from PIL import ImageTk, Image
import Tkinter as tk
import tkFileDialog
import VL53L0X
from tkFont import Font
import tkMessageBox
from functools import partial
import math
import RPi.GPIO as GPIO   
import time
import sys
from Queue import Empty
from multiprocessing import Process, Queue
import csv
import os
import signal
from spidev import SpiDev

# GPIO setup-----------------------------------------------
step = 11
Dir = 13
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(step, GPIO.OUT)
GPIO.setup(Dir, GPIO.OUT)
GPIO.setup(Dir, GPIO.HIGH)      # HIGH = inject; LOW = fill
#end of GPIO setup ---------------------------------------

#AMIS 30543 setup and SPI communication --------------------
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
        'WRITE':0x80
        }

spi = SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000

# End of AMIS driver setup---------------------------------------

 #numpad setup--------------------------------------------
num_run = 0
btn_funcid = 0
entry = 0

def click(btn):
	global num_run
	global entry_list
	text = "%s" % btn
	entry_list1 = [entrym1,entrym2,entryv2]
	widget = root.focus_get()
	if not text == "Del" and not text == "Close":
		if widget in entry_list1 or entry_list:
			widget.insert("insert", text)
	if text == 'Del':
		if widget in entry_list1 or entry_list:
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
        btn[n] = tk.Button(lf, text=label, width=5, height=2, font = myfont, command=cmd)
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
root =Tk()
root.configure(bg="RoyalBlue1")
#root.title('FI-EZ-PIPETTE')
tool_frame = Frame(root, bd=1, relief="raised")
tool_frame.pack(side= TOP, fill= X)
ws = root.winfo_screenwidth()
hs = root.winfo_screenheight()
root.geometry('%dx%d' % (ws, hs))
root.attributes("-fullscreen", False) 
img = PhotoImage(file = '/home/pi/icons/play.gif')
img2 = img.subsample(2,2)

#img3 = PhotoImage(file = '/home/pi/icons/stop.gif')
#img4 = img3.subsample(2,2) 

img5 = PhotoImage(file = '/home/pi/icons/FI.gif')

img7 = ImageTk.PhotoImage(Image.open('/home/pi/icons/check.jpg'))

tool_frame = Frame(root, bd=1, relief="raised")
tool_frame.pack(side= TOP, fill= X)

myfont  = Font(family = 'Times New Roman', size = 16)
titlefont = Font(family = 'Gentium basic', size = 20, weight ='bold', slant = 'italic' )

container = Frame(root)
container.pack(side=TOP, fill="both", expand=True)
		
#Progress bar----------------------------------------------
tof = VL53L0X.VL53L0X()
tof.start_ranging(VL53L0X.VL53L0X_BEST_ACCURACY_MODE)

s = ttk.Style()
s.theme_use("alt")

s.configure("red.Vertical.TProgressbar",foreground='red', background='green', thickness = 40)
progress = ttk.Progressbar(root, style="red.Vertical.TProgressbar", orient="vertical", length=105, maximum =5, mode="determinate")
progress.place(x=430, y=222)

w = Canvas(root, bg ='royalblue1', bd='0', highlightthickness='0', width = '50', height ='115')
w.place(x= 475, y=215)
line50 = w.create_line(0, 10, 20, 10,fill ='red', width = '2')
line45= w.create_line(0, 20, 10, 20, fill ='red', width = '2')
line40= w.create_line(0,30, 10, 30, fill ='red', width = '2')
line35 = w.create_line(0,40, 10, 40, fill ='red', width = '2')
line30= w.create_line(0,50, 10, 50, fill ='red', width = '2')
line25 = w.create_line(0,60, 20,60, fill ='red', width = '2')
line20 = w.create_line(0,70, 10, 70, fill ='red', width = '2')
line15 = w.create_line(0,80, 10,80, fill ='red', width = '2')
line10 = w.create_line(0,90, 10,90, fill ='red', width = '2')
line5 = w.create_line(0,100, 10,100, fill ='red', width = '2')
line0 = w.create_line(0,110, 20,110, fill ='red', width = '2')
text50 = w.create_text(35, 10, text ='5 mL')
text50 = w.create_text(35, 60, text ='2.5')
text0 = w.create_text(30, 110, text ='0')

	
def initial_bar():
	log = open(path, 'r')
	reader = csv.reader(log)
	added = sum([float(row[0]) for row in reader])
	volume = 5 - added
	if 0 < volume and volume <= 1:
			s.configure("red.Vertical.TProgressbar",background='red')
	elif 1< volume and volume <=2:
			s.configure("red.Vertical.TProgressbar", background='yellow')	
	elif 2< volume and volume<=5:
			s.configure("red.Vertical.TProgressbar", background='green')
	progress['value']= volume
	root.update_idletasks()
		
	
def bar_update():
	global barupdate_id
	distance = tof.get_distance()
	calib_distance = distance-33
	if calib_distance >= 25:		
		volume1 = (calib_distance+7.8)/11.7
		if 0 < volume1 and volume1 <= 1:
			s.configure("red.Vertical.TProgressbar",background='red')
		elif 1< volume1 and volume1<=2:
			s.configure("red.Vertical.TProgressbar", background='yellow')
		progress['value']= volume1
	elif calib_distance < 25:
		volume1 =(calib_distance+0.332)/8.665
		if 1< volume1 and volume1 <=2:
			s.configure("red.Vertical.TProgressbar", background='yellow')
		elif 2< volume1 and volume1 <=5:
			s.configure("red.Vertical.TProgressbar", background='green')
		progress['value']= volume1
	root.update_idletasks()
	barupdate_id = root.after(2000, bar_update)
	
# Edit, load and save Method ------------------------------------------------
global vol_array
global file_name
file_name = '/home/pi/Dispenser_gui/Methods/Method1.Met'
with open(file_name, "r") as f:
	vol_array =f.read().splitlines()
f.close()
ftypes = [('Method files', '*.Met'), ('All files', '*')]		
def load_method(opt):
	global vol_array
	global file_name
	if opt == 'editor':
		try:
			file_name = tkFileDialog.askopenfilename(filetypes = ftypes, initialdir = '/home/pi/Dispenser_gui/Methods' )
			if file_name != " ":
				vol_array = []
				with open(file_name, "r") as f:
					vol_array =f.read().splitlines()
				f.close()
				cnt= 0
				edit_window()
				for entry in entry_list:
					entry.delete(0,END)
					entry.insert(0, vol_array[cnt])
					cnt =cnt+1
		except Exception:
			pass
	if opt == 'loader':
		file_name = tkFileDialog.askopenfilename(filetypes = ftypes, initialdir = '/home/pi/Dispenser_gui/Methods' )
		if file_name != " ":
			try:
				vol_array = []
				with open(file_name, "r") as f:
					vol_array =f.read().splitlines()
				f.close()
				std1_button.config(text = '%s mL(S1)' %vol_array[0])
				std2_button.config(text = '%s mL(S2)' %vol_array[1])
				std3_button.config(text = '%s mL(S3)' %vol_array[2])
				std4_button.config(text = '%s mL(S4)' %vol_array[3])
				std5_button.config(text = '%s mL(S5)' %vol_array[4])
				chk_button.config(text = '%s mL(chk)' %vol_array[5])
				status_label.config(text = '%s' % (file_name.split('/')[5]))
			except Exception:
				pass
				
def save_method():
	global mtop	
	global file_name
	if file_name != "":
		vol_array= []
		with open(file_name, "w") as f:
			for entry in entry_list:
				f.write("%s\n" % entry.get())
		f.close()
		mtop.grab_release()
		mtop.destroy()			
	
# Method Top-Level window-----------------------------------------------------
global entry_list
mtop =None
def edit_window():
	global mtop	
	global entry_list
	entry_list =[]
	mtop = Toplevel(root)
	mtop.transient(master=root)
	mtop.grab_set()
	mtop.geometry('250x220+150+60')
	mtop.title('Edit')
	l1 = Label(mtop, text = "mL", font = myfont)
	l2 = Label(mtop, text = "mL", font = myfont)
	l3 = Label(mtop, text = "mL", font = myfont)
	l4 = Label(mtop, text = "mL", font = myfont)
	l5 = Label(mtop, text = "mL", font = myfont)
	l6 = Label(mtop, text = "mL", font = myfont)
	label1 = Label(mtop, text = "std 1", font = myfont)
	label2 = Label(mtop, text = "std 2", font = myfont)
	label3 = Label(mtop, text = "std 3", font = myfont)
	label4 = Label(mtop, text = "std 4", font = myfont)
	label5 = Label(mtop, text = "std 5", font = myfont)
	label6 = Label(mtop, text = "chk std", font = myfont)
	e1 = Entry(mtop, width =10, relief ="raised", font = myfont)
	e2 = Entry(mtop, width =10, relief ="raised",font = myfont)
	e3 = Entry(mtop, width =10, relief ="raised",font = myfont)
	e4 = Entry(mtop, width =10, relief ="raised",font = myfont)
	e5 = Entry(mtop, width =10, relief ="raised",font = myfont)
	e6 = Entry(mtop, width =10, relief ="raised",font = myfont)
	l1.grid(row=0, column=2, sticky ='W')
	l2.grid(row=1, column=2, sticky ='W')
	l3.grid(row=2, column=2, sticky ='W')
	l4.grid(row=3, column=2, sticky ='W')
	l5.grid(row=4, column=2, sticky ='W')
	l6.grid(row=5, column=2, sticky ='W')
	label1.grid(row=0, column=0, padx=5)
	label2.grid(row =1,column=0, padx=5)
	label3.grid(row=2,column=0, padx=5)
	label4.grid(row=3,column=0, padx=5)
	label5.grid(row=4,column=0, padx=5)
	label6.grid(row=5,column=0, padx=5)
	e1.grid(row =0,column=1)
	e2.grid(row=1, column=1)
	e3.grid(row=2, column=1)
	e4.grid(row=3, column=1)
	e5.grid(row=4, column=1)
	e6.grid(row=5, column=1)
	entry_list = [e1,e2,e3,e4,e5,e6]
	for entry in entry_list:
		entry.bind('<Button-1>', Topfocus)
	sav_button = Button(mtop, text = "Save Method",font = myfont,relief ="raised", command = save_method)
	sav_button.grid(row=6, column=0, columnspan=2, pady =5)

# dispenser start--------------------------------------------------------------
conc_mainframe = Frame(container, bg="RoyalBlue1")
THM_mainframe = Frame(container, bg="RoyalBlue1")
conc_mainframe.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
THM_mainframe.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
THM_mainframe.lift()

conc_frame = Frame(conc_mainframe, bg = "RoyalBlue1")
THM_frame = Frame(THM_mainframe, bg ="RoyalBlue1")

conc_frame.place(x = 20, y =20)
THM_frame.place(x=60, y=20)

def pageone():
    conc_mainframe.lift()

def pagetwo():
    THM_mainframe.lift()
    
sy_button = Button(tool_frame, text = "MANUAL", command = pageone, font = myfont)
sy_button.pack(side=LEFT, padx=2, pady=2)

dis_button = Button(tool_frame, text = " THM-RR ", command = pagetwo, font = myfont)
dis_button.pack(side=LEFT, padx=2, pady=2)

bigfont = Font(family = 'Times New Roman', size = 16)
root.option_add("*TCombobox*Listbox*Font", bigfont)

m1var = StringVar()
m1 ={ ' ppb(ug/L) ':0.001, ' ppt(ng/L) ':0.000001,'   g/L   ':1000, 'ppm(mg/L)': 1}
combovalues1 = m1.keys()
m1units = ttk.Combobox(conc_frame, textvariable = m1var, values = combovalues1, state="readonly", width =10, height = 5)
m1units.config(font = myfont)
m1var.set('-- units --')

global unit1
unit1 = IntVar()
def change_unit1(*args):
    global unit1
    unit1 = m1[m1var.get()]
m1var.trace('w', change_unit1)

m2var = StringVar()
m2 = {' ppb(ug/L) ':0.001, ' ppt(ng/L) ':0.000001, '   g/L   ':1000, 'ppm(mg/L)':1}
combovalues2 = m2.keys()
m2units = ttk.Combobox(conc_frame, textvariable = m2var, values = combovalues2, state="readonly", width =10, height =5)
m2units.config(font = myfont)
m2var.set('-- units --')

global unit2
unit2 = IntVar()
def change_unit2(*args):
    global unit2
    unit2 = m2[m2var.get()]

m2var.trace('w', change_unit2)

labelm1 = Label(conc_frame, text = "M1", font = myfont, bg = 'white')
labelm2 = Label(conc_frame, text = "M2",font = myfont, bg = 'white')
labelv1 = Label(conc_frame, text = "V1 (mL)",font = myfont, bg = 'white')
labelv2 = Label(conc_frame, text = "V2 (mL)", font = myfont, bg = 'white')

entrym1 = Entry(conc_frame, width =15, font = myfont, relief ="raised")
entrym2 = Entry(conc_frame, width =15, font = myfont,relief ="raised")
entryv1 = Entry(conc_frame, width =15, font = myfont, relief ="raised")
entryv2 = Entry(conc_frame, width =15, font = myfont,relief = "raised")

entrym1.bind('<Button-1>', Topfocus)
entrym2.bind('<Button-1>', Topfocus)
entryv2.bind('<Button-1>', Topfocus)

labelm1.grid (row=0, column=1)
labelm2.grid(row=0, column=2, padx=5)
m1units.grid(row=1, sticky = 'nsew')
entrym1.grid(row=1, column=1, pady=2, padx=7, ipady =6)
entrym2.grid(row=1, column=2, padx=7, ipady =6)
m2units.grid(row=1,column=3, sticky = 'nsew')
labelv1.grid (row=2, column=1, pady =2)
labelv2.grid(row=2, column=2, padx=5)
entryv1.grid(row=3, column=1,ipady =6)
entryv2.grid(row=3, column=2,padx=5,ipady =6)

path = '/home/pi/Dispenser_gui/python/volume.csv'

def start_process():
	bar_update()
	p1 = Process(target=dispense_loop)
	p1.deamon = True
	p1.start()

def volume1():
	try:
		global unit1
		global unit2
		m1 = float(entrym1.get())
		m2 =float(entrym2.get())
		v2= float(entryv2.get())
		v1 = (m2*float(unit2)*v2)/(m1*float(unit1))
		entryv1.delete(0,"end")
		entryv1.insert(0, v1)
		try:
			log = open(path, 'r')
			reader = csv.reader(log)
			added = sum([float(row[0]) for row in reader])
			rem_volume = 5 - (added+v1)
			log.close()
			if rem_volume > 0.01:
				if tkMessageBox.askyesno('proceed', 'V1 is %s mL, do you really want to proceed' % (v1)):
					steps = int((v1 + 0.000785)/0.0000502)
					p.put(steps)
					log =  open(path, 'a')
					writer = csv.writer(log)
					writer.writerow([v1])
					log.close()
					Enable(1, 0)
					start_process()
				else:
					Manbar.state(['!selected'])
					s.configure("Manbar.Horizontal.TProgressbar", background='RoyalBlue1')
					Manbar.stop()
			elif rem_volume <= 0:
				tkMessageBox.showwarning('warning', "Not Enough Volume. Refill ")
				Manbar.state(['!selected'])
				s.configure("Manbar.Horizontal.TProgressbar", background='RoyalBlue1')
				Manbar.stop()
		except Exception:
				if tkMessageBox.askyesno('proceed', 'V1 is %s mL, do you really want to proceed' % (v1)):
					steps = int((v1 + 0.000785)/0.0000502)
					p.put(steps)
					log =  open(path, 'a')
					writer = csv.writer(log)
					writer.writerow([v1])
					log.close()
					Enable(1, 0)
					start_process()
				else:
					Manbar.state(['!selected'])
					s.configure("Manbar.Horizontal.TProgressbar", background='RoyalBlue1')	
					Manbar.stop()	
	except (AttributeError, ValueError):
		Manbar.state(['!selected'])
		s.configure("Manbar.Horizontal.TProgressbar", background='RoyalBlue1')
		Manbar.stop()
		tkMessageBox.showwarning('warning', "Check Your values/units")
		
def THM_RR(volume, direction):
	steps = int((volume + 0.000785)/0.0000502)
	p.put(steps)
	if spi.xfer2([CMD['READ'] | REG['CR0'], 0])[1] != 0b10000010:    # compensated half step
		spi.writebytes([CMD['WRITE'] | REG['CR0'], 0b10100010])
		
	if spi.xfer2([CMD['READ'] | REG['CR2'], 0])[1] != 0b10000000:
		spi.writebytes([CMD['WRITE'] | REG['CR2'], 0b10000000])
		
	if direction == 1:												  # 1 = dispense, 0 = refill/retract, 2 = prime/purge, 
		if spi.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b01000000:
			spi.writebytes([CMD['WRITE'] | REG['CR1'], 0b01000000])
		log =  open(path, 'a')
		writer = csv.writer(log)
		writer.writerow([volume])
		log.close()
		std_stop()
	elif direction == 2:
		if spi.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b01000000:
			spi.writebytes([CMD['WRITE'] | REG['CR1'], 0b01000000])
		log =  open(path, 'a')
		writer = csv.writer(log)
		writer.writerow([volume])
		log.close()
	else:
		if spi.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b11000000:
			spi.writebytes([CMD['WRITE'] | REG['CR1'], 0b11000000])
	start_process()
	
	
def Enable(direction, prime):
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(step, GPIO.OUT)
	
	if spi.xfer2([CMD['READ'] | REG['CR0'], 0])[1] != 0b10000010:    # compensated half step
		spi.writebytes([CMD['WRITE'] | REG['CR0'], 0b10100010])
		
	if spi.xfer2([CMD['READ'] | REG['CR2'], 0])[1] != 0b10000000:
		spi.writebytes([CMD['WRITE'] | REG['CR2'], 0b10000000])
		
	if direction == 1:
		if spi.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b01000000:
			spi.writebytes([CMD['WRITE'] | REG['CR1'], 0b01000000])
    
	else:
		if spi.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b11000000:
			spi.writebytes([CMD['WRITE'] | REG['CR1'], 0b11000000])
		

def prime():
	try:
		log = open(path, 'r')
		reader = csv.reader(log)
		added = sum([float(row[0]) for row in reader])
		rem_volume = 5 - (added+0.075)
		log.close()
		if rem_volume > 0.01:
			if tkMessageBox.askyesno('proceed', 'Do you want to Prime the syringe'):
				THM_RR(0.075, 2)
				empty_queue()
		elif rem_volume <= 0:
			tkMessageBox.showwarning('warning', "Not Enough Volume.")
	except Exception:
		if tkMessageBox.askyesno('proceed', 'Do you want to Prime the syringe'):
			THM_RR(0.075, 2)
			empty_queue()
			
def Retract():
	if tkMessageBox.askyesno('proceed', 'Do you want to Retract the syringe'):
		THM_RR(0.075, 0)
		log =  open(path, 'a')
		writer = csv.writer(log)
		writer.writerow([-0.075])
		log.close()
		empty_queue()
		
def Rf_start():
	if tkMessageBox.askyesno('proceed', 'Do you want to Refill the syringe'):
		log = open(path, 'r')
		reader = csv.reader(log)
		added = abs(sum([float(row[0]) for row in reader]))
		if added != 0:
			THM_RR(added, 0)
			popup_window(0)
			writer = csv.writer(open(path, 'w'))
			for line in reader:
				writer.writerow(line)
			log.close()
		else:
			tkMessageBox.showinfo('Full', 'Syringe filled to 5 mL')
def purge():
	if tkMessageBox.askyesno('proceed', 'Do you want to empty the syringe'):
		log = open(path, 'r')
		reader = csv.reader(log)
		added = abs(sum([float(row[0]) for row in reader]))
		purge_vol = 4.98 - added
		if purge_vol != 0:
			THM_RR(purge_vol, 2)
			popup_window(1)
		else:
			tkMessageBox.showinfo('Full', 'Syringe Empty. Please Refill')
			
def dispense_loop():
	step = 11
	Dir = 13
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(step, GPIO.OUT)
	GPIO.setup(Dir, GPIO.OUT)
	pid1 = os.getpid()
	q.put(pid1)
	steps = p.get()
	for x in range (0, steps):
			GPIO.output(step, GPIO.LOW)
			time.sleep(0.0005)
			GPIO.output(step, GPIO.HIGH)
			time.sleep(0.0005)
	GPIO.cleanup()	
	r.put(1)   
	time.sleep(2)
	sys.exit(0)
	
def empty_queue():
	global barupdate_id
	qid = root.after(500,empty_queue)
	try:
		fork = r.get(False)
		if fork ==1:
			initial_bar()
			root.after_cancel(qid)
			root.after_cancel(barupdate_id)
			tkMessageBox.showinfo("DONE", "Prime/Retract Completed.")
	except Empty:
		pass
		
def top_close():
	global barupdate_id
	tid = root.after(500, top_close)
	try:
		fork = r.get(False)
		if fork ==1:
			initial_bar()
			top.destroy()
			root.after_cancel(tid)
			root.after_cancel(barupdate_id)
			tkMessageBox.showinfo("DONE", "Refill/Purging Completed.")
			top.grab_release()
	except Empty:
		pass

def popup_window(dmsg):
		global top,msg
		top = Toplevel()
		top.config(bg = 'royalblue1',relief = 'raised')
		top.geometry('160x160+260+250')
		top.overrideredirect(True)
		msg = Message(top, relief = 'raised', bg = 'white', font = myfont)
		msg.pack()
		if dmsg == 1:
			msg.config(text = 'Please wait until system Purge the syringe')
		else:
			msg.config(text = 'Please wait until system Refill')
		top.grab_set()
		top_close()

def button_call():
	if Manbar.instate(['selected']) == False and bar1.instate(['selected']) == False and bar2.instate(['selected']) == False and bar3.instate(['selected']) == False and bar4.instate(['selected']) == False and bar5.instate(['selected']) == False and chk.instate(['selected']) == False:
		s.configure("Manbar.Horizontal.TProgressbar", background='red')
		Manbar.start(10)
		Manbar.state(['!selected','selected'])
		std_stop()
		volume1()
	else:
		tkMessageBox.showwarning('warning', "Please wait untill current volume is Dispensed")
			
Dispense_button = Button(conc_frame, image = img2, width =100, height =60,bg = 'white', command=button_call)
Dispense_button.grid(row =5,column=1, pady = 10, columnspan=2)

def sys_check():
	chk_top = Toplevel()
	chk_top.title("Status Check")
	chk_top.config(bg ="white")
	chk_top.geometry('260x100+200+260')
	chk_msg = Message(chk_top,bg = "white",text = "Initial system check..Please wait", font = myfont, aspect =200)
	chk_msg.pack(fill = BOTH)
	spi.writebytes([CMD['WRITE'] | REG['CR2'], 0b10000000])
	if spi.xfer2([CMD['READ'] | REG['CR2'], 0])[1] != 0b10000000:
		tkMessageBox.showwarning('warning', "Registry failure. Power might be off or stepper driver not communicating with Pi")
		for x in (std1_button, std2_button, std3_button, std4_button, std5_button, chk_button, Dispense_button):
			x.config(state = "disabled")
		optionmenu.entryconfigure(0, state = "disabled")
		optionmenu.entryconfigure(2, state = "disabled")
		optionmenu.entryconfigure(4, state = "disabled")
		optionmenu.entryconfigure(6, state = "disabled")
		chk_top.destroy()
		return
	initial_bar()
	time.sleep(3)
	dist_array = []
	for x in range(0,4):
		distance = tof.get_distance()
		dist_array.append(distance)
		if dist_array == [-1,-1,-1,-1]:
			tkMessageBox.showwarning("Warning", "Distance sensor not working")
			return 0
		time.sleep(0.25)
	chk_top.destroy()
	tkMessageBox.showinfo("READY","CHECK COMPLETED.SYSTEM READY TO USE")

	
def sys_shut():
	root.destroy()
	os.system("sudo shutdown now -P")

def sys_reboot():
	root.destroy()
	os.system("sudo shutdown -r now")



## Menu widget--------------------------------------------------
menu=Menu(root, bg = 'floral white')
root.config(menu=menu)
optionmenu = Menu(menu, tearoff =0)
optionmenu.config(font = myfont)
menu.add_cascade(label="Options", menu=optionmenu, font = myfont)
menu.add_cascade(label="                         ",  font = myfont)
menu.add_cascade(label="",image = img5, font = myfont)
menu.add_cascade(label="EZ-PIPETTE",  font = titlefont)
optionmenu.add_command(label="Prime", command = prime)
optionmenu.add_separator()
optionmenu.add_command(label= "Retract", command = Retract) 
optionmenu.add_separator()
optionmenu.add_command(label= "Refill", command = Rf_start)
optionmenu.add_separator()
optionmenu.add_command(label= "Empty", command =purge)
optionmenu.add_separator()
optionmenu.add_command(label= "Reboot", command = sys_reboot)
optionmenu.add_separator()
optionmenu.add_command(label= "Quit", command = sys_shut)
### end of menu widget-------------------------------------------

### THM standard ------------------------------------------------
def std_stop():
	global barupdate_id
	std_id = root.after(500, std_stop)
	try:
		fork = r.get(False)
		if fork ==1:
			root.after_cancel(barupdate_id)
			root.after_cancel(std_id)
			if bar1.instate(['selected']) == True:
				bar1.stop()
				bar1.state(['!selected'])
				s.configure("bar1.Horizontal.TProgressbar", background='RoyalBlue1')
				std1_label.config(image =img7)
			elif bar2.instate(['selected']) == True:
				bar2.state(['!selected'])
				s.configure("bar2.Horizontal.TProgressbar", background='RoyalBlue1')
				bar2.stop()
				std2_label.config(image =img7)
			elif bar3.instate(['selected']) == True:
				bar3.state(['!selected'])
				s.configure("bar3.Horizontal.TProgressbar", background='RoyalBlue1')
				bar3.stop()
				std3_label.config(image =img7)	
			elif bar4.instate(['selected']) == True:
				bar4.state(['!selected'])
				s.configure("bar4.Horizontal.TProgressbar", background='RoyalBlue1')
				bar4.stop()
				std4_label.config(image =img7)	
			elif bar5.instate(['selected']) == True:
				bar5.state(['!selected'])
				s.configure("bar5.Horizontal.TProgressbar", background='RoyalBlue1')
				bar5.stop()
				std5_label.config(image =img7)
			elif chk.instate(['selected']) == True:
				chk.state(['!selected'])
				s.configure("chk.Horizontal.TProgressbar", background='RoyalBlue1')
				chk.stop()
				chk_label.config(image =img7)
			elif Manbar.instate(['selected']) == True:
				Manbar.state(['!selected'])
				s.configure("Manbar.Horizontal.TProgressbar", background='RoyalBlue1')
				Manbar.stop()
			initial_bar()					
	except Empty:
		pass

def std1_vol():
	global vol_array
	if bar1.instate(['selected']) == False and bar2.instate(['selected']) == False and bar3.instate(['selected']) == False and bar4.instate(['selected']) == False and bar5.instate(['selected']) == False and chk.instate(['selected']) == False and Manbar.instate(['selected']) == False :
		try:
			log = open(path, 'r')
			reader = csv.reader(log)
			added = sum([float(row[0]) for row in reader])
			rem_volume = 5 - (added+float(vol_array[0]))
			log.close()
			if rem_volume > 0.01:
				if tkMessageBox.askyesno('proceed', 'Do you want to do std1'):
					THM_RR(float(vol_array[0]),1 )
					s.configure("bar1.Horizontal.TProgressbar", background='red')
					bar1.start(10)
					bar1.state(['!selected', 'selected'])
			elif rem_volume <= 0:
				tkMessageBox.showwarning('warning', "Not Enough Volume. Refill ")
		except Exception:
			if tkMessageBox.askyesno('proceed', 'Do you want to do std1'):
				THM_RR(float(vol_array[0]), 1)
				s.configure("bar1.Horizontal.TProgressbar", background='red')
				bar1.start(10)
				bar1.state(['!selected', 'selected'])
	else:
		tkMessageBox.showwarning('warning', "Please wait untill current volume is Dispensed")
	
def std2_vol():
	global vol_array
	if bar2.instate(['selected']) == False and bar1.instate(['selected']) == False and bar3.instate(['selected']) == False and bar4.instate(['selected']) == False and bar5.instate(['selected']) == False and chk.instate(['selected']) == False and Manbar.instate(['selected']) == False:
		try:
			log = open(path, 'r')
			reader = csv.reader(log)
			added = sum([float(row[0]) for row in reader])
			rem_volume = 5 - (added+float(vol_array[1]))
			log.close()
			if rem_volume > 0.01:
				if tkMessageBox.askyesno('proceed', 'Do you want to do std2'):
					THM_RR(float(vol_array[1]),1)
					s.configure("bar2.Horizontal.TProgressbar", background='red')
					bar2.start(10)
					bar2.state(['!selected', 'selected'])
			elif rem_volume <= 0:
				tkMessageBox.showwarning('warning', "Not Enough Volume. Refill ")
		except Exception:
			if tkMessageBox.askyesno('proceed', 'Do you want to do std2'):
				THM_RR(float(vol_array[1]),1)
				s.configure("bar2.Horizontal.TProgressbar", background='red')
				bar2.start(10)
				bar2.state(['!selected', 'selected'])
	else:
		tkMessageBox.showwarning('warning', "Please wait untill current volume is Dispensed")
		
def std3_vol():
	global vol_array
	if bar3.instate(['selected']) == False and bar1.instate(['selected']) == False and bar2.instate(['selected']) == False and bar4.instate(['selected']) == False and bar5.instate(['selected']) == False and chk.instate(['selected']) == False and Manbar.instate(['selected']) == False:
		try:
			log = open(path, 'r')
			reader = csv.reader(log)
			added = sum([float(row[0]) for row in reader])
			rem_volume = 5 - (added+float(vol_array[2]))
			log.close()
			if rem_volume > 0.01:
				if tkMessageBox.askyesno('proceed', 'Do you want to do std3'):
					THM_RR(float(vol_array[2]),1)
					s.configure("bar3.Horizontal.TProgressbar", background='red')
					bar3.start(10)
					bar3.state(['!selected', 'selected'])
			elif rem_volume <= 0:
				tkMessageBox.showwarning('warning', "Not Enough Volume. Refill ")
		except Exception:
			if tkMessageBox.askyesno('proceed', 'Do you want to do std3'):
				THM_RR(float(vol_array[2]), 1)
				s.configure("bar3.Horizontal.TProgressbar", background='red')
				bar3.start(10)
				bar3.state(['!selected', 'selected'])
	else:
		tkMessageBox.showwarning('warning', "Please wait untill current volume is Dispensed")
		
def std4_vol():
	global vol_array
	if bar4.instate(['selected']) == False and bar1.instate(['selected']) == False and bar2.instate(['selected']) == False and bar3.instate(['selected']) == False and bar5.instate(['selected']) == False and chk.instate(['selected']) == False and Manbar.instate(['selected']) == False:
		try:
			log = open(path, 'r')
			reader = csv.reader(log)
			added = sum([float(row[0]) for row in reader])
			rem_volume = 5 - (added+float(vol_array[3]))
			log.close()
			if rem_volume > 0.01:
				if tkMessageBox.askyesno('proceed', 'Do you want to do std4'):
					THM_RR(float(vol_array[3]),1)
					s.configure("bar4.Horizontal.TProgressbar", background='red')
					bar4.start(10)
					bar4.state(['!selected', 'selected'])
			elif rem_volume <= 0:
				tkMessageBox.showwarning('warning', "Not Enough Volume. Refill ")
		except Exception:
			if tkMessageBox.askyesno('proceed', 'Do you want to do std4'):
				THM_RR(float(vol_array[3]),1)
				s.configure("bar4.Horizontal.TProgressbar", background='red')
				bar4.start(10)
				bar4.state(['!selected', 'selected'])
	else:
		tkMessageBox.showwarning('warning', "Please wait untill current volume is Dispensed")
	
def std5_vol():
	global vol_array
	if bar5.instate(['selected']) == False and bar1.instate(['selected']) == False and bar2.instate(['selected']) == False and bar3.instate(['selected']) == False and bar4.instate(['selected']) == False and chk.instate(['selected']) == False and Manbar.instate(['selected']) == False:
		try:
			log = open(path, 'r')
			reader = csv.reader(log)
			added = sum([float(row[0]) for row in reader])
			rem_volume = 5 - (added+float(vol_array[4]))
			log.close()
			if rem_volume > 0.01:
				if tkMessageBox.askyesno('proceed', 'Do you want to do std5'):
					THM_RR(float(vol_array[4]),1)
					s.configure("bar5.Horizontal.TProgressbar", background='red')
					bar5.start(10)
					bar5.state(['!selected', 'selected'])
			elif rem_volume <= 0:
				tkMessageBox.showwarning('warning', "Not Enough Volume. Refill ")
		except Exception:
			if tkMessageBox.askyesno('proceed', 'Do you want to do std5'):
				THM_RR(float(vol_array[4]),1)
				s.configure("bar5.Horizontal.TProgressbar", background='red')
				bar5.start(10)
				bar5.state(['!selected', 'selected'])
	else:
		tkMessageBox.showwarning('warning', "Please wait untill current volume is Dispensed")
def chk_vol():
	global vol_array
	if chk.instate(['selected']) == False and bar1.instate(['selected']) == False and bar2.instate(['selected']) == False and bar3.instate(['selected']) == False and bar4.instate(['selected']) == False and bar5.instate(['selected']) == False and Manbar.instate(['selected']) == False:
		try:
			log = open(path, 'r')
			reader = csv.reader(log)
			added = sum([float(row[0]) for row in reader])
			rem_volume = 5 - (added+float(vol_array[5]))
			log.close()
			if rem_volume > 0.01:
				if tkMessageBox.askyesno('proceed', 'Do you want to do check std'):
					THM_RR(float(vol_array[5]),1)
					s.configure("chk.Horizontal.TProgressbar", background='red')
					chk.start(10)
					chk.state(['!selected', 'selected'])
			elif rem_volume <= 0:
				tkMessageBox.showwarning('warning', "Not Enough Volume. Refill ")
		except Exception:
			if tkMessageBox.askyesno('proceed', 'Do you want to do check std'):
				THM_RR(float(vol_array[5]),1)
				s.configure("chk.Horizontal.TProgressbar", background='red')
				chk.start(10)
				chk.state(['!selected', 'selected'])
	else:
		tkMessageBox.showwarning('warning', "Please wait untill current volume is Dispensed")
		
def reset_label():
	std1_label.config(image= '') 
	std2_label.config(image = '') 
	std3_label.config(image = '') 
	std4_label.config(image = '') 
	std5_label.config(image= '') 
	chk_label.config(image = '') 

std1_button = Button(THM_frame, width = 10, text = '%s mL(S1)' %vol_array[0], font = myfont, command = std1_vol)
std2_button = Button(THM_frame, width = 10, text = '%s mL(S2)' %vol_array[1], font = myfont, command = std2_vol)
std3_button = Button(THM_frame, width = 10, text = '%s mL(S3)' %vol_array[2], font = myfont, command = std3_vol)
std4_button = Button(THM_frame, width = 10, text = '%s mL(S4)' %vol_array[3], font = myfont, command = std4_vol)
std5_button = Button(THM_frame, width = 10, text = '%s mL(S5)' %vol_array[4], font = myfont,command = std5_vol)
chk_button = Button(THM_frame, width = 10,  text = '%s mL(chk)' %vol_array[5], font = myfont,command = chk_vol)
reset_button = Button(THM_frame, width = 10,  text = 'CLEAR', font = myfont,command = reset_label)

s.configure("bar1.Horizontal.TProgressbar",troughcolor='RoyalBlue1', background='RoyalBlue1', thickness = 2)
s.configure("bar2.Horizontal.TProgressbar",troughcolor='RoyalBlue1', background='RoyalBlue1', thickness = 2)
s.configure("bar3.Horizontal.TProgressbar",troughcolor='RoyalBlue1', background='RoyalBlue1', thickness = 2)
s.configure("bar4.Horizontal.TProgressbar",troughcolor='RoyalBlue1', background='RoyalBlue1', thickness = 2)
s.configure("bar5.Horizontal.TProgressbar",troughcolor='RoyalBlue1', background='RoyalBlue1', thickness = 2)
s.configure("chk.Horizontal.TProgressbar",troughcolor='RoyalBlue1', background='RoyalBlue1', thickness = 2)
s.configure("Manbar.Horizontal.TProgressbar",troughcolor='RoyalBlue1', background='RoyalBlue1', thickness = 2)

bar1 = ttk.Progressbar(THM_frame, style="bar1.Horizontal.TProgressbar", orient="horizontal", length=137, mode="indeterminate")
bar2 = ttk.Progressbar(THM_frame, style="bar2.Horizontal.TProgressbar", orient="horizontal", length=137, mode="indeterminate")
bar3 = ttk.Progressbar(THM_frame, style="bar3.Horizontal.TProgressbar", orient="horizontal", length=137, mode="indeterminate")
bar4 = ttk.Progressbar(THM_frame, style="bar4.Horizontal.TProgressbar", orient="horizontal", length=137, mode="indeterminate")
bar5 = ttk.Progressbar(THM_frame, style="bar5.Horizontal.TProgressbar", orient="horizontal", length=137, mode="indeterminate")
chk = ttk.Progressbar(THM_frame, style="chk.Horizontal.TProgressbar", orient="horizontal", length=137, mode="indeterminate")
Manbar = ttk.Progressbar(conc_frame, style="Manbar.Horizontal.TProgressbar", orient="horizontal", length=107, mode="indeterminate")
bar1.place(y=47)
bar2.place(y=105)
bar3.place(y=161)
bar4.place(y=219)
bar5.place(y=275)
chk.place(y=332)
Manbar.place(x=261, y=219) 

std1_label = Label(THM_frame, width = 25, bg = 'RoyalBlue1')
std2_label = Label(THM_frame, width = 25, bg = 'RoyalBlue1')
std3_label = Label(THM_frame, width = 25, bg = 'RoyalBlue1')
std4_label = Label(THM_frame, width = 25, bg = 'RoyalBlue1')
std5_label = Label(THM_frame, width = 25, bg = 'RoyalBlue1')
chk_label = Label(THM_frame, width = 25, bg = 'RoyalBlue1')
status_label = Label(THM_frame, width = 13, bg = 'White', text = ' ',font = myfont)
status_label.config(text = '%s' % (file_name.split('/')[5]))

std1_button.grid(row=0, pady=10)
std2_button.grid(row=1, pady=10)
std3_button.grid(row=2, pady=10)
std4_button.grid(row=3, pady=10)
std5_button.grid(row=4, pady=10)
chk_button.grid(row=5, pady=10)
reset_button.grid(row=5, column =2, pady =10, sticky ='E')

std1_label.grid(row=0, column = 1, pady=10, padx=3,sticky ='W') 
std2_label.grid(row=1, column = 1, pady=10,padx=3,sticky ='W') 
std3_label.grid(row=2, column = 1, pady=10,padx=3,sticky ='W')
std4_label.grid(row=3, column = 1, pady=10,padx=3,sticky ='W')
std5_label.grid(row=4, column = 1, pady=10,padx=3,sticky ='W')
chk_label.grid(row=5, column = 1, pady=10,padx=3,sticky ='W')
status_label.grid(row=0, column =3, pady =10, padx=10, sticky ='W')

sel_button = Button(THM_frame, text = "Load Method", width=10, command = lambda: load_method('loader'), font = myfont)
sel_button.grid(row=0, column=2,sticky ='E')
edit_button = Button(THM_frame, text = "Edit Method",width =10, command =lambda: load_method('editor'), font = myfont)
edit_button.grid(row=1, column=2,sticky ='E')
#dispenser end-----------------------------------------------------------------


if __name__ == '__main__':
	p = Queue()
	q = Queue()
	r= Queue()
	root.after(100, sys_check)
	#root.after(100, initial_bar)
	root.mainloop()
