"""Make summary plot for every unit."""

import constants
import inter_spike_interval
import json
from matplotlib import pyplot as plt
import numpy as np
import os
import psth
import raster
import sys
import waveform


def _make_plot(probe_metadata,
               session_dir,
               start_times,
               relative_phase_times,
               print_cluster_id=False):
    
    # Extract subject and session date for plot title
    subject = session_dir.split('/')[-3]
    session_date = session_dir.split('/')[-2]

    # Get probe data
    probe_label = probe_metadata['label']
    print(f'Probe {probe_label}')
    probe_dir = os.path.join(session_dir, probe_label)
    labels_path = os.path.join(probe_dir, 'clusters.labels.tsv')
    labels = np.genfromtxt(
        labels_path,
        delimiter='\t',
        skip_header=True,
        dtype=str,
    )
    waveforms = np.load(os.path.join(probe_dir, 'clusters.waveforms.npy'))
    if waveforms.shape[0] != len(labels):
        raise ValueError(
            f'waveforms.shape[0] = {waveforms.shape[0]} but len(labels) = '
            f'{len(labels)}'
        )
    num_clusters = len(labels)

    spikes_clusters = np.load(os.path.join(probe_dir, 'spikes.clusters.npy'))
    spikes_times = np.load(os.path.join(probe_dir, 'spikes.times.npy'))




    # sample_rate = 30000.
    # spikes_clusters = np.squeeze(np.load(os.path.join(probe_dir, 'spike_clusters.npy')))
    # spikes_times_ks = np.squeeze(np.load(os.path.join(probe_dir, 'spike_times.npy')))
    # adj_spike_times = spikes_times_ks / sample_rate
    # oe_start_bad_time = 1849.7108999999966
    # oe_end_bad_time = 1963.1731384071338
    # oe_after_boost = 281.0703980748031
    # before_inds = adj_spike_times < oe_start_bad_time
    # after_inds = adj_spike_times > oe_end_bad_time
    # spikes_times = np.concatenate(
    #     [adj_spike_times[before_inds], oe_after_boost + adj_spike_times[after_inds]]
    # )
    # spikes_clusters = np.concatenate(
    #     [spikes_clusters[before_inds], spikes_clusters[after_inds]]
    # )
    # # transform into mworks timescale
    # coef = 0.9999660856877924
    # intercept = -62.243346439713605
    # recording_start_time = 2.261333333333
    # open_source_minus_processed = -50.144393
    # spikes_times = (
    #     coef * spikes_times +
    #     intercept +
    #     open_source_minus_processed +
    #     recording_start_time
    # )
    # # Get good indices
    # keep_cluster_ids = labels[:, 0].astype(int)
    # new_spikes_clusters = np.array(
    #     [x for x in spikes_clusters if x in keep_cluster_ids])
    # new_spikes_times = np.array([
    #     t for x, t in zip(spikes_clusters, spikes_times)
    #     if x in keep_cluster_ids
    # ])
    # write_times_path = os.path.join(probe_dir, 'new_spike_times')
    # write_clusters_path = os.path.join(probe_dir, 'new_spike_clusters')
    # np.save(write_clusters_path, new_spikes_clusters)
    # np.save(write_times_path, new_spikes_times)
    # import pdb; pdb.set_trace()





    # Get write directory
    write_dir = os.path.join(
        constants.WRITE_DIR, subject, session_date, probe_label)
    if not os.path.exists(write_dir):
        os.makedirs(write_dir)

    # Iterate through units and plot rasters
    all_stable_trial_inds = []
    # for i in [0]:
    for i in range(num_clusters):
        (cluster_id, label) = labels[i]
        cluster_id = cluster_id.astype(np.uint32)
        
        # cluster_id = 99
        # label = 'mua'

        if print_cluster_id:
            print(f'cluster_id: {cluster_id}')
        spike_times = spikes_times[
            np.argwhere(spikes_clusters == cluster_id)[:, 0]
        ]
        
        # Create figure and axes
        fig = plt.figure(figsize=(8, 10))
        gridspec = fig.add_gridspec(1, 2)
        gridspec_left = gridspec[0].subgridspec(2, 1, height_ratios=(5, 1))
        gridspec_right = gridspec[1].subgridspec(2, 1, height_ratios=(2, 1))
        ax_raster = fig.add_subplot(gridspec_left[0])
        ax_psth = fig.add_subplot(gridspec_left[1])
        ax_waveform = fig.add_subplot(gridspec_right[0])
        ax_inter_spike_interval = fig.add_subplot(gridspec_right[1])

        # Plot raster, psth, waveform, and inter_spike_interval
        spike_times_per_completed_trial, stable_trial_inds = raster.plot_raster(
            ax_raster, spike_times, start_times, relative_phase_times)
        all_stable_trial_inds.append(stable_trial_inds)
        psth.plot_psth(ax_psth, spike_times_per_completed_trial)
        waveform.plot_waveform(ax_waveform, waveforms[i])
        inter_spike_interval.plot_inter_spike_interval(
            ax_inter_spike_interval, spike_times)

        # Make plot title
        fig.suptitle(
            f'{subject}/{session_date}, unit {cluster_id}, {label}',
            fontsize=16, y=0.99,
        )
        plt.tight_layout()
        
        # Save and close figure
        fig_path = os.path.join(write_dir, str(cluster_id) + '.png')
        fig.savefig(fig_path)
        if print_cluster_id:
            print(f'Figure saved to {fig_path}')
        plt.close(fig)
        
    # Save all_stable_trial_inds
    stable_trial_inds_path = os.path.join(
        probe_dir, 'clusters.stable_trials.json')
    json.dump(all_stable_trial_inds, open(stable_trial_inds_path, 'w'))

    return


def _process_session(session_dir):
    print(session_dir)

    # Load trial start time, end time, and relative phase times
    start_times_path = os.path.join(
        session_dir, 'task', 'trials.start_times.json')
    start_times = json.load(open(start_times_path, 'r'))
    relative_phase_times_path = os.path.join(
        session_dir, 'task', 'trials.relative_phase_times.json')
    relative_phase_times = json.load(open(relative_phase_times_path, 'r'))

    # Load probe metadata
    probes_metadata_path = os.path.join(session_dir, 'probes.metadata.json')
    probes_metadata = json.load(open(probes_metadata_path, 'r'))
    
    # Iterate through probes and units
    for probe_metadata in probes_metadata:
        _make_plot(
            probe_metadata, session_dir, start_times, relative_phase_times,
        )


# def main():
def main(subject_index, session_index):
    """Make summary plot for every unit."""

    # Monkey 0: 51
    # Monkey 1: 75

    print(f'subject_index: {subject_index}')
    print(f'session_index: {session_index}')

    subject = sorted(os.listdir(constants.DATA_DIR))[int(subject_index)]
    # subject = 'monkey1'
    subject_dir = os.path.join(constants.DATA_DIR, subject)
    session_date = sorted(os.listdir(subject_dir))[int(session_index)]
    # session_date = '2022-06-25'
    session_dir = os.path.join(subject_dir, session_date, '001')
    _process_session(session_dir)
    print('\nDONE')
            

if __name__ == "__main__":
    subject_index=sys.argv[1]
    session_index=sys.argv[2]
    # main(None, None)
    main(subject_index, session_index)


"""
To REVISIT:

Perle/2022-04-07, probe02
"""
