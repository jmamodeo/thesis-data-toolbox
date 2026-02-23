import random
import numpy as np
import spikeinterface.full as si

def run_kilosort(data):
    rec_object = data['rec_object']
    sort_path = data['sort_path']
    pass_1_threshold = data['pass_1_threshold']
    pass_2_threshold = data['pass_2_threshold']
    chunk_dur = data['chunk_dur']

    job_kwargs = {"n_jobs": 1, "chunk_duration": f"{chunk_dur}s"}
    si.set_global_job_kwargs(**job_kwargs)

    print(f"Running kilosort with threshold {pass_2_threshold}...")

    sorter_params = {
        'sorter_name': 'kilosort4',
        'Th_universal': pass_1_threshold,
        'Th_learned': pass_2_threshold,
        'do_CAR': False,
        'skip_kilosort_preprocessing': True,
    }
    
    si.run_sorter(
        recording=rec_object,
        folder=sort_path,
        raise_error=True,
        **sorter_params
    )
