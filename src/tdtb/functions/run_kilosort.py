import random
import numpy as np
import spikeinterface.full as si

def run_kilosort(data):
    rec_object = data['rec_object']
    threshold = data['threshold']
    sort_path = data['sort_path']
    pca_seed = data['pca_seed']
    chunk_dur = data['chunk_dur']

    job_kwargs = {"n_jobs": 1, "chunk_duration": f"{chunk_dur}s"}
    si.set_global_job_kwargs(**job_kwargs)

    np.random.seed(pca_seed)
    random.seed(pca_seed)

    print(f"Running kilosort with threshold {threshold}...")

    sorter_params = {
        'sorter_name': 'kilosort4',
        'Th_universal': threshold,
        'Th_learned': threshold,
        'do_CAR': False,
        'skip_kilosort_preprocessing': True,
    }
    
    si.run_sorter(
        recording=rec_object,
        folder=sort_path,
        raise_error=True,
        **sorter_params
    )
