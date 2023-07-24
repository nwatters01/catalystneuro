#!/usr/bin/env bash

#SBATCH -o ./slurm_logs/%A/%a.out
#SBATCH -t 00:30:00
#SBATCH -n 1
#SBATCH --mem-per-cpu 8G
#SBATCH --mail-type=NONE
#SBATCH --mail-user=nwatters@mit.edu
#SBATCH --partition=use-everything

SUBJECT_INDEX=$1

# Make metadata to associate slurm task ID
SESSION_INDEX=${SLURM_ARRAY_TASK_ID}
metadata="SESSION_INDEX: ${SLURM_ARRAY_TASK_ID}"

# Run python
echo "SOURCING BASHRC"
source /home/nwatters/.bashrc
echo "SOURCING CONDA ENVIRONMENT"
conda activate /om/user/nwatters/venvs/numpy_matplotlib
echo "RUNNING PYTHON"
python3 run_summary_plots.py $SUBJECT_INDEX $SESSION_INDEX

