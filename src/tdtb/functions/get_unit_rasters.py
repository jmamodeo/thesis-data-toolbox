from pathlib import Path
import spikeinterface.full as si
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from tdtb.functions.filter_task_table import filter_task_table
from tdtb.functions.get_trial_frames import get_trial_frames

def get_trial_frames(data):
    task_data = data['task_data']
    time_range = data['time_range']
    event_name = data['event_name']

    trial_frames = []
    for onset_time in task_data[event_name]:
        start = onset_time + time_range[0]
        end = onset_time + time_range[1]
        trial_frame = (start, end)
        trial_frames.append(trial_frame)

    data['trial_frames'] = trial_frames

    return data

def get_trial_spikes(data):
    sorting = data['sorting']
    unit_ids = data['unit_ids']
    trial_frames = data['trial_frames']

    sampling_rate = sorting.get_sampling_frequency()
    trial_spikes = {}

    for unit_id in unit_ids:
        unit_samples = sorting.get_unit_spike_train(unit_id)
        unit_spikes = unit_samples / sampling_rate
        trial_trains = []

        for trial_frame in trial_frames:
            lower_bound = (unit_spikes > trial_frame[0])
            upper_bound = (unit_spikes < trial_frame[1])
            trial_train = unit_spikes[lower_bound & upper_bound] - trial_frame[0]
            trial_trains.append(trial_train)

        trial_spikes[unit_id] = trial_trains

    data['trial_spikes'] = trial_spikes

    return data

def plot_spike_rasters(data):
    unit_ids = data['unit_ids']
    trial_spikes = data['trial_spikes']
    rast_path = data['rast_path']
    trial_numbers = data.get('trial_numbers', None)

    with PdfPages(rast_path) as pdf:
        for unit in unit_ids:
            unit_spikes = trial_spikes[unit]
            trial_indices = np.arange(len(unit_spikes))
            fig, ax = plt.subplots()
            ax.eventplot(
                unit_spikes,
                lineoffsets=trial_indices,
                linelengths=0.2,
                color='black',
            )
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Trials")
            ax.set_yticks(trial_indices)
            if trial_numbers is not None and len(trial_numbers) == len(unit_spikes):
                ax.set_yticklabels([f"{int(tn)}" for tn in trial_numbers])
            else:
                ax.set_yticklabels([f"{i + 1}" for i in trial_indices])
            ax.set_title(f"Unit {unit}")
            pdf.savefig(fig)
            plt.close(fig)

    return data

def get_unit_rasters(thresh_path):
    thresh_path = Path(thresh_path)
    analysis_path = thresh_path.parent.parent.parent
    task_path = analysis_path / "task_table.csv"
    sort_path = thresh_path / "sort_object"
    rast_path = thresh_path / "spike_rast.pdf"

    if rast_path.exists():
        rast_path.unlink()

    sort_obj = si.load(sort_path)
    task_table = pd.read_csv(task_path)
    task_table = filter_task_table(task_table)

    trial_max = 30  
    if len(task_table) > trial_max:
        task_table = task_table.sort_values('Tcnt').reset_index(drop=True)
        indices = np.linspace(0, len(task_table) - 1, trial_max, dtype=int)
        task_table = task_table.iloc[indices]
    trial_numbers = task_table['Tcnt'].values

    event_name = 'gabors_on_time'
    frame_start = -0.5
    frame_stop = 1.25

    unit_ids = sort_obj.get_unit_ids()
    unit_ids = sorted(unit_ids)

    data = {
        "sorting": sort_obj,
        "task_data": task_table,
        "unit_ids": unit_ids,
        "time_range": (frame_start, frame_stop),
        'event_name': event_name,
        'rast_path': rast_path,
        'trial_numbers': trial_numbers,
    }

    data = get_trial_frames(data)
    data = get_trial_spikes(data)
    data = plot_spike_rasters(data)
