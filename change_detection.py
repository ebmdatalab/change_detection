import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import subprocess


class change_detection(object):
    '''requires the name of a sql query file (with suffix .sql)
    and the number of CPU cores to split the dataframe over for running R'''
    
    def __init__(self, name, num_cores=1):
        query = name + '.sql'
        with open(query) as q:
            self.query = q.read()
        self.name = name
        self.num_cores = num_cores
        
        ## Create dir for results
        self.working_dir = os.getcwd() + "\\data\\" + self.name
        os.makedirs(self.working_dir, exist_ok=True)
    
    def run_query(self):
        self.data = pd.read_gbq(self.query,
                                dialect='standard',
                                project_id='ebmdatalab')
        return self.data
    
    def shape_dataframe(self):
        input_df = self.run_query()
        input_df = input_df.sort_values(['code','month'])
        input_df['ratio'] = input_df['numerator'] / (input_df['denominator'] / 1000)
        input_df['code'] = 'ratio_quantity.' + input_df['code'] ## R code requires this header format
        input_df = input_df.set_index(['month','code'])
        
        ## drop small numbers
        mask = (input_df['numerator'] > 50) & (input_df['denominator']> 1000)
        input_df = input_df.loc[mask]
        input_df = input_df.drop(columns=['numerator','denominator'])
        
        ## unstack
        input_df = input_df.unstack().reset_index(col_level=1)
        input_df.columns = input_df.columns.droplevel()
        input_df['month'] = pd.to_datetime(input_df['month'])
        input_df = input_df.set_index('month')
        
        ## drop columns with missing values
        input_df = input_df.dropna(axis=1)
        
        ## drop columns with all identical values
        cols = input_df.select_dtypes([np.number]).columns
        std = input_df[cols].std()
        cols_to_drop = std[std==0].index
        input_df = input_df.drop(cols_to_drop, axis=1)
        
        ## date to unix timecode (for R)
        input_df.index = (input_df.index - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')
        
        return input_df #None
    
    
    def r_detect(self):
        '''
        Splits the DataFrame in pieces and runs the change detection algorithm
        on a separate process for each piece
        - minor issue with this is that it turns the R output into garbled
          nonsense 
            - presumably as it tries to display outputs from multiple
              processes simultaneously
            - for debugging purposes, can just use a single instance
              of a reduced sample
        
        Requires the following R modules:
        # zoo
        # caTools
        # gets
        Done from within the R code
        (install commands now commented out in R code).
        '''
        
        ## Get data and split
        split_df = np.array_split(self.shape_dataframe(),self.num_cores, axis=1)
        
        ## Initiate a seperate R process for each sub-DataFrame
        i = 0
        processes = []
        for item in split_df:
            df = pd.DataFrame(item)
            csv_name = "r_input_%s.csv" % (i)
            output_name = "r_output_%s.RData" % (i)
            df.to_csv(self.working_dir + '\\' + csv_name)
            
            ## Define command and arguments
            command = 'Rscript'
            path2script = os.getcwd() + '\\change_detection.R'
            
            ## Variable number of args in a list
            args = [self.working_dir, csv_name, output_name]
            
            ## Build subprocess command
            cmd = [command, path2script] + args
            
            import time
            tic = time.clock()
            
            ## run the command (results stored as RData files to be appended later)
            process = subprocess.Popen(cmd)
            processes.append(process)
            i += 1
        
        for process in processes:
            process.wait()
            
            toc = time.clock()
            print(toc - tic)
        return None
    
    def r_extract(self):
        os.makedirs(self.working_dir + '\\figures', exist_ok=True)
        r_detect()
        
        return None