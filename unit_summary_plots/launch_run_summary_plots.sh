#!/bin/bash
# This script runs a slurm job array.

SUBJECT_INDEX=0
NUM_SESSIONS=51

# Submit job array to SLURM
array_launch=$(\
    sbatch --array=0-$NUM_SESSIONS run_summary_plots.sbatch $SUBJECT_INDEX
    )
job_id=${array_launch##*' '}
echo "Launched job ${job_id}"

# Create directory for logs
mkdir -p slurm_logs/${job_id}

# Perle:  29543643
# Elgar:  29543566