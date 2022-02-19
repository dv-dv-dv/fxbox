import numpy as np

samplerate = 44100
buffer = 1024
bytes_per_channel = 2
channels = 2

#default compressor variables
threshold = -50
ratio = 7
knee_width = 10
pre_gain = 0
post_gain = 0
attack = 0.005
release = 0.5

# default convolver variables
wet = 1
dry = 1
post = 0.5

# convolver engine variables, do not touch
height = 8
n_cap = 8

# define types
float_size = 2
int_size = 2
