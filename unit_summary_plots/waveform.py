"""Function for making waveform plot."""

import numpy as np

_PHYS_SAMPLE_RATE = 30000


def plot_waveform(ax, waveform):
    """Plot waveform.
    
    Args:
        ax: Matplotlib Axes instance.
        waveform: Float array of shape [timesteps, channels].
    """

    # Find channel with maximum amplitude and channel spacing
    norm_waveform = waveform - np.mean(waveform, axis=0, keepdims=True)
    amplitudes = np.max(norm_waveform, axis=0) - np.min(norm_waveform, axis=0)
    max_amplitude_channel = np.argmax(amplitudes)
    channel_separation = 0.5 * np.max(amplitudes)

    # Find out if neuropixel or v-probe
    num_channels = norm_waveform.shape[1]
    if num_channels == 384:
        probe_type = 'np'
        chans_to_plot = 37
    elif num_channels == 64:
        probe_type = 'v_probe'
        chans_to_plot = 13
    else:
        raise ValueError(f'Invalid num_channels {num_channels}')

    # Plot each channel of norm_waveform
    chans_plotted = []
    for i in range(chans_to_plot):
        chan_ind = i + max_amplitude_channel - chans_to_plot // 2
        chans_plotted.append(chan_ind)
        if chan_ind < 0 or chan_ind >= num_channels:
            continue

        x_values = np.arange(norm_waveform.shape[0]) * 1000. / _PHYS_SAMPLE_RATE
        if probe_type == 'np':
            if chan_ind % 2 == 1:
                x_values += 3.
        
        y_values = chan_ind * channel_separation + norm_waveform[:, chan_ind]
        ax.plot(x_values, y_values, c='b', linewidth=3)
    
    # Axis handling
    ax.set_ylim(
        channel_separation * (chans_plotted[0] - 1),
        channel_separation * (chans_plotted[-1] + 1),
    )
    tick_chans = np.array(chans_plotted[::2])
    tick_chans = tick_chans[
        np.logical_and(tick_chans >= 0, tick_chans < num_channels)
    ]
    _ = ax.set_yticks(channel_separation * tick_chans)
    _ = ax.set_yticklabels(tick_chans)
    ax.set_ylabel('Channel')
    ax.set_xlabel('Time (ms)')
    ax.set_title('Waveform', fontsize=12, weight='bold')
    
    return
