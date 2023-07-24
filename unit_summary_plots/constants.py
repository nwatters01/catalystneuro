"""Constants."""

import colorsys

################################################################################
####  DATA AND WRITE PATHS
################################################################################

DATA_DIR = (
    '/om2/user/nwatters/multi_prediction/datasets/data_open_source/Subjects'
)
WRITE_DIR = (
    '/om2/user/nwatters/multi_prediction/phys_analysis/unit_summary_plots/plots'
)
# DATA_DIR = (
#     '/Users/nicholaswatters/Desktop/grad_school/research/mehrdad/'
#     'multi_prediction/datasets/data_open_source/Subjects'
# )
# WRITE_DIR = (
#     '/Users/nicholaswatters/Desktop/grad_school/research/mehrdad/'
#     'multi_prediction/phys/phys_analysis/unit_summary_plots/plots_test'
# )

################################################################################
####  COLOR SCHEME FOR TASK PHASES
################################################################################

PHASE_COLORS = [
    ('stimulus', colorsys.hsv_to_rgb(0.28, 1., 1.)),  # stimulus onset
    ('delay', colorsys.hsv_to_rgb(0.4, 1., 1.)),  # delay onset
    ('cue', colorsys.hsv_to_rgb(0.52, 1., 1.)),  # cue onset
    ('response', colorsys.hsv_to_rgb(0.64, 1., 1.)),  # response onset
    ('reveal', colorsys.hsv_to_rgb(0.76, 1., 1.)),  # reveal onset
]

################################################################################
####  TRIAL TIME RANGE FOR RASTER AND PSTH PLOTS
################################################################################

# How long (seconds) before stimulus onset to begin raster plot
T_BEFORE_STIMULUS_ONSET = 0.5
# How long (seconds) after stimulus onset to end raster plot
T_AFTER_STIMULUS_ONSET = 3.25

################################################################################
####  PSTH PARAMETERS
################################################################################

PSTH_BOOTSTRAP_NUM = 100
PSTH_BIN_WIDTH = 0.03
# Number of bins in half the range of the tooth smoothing function for PSTHs
PSTH_KERNEL_HALF_WIDTH = 5

################################################################################
####  INTER-SPIKE INTERVAL PLOT PARAMETERS
################################################################################

ISI_BIN_WIDTH = 0.001
ISI_MAX = 0.1

################################################################################
####  STABILITY PARAMETERS
################################################################################

STABILITY_ROLLING_AVERAGE_WINDOW_SIZE = 51
UNSTABLE_FR_WINDOW_SIZE = 51
UNSTABLE_FR_RATIO = 2.2
UNSTABLE_BLOCK_FR_RATIO = 2.
STABLE_BLOCK_SIZE = 150
FIRING_RATE_THRESHOLD = 0.25
NUM_SWITCHES_TO_DOUBLE_WINDOW_SIZE = 20