import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path
import pandas as pd
import spikeinterface.full as si

from tdtb.functions.filter_task_table import filter_task_table
from tdtb.functions.get_trial_frames import get_trial_frames

def plot_trace_raster(plot_data):
    rec_obj = plot_data['rec_obj']
    trial_frames = plot_data['trial_frames']
    channel = plot_data['channel']
    trial_numbers = plot_data.get('trial_numbers', None)

    linewidth = 0.7
    row_gap_scale = 10.0
    # Match a full PDF page (US Letter) for full-length plots
    figsize = (8.5, 11)

    sf = rec_obj.get_sampling_frequency()
    num_frames = rec_obj.get_num_frames()
    traces = []
    stds = []
    durs = []

    used_trial_numbers = []

    # Slice traces per window
    for idx, (t0, t1) in enumerate(trial_frames):
        if not (np.isfinite(t0) and np.isfinite(t1)):
            continue

        start = int(np.floor(t0 * sf))
        end   = int(np.ceil(t1 * sf))
        
        start = max(0, start)
        end = min(num_frames, end)
        
        if start >= end:
            continue
            
        tr = rec_obj.get_traces(start_frame=start, end_frame=end, channel_ids=[channel]).squeeze()

        # Keep native spikeinterface units (µV)
        # Calculate std in native units for spacing purposes (ddof=1 for an unbiased std estimate)
        sd = tr.std(ddof=1) if tr.std() > 0 else 1.0

        traces.append(tr)
        stds.append(sd)
        durs.append(t1 - t0)
        if trial_numbers is not None and idx < len(trial_numbers):
            used_trial_numbers.append(trial_numbers[idx])

    # Common time axis for each window (independent length per row is okay)
    # We'll build per-row time vectors
    time_axes = [np.linspace(0, dur, tr.size) for tr, dur in zip(traces, durs)]

    # Vertical spacing based on the median std
    med_std = np.median(stds) if len(stds) else 1.0
    row_step = row_gap_scale * med_std
    offsets = np.arange(len(traces)) * row_step

    fig, ax = plt.subplots(figsize=figsize)

    # Plot each row
    for i, (tr, tvec, sd_val) in enumerate(zip(traces, time_axes, stds)):
        y0 = offsets[i]
        ax.plot(tvec, tr + y0, lw=linewidth, color='black')

    max_dur = max(durs) if durs else 0
    ax.set_xlim(0, max_dur)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Trials")
    ax.set_title(f"Channel {channel + 1}")
    # Label y-ticks by actual trial number
    ax.set_yticks(offsets)
    if trial_numbers is not None:
        ax.set_yticklabels([f"{int(tn)}" for tn in used_trial_numbers])
    else:
        ax.set_yticklabels([f"{i+1}" for i in range(len(traces))])
    # Light grid
    ax.grid(True, axis='x', alpha=0.2)

    # Use nearly full page area in the PDF
    fig.subplots_adjust(left=0.08, right=0.98, top=0.96, bottom=0.06)
    return fig 

def get_chan_traces(parent_path):
    parent_path = Path(parent_path)
    analysis_path = parent_path.parent
    task_path = analysis_path / "task_table.csv"
    rec_path = parent_path / "rec_object"
    trace_path = parent_path / "chan_traces.pdf"

    if trace_path.exists():
        trace_path.unlink()

    rec_object = si.load(rec_path)
    task_table = pd.read_csv(task_path)
    task_table = filter_task_table(task_table)

    trial_max = 30
    if len(task_table) > trial_max:
        # Sample evenly across trial count (temporal distribution)
        task_table = task_table.sort_values('Tcnt').reset_index(drop=True)
        indices = np.linspace(0, len(task_table) - 1, trial_max, dtype=int)
        task_table = task_table.iloc[indices]

    event_name = 'gabors_on_time'
    frame_start = -0.2
    frame_stop = 1.0

    data = {
        "task_data": task_table,
        "time_range": (frame_start, frame_stop),
        "event_name": event_name,
    }
    data = get_trial_frames(data)
    trial_frames = data['trial_frames']
    trial_numbers = task_table['Tcnt'].values

    channels = rec_object.get_channel_ids()
    channels = sorted(channels)

    with PdfPages(trace_path) as pdf:
        for channel in channels:
            data = {
                'rec_obj': rec_object,
                'channel': channel,
                'trace_path': trace_path,
                'trial_frames': trial_frames,
                'trial_numbers': trial_numbers,
            }
            fig = plot_trace_raster(data)
            pdf.savefig(fig)
            plt.close(fig)
