# master parameters
buffer_size = 256
samplerate = 44100 # do not change
bytes_per_channel = 2 # do not change
channels = 2 # do not change
#
master_pre_gain_db = 0
master_post_gain_db = 0
# compressor variables
threshold = -40
ratio = 10
knee_width = 10
pre_gain = 0
post_gain = 15
attack = 0.02
release = 0.2
rms = True
hold = 0.01 # not yet implemented

# convolver variablesg here",
imps = ["do not put anythin",
        "IMP Spring 04",
        "IMP Spring 06",
        "IMP Cabinet Model A",
        "IMP Cabinet Model B"]

imp_number = 1
wet = 1
dry = 1
post = 0.5

# equalizer variables
lpf_fc = 5000
lpf_N = 2
lpf_en= 0

hpf_fc = 100
hpf_N = 1
hpf_en = 0

bll1_fgm = 1000
bll1_N = 1
bll1_gdb = 3
bll1_bfac = 0.5
bll1_en = 1

bll2_fgm = 10000
bll2_N = 1
bll2_gdb = 3
bll2_bfac = 0.5
bll2_en = 1

# convolver engine variables
n_step = 2 # any number greater than 1, dont set this higher than 3, probably
first_filter_power = 2
n_start = first_filter_power - 1
filter_size_cap = 8192
height = 4
