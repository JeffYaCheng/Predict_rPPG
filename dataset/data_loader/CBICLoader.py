"""The dataloader for PURE datasets.

Details for the PURE Dataset see https://www.tu-ilmenau.de/universitaet/fakultaeten/fakultaet-informatik-und-automatisierung/profil/institute-und-fachgebiete/institut-fuer-technische-informatik-und-ingenieurinformatik/fachgebiet-neuroinformatik-und-kognitive-robotik/data-sets-code/pulse-rate-detection-dataset-pure
If you use this dataset, please cite the following publication:
Stricker, R., Müller, S., Gross, H.-M.
Non-contact Video-based Pulse Rate Measurement on a Mobile Service Robot
in: Proc. 23st IEEE Int. Symposium on Robot and Human Interactive Communication (Ro-Man 2014), Edinburgh, Scotland, UK, pp. 1056 - 1062, IEEE 2014
"""
import glob
import glob
import json
import os
import re

import cv2
import numpy as np
import pandas as pd
from dataset.data_loader.BaseLoader import BaseLoader
from tqdm import tqdm


class CBICLoader(BaseLoader):
    """The data loader for the PURE dataset."""

    def __init__(self, name, data_path, config_data):
        """Initializes an PURE dataloader.
            Args:
                data_path(str): path of a folder which stores raw video and bvp data.
                e.g. data_path should be "RawData" for below dataset structure:
                -----------------
                     RawData/
                     |   |-- 01-01/
                     |      |-- output.avi
                     |      |-- PPG_R.csv
                     |   |-- 01-02/
                     |      |-- output.avi
                     |      |-- PPG_R.csv
                     |...
                     |   |-- ii-jj/
                     |      |-- output.avi
                     |      |-- PPG_R.csv
                -----------------
                name(str): name of the dataloader.
                config_data(CfgNode): data settings(ref:config.py).
        """
        super().__init__(name, data_path, config_data)

    def get_raw_data(self, data_path):
        """Returns data directories under the path(For PURE dataset)."""

        data_dirs = glob.glob(data_path + os.sep + "*-*")
        if not data_dirs:
            raise ValueError(self.dataset_name + " data paths empty!")
        dirs = list()
        for data_dir in data_dirs:
            subject_trail_val = os.path.split(data_dir)[-1].replace('-', '')
            index = int(subject_trail_val)
            subject = int(subject_trail_val[0:2])
            dirs.append({"index": index, "path": data_dir, "subject": subject})
        return dirs

    def split_raw_data(self, data_dirs, begin, end):
        """Returns a subset of data dirs, split with begin and end values, 
        and ensures no overlapping subjects between splits"""

        if begin == 0 and end == 1:  # return the full directory if begin == 0 and end == 1
            return data_dirs

        file_num = len(data_dirs)
        choose_range = range(int(begin * file_num), int(end * file_num))
        data_dirs_new = []

        for i in choose_range:
            data_dirs_new.append(data_dirs[i])
            
        print(data_dirs_new)
        return data_dirs_new
    
        #split by people (07-01'07-02'    08-01'08-02   09-11'09-15)
        """
        # return the full directory
        if begin == 0 and end == 1:
            return data_dirs

        # get info about the dataset: subject list and num vids per subject
        data_info = dict()
        for data in data_dirs:
            subject = data['subject']
            data_dir = data['path']
            index = data['index']
            # creates a dictionary of data_dirs indexed by subject number
            if subject not in data_info:  # if subject not in the data info dictionary
                data_info[subject] = []  # make an emplty list for that subject
            # append a tuple of the filename, subject num, trial num, and chunk num
            data_info[subject].append({"index": index, "path": data_dir, "subject": subject})

        subj_list = list(data_info.keys())  # all subjects by number ID (1-27)
        subj_list = sorted(subj_list)
        num_subjs = len(subj_list)  # number of unique subjects

        # get split of data set (depending on start / end)
        subj_range = list(range(0, num_subjs))
        if begin != 0 or end != 1:
            subj_range = list(range(int(begin * num_subjs), int(end * num_subjs)))

        # compile file list
        data_dirs_new = []
        for i in subj_range:
            subj_num = subj_list[i]
            subj_files = data_info[subj_num]
            data_dirs_new += subj_files  # add file information to file_list (tuple of fname, subj ID, trial num,
            # chunk num)

        return data_dirs_new
        """

    def preprocess_dataset_subprocess(self, data_dirs, config_preprocess, i, file_list_dict):
        """ Invoked by preprocess_dataset for multi_process. """
        filename = os.path.split(data_dirs[i]['path'])[-1]
        saved_filename = data_dirs[i]['index']

        # Read Frames
        if 'None' in config_preprocess.DATA_AUG:
            # Utilize dataset-specific function to read video
            frames = self.read_video(
                os.path.join(data_dirs[i]['path'], "output.avi"))
        elif 'Motion' in config_preprocess.DATA_AUG:
            # Utilize general function to read video in .npy format
            frames = self.read_npy_video(
                glob.glob(os.path.join(data_dirs[i]['path'], filename, '*.npy')))
        else:
            raise ValueError(f'Unsupported DATA_AUG specified for {self.dataset_name} dataset! Received {config_preprocess.DATA_AUG}.')

        # Read Labels
        if config_preprocess.USE_PSUEDO_PPG_LABEL:
            bvps = self.generate_pos_psuedo_labels(frames, fs=self.config_data.FS)
        else:
            bvps = self.read_wave(os.path.join(data_dirs[i]['path'], "PPG_R.csv"))

        target_length = frames.shape[0]
        bvps = BaseLoader.resample_ppg(bvps, target_length)
        frames_clips, bvps_clips = self.preprocess(frames, bvps, config_preprocess)
        input_name_list, label_name_list = self.save_multi_process(frames_clips, bvps_clips, saved_filename)
        file_list_dict[i] = input_name_list

    @staticmethod
    def read_video(video_file):
        """Reads a video file, returns frames(T, H, W, 3) """
        VidObj = cv2.VideoCapture(video_file)
        VidObj.set(cv2.CAP_PROP_POS_MSEC, 0)
        success, frame = VidObj.read()
        frames = list()
        while success:
            frame = cv2.cvtColor(np.array(frame), cv2.COLOR_BGR2RGB)
            frame = np.asarray(frame)
            frames.append(frame)
            success, frame = VidObj.read()
        return np.asarray(frames)

    @staticmethod
    def read_wave(bvp_file):
        """Reads a bvp signal file."""
        waves=pd.read_csv(bvp_file)
        waves=waves*-1
        waves=waves.values.reshape(1,-1)
        waves=waves.tolist()
        waves=waves[0]
        for i in range(len(waves)):
            waves[i]=int(waves[i])
        return np.asarray(waves)
