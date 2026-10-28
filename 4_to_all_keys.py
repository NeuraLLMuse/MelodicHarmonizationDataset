from utils import transpose_to_all_keys
import os
from dotenv import load_dotenv

load_dotenv()

names = ['HOOK', 'JAZZ', 'NOTT', 'WIKI']
for n in names:
    for tv in ['_TRAIN', '_VAL']:
        print(f'Processing {n} - {tv}.')
        input_root = os.getenv(n + '_CA' + tv)
        output_root = os.getenv(n + '_12' + tv)
        os.makedirs(output_root, exist_ok=True)
        transpose_to_all_keys(input_root, output_root)