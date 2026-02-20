import spikeinterface.full as si

def run_sort_analyzer(data):
    rec_object = data['rec_object']
    sort_path = data['sort_path']
    qual_path = data['qual_path']

    job_kwargs = {"n_jobs": 20, "chunk_duration": "10s"}
    si.set_global_job_kwargs(**job_kwargs)
    
    print(f'Calculating quality metrics...')

    sort_obj = si.load(sort_path)
    qual_obj = si.create_sorting_analyzer(sorting=sort_obj, recording=rec_object, sparse=False)
    qual_obj.compute({
        'waveforms': {},
        'random_spikes': {},
        'noise_levels': {},
        'templates': {},
        'template_similarity': {},
        'unit_locations': {},
        'spike_amplitudes': {},
        'correlograms': {}
    })

    qual_obj.save_as(folder=qual_path, format='binary_folder')
