from pathlib import Path
import shutil
import pandas as pd
import spikeinterface.full as si
from concurrent.futures import ProcessPoolExecutor

from tdtb.functions.filter_task_table import filter_task_table
from tdtb.functions.run_mountainsort import run_mountainsort
from tdtb.functions.get_unit_rasters import get_unit_rasters
from tdtb.functions.get_trial_frames import get_trial_frames
from tdtb.functions.get_trial_spikes import get_trial_spikes
from tdtb.functions.get_sort_score import get_sort_score

def get_score_log(data):
    rec_object = data['rec_object']
    task_table = data['task_table']
    seed_path = data['seed_path']
    pca_seed = data['pca_seed']
    thresholds = data['thresholds']
    num_workers = data['num_workers']
    chunk_dur = data['chunk_dur']

    event_name = 'gabors_on_time'
    time_range = (-0.2, 1.0)

    sort_dicts = []
    for threshold in thresholds:
        sort_path = seed_path / f'threshold_{threshold}' / 'sort_object'
        sort_dict = {
            'rec_object': rec_object,
            'threshold': threshold,
            'sort_path': sort_path,
            'pca_seed': pca_seed,
            'chunk_dur': chunk_dur,
        }
        sort_dicts.append(sort_dict)

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        list(executor.map(run_mountainsort, sort_dicts))

    thresh_list = [d.name for d in seed_path.iterdir() if d.is_dir()]

    score_dicts = []
    for thresh_dir in thresh_list:
        thresh_path = seed_path / thresh_dir
        sort_path = thresh_path / 'sort_object'
        sort_obj = si.load(sort_path)
        unit_ids = sort_obj.get_unit_ids()

        get_unit_rasters(thresh_path)

        score_data = {
            'task_data': task_table,
            'time_range': time_range,
            'event_name': event_name,
            'sorting': sort_obj,
            'unit_ids': unit_ids,
        }
        score_data = get_trial_frames(score_data)
        score_data = get_trial_spikes(score_data)
        score = get_sort_score(score_data)
        threshold = float(thresh_dir.split('_')[1])

        score_dict = {
            'threshold': threshold,
            'score': score,
        }
        score_dicts.append(score_dict)

    score_log = pd.DataFrame(score_dicts)
    score_log = score_log.sort_values(by='threshold')

    return score_log

def searchms():
    tdt_path = input("TDT block path: ").strip().strip("'").strip()
    analysis_path = Path(tdt_path) / 'analysis'
    task_path = analysis_path / "task_table.csv"
    rec_path = analysis_path / "whitened_rec" / "rec_object"
    sort_lib_path = analysis_path / "sort_library"

    if sort_lib_path.exists():
        shutil.rmtree(sort_lib_path)
    sort_lib_path.mkdir()

    pca_seed_range = input("PCA seed range: ").strip()
    pca_seed_range = [int(i) for i in pca_seed_range.split('-')]
    thesh_range = input("Threshold range: ").strip()
    thesh_range = [(int(i) * 10) for i in thesh_range.split('-')]
    num_workers = int(input("Number of workers: ").strip())
    chunk_dur = input("Chunk duration (s): ").strip()

    pca_seeds = [i for i in range(pca_seed_range[0], pca_seed_range[1] + 1)]
    thresholds = [i/10 for i in range(thesh_range[0], (thesh_range[1] + 1))]

    task_table = pd.read_csv(task_path)
    task_table = filter_task_table(task_table)
    rec_object = si.load(rec_path)

    best_scores = []
    for pca_seed in pca_seeds:
        seed_path = sort_lib_path / f'pca_seed_{pca_seed}'
        data = {
            'rec_object': rec_object,
            'task_table': task_table,
            'seed_path': seed_path,
            'pca_seed': pca_seed,
            'thresholds': thresholds,
            'num_workers': num_workers,
            'chunk_dur': chunk_dur,
        }

        score_log = get_score_log(data)
        log_path = seed_path / f'pca_seed_{pca_seed}_score_log.csv'
        score_log.to_csv(log_path, index=False)

        best_score = score_log.loc[score_log['score'].idxmax()]
        best_scores.append({
            'pca_seed': pca_seed,
            'threshold': best_score['threshold'],
            'score': best_score['score'],
        })

    best_scores_log = pd.DataFrame(best_scores)
    best_scores_log = best_scores_log.sort_values(by='score', ascending=False)
    best_scores_log_path = sort_lib_path / 'pca_seed_best_scores_log.csv'
    best_scores_log.to_csv(best_scores_log_path, index=False)
