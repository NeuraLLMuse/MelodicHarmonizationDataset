from utils import transpose_to_c_major_a_minor_bulk
import os
from dotenv import load_dotenv

load_dotenv()

names = ['HOOK', 'JAZZ', 'NOTT', 'WIKI']
for n in names:
    for tv in ['_TRAIN', '_VAL']:
        input_root = os.getenv(n + tv)
        output_root = os.getenv(n + '_CA' + tv)
        print(f'Processing input: {input_root} - output: {output_root}')
        os.makedirs(output_root, exist_ok=True)
        transpose_to_c_major_a_minor_bulk(input_root, output_root)