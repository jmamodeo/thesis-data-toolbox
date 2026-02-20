import numpy as np

def get_sort_score(data):
    unit_ids = data['unit_ids']
    trial_spikes = data['trial_spikes']
    task_data = data['task_data']
    event_name = data['event_name']

    sort_scores = []
    for unit_id in unit_ids:
        unit_spikes = trial_spikes[unit_id]

        print(f'Calculating sort score for unit {unit_id}...')

        pre_rates = []
        post_rates = []
        # Enumerate to guarantee positional alignment with trial_spikes list even if task_data index is non-contiguous
        for idx, stim_onset in enumerate(task_data[event_name]):
            pre_window = (stim_onset - 0.1, stim_onset)
            post_window = (stim_onset, stim_onset + 1.0)

            spikes = unit_spikes[idx]
            pre_rate = np.sum((spikes >= pre_window[0]) & (spikes < pre_window[1])) / (pre_window[1] - pre_window[0])
            post_rate = np.sum((spikes >= post_window[0]) & (spikes < post_window[1])) / (post_window[1] - post_window[0])

            pre_rates.append(pre_rate)
            post_rates.append(post_rate)

        pre_rate = np.mean(pre_rates)
        post_rate = np.mean(post_rates)

        unit_score = max(0, (post_rate - pre_rate)) / np.sqrt(pre_rate + 1e-6)
        sort_scores.append(unit_score)

    responsive_units = sum(1 for s in sort_scores if s > 0)
    sort_score = np.sum(sort_scores) * responsive_units

    return sort_score
