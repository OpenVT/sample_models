from mpi4py import MPI 
import numpy as np
import pandas as pd
from shutil import rmtree
import pcdl

from uq_physicell.uq_physicell import PhysiCell_Model

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

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

if __name__ == '__main__':
    PhysiCellModel = PhysiCell_Model("config/PhysiCell_Model.ini", 'physicell_model')
    
    # Sample parameters in regular grid
    Parameters_dic = {} # dic of parameters sample
    Parameters_rule_dic = {} # dic of parameters rule sample
    sample_cout = 0
    for base_migration_bias in [0.1]:
        for substrate_field in ['linear','half gaussian','exponential decay']:
            for saturation_bias in [0.5,0.75,1.0]:
                for saturation_speed in [0.5,0.75,1.0]:
                    for half_max_bias in [0.001,0.003,0.005]:
                        for half_max_speed in [0.001,0.003,0.005]:
                            Parameters_dic[sample_cout] = np.array([base_migration_bias,substrate_field])
                            Parameters_rule_dic[sample_cout] = np.array([saturation_bias,saturation_speed,half_max_bias,half_max_speed])
                            sample_cout += 1 
    
    NumSimulations = len(Parameters_dic)*PhysiCellModel.numReplicates
    NumSimulationsPerRank  = int(NumSimulations/size)
    
    # Generate a three list with size NumSimulations
    Parameters = []; ParametersRules = []; Samples = []; Replicates = [];
    for sampleID, par_value, par_rules_value in zip(Parameters_dic.keys(), Parameters_dic.values(), Parameters_rule_dic.values()):
        for replicateID in np.arange(PhysiCellModel.numReplicates):
            Parameters.append(par_value)
            ParametersRules.append(par_rules_value)
            Samples.append(sampleID)
            Replicates.append(replicateID)
    
    SplitIndexes = np.array_split(np.arange(NumSimulations),size, axis=0) # split [0,1,...,NumSimulations-1] in size arrays equally (or +1 in some ranks)
    
    print(f"Total number of simulations: {NumSimulations} Simulations per rank: {NumSimulationsPerRank}")

    for ind_sim in SplitIndexes[rank]:
        print('Rank: ',rank, ', Simulation: ', ind_sim, ', Sample: ', Samples[ind_sim],', Replicate: ', Replicates[ind_sim])
        PhysiCellModel.RunModel(SampleID=Samples[ind_sim], ReplicateID=Replicates[ind_sim], Parameters=Parameters[ind_sim], ParametersRules=ParametersRules[ind_sim], SummaryFunction=summary_function)
    
    MPI.Finalize()
