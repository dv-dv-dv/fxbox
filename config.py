samplerate = 44100
buffer = 64
bytes_per_channel = 2
channels = 2

# compressor variables
threshold = -50
ratio = 7
knee_width = 10
pre_gain = 0
post_gain = 20
attack = 0.005
release = 0.5

# convolver variables
wet = 1
dry = 1
post = 0.5

# convolver engine variables
# do not touch, probably
n_step = 2 # any number greater than 1, dont set this higher than 3, probably
first_filter_power = 5
n_start = first_filter_power - 1
filter_size_cap = 16384
height = 2**(n_step)
parallel_max = 2
power_ratio = 2 # doesnt work for numbers above 2
trim = False
force_trim = False
trim_trigger = 100
trim_window = 50