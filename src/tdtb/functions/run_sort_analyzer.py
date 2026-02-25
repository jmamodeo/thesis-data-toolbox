import spikeinterface.full as si

def run_sort_analyzer(data):
    rec_object = data['rec_object']
    sort_object = data['sort_object']
    qual_path = data['qual_path']

    job_kwargs = {"n_jobs": 20, "chunk_duration": "10s"}
    si.set_global_job_kwargs(**job_kwargs)
    
    print(f'Calculating quality metrics...')

    qual_object = si.create_sorting_analyzer(sorting=sort_object, recording=rec_object, sparse=False)
    qual_object.compute({
        'waveforms': {},
        'random_spikes': {},
        'noise_levels': {},
        'templates': {},
        'template_similarity': {},
        'unit_locations': {},
        'spike_amplitudes': {},
        'correlograms': {}
    })

    qual_object.save_as(folder=qual_path, format='binary_folder')
