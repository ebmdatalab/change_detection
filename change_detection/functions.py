import os
import subprocess
import time
from multiprocessing import cpu_count, Process
import glob
import pandas as pd
import numpy as np
from ebmdatalab import bq

'''
required R packages:
# zoo
# caTools
# gets
'''
def install_r_packages():
    import rpy2.robjects.packages as rpackages
    from rpy2.robjects.vectors import StrVector
    utils = rpackages.importr('utils')
    utils.chooseCRANmirror(ind=1)
    
    packnames = ['zoo','caTools','gets']
    names_to_install = [pkg for pkg in packnames if not rpackages.isinstalled(pkg)]
    if len(names_to_install) > 0:
        utils.install_packages(StrVector(names_to_install))
        print('Installed ' + str(names_to_install))
install_r_packages()

def run_r_script(path):
    command = 'Rscript'
    path2script = os.path.join(os.getcwd(), path)
    cmd = [command, path2script]
    return subprocess.call(cmd)


class ChangeDetection(object):
    '''
    Requires the name of a sql query file 
        - file must have suffix ".sql"
        - but not the name.
    '''
    def __init__(self,
                 name,
                 verbose=False,
                 sample=False,
                 measure=False,
                 direction='both',
                 use_cache=True,
                 csv_name='bq_cache.csv',
                 overwrite=False,
                 draw_figures='no',
                 measure_folder='measures'
                 ):
        
        self.name = name
        self.num_cores = cpu_count() - 1
        self.verbose = verbose
        self.sample = sample
        self.measure = measure
        self.direction = direction
        self.use_cache = use_cache
        self.csv_name = csv_name
        self.overwrite = overwrite
        self.draw_figures = draw_figures
        self.measure_folder = measure_folder
    
    def get_working_dir(self, folder):
        folder_name = folder.replace('%', '')
        return os.path.join(os.getcwd(), 'data', folder_name)
    
    def create_dir(self, dir_path):
        os.makedirs(dir_path, exist_ok=True)
        os.makedirs(os.path.join(dir_path, 'figures'), exist_ok=True)
    
    def get_measure_list(self):
        query = '''
        SELECT
          table_id
        FROM
          ebmdatalab.{measure_folder}.__TABLES__
        WHERE
          table_id LIKE "{name}"
        '''.format(
            measure_folder=self.measure_folder,
            name=self.name
            )
        dir_path = self.get_working_dir(self.name)
        csv_path = os.path.join(dir_path, "measure_list.csv")
        os.makedirs(dir_path, exist_ok=True)
        measure_list = bq.cached_read(
            query,
            csv_path=csv_path,
            use_cache=self.use_cache
            )
        return measure_list['table_id']
    
    def get_measure_query(self, measure_name):
        if 'practice' in self.name:
            code_col = 'practice_id'
        elif 'ccg' in self.name:
            code_col = 'pct_id'
        q = '''
        SELECT
          month,
          {code_col} AS code,
          numerator,
          denominator
        FROM
          ebmdatalab.{measure_folder}.{measure_name}
        '''.format(
            code_col=code_col,
            measure_folder=self.measure_folder,
            measure_name=measure_name
            )
        return q
    
    def get_custom_query(self):
        query = os.path.join(os.getcwd(), self.name + '.sql')
        with open(query) as q:
            return q.read()
    
    def get_data(self):
        if self.measure:
            for measure_name in self.measure_list:
                folder_name = os.path.join(self.name, measure_name)
                get_data_dir = self.get_working_dir(folder_name)
                self.create_dir(get_data_dir)
                query = self.get_measure_query(measure_name)
                csv_path = os.path.join(get_data_dir, self.csv_name)
                bq.cached_read(query,
                               csv_path=csv_path,
                               use_cache=self.use_cache)
        else:
            get_data_dir = self.get_working_dir(self.name)
            self.create_dir(get_data_dir)
            query = self.get_custom_query()
            csv_path = os.path.join(get_data_dir, self.csv_name)
            bq.cached_read(query,
                           csv_path=csv_path,
                           use_cache=self.use_cache)
    
    def shape_dataframe(self):
        '''
        Returns data in a dataframe in the format needed for `r_detect()`
        
        Args:
            csv_name: the name of the CSV file to process. The CSV file is 
            assumed to be located in `self.working_dir`. Default 
            `bq_cache.csv`
        '''
        csv_path = os.path.join(self.working_dir, self.csv_name)
        while not os.path.exists(csv_path):
            time.sleep(0.5)
        #time.sleep(3)
        input_df = pd.read_csv(csv_path)
        input_df = input_df.sort_values(['code', 'month'])
        input_df['ratio'] = input_df['numerator']/(input_df['denominator'])
        ## R script requires this header format:
        input_df['code'] = 'ratio_quantity.' + input_df['code'] 
        input_df = input_df.set_index(['month', 'code'])
        
        ## drop small numbers
        #mask = (input_df['denominator']>=5)
        #input_df = input_df.loc[mask]
        
        ## remove num/denom columns
        input_df = input_df.drop(columns=['numerator', 'denominator'])
        
        ## unstack
        input_df = input_df.unstack().reset_index(col_level=1)
        input_df.columns = input_df.columns.droplevel()
        input_df['month'] = pd.to_datetime(input_df['month'])
        input_df = input_df.set_index('month')
        
        ## replace inf and -inf with NaN
        input_df = input_df.replace([np.inf, -np.inf], np.nan)
        
        ## drop columns with missing values
        #input_df = input_df.dropna(axis=1) # removed after implementing fix
                                            # to include missing vals
                                            
        ## drop columns with all identical values
        cols = input_df.select_dtypes([np.number]).columns
        std = input_df[cols][:-5].std() #added [:-5] to remove ones with
                                        #a few wierd values at the end
        cols_to_drop = std[(std == 0)|(std.isna())].index
        input_df = input_df.drop(cols_to_drop, axis=1)
        
        ## drop columns with high proporiton of missing values
        mask = input_df.isna().sum() < len(input_df)/2
        input_df = input_df[input_df.columns[mask]]
        
        ## date to unix timecode (for R)
        input_df.index = input_df.index - pd.Timestamp("1970-01-01")
        input_df.index = input_df.index // pd.Timedelta('1s')
        
        ## Select random sample
        if self.sample:
            input_df = input_df.sample(n=100, random_state=1234, axis=1)
        
        return input_df
    
    def run_r_script(self, i, script_name, input_name, output_name, *args):
        '''        
        - have reduced outputs (a bit faster that way)
            - for debugging purposes use `verbose` argument"
        '''
        ## Define R command
        command = 'Rscript'
        module_folder = os.path.dirname(os.path.realpath(__file__))
        path2script = os.path.join(module_folder, script_name)
        cmd = [command, path2script]

        ## Define arguments to pass to R
        arguments = [self.working_dir, input_name, output_name]
        for arg in args:
            arguments.append(arg)

        ## run the command
        if i == 0:
            if self.verbose:
                return subprocess.Popen(cmd + arguments)
            return subprocess.Popen(cmd + arguments,
                                    stderr=subprocess.DEVNULL)
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
            script_name = 'change_detection.R'
            input_name = "r_input_{}.csv".format(i)
            output_name = "r_intermediate_{}.RData".format(i)
            
            df = pd.DataFrame(item)
            df.to_csv(os.path.join(self.working_dir, input_name))
            
            process = self.run_r_script(i,
                                        script_name,
                                        input_name,
                                        output_name)
            processes.append(process)
            i += 1
        
        for process in processes:
            process.wait()
            assert process.returncode == 0, \
              'Change detection process failed {}'.format(process.args)
    
    def r_extract(self):
        '''
        This R script could technically be combined with the r_detect one,
        but it was easier/more flexible to keep them separate when writing
        '''
        processes = []
        for i in range(0, self.num_cores):
            script_name = 'results_extract.R'
            input_name = "r_intermediate_{}.RData".format(i)
            output_name = "r_output_{}.csv".format(i)
            module_folder = os.path.dirname(os.path.realpath(__file__))
            
            process = self.run_r_script(i,
                                        script_name,
                                        input_name,
                                        output_name,
                                        module_folder,
                                        self.direction,
                                        self.draw_figures)
            processes.append(process)
        
        for process in processes:
            process.wait()
            assert process.returncode == 0, \
              'Results extraction process failed {}'.format(process.args)
    
    def concatenate_split_dfs(self):
        files = glob.glob(os.path.join(self.working_dir, 'r_output_*.csv'))
        df_to_concat = (pd.read_csv(f) for f in files)
        df = pd.concat(df_to_concat)
        df = df.drop('Unnamed: 0', axis=1)
        df['name'] = df['name'].str.lstrip('ratio_quantity.')
        df = df.set_index('name')
        df.to_csv(os.path.join(self.working_dir, 'r_output.csv'))
    
    def run_if_needed(self, out_path):
        if self.overwrite | (not os.path.exists(out_path)):
            self.r_detect()
            self.r_extract()
            self.concatenate_split_dfs()

    def detect_change(self):
        if self.measure:
            for measure_name in self.measure_list:
                folder_name = os.path.join(self.name, measure_name)
                self.working_dir = self.get_working_dir(folder_name)
                out_path = os.path.join(self.working_dir, 'r_output.csv')
                self.run_if_needed(out_path)
        else:
            self.working_dir = self.get_working_dir(self.name)
            if not os.path.isdir(os.path.join(self.working_dir, 'figures')):
                self.create_dir(self.working_dir)
            out_path = os.path.join(self.working_dir, 'r_output.csv')
            self.run_if_needed(out_path)
    
    def clear(self):
        os.system( 'cls' )
    
    def run(self):
        if self.measure:
            self.measure_list = self.get_measure_list()
        if self.csv_name == 'bq_cache.csv':
            p1 = Process(target = self.get_data)
            p1.start()
        p2 = Process(target = self.detect_change)
        p2.start()
    
    def concatenate_outputs(self, folder_suffix=''):
        assert self.measure, "Not to be used on single outputs"
        working_dir = self.get_working_dir('{}{}'.format(self.name,folder_suffix))
        folders = [entry.name for entry in
                   os.scandir(working_dir) if entry.is_dir()]
        files = []
        for folder in folders:
            file = os.path.join(working_dir, folder, 'r_output.csv')
            files.append(file)
        df_to_concat = (pd.read_csv(f) for f in files)
        df_to_concat = list(df_to_concat)
        for i in range(0, len(folders)):
            df_to_concat[i]['measure'] = folders[i]
        df = pd.concat(df_to_concat)
        df = df.sort_values(['measure','name'])
        return df.set_index(['measure','name'])


    def national_changes(self):
        measures = self.get_measure_list()
        for measure in measures:
            data_path = os.path.join(
                self.get_working_dir(self.name),
                measure,
                'bq_cache.csv')

            self.working_dir = os.path.join(
                self.get_working_dir('{}_national'.format(self.name)),
                 measure)
            if not os.path.isdir(os.path.join(self.working_dir, 'figures')):
                self.create_dir(self.working_dir)
            csv_path = os.path.join(self.working_dir, self.csv_name)
            entity_level = pd.read_csv(data_path, index_col='code')
            national_level = entity_level.groupby('month',as_index=False).sum()
            national_level['code'] = measure
            national_level = national_level.set_index('code')
            national_level.to_csv(csv_path)
            out_path = os.path.join(self.working_dir, 'r_output.csv')
            self.run_if_needed(out_path)
