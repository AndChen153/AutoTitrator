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
import RPi.GPIO as GPIO
from Queue import Empty
from multiprocessing import Process, Queue
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


