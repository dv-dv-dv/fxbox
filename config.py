samplerate = 44100
buffer = 256
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
post = 1

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
