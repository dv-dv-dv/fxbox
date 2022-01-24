
import numpy as np
import math

#user imports
import settings as cfg



class Compressor:
    k = (2**(cfg.bytes_per_channel*8))/2
    def __init__(self, T=-30, R=7, W=10, M=0, atk=0.005, rel=0.5):
        self.T = T
        self.R = R
        self.W = W
        self.M = M
        self.atk = math.exp(-1/(atk*cfg.samplerate))
        self.rel = math.exp(-1/(rel*cfg.samplerate))
        self.vtoLin = np.vectorize(self.toLin)
        self.vtoDb = np.vectorize(self.toDb)
        self.vgainComp = np.vectorize(self.gainComp)
        self.vlvlDetect = np.vectorize(self.lvlDetect)
        self.outnminus1 = 0
        
    def compressor(self, i):
        in1 = i[:,0]
        in2 = i[:,1]
        il = abs(i[:,0] + i[:,1])
        odb1 = self.vtoDb(il)
        odb2 = self.vgainComp(odb1)
        odb3 = odb1 - odb2
        odb4 = self.vlvlDetect(odb3)
        gdb1 = odb4 - self.M
        g = self.vtoLin(gdb1)
        out1 = np.multiply(in1.astype(float),g)
        out2 = np.multiply(in2.astype(float),g)
        out = np.stack((out1,out2),axis=1)
        o = out.astype('i2')
        return o
    
    def lvlDetect(self, i):
        if i > self.outnminus1:
            o = self.atk*self.outnminus1+(1-self.atk)*i
        else:
            o = self.rel*self.outnminus1+(1-self.rel)*i
        self.outnminus1 = o
        return o
    
    def gainComp(self, i):
        if 2*(i - self.T) < -self.W:
            o = i
        elif 2*abs(i - self.T) <= self.W:
            o = i + (1/self.R-1)*((i - self.T + self.W/2)**2)/(2*self.W)
        elif 2*(i - self.T) > self.W:
            o = self.T + (i - self.T)/self.R
        return o
    
    def toDb(self, i):
        if(i==0):
            o = -9999.0
        else:
            infl = float(i)/Compressor.k
            o = 20*math.log10(infl)
        return o
    
    def toLin(self, i):
        o = 10**(-i/20)
        return o
    
    