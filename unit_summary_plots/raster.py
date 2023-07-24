"""Function for making raster plot.

This file also contains a function for evaluating stability of units, computing
indices of trials where the unit was stable.
"""

import constants
from matplotlib import lines as mlp_lines
from matplotlib import pyplot as plt
import numpy as np


def _get_trial_firing_rate(trial_spike_times, relative_phase_times):
    """Estimate firing rate for a trial given spike times.
    
    Args:
        trial_spike_times: Float array of spike times relative to the start of
            that trial (or the start of the visible phase of that trial).
        relative_phase_times: List or array of relative phase times for the
            trial.

    Returns:
        firing_rate: Float or NaN. Estimated firing rate for the trial.
    """
    num_spikes = len(trial_spike_times)
    if num_spikes == 0:
        # No spikes. If the trial had fewer than 3 phases, then it was not long
        # enough to get an estimate of the number of spikes, so return NaN.
        # Otherwise return 0 firing rate.
        if len(relative_phase_times) < 3:
            return np.NaN
        else:
            return 0.
    elif num_spikes < 3:
        # Not enough spikes to estimate firing rate from spikes alone, so
        # instead estimate it from the duration of the trial
        duration = constants.T_BEFORE_STIMULUS_ONSET
        if len(relative_phase_times) > 1:
            duration += min(
                relative_phase_times[-1], constants.T_AFTER_STIMULUS_ONSET)
    else:
        # Estimate firing rate from spikes alone
        duration = trial_spike_times[-1] - trial_spike_times[0]
        num_spikes -= 1
    
    firing_rate = num_spikes / duration
    return firing_rate


def _get_stable_trial_inds(spike_times_per_trial,
                           relative_phase_times,
                           rolling_average_window_size):
    """Get indices of trials where unit seems stable.

    The general approach to evaluating stability is as follows:
        * Estimate firing rate for each trial
        * Smooth the firing rate with a rolling average of 
            constants.STABILITY_ROLLING_AVERAGE_WINDOW_SIZE trials.
        * If this smoothed firing rate exhibits a dramatic relative change in a
            small window, mark the trial in the middle of this window as
            unstable. The window size is again
            constants.STABILITY_ROLLING_AVERAGE_WINDOW_SIZE, and a dramatic
            relative change means that within this window, the difference
            between and max and min rolling average firing rate is more than a
            multiple of constants.UNSTABLE_FR_RATIO.
        * Fill in short blocks of stable trials. If there are fewer than
            constants.STABLE_BLOCK_SIZE consecutive stable trials between those
            marked unstable, mark the entire block as unstable.
        * If there are multiple blocks of consecutive trials remaining, choose
            the longest such block and mark as unstable any blocks that differ
            significantly in mean firing rate from this longest block.
    
    Empirically, this method gives reasonable stability evaluations for our
    dataset.

    Args:
        spike_times_per_trial: List of length num_trials. Each element is a
            float array of spike times.
        relative_phase_times: List of length num_trials. Each element is a
            float array of relative phase times.

    Returns:
        stable_trial_inds: Integer array of indices of trials to keep, namely
            trials where the unit seems stable.
    """
    if len(spike_times_per_trial) != len(relative_phase_times):
        raise ValueError(
            f'len(spike_times_per_trial) = {len(spike_times_per_trial)} but '
            f'len(relative_phase_times) = {len(relative_phase_times)}'
        )
    unstable_fr_window_size = (
        constants.UNSTABLE_FR_WINDOW_SIZE)
    if rolling_average_window_size % 2 == 0:
        raise ValueError(
            f'rolling_average_window_size = {rolling_average_window_size}, but '
            'must be an odd number'
        )

    # Compute firing rate per trial
    firing_rates = np.array([
        _get_trial_firing_rate(trial_spike_times, rel_phase_times)
        for trial_spike_times, rel_phase_times in zip(
            spike_times_per_trial, relative_phase_times)
    ])
    firing_rate_finite_inds = np.argwhere(np.isfinite(firing_rates))[:, 0]
    firing_rate_nan_inds = np.argwhere(np.isnan(firing_rates))[:, 0]
    firing_rates_finite = firing_rates[firing_rate_finite_inds]

    # Rolling average of firing rate
    kernel = np.arange(1 + rolling_average_window_size // 2, dtype=float)
    kernel = np.concatenate([kernel[:-1], kernel[::-1]])
    kernel /= np.sum(kernel)
    rolling_firing_rates = np.convolve(
        firing_rates_finite,
        kernel,
        mode='valid',
    )

    # Times when the firing rate changes by over a factor of
    # constants.UNSTABLE_FR_RATIO in one window are deemed unstable
    len_stable = len(rolling_firing_rates) - unstable_fr_window_size + 1
    stable = np.ones(len(rolling_firing_rates))
    for i in range(len_stable - unstable_fr_window_size + 1):
        window = rolling_firing_rates[i: i + unstable_fr_window_size]
        max_window = np.max(window)
        if max_window == 0:
            stable[i] = 0.
        else:
            unstable_window_inds = (
                window < max_window / constants.UNSTABLE_FR_RATIO)
            stable[i: i + unstable_fr_window_size][unstable_window_inds] = 0.

    stable_unstable_switches = np.sum(
        np.convolve(2 * stable - 1, [-1, 1], mode='valid') == 2.)
    if stable_unstable_switches > constants.NUM_SWITCHES_TO_DOUBLE_WINDOW_SIZE:
        new_rolling_average_window_size = 2 * rolling_average_window_size - 1
        return _get_stable_trial_inds(spike_times_per_trial,
                                      relative_phase_times,
                                      new_rolling_average_window_size)

    orig_stable = np.copy(stable)

    # Blocks of less than constants.STABLE_BLOCK_SIZE consecutive stable trials
    # are deemed unstable
    last_unstable = -1
    for i, s in enumerate(stable):
        if not s or i == len(stable) - 1:
            if last_unstable > i - constants.STABLE_BLOCK_SIZE:
                stable[last_unstable + 1: i + 1] = False
            last_unstable = i
    
    # If there are multiple blocks of stable trials and they have drastically
    # different firing rates (off by a multiple of over
    # constants.UNSTABLE_BLOCK_FR_RATIO), pick the largest block
    stable_block_starts = []
    stable_block_ends = []
    prev_stable = 0
    for i, s in enumerate(stable):
        if s and i == len(stable) - 1:
            stable_block_ends.append(i + 1)
        if s and not prev_stable:
            stable_block_starts.append(i)
        if prev_stable and not s:
            stable_block_ends.append(i)
        prev_stable = s
    stable_blocks = list(zip(stable_block_starts, stable_block_ends))

    # Mark blocks with mean firing rate lower than
    # constants.FIRING_RATE_THRESHOLD as unstable
    low_fr_block_inds = []
    for i, (start, end) in enumerate(stable_blocks):
        block_fr = np.mean(rolling_firing_rates[start: end])
        if block_fr < constants.FIRING_RATE_THRESHOLD:
            stable[start:end] = 0
            low_fr_block_inds.append(i)
    for i in low_fr_block_inds[::-1]:
        stable_blocks.pop(i)

    if len(stable_blocks) > 1:
        stable_block_firing_rates = [
            np.mean(rolling_firing_rates[start: end])
            for start, end in stable_blocks
        ]
        block_rf_ratio = constants.UNSTABLE_BLOCK_FR_RATIO
        min_thresh = block_rf_ratio * min(stable_block_firing_rates)
        if max(stable_block_firing_rates) > min_thresh:
            # Find the largest block with firing rate > 1. This will be our
            # reference block.
            block_lengths = np.array([
                end - start if fr > 1. else 0.
                for (start, end), fr in zip(
                    stable_blocks, stable_block_firing_rates)
            ])
            if np.all(block_lengths == 0.):
                # No block had firing rate > 1., so use all blocks
                block_lengths = np.array([
                    end - start for (start, end) in stable_blocks
                ])
            max_block_ind = int(np.argmax(block_lengths))
            max_block_firing_rate = stable_block_firing_rates[max_block_ind]
            for i, fr in enumerate(stable_block_firing_rates):
                ratio = fr / max_block_firing_rate
                if not 1. / block_rf_ratio < ratio < block_rf_ratio:
                    # Make block unstable
                    stable[stable_blocks[i][0]: stable_blocks[i][1]] = 0.

    # Convert back to firing_rates_finite shape
    buffer_len = rolling_average_window_size // 2
    beginning_buffer = np.ones(buffer_len)
    end_buffer = np.ones(buffer_len)
    if not stable[0]:
        beginning_buffer *= 0.
    if not stable[-1]:
        end_buffer *= 0.
    stable = np.concatenate([beginning_buffer, stable, end_buffer])

    # Convert back to firing_rates shape by filling in the nan trials
    stable_trials = np.ones(len(firing_rates))
    stable_trials[firing_rate_finite_inds] = stable
    for i in firing_rate_nan_inds:
        if firing_rate_finite_inds[-1] > i:
            neighbor = np.argwhere([firing_rate_finite_inds > i])[0, 1]
            if not stable[neighbor]:
                stable_trials[i] = 0.
        if firing_rate_finite_inds[0] < i:
            neighbor = np.argwhere([firing_rate_finite_inds < i])[-1, 1]
            if not stable[neighbor]:
                stable_trials[i] = 0.

    stable_trial_inds = np.argwhere(stable_trials)
    if len(stable_trial_inds) > 0:
        stable_trial_inds = stable_trial_inds[:, 0].tolist()
    else:
        stable_trial_inds = []

    # plt.figure()
    # plt.plot(rolling_firing_rates)
    # plt.plot(orig_stable)
    
    return stable_trial_inds


def plot_raster(ax, spike_times, start_times, relative_phase_times):
    """Make raster plot."""
    spikes_raster_x = []
    spikes_raster_y = []

    phase_times_raster_x = []
    phase_times_raster_y = []
    phase_times_raster_colors = []

    spike_times_per_trial = []

    num_trials = len(start_times)
    spike_index = 0
    completed_trial_inds = []
    for trial_num in range(num_trials):
        start_t = start_times[trial_num]
        
        if not np.isfinite(start_t):
            spike_times_per_trial.append([])
            continue

        rel_phase_t = relative_phase_times[trial_num]
        rel_visible_phase_t = rel_phase_t[0]
        stimulus_onset_t = start_t + rel_visible_phase_t

        # Append the relative phase times to raster data
        for i, t in enumerate(rel_phase_t):
            if i >= len(constants.PHASE_COLORS):
                break
            phase_times_raster_x.append(t - rel_visible_phase_t)
            phase_times_raster_y.append(trial_num)
            phase_times_raster_colors.append(constants.PHASE_COLORS[i][1])
            
        # Count spike times per completed trial if this trial has all phases
        completed_trial = len(rel_phase_t) == 6
        completed_trial_inds.append(completed_trial)
        spike_times_this_trial = []
        
        # Update spikes raster data based on spike times
        next_trial = False
        while not next_trial:
            if spike_index >= len(spike_times):
                # No more spikes for this neuron, so move on to next trial
                next_trial = True
                continue
            
            spike_t = spike_times[spike_index]

            if spike_t > stimulus_onset_t + constants.T_AFTER_STIMULUS_ONSET:
                # Trial is completed, so move on to next trial
                next_trial = True
                continue
            
            if (trial_num < len(start_times) - 1 and
                    spike_t > start_times[trial_num + 1]):
                # Trial is completed, so move on to next trial
                next_trial = True
                continue

            if spike_t < stimulus_onset_t - constants.T_BEFORE_STIMULUS_ONSET:
                # Have yet to reach beginning of trial, so move on to next spike
                spike_index += 1
                continue

            # Append the spike time to raster data
            spikes_raster_x.append(spike_t - stimulus_onset_t)
            spikes_raster_y.append(trial_num)
            spike_index += 1

            # Append spike time to spike_times_this_trial if necessary
            if completed_trial:
                spike_times_this_trial.append(spike_t - stimulus_onset_t)
        
        # Append spike_times_this_trial to spike_times_per_trial
        spike_times_per_trial.append(spike_times_this_trial)
    

    spike_times_per_completed_trial = [
        x for completed, x in zip(completed_trial_inds, spike_times_per_trial)
        if completed and len(x) > 0
    ]

    # Scatter spike times and phases
    ax.scatter(spikes_raster_x, spikes_raster_y, c='k', s=0.2)
    ax.scatter(
        phase_times_raster_x, phase_times_raster_y, c=phase_times_raster_colors,
        s=0.2)

    # Add gray dot for trials in stable_trial_inds
    stable_trial_inds = _get_stable_trial_inds(
        spike_times_per_trial,
        relative_phase_times,
        constants.STABILITY_ROLLING_AVERAGE_WINDOW_SIZE,
    )
    ax.scatter(
        len(stable_trial_inds) * [constants.T_AFTER_STIMULUS_ONSET + 0.1],
        stable_trial_inds, color=[0.7, 0.7, 0.7], s=1, marker='s',
    )

    # Create axis labels
    ax.set_xlabel('Time within trial (sec)', fontsize=10)
    ax.set_ylabel('Trial number', fontsize=12)
    ax.set_xlim(
        -0.1 - constants.T_BEFORE_STIMULUS_ONSET,
        0.2 + constants.T_AFTER_STIMULUS_ONSET,
    )
    ax.set_ylim(-10, num_trials + 10)
    ax.set_title('Raster Plot', fontsize=12, weight='bold', y=1.03)

    # Create legend
    legend_handles = [
        mlp_lines.Line2D(
            [], [], marker='.', color=color, markerfacecolor=color,
            markersize=3.5, label=label, linewidth=0.)
        for label, color in constants.PHASE_COLORS
    ]
    ax.legend(
        handles=legend_handles, loc='upper center', bbox_to_anchor=(0.45, 1.04),
        ncol=5, fancybox=True, markerscale=3, borderpad=0.,
        columnspacing=0.6, handletextpad=0., handlelength=1.5, fontsize=9,
    )
    
    return spike_times_per_completed_trial, stable_trial_inds
