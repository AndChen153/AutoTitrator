import pandas as pd
from pandastable import Table, TableModel

class Create_table:
	def __init__(self):
		report_subframe_Hardness = Frame(Hardness_mainframe)
		report_subframe_Hardness.pack(fill=BOTH, expand=1)
		report_subframe_Alkalinity = Frame(Alkalinity_mainframe)
		report_subframe_Alkalinity.pack(fill=BOTH, expand=1)
		Alkalinity = pd.read_csv('/home/pi/Dispenser_gui/Alkalinity_Result_log.csv', delimiter=',')
		Hardness = pd.read_csv('/home/pi/Dispenser_gui/Hardness_Result_log.csv', delimiter=',')
		#df = pd.concat([Hardness,Alkalinity], axis=1)
		self.table_Hardness = pt_H = Table(
			report_subframe_Hardness, dataframe=Hardness.sort_values(by=['Date/Time(H)'], 
			ascending=False), showtoolbar=False, showstatusbar=False) 
		self.table_Alkalinity = pt_A = Table(
			report_subframe_Alkalinity, dataframe=Alkalinity.sort_values(by=['Date/Time'], 
			ascending=False), showtoolbar=False, showstatusbar=False)                                         
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