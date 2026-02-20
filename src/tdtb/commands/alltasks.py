from pathlib import Path
from tdt import read_block
import numpy as np
import pandas as pd

def dat2csv(dat_path):
    file_data = pd.read_csv(dat_path, sep=" ")
    drop_cols = [col for col in file_data.columns if "Unnamed" in col]
    file_data = file_data.drop(columns=drop_cols)

    return file_data

def alltasks():
    tdt_path = input("TDT block path: ").strip().strip("'").strip()
    analysis_path = Path(tdt_path) / "analysis"
    task_path = analysis_path / "task_table.csv"

    if not analysis_path.exists():
        analysis_path.mkdir()

    print('Loading event data from block...')

    headers = read_block(tdt_path, headers=1)
    for store_name in headers.stores.keys():
        store = headers.stores[store_name]
        if hasattr(store, "chan"):
            store.chan = store.chan.astype(np.int32)
    event_data = read_block(
        tdt_path,
        headers=headers,
        evtype=["epocs"]
    )
    event_table = pd.DataFrame({
        "events": event_data["epocs"]["eve_"]["data"],
        "times": event_data["epocs"]["eve_"]["onset"],
    })

    file_count = input("File count: ").strip()
    path_list = []
    for i in range(int(file_count)):
        path = input(f"File {i+1} path: ").strip()
        path_list.append(path)

    print('Loading task data from files...')

    df_list = []
    for path in path_list:
        if path.endswith('.dat'):
            df = dat2csv(path)
        elif path.endswith('.csv'):
            df = pd.read_csv(path)
        else:
            raise ValueError(f"Invalid file type: {path}")
        df_list.append(df)

    print('Concatenating task data...')

    task_table = pd.concat(df_list)
    valid_outcomes = ['Correct', 'Miss']
    task_table = task_table[task_table['Outcome'].isin(valid_outcomes)]
    event_name = 'gabors_on_time'

    if 'TrialID' in task_table.columns:

        print('Calculating gabors on time...')

        gabors_on_time = []
        for trial_id in task_table['TrialID']:
            trial_data = event_table[event_table['events'] == trial_id]
            try:
                gabors_on = trial_data['times'].iloc[0]
            except:
                print(f"Trial ID {trial_id} not found in event data")
                gabors_on = np.nan
            gabors_on_time.append(gabors_on)

        task_table[event_name] = gabors_on_time
        task_table = task_table.dropna(subset=[event_name])

    if task_path.exists():
        task_path.unlink()

    task_table.to_csv(task_path, index=False)
