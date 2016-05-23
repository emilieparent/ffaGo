import numpy as np
import math
import time
import sys
import os
import ConfigParser
import ast
import re
import matplotlib.pyplot as plt
import scipy.signal
import glob
import subprocess

import ffa_tools as ft
import ffa_stages as fs
import sifting_ffa as sf
import FFA_cy as FFA

total_time=time.time()

# ------------- 	Declare list variable    ------------------
all_SNs_x1,all_SNs1 = [],[]
all_Ps_x1,all_Ps1 = [] ,[]
all_SNs_x2,all_SNs_2 = [],[]
all_Ps_x2,all_Ps_2= [],[]
all_SNs_x3,all_SNs_3 = [],[]
all_Ps_x3,all_Ps_3 = [],[]
SNs1 = []
SNs2_phase1, SNs2_phase2 = [], []
SNs4_phase1, SNs4_phase2 ,SNs4_phase3, SNs4_phase4 = [],[],[],[]
SNs8_phase1 ,SNs8_phase2 ,SNs8_phase3, SNs8_phase4 = [],[],[],[] 
SNs8_phase5 ,SNs8_phase6 ,SNs8_phase7, SNs8_phase8 = [],[],[],[]
SNs3_phase1 ,SNs3_phase2, SNs3_phase3 = [], [], []
SNs9_phase1 ,SNs9_phase2 ,SNs9_phase3 ,SNs9_phase4 = [],[],[],[]
SNs9_phase5 ,SNs9_phase6 ,SNs9_phase7 ,SNs9_phase8 ,SNs9_phase9 = [],[],[],[],[]
SNs27_phase1, SNs27_phase2, SNs27_phase3, SNs27_phase4 = [], [], [], []
SNs27_phase5, SNs27_phase6, SNs27_phase7, SNs27_phase8 = [], [], [], []
SNs27_phase9, SNs27_phase10, SNs27_phase11, SNs27_phase12 = [], [], [], []
SNs27_phase13, SNs27_phase14, SNs27_phase15, SNs27_phase16 = [], [], [], []
SNs27_phase17, SNs27_phase18, SNs27_phase19, SNs27_phase20 = [], [], [], []
SNs27_phase21, SNs27_phase22, SNs27_phase23, SNs27_phase24 = [], [], [], []
SNs27_phase25, SNs27_phase26,SNs27_phase27 = [], [], []
Ps1, Ps2, Ps4, Ps8, Ps3, Ps9, Ps27 = [],[],[],[],[],[],[]
dts_x1,dts_1 = [],[]
dts_x2,dts_2 = [],[]
dts_x3,dts_3 = [],[]
dt1s,dt2s,dt4s,dt8s,dt3s,dt9s,dt27s = [],[],[],[],[],[],[]

# ------------- 	Read configuration file		------------------

cfg = ConfigParser.ConfigParser()
cfg.read('config_ffa.cfg')
#cfg.read(str(sys.argv[2]))

p_ranges = eval(cfg.get('FFA_settings','p_ranges'))
dt_list = eval(cfg.get('FFA_settings','dt_list'))
SN_tresh = float(cfg.get('FFA_settings','SN_tresh'))
min_dc = ast.literal_eval(cfg.get('FFA_settings','min_dc'))

# ------------- 	Select beam	------------------
beam = sys.argv[1]
#beam = 'J1901+0413_dm600.dat'
ts,name = ft.get_timeseries(beam)
T,dt,DM = ft.get_info_beam(name+'.inf')
N = int(T/dt)

# ------------- 	Downsampling	------------------
# min_dc : minimum duty-cycle tested, set in cfg file 
if min_dc > 0.5:
	if min_dc ==1: 
		dt_list = 2*dt_list 
	if min_dc ==1.5: 
		dt_list = 3*dt_list  
dwn_ideal = int(dt_list[0]/dt)

# min,max :give a range of accepted downsampling amount - for initial downsampling
minimum_dwn,maximum_dwn  = dwn_ideal-int(dwn_ideal*0.10),dwn_ideal+int(dwn_ideal*0.20)
ts,dwn = ft.select_factor(ts,minimum_dwn,maximum_dwn)

print 'Downsampling the time series ..' 
ts = ft.downsample(ts, dwn)

# ------------- 	Detrending	------------------

print "Detrending .."
#window size : over which statistics are computed 
window_size = 50*int(len(ts)/T)		
break_points = np.arange(0,len(ts),window_size) 
ts = scipy.signal.detrend(ts,bp=break_points)

# Normalize w.r.t. maximum
ts = ts/max(ts)
sigma_total= np.std(ts)

#===================================	FFA	===================================
print "Entering FFA"
dt= T/len(ts)

# count_lim: used in stage 2 and 3; how many consecutive downsamplings 
count_lim = 2		

# Going through subsequent sub-ranges of periods (set in config_ffa.cfg)
# Each range of periods has it own initial sampling interval
for num in range(len(p_ranges)):
	if num > 0:
		dwn_ideal = int(dt_list[num]/dt)
		if (dwn_ideal ==1) or (dwn_ideal == 0) :
			dwn_ideal =2 
		minimum_dwn,maximum_dwn = dwn_ideal-int(dwn_ideal*0.05),dwn_ideal+int(dwn_ideal*0.15)
		ts,dwn = ft.select_factor(ts,minimum_dwn,maximum_dwn)
		ts = ft.downsample(ts, dwn)
		sigma_total=sigma_total*np.sqrt(dwn)
		dt = T/len(ts)
	print " Folding, period range of ", p_ranges[num], " ..."
	all_SNs_x1, all_Ps_x1, dts_x1 = fs.ffa_code_stage1(ts, dt,T, sigma_total,p_ranges[num][0],\
		p_ranges[num][1], count_lim,name)
	all_SNs1.append(all_SNs_x1), all_Ps1.append(all_Ps_x1), dts_1.append(dts_x1)
	all_SNs_x2, all_Ps_x2 , dts_x2 = fs.ffa_code_stage2(ts, dt,T, sigma_total,p_ranges[num][0],\
		p_ranges[num][1], count_lim,name)
	all_SNs_2.append(all_SNs_x2), all_Ps_2.append(all_Ps_x2), dts_2.append(dts_x2)
	all_SNs_x3, all_Ps_x3 , dts_x3 = fs.ffa_code_stage3(ts, dt,T, sigma_total,p_ranges[num][0],\
		p_ranges[num][1], count_lim,name)
	all_SNs_3.append(all_SNs_x3), all_Ps_3.append(all_Ps_x3), dts_3.append(dts_x3)


# ------------- 		end of FFA		------------------

# Format the lists of S/N, periods, sampling intervals
for i in range(len(all_Ps1)):
    Ps1.extend(all_Ps1[i]), dt1s.extend(dts_1[i]) , SNs1.extend(all_SNs1[i])
    SNs2_phase1.extend(all_SNs_2[i][0]), SNs2_phase2.extend(all_SNs_2[i][1])
    Ps2.extend(all_Ps_2[i][0]), dt2s.extend(dts_2[i][0])
    SNs4_phase1.extend(all_SNs_2[i][2]), SNs4_phase2.extend(all_SNs_2[i][3])
    SNs4_phase3.extend(all_SNs_2[i][4]), SNs4_phase4.extend(all_SNs_2[i][5])
    Ps4.extend(all_Ps_2[i][1]), dt4s.extend(dts_2[i][1])
    SNs3_phase1.extend(all_SNs_3[i][0]), SNs3_phase2.extend(all_SNs_3[i][1])
    SNs3_phase3.extend(all_SNs_3[i][2])
    Ps3.extend(all_Ps_3[i][0]), dt3s.extend(dts_3[i][0])
    SNs9_phase1.extend(all_SNs_3[i][3]), SNs9_phase2.extend(all_SNs_3[i][4])
    SNs9_phase3.extend(all_SNs_3[i][5]), SNs9_phase4.extend(all_SNs_3[i][6])
    SNs9_phase5.extend(all_SNs_3[i][7]), SNs9_phase6.extend(all_SNs_3[i][8])
    SNs9_phase7.extend(all_SNs_3[i][9]), SNs9_phase8.extend(all_SNs_3[i][10])
    SNs9_phase9.extend(all_SNs_3[i][11])
    Ps9.extend(all_Ps_3[i][1]), dt9s.extend(dts_3[i][1])
    if count_lim ==2:
	SNs8_phase1.extend(all_SNs_2[i][6]), SNs8_phase2.extend(all_SNs_2[i][7])
	SNs8_phase3.extend(all_SNs_2[i][8]), SNs8_phase4.extend(all_SNs_2[i][9])
	SNs8_phase5.extend(all_SNs_2[i][10]), SNs8_phase6.extend(all_SNs_2[i][11])
	SNs8_phase7.extend(all_SNs_2[i][12]), SNs8_phase8.extend(all_SNs_2[i][13])
    	Ps8.extend(all_Ps_2[i][2]), dt8s.extend(dts_2[i][2])
	SNs27_phase1.extend(all_SNs_3[i][12]), SNs27_phase2.extend(all_SNs_3[i][13])
	SNs27_phase3.extend(all_SNs_3[i][14]), SNs27_phase4.extend(all_SNs_3[i][15])
	SNs27_phase5.extend(all_SNs_3[i][16]), SNs27_phase6.extend(all_SNs_3[i][17])
	SNs27_phase7.extend(all_SNs_3[i][18]), SNs27_phase8.extend(all_SNs_3[i][19])
	SNs27_phase9.extend(all_SNs_3[i][20]), SNs27_phase10.extend(all_SNs_3[i][21])
	SNs27_phase11.extend(all_SNs_3[i][22]), SNs27_phase12.extend(all_SNs_3[i][23])
	SNs27_phase13.extend(all_SNs_3[i][24]), SNs27_phase14.extend(all_SNs_3[i][25])
	SNs27_phase15.extend(all_SNs_3[i][26]), SNs27_phase16.extend(all_SNs_3[i][27])
	SNs27_phase17.extend(all_SNs_3[i][28]), SNs27_phase18.extend(all_SNs_3[i][29])
	SNs27_phase19.extend(all_SNs_3[i][30]), SNs27_phase20.extend(all_SNs_3[i][31])
	SNs27_phase21.extend(all_SNs_3[i][32]), SNs27_phase22.extend(all_SNs_3[i][33])
	SNs27_phase23.extend(all_SNs_3[i][34]), SNs27_phase24.extend(all_SNs_3[i][35])
	SNs27_phase25.extend(all_SNs_3[i][36]), SNs27_phase26.extend(all_SNs_3[i][37])
	SNs27_phase27.extend(all_SNs_3[i][38])
    	Ps27.extend(all_Ps_3[i][2]), dt27s.extend(dts_3[i][2])
Ps1, SNs1 = np.concatenate(Ps1), np.concatenate(SNs1)

print "FFA finished for ",name
time_tot =  (time.time() - total_time)
print ( " --- %.7s seconds is the FFA time ---" % time_tot),'\n'


# ==============================	 Post - FFA	=========================================
print "Picking cands .."
# Calculate the mode and the MAD of array of S/N, for 7 (or 5) diff. duty cycles.
# Assumes that the statistics are the same when duty cycle is the same
loc1, scale1  = ft.param_sn_uniform(SNs1)
loc2, scale2 = ft.param_sn_uniform(SNs2_phase1)
loc4, scale4 = ft.param_sn_uniform(SNs4_phase1)
loc3, scale3 = ft.param_sn_uniform(SNs3_phase1)
loc9, scale9 = ft.param_sn_uniform(SNs9_phase1)
if count_lim==2:
	loc8, scale8 = ft.param_sn_uniform(SNs8_phase1)
	loc27, scale27 = ft.param_sn_uniform(SNs27_phase1)
# Making lists of arrays ; all S/Ns for each duty cycle in one object 
list_SNS = [SNs1,SNs2_phase1, SNs2_phase2, SNs4_phase1, SNs4_phase2, SNs4_phase3, SNs4_phase4, 
		SNs3_phase1, SNs3_phase2, SNs3_phase3, SNs9_phase1, SNs9_phase2, SNs9_phase3,	
		SNs9_phase4, SNs9_phase5, SNs9_phase6, SNs9_phase7, SNs9_phase8, SNs9_phase9]

list_PS = [Ps1, Ps2,Ps2,  Ps4,Ps4,Ps4,Ps4,  Ps3,Ps3,Ps3,  Ps9,Ps9,Ps9,Ps9,Ps9,Ps9,Ps9,Ps9,Ps9]
list_DTS = [dt1s, dt2s,dt2s, dt4s,dt4s,dt4s,dt4s, dt3s,dt3s,dt3s,   
	    dt9s,dt9s,dt9s,dt9s,dt9s,dt9s,dt9s,dt9s,dt9s]

list_locs = [loc1, loc2,loc2, loc4,loc4,loc4,loc4, loc3,loc3,loc3, 
		loc9,loc9,loc9,loc9,loc9,loc9,loc9,loc9,loc9] 

list_scales = [scale1, scale2,scale2, scale4,scale4,scale4,scale4, scale3,scale3,scale3,
		scale9,scale9,scale9,scale9,scale9,scale9,scale9,scale9,scale9]

if count_lim ==2:
	list_SNS = list_SNS + [SNs8_phase1, SNs8_phase2, SNs8_phase3, SNs8_phase4, SNs8_phase5, 
				SNs8_phase6, SNs8_phase7, SNs8_phase8, SNs27_phase1, SNs27_phase2, 
				SNs27_phase3, SNs27_phase4, SNs27_phase5, SNs27_phase6, SNs27_phase7, 
				SNs27_phase8, SNs27_phase9, SNs27_phase10, SNs27_phase11, SNs27_phase12,
				SNs27_phase13, SNs27_phase14, SNs27_phase15, SNs27_phase16, SNs27_phase17,
				SNs27_phase18, SNs27_phase19, SNs27_phase20, SNs27_phase21, SNs27_phase22,
				SNs27_phase23, SNs27_phase24, SNs27_phase25, SNs27_phase26, SNs27_phase27]
	list_PS = list_PS + [Ps8, Ps8, Ps8, Ps8, Ps8, Ps8, Ps8, Ps8,
				Ps27, Ps27, Ps27, Ps27, Ps27, Ps27, Ps27, Ps27, Ps27, Ps27, Ps27, Ps27, 
				Ps27, Ps27, Ps27, Ps27, Ps27, Ps27, Ps27, Ps27, Ps27, Ps27, Ps27, Ps27, 				Ps27, Ps27, Ps27 ]
	list_DTS = list_DTS + [dt8s, dt8s, dt8s, dt8s, dt8s, dt8s, dt8s, dt8s, 
				dt27s, dt27s, dt27s, dt27s, dt27s, dt27s, dt27s, dt27s, dt27s, dt27s, 
				dt27s, dt27s, dt27s, dt27s, dt27s, dt27s, dt27s, dt27s, dt27s, dt27s, 
				dt27s, dt27s, dt27s, dt27s, dt27s, dt27s, dt27s ]

	list_locs = list_locs +  [loc8, loc8, loc8, loc8, loc8, loc8, loc8, loc8, 
				loc27, loc27, loc27, loc27, loc27, loc27, loc27, loc27, loc27, loc27, 
				loc27, loc27, loc27, loc27, loc27, loc27, loc27, loc27, loc27, loc27, 
				loc27, loc27, loc27, loc27, loc27, loc27, loc27] 
	list_scales = list_scales + [scale8,  scale8, scale8, scale8, scale8, scale8, scale8, scale8, 
				scale27, scale27, scale27, scale27, scale27, scale27, scale27, scale27, 
				scale27, scale27, scale27, scale27, scale27, scale27, scale27, scale27, 
				scale27, scale27, scale27, scale27, scale27, scale27, scale27, scale27, 
				scale27, scale27, scale27]

# write cands: only True when you get to the end. 
write_cands, write_cands[-1] = [False]*len(list_SNS), True
# Make all S/Ns uniform
list_SNS = [(list_SNS[i] -list_locs[i])/list_scales[i] for i in range(len(list_SNS))]
for i in range(len(list_SNS)):
	cands=ft.pick_cands(list_PS[i], list_SNS[i], list_DTS[i], SN_tresh, write_cands[i], name,"_precands.ffa")

#making precands list (must be sifted)
candsfile_str = 'for_sifting_'+name+'.txt'
candsfile_list = open(candsfile_str ,'w')
candsfile_list.write(name+'_precands.ffa')
candsfile_list.close()
print "Sifting the precands list .. "
if os.stat(name+'_precands.ffa').st_size >0:
	#name = "_dm".join(name.split("_dm")[:-1])
	ft.apply_sifting(candsfile_str,name+'_cands.ffa')
	subprocess.call(["rm",candsfile_str])
else:
	print "No cands with S/N > ",SN_tresh," were detected"
print "Completed ", name
