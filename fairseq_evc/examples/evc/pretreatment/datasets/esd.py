import argparse
import glob
import os
import random
import soundfile as sf
from tqdm import tqdm
import pandas as pd
import numpy as np
from moviepy.editor import AudioFileClip
import ffmpeg
import re
from scipy.io.wavfile import write as write_wav
import librosa as lib

def save_wav(save_path, audio, sr=16000):
    '''Function to write audio'''
    save_path = os.path.abspath(save_path)
    destdir = os.path.dirname(save_path)
    if not os.path.exists(destdir):
        try:
            os.makedirs(destdir)
        except:
            pass
    write_wav(save_path, sr, audio)
    return

# 
def contains_chinese(s):
    return re.search(r'[\u4e00-\u9fff]+', s) is not None

def convert2wav(path):
    save_path = path.split(".")[0] + ".wav"
    if os.path.exists(save_path):
        return save_path
    stream = ffmpeg.input(path)
    stream = ffmpeg.output(stream, save_path, ar=16000, ac=1)
    ffmpeg.run(stream)
    return save_path

def find_spk(text):
    pattern = r'\bsubject ([0-9]|[1-4][0-9]|50)\b'
    matches = re.findall(pattern, text)
    return matches

from pathlib import Path
def get_all_wavs(root, suffix):
    files = []
    for p in Path(root).iterdir():
        if str(p).endswith(".%s"%suffix):
            files.append(str(p))
        for s in p.rglob("*.%s"%suffix):
            files.append(str(s))
    return list(set(files))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='data')
    parser.add_argument('--data-home', type=str)
    args = parser.parse_args()
    emo_dict = {
        "Sad": "sad",
        "Happy": "happy",
        "Angry": "angry",
        "Surprise": "surprised",
        "Neutral": "neutral",
    }
    
    # download data from https://hltsingapore.github.io/ESD/
    data_name = "Emotional_Speech_Dataset"
    root = os.path.join(args.data_home, data_name)
    trans_dict = {}
    for path in get_all_wavs(root, "txt"):
        with open(path, "r") as rf:
            if path.find("ReadMe") != -1:
                continue
            lines = [line.strip() for line in rf.readlines() if line.strip() != ""]
            print(lines)
            for line in lines:
                print(line)
                if line[11] != "\t": # 0013_000431 I never had a whooping cough why.   Angry
                    line = line[:11] + "\t" + line[12:]
                name, trans, emo = line.split("\t")
                trans_dict[name] = (trans, emo)
    print(trans_dict)
    
    with open(os.path.join(root, "train_info.tsv"), "w") as train_f:
        with open(os.path.join(root, "test_info.tsv"), "w") as test_f:
            with open(os.path.join(root, "dev_info.tsv"), "w") as dev_f:
                for path in get_all_wavs(root, "wav"):
                    name = os.path.basename(path).split(".")[0]
                    if name not in trans_dict.keys():
                        print(name)
                        continue
                    trans, emo = trans_dict[name]
                    if contains_chinese(trans):
                        continue
                    
                    audio, sr = sf.read(path)
                    if len(audio.shape) > 1:
                        audio = audio[0]
                    
                    if sr != 16000:
                        path = path.replace(f"/{data_name}/", f"/{data_name}_16k/")
                        audio = lib.resample(audio, orig_sr=sr, target_sr=16000)
                        save_wav(path, audio)
                        sr = 16000
                        
                    if path.find("train") != -1:
                        out_file = train_f
                    elif path.find("test") != -1:
                        out_file = test_f
                    else:
                        out_file = dev_f
                    
                    emo = emo_dict[emo]
                    spk = os.path.basename(path).split("_")[0]
                    
                    print(
                        "{}\t{}\t{}\t{}\t{}\t{}\t{}".format(path, sr, len(audio), spk, emo, "_", trans), file=out_file
                    )