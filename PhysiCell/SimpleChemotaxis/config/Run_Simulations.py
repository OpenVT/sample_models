from uq_physicell.uq_physicell import PhysiCell_Model
import numpy as np
import pandas as pd
from shutil import rmtree
import pcdl
import glob 
import os 

def summary_function(OutputFolder,SummaryFile, dic_params, SampleID, ReplicateID):
    mcds_ts = pcdl.TimeSeries(OutputFolder, microenv=False, graph=False, settingxml=None, verbose=False)
    # Initial condition
    previous_posx = -220.0
    previous_posy = 0.0
    previous_time = 0.0
    total_distance = 0.0
    previous_veloc_x = 0.0
    previous_veloc_y = 0.0
    for mcds in mcds_ts.get_mcds_list():
        current_time = mcds.get_time()
        df_cell = mcds.get_cell_df()
        position_x = df_cell['position_x'][0] 
        position_y = df_cell['position_y'][0] 
        delta_t = (current_time - previous_time)
        # Total distance traveled
        total_distance += np.sqrt((position_x - previous_posx)**2 + (position_y - previous_posy)**2)
        if (current_time > 0): 
            # Average speed for the complete trajectory:- current time = delta t total (as IC is in time 0)
            average_speed = total_distance/current_time 
            # Instantaneous Velocity
            velocity_x = (position_x - previous_posx)/delta_t
            velocity_y = (position_y - previous_posy)/delta_t
            # Instantaneous Acceleration
            acceleration_x = (previous_veloc_x-velocity_x)/delta_t
            acceleration_y = (previous_veloc_y-velocity_y)/delta_t
        else:
            average_speed = 0.0 
            velocity_x = 0.0; velocity_y = 0.0
            acceleration_x = 0.0; acceleration_y = 0.0
        
        # Update the previous values
        previous_posx = position_x; previous_posy = position_y
        previous_veloc_x = velocity_x; previous_veloc_y = velocity_y
        previous_time = current_time
        data = {'time': current_time, 'sampleID': SampleID, 'replicateID': ReplicateID, 
                'position_x': position_x, 'position_y': position_y, 
                'velocity_x': velocity_x, 'velocity_y': velocity_y, 
                'acceleration_x': acceleration_x, 'acceleration_y': acceleration_y,
                'total_distance': total_distance, 'average_speed': average_speed,
                'run_time_sec': mcds.get_runtime()}
        data_conc = {**data,**dic_params} # concatenate output data and parameters
        if ( mcds.get_time() == 0 ): df = pd.DataFrame([data_conc]) # create the dataframe
        else: df.loc[len(df)] = data_conc # append the dictionary to the dataframe
    # remove replicate output folder
    rmtree( OutputFolder )
    df.to_csv(SummaryFile, sep='\t', encoding='utf-8')

def Test_Model():
    PhysiCellModel = PhysiCell_Model("config/PhysiCell_Model.ini", 'physicell_model')
    
    Parameters_dic = {1: np.array([0.5,'linear']), 
                      2: np.array([0.5,'half gaussian']), 
                      3: np.array([0.5,'exponential decay'])} # dic of parameters sample
    Parameters_rule_dic = {1: np.array([0.5,1.0,0.001,0.005]), 
                           2: np.array([0.75,0.5,0.003,0.001]), 
                           3: np.array([1.0,0.75,0.005,0.003])} # dic of parameters sample
    
    print(f"Total number of simulations: {len(Parameters_dic)*PhysiCellModel.numReplicates}")
    for sampleID, par_value, par_rules_value in zip(Parameters_dic.keys(), Parameters_dic.values(), Parameters_rule_dic.values()):
        for replicateID in np.arange(PhysiCellModel.numReplicates):
            print('Sample: ', sampleID,', Replicate: ', replicateID)
            PhysiCellModel.RunModel(SampleID=sampleID, ReplicateID=replicateID,Parameters=par_value, ParametersRules=par_rules_value, SummaryFunction=summary_function)

def Read_csv(file):
    return pd.read_csv(file, delimiter='\t')

def Merger_dataframes(output_folder, SummaryFilesExp, MergedFile):
    # merging the files 
    joined_files = os.path.join(output_folder, SummaryFilesExp) 
    
    # A list of all joined files is returned 
    joined_list = glob.glob(joined_files) 
    print(joined_list)
    
    # Finally, the files are joined 
    df = pd.concat(map(Read_csv, joined_list), ignore_index=True) 
    print(df.head()) 
    df.to_csv(MergedFile, sep='\t', encoding='utf-8')

if __name__ == '__main__':
    # Test_Model()

    # Merge dataframes
    output_folder = "output_test"
    SummaryFilesExp = "SummaryFile_00*.csv"
    MergedFile = "merged_df.csv"
    Merger_dataframes(output_folder, SummaryFilesExp, MergedFile)