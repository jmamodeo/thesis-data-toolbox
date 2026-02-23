import random
import numpy as np
import spikeinterface.full as si

def run_kilosort(data):
    rec_object = data['rec_object']
    sort_path = data['sort_path']
    pass_1_thresh = data['pass_1_thresh']
    pass_2_thresh = data['pass_2_thresh']
    chunk_dur = data['chunk_dur']

    job_kwargs = {"n_jobs": 1, "chunk_duration": f"{chunk_dur}s"}
    si.set_global_job_kwargs(**job_kwargs)

    print(f"Running kilosort with threshold {pass_2_thresh}...")

    sorter_params = {
        'sorter_name': 'kilosort4',
        'Th_universal': pass_1_thresh,
        'Th_learned': pass_2_thresh,
        'do_CAR': False,
        'skip_kilosort_preprocessing': True,
    }
    
    si.run_sorter(
        recording=rec_object,
        folder=sort_path,
        raise_error=True,
        **sorter_params
    )
