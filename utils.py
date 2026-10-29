import os
import random
import shutil
from tqdm import tqdm
from music21 import converter, key, interval
from pathlib import Path

def split_dataset(input_root, train_root, test_root, train_ratio=0.9):
    """
    Splits a folder with subfolders and files into train and test sets, preserving the folder structure.

    Args:
        input_root (str): Path to the root folder containing the original dataset.
        train_root (str): Path to the root folder to save the training dataset.
        test_root (str): Path to the root folder to save the testing dataset.
        train_ratio (float): Ratio of files to include in the training set (default: 0.9).
    """
    # Collect all files with their relative paths
    all_files = []
    total_files = sum(len(files) for _, _, files in os.walk(input_root))
    for root, _, files in os.walk(input_root):
        for file in tqdm(files, total=total_files, desc="Processing"):
            input_path = os.path.join(root, file)
            relative_path = os.path.relpath(input_path, input_root)  # Path relative to input_root
            all_files.append(relative_path)
    
    # Shuffle files and split into train and test
    random.shuffle(all_files)
    split_index = int(len(all_files) * train_ratio)
    train_files = all_files[:split_index]
    test_files = all_files[split_index:]
    
    # Copy files to train and test directories
    for relative_path in train_files:
        copy_file_to_output(input_root, train_root, relative_path)
    
    for relative_path in test_files:
        copy_file_to_output(input_root, test_root, relative_path)
    
    print(f"Dataset split completed: {len(train_files)} files in train, {len(test_files)} files in test.")
# end split_dataset

def copy_file_to_output(input_root, output_root, relative_path):
    """
    Copies a file from the input folder to the output folder, preserving the folder structure.

    Args:
        input_root (str): Root directory of the original dataset.
        output_root (str): Root directory for the output dataset.
        relative_path (str): Path of the file relative to the input root.
    """
    input_path = os.path.join(input_root, relative_path)
    output_path = os.path.join(output_root, relative_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)  # Create necessary subfolders
    shutil.copy2(input_path, output_path)  # Copy file while preserving metadata (e.g., modification time)
# end copy_file_to_output

def transpose_to_c_major_a_minor_bulk(input_root, output_root):
    """
    Recursively transposes all MIDI (.midi or .mid) files in the input directory to C major or A minor,
    and saves them in the output directory, preserving the folder structure.

    Args:
        input_root (str): Root directory containing the input files.
        output_root (str): Root directory to save the transposed files.
    """
    # Collect all .mid or .midi files and their relative paths
    midi_files = []
    for root, _, files in os.walk(input_root):
        for file in files:
            if file.endswith('.mid') or file.endswith('.midi'):
                input_path = os.path.join(root, file)
                relative_path = os.path.relpath(root, input_root)  # Subfolder path relative to input root
                output_dir = os.path.join(output_root, relative_path)
                os.makedirs(output_dir, exist_ok=True)  # Create the output subfolder if it doesn't exist
                output_path = os.path.join(output_dir, file)
                midi_files.append((input_path, output_path))
    
    # Initialize the error log for this run.
    data_dir = Path(__file__).resolve().parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    error_log_path = data_dir / "transposition_errors.txt"

    # Process files with a progress bar
    with error_log_path.open("w", encoding="utf-8") as error_log:
        for input_path, output_path in tqdm(midi_files, desc="Processing files", unit="file"):
            try:
                transpose_to_c_major_a_minor_single(input_path, output_path)
            except Exception as e:
                error_message = f"Error processing {input_path}: {e}"
                print(error_message)
                error_log.write(error_message + "\n")
# end transpose_to_c_major_a_minor_bulk

def transpose_to_c_major_a_minor_single(input_path, output_path):
    """
    Transposes a single MIDI file to C major or A minor if necessary, and saves the result.

    Args:
        input_path (str): Path to the input MIDI file.
        output_path (str): Path to save the transposed MIDI file.
    """
    # Load the MIDI file
    score = converter.parse(input_path)
    
    # Analyze the key
    original_key = score.analyze('key')
    # print(f"Processing {input_path} | Original key: {original_key}")
    
    # Check if the key is already C major or A minor
    if (original_key.tonic.name == 'C' and original_key.mode == 'major') or \
       (original_key.tonic.name == 'A' and original_key.mode == 'minor'):
        # print(f"The piece is already in C major or A minor. Skipping {input_path}.")
        # just copy file
        shutil.copyfile(input_path, output_path)
        return
    
    # Determine the target key (C major or A minor)
    target_key = key.Key('C') if original_key.mode == 'major' else key.Key('A')
    
    # Calculate the transposition interval
    transposition_interval = interval.Interval(original_key.tonic, target_key.tonic)
    
    # Transpose the score
    transposed_score = score.transpose(transposition_interval)

    # for harmony in transposed_score.recurse().getElementsByClass('Harmony'):
    #     print(f"Chord: {harmony.figure}, Bass: {harmony.bass()}")
    for harmony in transposed_score.recurse().getElementsByClass('Harmony'):
        if '/' in harmony.figure:  # Check for slash chords
            root, bass = harmony.figure.split('/')
            harmony.figure = f"{root}/{bass}"
        elif harmony.bass():  # Ensure inversion info is retained
            harmony.figure = f"{harmony.figure}/{harmony.bass().name}"
    # Save the transposed score to the output file
    # transposed_score.write('musicxml', fp=output_path)
    transposed_score.write('midi', fp=output_path)
    # print(f"Transposed score saved to {output_path}")
# end transpose_to_c_major_a_minor_single

def transpose_to_all_keys(in_folder, out_folder):
    # Define transposition intervals (-5 to +6)
    transposition_intervals = range(-5, 7)  # Includes -5, -4, ..., 0, ..., +6

    # Define input and output directories
    input_root = Path(in_folder)  # Change this to your directory
    output_root = Path(out_folder)        # Change this to where you want the results

    # Ensure output directory exists
    output_root.mkdir(parents=True, exist_ok=True)

    # Find all MusicXML files
    midi_files = [file for ext in ["*.mid", "*.midi", "*.xml", "*.mxl", "*.musicxml"] for file in input_root.rglob(ext)]

    # Initialize the error log for this run.
    data_dir = Path(__file__).resolve().parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    error_log_path = data_dir / "transposition_12_errors.txt"

    with error_log_path.open("w", encoding="utf-8") as error_log:
        # Setup progress bar
        with tqdm(total=len(midi_files) * (len(transposition_intervals) - 1), desc="Processing Files") as pbar:
            for input_path in midi_files:
                rel_path = input_path.relative_to(input_root)  # Preserve subfolder structure
                
                try:
                    score = converter.parse(input_path)  # Load the MIDI file
                except Exception as e:
                    message = f"Error loading {input_path}: {e}"
                    print(message)
                    error_log.write(message + "\n")
                    continue  # Skip to the next file
                # Ensure output directory exists
                output_root.mkdir(parents=True, exist_ok=True)
                
                midi_extensions = {".mid", ".midi"}
                musicxml_extensions = {".xml", ".mxl", ".musicxml"}
                extension = input_path.suffix.lower()
                if extension in midi_extensions:
                    output_ext = '.mid'
                    write_type = 'midi'
                elif extension in musicxml_extensions:
                    output_ext = '.xml'
                    write_type = 'xml'
                else:
                    print('ERROR: unknown extension')
                
                # Process transpositions
                for interval in transposition_intervals:
                    try:
                        # Transpose and create output path
                        transposed_score = score.transpose(interval)
                        output_file = output_root / rel_path.with_stem(f"{input_path.stem}_tr_{interval}")
                        output_file = output_file.with_suffix(output_ext)
                        
                        # Create necessary subdirectories
                        output_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Write to file
                        transposed_score.write(write_type, output_file)
                        pbar.update(1)  # Update progress bar
                        
                    except Exception as e:
                        message = f"Error transposing {input_path}: {e}"
                        print(message)
                        error_log.write(message + "\n")