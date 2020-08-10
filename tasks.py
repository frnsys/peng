import ee
from tqdm import tqdm
from multiprocessing import Pool

ee.Initialize()

def cancel(t):
    if t['state'] in ['READY', 'RUNNING']:
        ee.data.cancelTask(t['id'])

def cancel_all():
    tasks = ee.data.getTaskList()
    with Pool() as p:
        for _ in tqdm(p.imap(cancel, tasks), total=len(tasks), desc='Cancelling tasks'):
            pass