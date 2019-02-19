import pandas as pd
import numpy as np
import os
import subprocess
import multiprocessing
import glob
from ebmdatalab import bq

'''
still need to:
    - implement missing data pass through (see Felix email)
    - make sample function optional
'''


def install_r_packages():
    '''
    Installs the following R modules:
    # zoo
    # caTools
    # gets
    '''
    command = 'Rscript'
    path2script = os.getcwd() + '\\install_packages.R'
    cmd = [command, path2script]
    return subprocess.call(cmd)


class ChangeDetection(object):
    '''
    Requires the name of a sql query file 
        - file must have suffix ".sql"
        - but not the name.
    '''
    def __init__(self, name, verbose=False):
        query = 'queries/' + name + '.sql'
        with open(query) as q:
            self.query = q.read()
        self.name = name
        self.num_cores = multiprocessing.cpu_count()
        self.verbose = verbose
        
        ## Create dir for results
        self.working_dir = os.getcwd() + "\\data\\" + self.name
        os.makedirs(self.working_dir, exist_ok=True)
        
    def shape_dataframe(self):
        input_df = bq.cached_read(
                self.query,
                csv_path='bq_cache.csv')
        input_df = input_df.sort_values(['code','month'])
        input_df['ratio'] = input_df['numerator']/(input_df['denominator'])
        input_df['code'] = 'ratio_quantity.' + input_df['code'] ## R script requires this header format
        input_df = input_df.set_index(['month','code'])
        
        ## drop small numbers
        #mask = (input_df['numerator']>50) & (input_df['denominator']>1000)
        #input_df = input_df.loc[mask]
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
        input_df.index = input_df.index - pd.Timestamp("1970-01-01")
        input_df.index = input_df.index // pd.Timedelta('1s')
        
        ## Select random sample
        input_df = input_df.sample(n=100, random_state=1234, axis=1)
        
        return input_df
    
    def run_r_script(self, i, script_name, input_name, output_name, *args):
        '''        
        - have reduced outputs (a bit faster that way)
            - for debugging purposes remove "stderr=subprocess.DEVNULL"
        '''
        ## Define R command
        command = 'Rscript'
        path2script = os.getcwd() + script_name
        cmd = [command, path2script]

        ## Define arguments to pass to R
        arguments = [self.working_dir, input_name, output_name]
        for arg in args:
            arguments.append(arg)

        ## run the command (results stored as RData files to be appended later)
        if i==0:
            if self.verbose:
                return subprocess.Popen(cmd + arguments)
            else:
                return subprocess.Popen(cmd + arguments,
                                        stderr=subprocess.DEVNULL)
        else:
            return subprocess.Popen(cmd + arguments,
                                    stderr=subprocess.DEVNULL,
                                    stdout=subprocess.DEVNULL)
    
    def r_detect(self):
        '''
        Splits the DataFrame in pieces and runs the change detection algorithm
        on a separate process for each piece
        '''
        ## Get data and split
        split_df = np.array_split(self.shape_dataframe(),
                                  self.num_cores,
                                  axis=1)
        
        ## Initiate a seperate R process for each sub-DataFrame
        i = 0
        processes = []
        for item in split_df:
            script_name = '\\change_detection.R'
            input_name = "r_input_%s.csv" % (i)
            output_name = "r_intermediate_%s.RData" % (i)
            
            df = pd.DataFrame(item)
            df.to_csv(self.working_dir + '\\' + input_name)
            
            process = self.run_r_script(i,
                                        script_name,
                                        input_name,
                                        output_name)
            processes.append(process)
            i += 1
        
        for process in processes:
            process.wait()
        
        return None
    
    def r_extract(self):
        '''
        This R script could technically be combined with the r_detect one,
        but it was easier/more flexible to keep them separate when writing
        '''
        os.makedirs(self.working_dir + '\\figures', exist_ok=True)
        self.r_detect()
        
        processes = []
        for i in range(0, self.num_cores):
            script_name ='\\results_extract.R'
            input_name = "r_intermediate_%s.RData" % (i)
            output_name = "r_output_%s.csv" % (i)
            
            process = self.run_r_script(i,
                                        script_name,
                                        input_name,
                                        output_name,
                                        os.getcwd())
            processes.append(process)
        
        for process in processes:
            process.wait()
        
        return None
    
    def detect_change(self):
        '''
        Runs r_extract and combines R outputs into a single pd dataframe
        '''
        self.r_extract()
        files = glob.glob(os.path.join(self.working_dir, 'r_output_*.csv'))
        df_to_concat = (pd.read_csv(f) for f in files)
        df = pd.concat(df_to_concat)
        df = df.drop('Unnamed: 0',axis=1)
        df['name'] = df['name'].str.lstrip('ratio_quantity.')
        df = df.set_index('name')
        return df