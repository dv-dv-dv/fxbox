samplerate = 44100
buffer = 256
bytes_per_channel = 2
channels = 2

# compressor variables
threshold = -30.1
ratio = 7
knee_width = 1
pre_gain = 0
post_gain = 0
attack = 0.02065
release = 0.10046

# convolver variables
wet = 1
dry = 1
post = 0.5

# equalizer variables
lowpass_enabled = True
lowpass_cutoff = 5000
lowpass_order = 2

highpass_enabled = True
highpass_cutoff = 100
highpass_order = 2

peaking_gain = [5, 5, 5] # in db
peaking_cutoff = [100, 1000, 10000]
peaking_bandwidth = []
peaking_order = [1, 1, 1] # multiplied by 2

# convolver engine variables
# do not touch, probably
n_step = 2 # any number greater than 1, dont set this higher than 3, probably
first_filter_power = 5
n_start = first_filter_power - 1
filter_size_cap = 16384
height = 2**(n_step)
parallel_max = 1
trim = False
force_trim = False
trim_trigger = 100
trim_window = 50