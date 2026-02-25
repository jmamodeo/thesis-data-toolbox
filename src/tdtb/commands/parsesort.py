from pathlib import Path
import pandas as pd
import spikeinterface.full as si
import shutil

from tdtb.functions.run_sort_analyzer import run_sort_analyzer
from tdtb.functions.get_unit_waveforms import get_unit_waveforms

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
    sort_object = data['sort_object']
    unit_ids = data['unit_ids']
    trial_frames = data['trial_frames']

    sampling_rate = sort_object.get_sampling_frequency()
    trial_spikes = {}

    for unit_id in unit_ids:
        unit_samples = sort_object.get_unit_spike_train(unit_id)
        unit_spikes = unit_samples / sampling_rate

        print(f'Collecting spikes for unit {unit_id}...')
        
        trial_trains = []
        for trial_frame in trial_frames:
            lower_bound = (unit_spikes > trial_frame[0])
            upper_bound = (unit_spikes < trial_frame[1])
            trial_train = unit_spikes[lower_bound & upper_bound].tolist()
            trial_trains.append(trial_train)

        trial_spikes[unit_id] = trial_trains

    data['trial_spikes'] = trial_spikes

    return data

def get_unit_tables(data):
    unit_ids = data['unit_ids']
    trial_spikes = data['trial_spikes']
    units_path = data['units_path']

    print(f'Calculating spike rates...')

    for unit_id in unit_ids:
        unit_path = units_path / f'unit_{unit_id}.csv'
        unit_spikes = trial_spikes[unit_id]
        unit_table = data['task_data'].copy()
        unit_table['spikes'] = unit_spikes

        if 'Outcome' in unit_table.columns:
            unit_table = unit_table[unit_table['Outcome'] == 'Correct']

        unit_table.to_csv(unit_path, index=False)

def parsesort():
    parent_path = input("Sort parent path: ").strip().strip("'").strip()
    parent_path = Path(parent_path)
    analysis_path = parent_path.parent.parent.parent
    task_path = analysis_path / "task_table.csv"
    rec_path = analysis_path / "whitened_rec" / "rec_object"
    sort_path = parent_path / "sort_object"
    qual_path = parent_path / "qual_object"

    stage_path = '/Users/johnamodeo/Desktop/rec_data'
    stage_path = Path(stage_path)
    session_path = analysis_path.parent.parent
    units_path = stage_path / session_path.name / "unit_tables"

    if units_path.exists():
        shutil.rmtree(units_path)
    units_path.mkdir(parents=True, exist_ok=True)

    task_table = pd.read_csv(task_path)
    rec_object = si.load(rec_path)
    sort_object = si.load(sort_path)

    frame_start = -0.2
    frame_stop = 1.0
    event_name = 'gabors_on_time'

    unit_ids = sort_object.get_unit_ids()
    unit_ids = sorted(unit_ids)

    data = {
        'task_data': task_table,
        'rec_object': rec_object,
        'sort_object': sort_object,
        'unit_ids': unit_ids,
        'time_range': (frame_start, frame_stop),
        'event_name': event_name,
        'units_path': units_path,
        'qual_path': qual_path,
    }

    run_sort_analyzer(data)
    get_unit_waveforms(parent_path)

    data = get_trial_frames(data)
    data = get_trial_spikes(data)
    get_unit_tables(data)


