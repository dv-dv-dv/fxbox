import numpy as np
import math

#user imports
import settings as cfg

ldprevout = 0
T = -30
R = 7
W = 10
M = 0
atk = math.exp(-1/(0.005*cfg.samplerate))
rel = math.exp(-1/(0.2*cfg.samplerate))

def compressor(i):
    o = np.ones((i.size/2, 2), dtype='i2')
    il = abs(i[:,0] + i[:,1])
    odb1 = toDb(il)
    odb2 = gainComp(odb1)
    odb3 = odb1 - odb2
    odb4 = lvlDetect(odb3)
    gdb1 = odb4 - M
    g = toLin(gdb1)
    for n in range(i.size/2):
        o[n,0] = int(float(i[n,0]) * g[n])
        o[n,1] = int(float(i[n,1]) * g[n])
    return o

def lvlDetect(i):
    global ldprevout
    o = np.zeros((i.size, 1))
    outnminus1 = ldprevout
    for n in range(i.size):
        if i[n] > outnminus1:
            o[n] = atk*outnminus1+(1-atk)*i[n]
        else:
            o[n] = rel*outnminus1+(1-rel)*i[n]
        outnminus1 = o[n]
    if i.size - 1 < 0:
        ldprevout = 0
    else:
        ldprevout = o[i.size-1]
    return o

def gainComp(i):
    o = np.zeros((i.size, 1))
    for n in range(i.size):
        if 2*(i[n]-T) < -W:
            o[n] = i[n]
        elif 2*abs(i[n]-T) <= W:
            o[n] = i[n] + (1/R-1)*((i[n] - T + W/2)**2)/(2*W)
        elif 2*(i[n] - T) > W:
            o[n] = T + (i[n] - T)/R
    return o

def toDb(i):
    o = np.zeros((i.size, 1))
    k = (2**(cfg.bytes_per_channel*8))/2
    for n in range(i.size):
        if i[n] == 0:
            o[n] = -999.0;
        else:
            infl = float(i[n])/k
            o[n] =20*math.log10(infl)
    return o

def toLin(i):
    o = np.zeros((i.size,1))
    for n in range(i.size):
        o[n] = 10**(-i[n]/20)
    return o