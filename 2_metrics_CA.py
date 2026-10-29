from metrics_utils import compute_folder_metrics
import os
from dotenv import load_dotenv

load_dotenv()

names = ['HOOK', 'JAZZ', 'NOTT', 'WIKI']
for n in names:
    for tv in ['_TRAIN', '_VAL']:
        print(f'Processing {n} - {tv}.')
        input_root = os.getenv(n + '_CA' + tv)
        df = compute_folder_metrics(
            input_root,
            recursive=True,
            include_errors=False,
        )
        df.to_csv(input_root + '_df.csv')