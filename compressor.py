
import numpy as np
import math

#user imports
import settings as cfg

outnminus1 = 0
T = -30
R = 7
W = 10
M = 0
atk = math.exp(-1/(0.005*cfg.samplerate))
rel = math.exp(-1/(0.2*cfg.samplerate))
k = (2**(cfg.bytes_per_channel*8))/2

def compressor(i):
    in1 = i[:,0]
    in2 = i[:,1]
    il = abs(i[:,0] + i[:,1])
    odb1 = vtoDb(il)
    odb2 = vgainComp(odb1)
    odb3 = odb1 - odb2
    odb4 = vlvlDetect(odb3)
    gdb1 = odb4 - M
    g = vtoLin(gdb1)
    out1 = np.multiply(in1.astype(float),g)
    out2 = np.multiply(in2.astype(float),g)
    out = np.stack((out1,out2),axis=1)
    o = out.astype('i2')
    return o

def lvlDetect(i):
    global outnminus1
    if i > outnminus1:
        o = atk*outnminus1+(1-atk)*i
    else:
        o = rel*outnminus1+(1-rel)*i
    outnminus1 = o
    return o

def gainComp(i):
    if 2*(i - T) < -W:
        o = i
    elif 2*abs(i - T) <= W:
        o = i + (1/R-1)*((i - T + W/2)**2)/(2*W)
    elif 2*(i - T) > W:
        o = T + (i - T)/R
    return o

def toDb(i):
    if(i==0):
        o = -9999.0
    else:
        infl = float(i)/k
        o = 20*math.log10(infl)
    return o

def toLin(i):
    o = 10**(-i/20)
    return o

vtoLin = np.vectorize(toLin)
vtoDb = np.vectorize(toDb)
vgainComp = np.vectorize(gainComp)
vlvlDetect = np.vectorize(lvlDetect)