from utils import split_dataset
import os
from dotenv import load_dotenv

load_dotenv()

names = ['HOOK', 'JAZZ', 'NOTT', 'WIKI']
for n in names:
    print(f'Processing {n}')
    input_root = os.getenv(n)
    train_root = os.getenv(n + '_TRAIN')
    val_root   = os.getenv(n + '_VAL')
    print(f'Processing input: {input_root} - train: {train_root} - val: {val_root}')
    os.makedirs(train_root, exist_ok=True)
    os.makedirs(val_root, exist_ok=True)
    split_dataset(input_root, train_root, val_root, train_ratio=0.9)