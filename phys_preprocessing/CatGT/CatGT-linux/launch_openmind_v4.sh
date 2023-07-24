#!/usr/bin/env bash

# Run CatGT on raw spikeglx data.

#SBATCH -o ./slurm_logs/%A.out
#SBATCH -t 24:00:00
#SBATCH -n 1
#SBATCH --mem-per-cpu 128G
#SBATCH --mail-type=NONE
#SBATCH --mail-user=nwatters@mit.edu
#SBATCH --partition=jazayeri

mkdir /om2/user/nwatters/multi_prediction/phys_data/Elgar/2022-06-22/raw_data/spikeglx_v4

bash runit.sh \
-dir=/om2/user/nwatters/multi_prediction/phys_data/Elgar/2022-06-22/raw_data/spikeglx/ \
-run=2022_06_22_elgar_task \
-dest=/om2/user/nwatters/multi_prediction/phys_data/Elgar/2022-06-22/raw_data/spikeglx_v4/ \
-no_run_fld \
-ap \
-prb=0 \
-g=0 \
-t=0 \
-xa=0,0,2,3.0,4.5,25 \
-xd=2,0,384,6,500 \
-xia=0,0,2,3.0,4.5,2 \
-xid=2,0,384,6,50 \
-gblcar \
-loccar=40,160

