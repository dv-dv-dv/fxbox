samplerate = 44100
buffer = 256
bytes_per_channel = 2
channels = 2

# compressor variables
threshold = -40
ratio = 7
knee_width = 1
pre_gain = 0
post_gain = 18
attack = 0.015
release = 0.2

# convolver variables
imps = ["leave this empty",
        "IMP Spring 04",
        "IMP Cabinet Model A"]
wet = 1
dry = 0
post = 1

# equalizer variables
lowpass_enabled = True
lowpass_cutoff = 500
lowpass_order = 2

highpass_enabled = False
highpass_cutoff = 100
highpass_order = 2

peaking_enabled = [False, False, False]
peaking_gain = [5, 5, 5] # in db
peaking_cutoff = [100, 1000, 10000]
peaking_bandwidth = []
peaking_order = [1, 1, 1] # multiplied by 2

# convolver engine variables
# do not touch, probably
n_step = 2 # any number greater than 1, dont set this higher than 3, probably
first_filter_power = 4
n_start = first_filter_power - 1
filter_size_cap = 8192
height = 4
parallel_max = 4
trim = False
force_trim = False
trim_trigger = 100
trim_window = 50
