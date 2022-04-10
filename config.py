samplerate = 44100
buffer_size = 256
bytes_per_channel = 2
channels = 2

# compressor variables
threshold = -40
ratio = 30
knee_width = 10
pre_gain = 0
post_gain = 15
attack = 0.0018
release = 0.2
rms = True
hold = 0.01

# convolver variables
imps = ["leave this empty",
        "IMP Spring 04",
        "IMP Spring 05",
        "IMP Cabinet Model A",
        "IMP Cabinet Model B"]

imp_number = 1
wet = 1
dry = 1
post = 0.5

# equalizer variables
lpf_fc = 10000
lpf_N = 2
lpf_en= True

hpf_fc = 100
hpf_N = 2
hpf_en = True

bll_fgm = 1000
bll_N = 1
bll_gdb = 6
bll_bfac = 0.5
bll_en = True

# convolver engine variables
# do not touch, probably
n_step = 2 # any number greater than 1, dont set this higher than 3, probably
first_filter_power = 4
n_start = first_filter_power - 1
filter_size_cap = 8192
height = 4
trim = False
force_trim = False
trim_trigger = 100
trim_window = 50
