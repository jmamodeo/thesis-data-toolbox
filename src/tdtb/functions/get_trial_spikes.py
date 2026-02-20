
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
            trial_train = unit_spikes[lower_bound & upper_bound]
            trial_trains.append(trial_train)

        trial_spikes[unit_id] = trial_trains

    data['trial_spikes'] = trial_spikes

    return data