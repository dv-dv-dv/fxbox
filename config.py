samplerate = 44100
buffer = 1024
bytes_per_channel = 2
channels = 2

#default compressor variables
threshold = -50
ratio = 7
knee_width = 10
pre_gain = 0
post_gain = 20
attack = 0.005
release = 0.5

# default convolver variables
wet = 1
dry = 1
post = 0.5

# convolver engine variables
# do not touch, probably
n_step = 1 # any number greater than 1, dont set this higher than 3, probably
filter_size_cap = 16384
delay_amount = 0 # delays the convolution by 2**n buffer counts, improves performance significantly
height = 2**(n_step) 