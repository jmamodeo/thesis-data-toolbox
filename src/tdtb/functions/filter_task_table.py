

def filter_task_table(task_table):
    if 'Outcome' in task_table.columns:
        task_table = task_table[task_table['Outcome'] == 'Correct']
    
    if 'Experiment' in task_table.columns:
        experiments = list(task_table["Experiment"].unique())
        if 'AttendGrat' in experiments:
            task_table = task_table[task_table["Experiment"] == 'AttendGrat']
            task_table = task_table[task_table['Cued'] == 1]
            task_table = task_table[task_table['TargQuad'] == 1]

    return task_table