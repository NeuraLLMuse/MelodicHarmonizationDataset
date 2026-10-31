from data_utils import CSGridMLMDataset
from GridMLM_tokenizers import CSGridMLMTokenizer
import os
from dotenv import load_dotenv

load_dotenv()

tokenizer = CSGridMLMTokenizer(
    fixed_length=80,
    quantization='4th',
    intertwine_bar_info=True,
    trim_start=False,
    use_pc_roll=True,
    use_full_range_melody=False
)

names = ['HOOK', 'JAZZ', 'NOTT', 'WIKI']
for n in names:
    for tv in ['_TRAIN', '_VAL']:
        for tr in ['_12']: #['_CA', '_12']:
            folder = os.getenv(n + tr + tv)
            print(f'Processing: {folder}')
            _ = CSGridMLMDataset(folder, tokenizer, frontloading=True, name_suffix='Q4_L80_bar_PC')