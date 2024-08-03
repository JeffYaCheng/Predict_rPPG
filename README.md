# Predict rPPG 
- This is modified by [rPPG-Toolbox](https://github.com/ubicomplab/rPPG-Toolbox)
- Use video to predict rPPG Signal

# CBIC Dataset Format
 -----------------
       datasets/CBIC/
         |   |-- 01-01/
         |      |-- output.avi
         |      |-- syn_PPG_R.csv
         |   |-- 01-02/
         |      |-- output.avi
         |      |-- syn_PPG_R.csv
         |...
         |   |-- ii-jj/
         |      |-- output.avi
         |      |-- syn_PPG_R.csv
-----------------

# Use Pre-trained model to inference
- modify `PURE_CBIC_TSCAN.yaml` file in `./configs/infer_configs/PURE_CBIC_TSCAN.yaml`
    - `DO_PREPROCESS`： True / False     
        - if first time, should be true! Preprocess img to correct model input format
    - `DATA_PATH`:  r"./datasets/CBIC"                     
        - Raw dataset path, need to be updated
    - `CACHED_PATH`: r"./datasets/PreprocessedData"    
        - Processed dataset save path, need to be updated
    - `EXP_DATA_NAME`: "CBIC_rPPG" 
        - The name of this run result
    - `BACKEND`： HAND / HC
        - HAND：using hand to predict rPPG
        - HC：using face to predict rPPG
    - You can modify other paramter depend on your situation
- Run `python main.py --config_file ./configs/infer_configs/PURE_CBIC_TSCAN.yaml`
- Preprocessing images will save in the `CACHED_PATH`
- Signal wave picture will save in the `runs/exp/EXP_DATA_NAME/saved_test_outputs/waveforms`
- Signal wave csv fils will save in the `DATA_PATH`
- 
# Reference
- [rPPG-Toolbox](https://github.com/ubicomplab/rPPG-Toolbox)