
import logging
import multiprocessing
import sys

### Importing the local change_detection functions
sys.path.append('../')
from change_detection import functions as chg

if __name__ == '__main__':
    multiprocessing.log_to_stderr()
    logger = multiprocessing.get_logger()
    logger.setLevel(logging.INFO)
    
    #################################################################
    #################################################################
    ### Examples of analyses where .csv files are provided ##########
    #################################################################
    #################################################################

    ### A ChangeDetection analysis informed by data provided in the file
    ### csv_test/csv_test_file.csv. To draw figures from the analysis,
    ### uncomment the draw_figures line; figures will be saved to a
    ### figures directory in the csv_test/figures directory.
    csv_test_1 = chg.ChangeDetection('csv_test',
                                    #  draw_figures='yes',
                                     csv_name='csv_test_file.csv')
    csv_test_1.run()

    ### A ChangeDetection analysis informed by data provided in the file
    ### csv_test/csv_test_file_column-fix-required.csv. The column names
    ### in the file are not as expected so the numerator_variable and
    ### denominator_variable are provided so as to identify the columns
    ### of interest. Analyses are carried out, even if the output files
    ### already exist (overwrite=True) and additional information is printed
    ### to stdout (verbose=True).
    csv_test_2 = chg.ChangeDetection('csv_test',
                                   verbose=True,
                                   numerator_variable="indicator_numerator",
                                   denominator_variable="indicator_denominator",
                                   overwrite=True,
                                   csv_name='csv_test_file_column-fix-required.csv')
    csv_test_2.run()

    ### A ChangeDetection analysis informed by data provided in the file
    ### csv_test/csv_test_file_column-fix-required+date-format.csv. The column
    ### names in the file are provided as shown in the previous example. In
    ### addition, the date format in the csv file varies from what is expected;
    ### to accommodate that, the existing format is provided, which allows
    ### conversion. Other parameters (verbose=True and overwrite=True) are
    ### as in the previous example.
    csv_test_3 = chg.ChangeDetection('csv_test',
                                   verbose=True,
                                   numerator_variable="indicator_numerator",
                                   denominator_variable="indicator_denominator",
                                   date_format="%d.%m.%y",
                                   overwrite=True,
                                   csv_name='csv_test_file_column-fix-required+date-format.csv')
    csv_test_3.run()

    ### A ChangeDetection analysis informed by data provided in the file
    ### pincer-test/measure_indicator_a_rate.csv. Other parameters explained
    ### in previous examples. This file contains more columns than are required
    ### but the ChangeDetection funtions are able to handle that. If the inputs
    ### and outputs are in a separate place, these can be specified by the
    ### base_dir and data_subdir parameters (note that the base_dir needs to be
    ### provided as an absolute reference, not a relative reference).
    measure_indicator = chg.ChangeDetection('pincer-test',
                                   verbose=True,
                                   code_variable="practice",
                                   numerator_variable="indicator_a_numerator",
                                   denominator_variable="indicator_a_denominator",
                                   date_variable="date",
                                   date_format="%Y-%m-%d",
                                   overwrite=True,
                                   draw_figures='yes',
                                   #base_dir = '/place/to/directory',
                                   #data_subdir='dirname',
                                   csv_name='measure_indicator_a_rate.csv')
    measure_indicator.run()

    #################################################################
    #################################################################
    ### Examples of analyses where data are obtained via queries ####
    #################################################################
    #################################################################

    ### A ChangeDetection analysis informed by data obtained via
    ### an SQL query to ebmdatalab (access is managed via the
    ### ebmdatalab module. The items of interested are defined using
    ### the name parameter, with wildcards as used in SQL (eg below,
    ### all objects that match ccg_data_lpa.* will be analysed).
    ccg_data = chg.ChangeDetection(name='ccg_data_lpa%',
                             measure=True,
                             overwrite=True,
                             verbose=True)
    ccg_data.run()
    
    ### Where multiple objects are analysed, the data can be
    ### concatenated, but only after the processes have completed.
    ### The command for this is provided below.
    # ccg_data_ALL = ccg_data.concatenate_outputs()

    ### A ChangeDetection analysis informed by data obtained via
    ### an SQL query to ebmdatalab (access is managed via the
    ### ebmdatalab module. This query will look at a specific
    ### object - practice_data_lpfentanylir - as no wildcards are
    ### provided.
    lpfentanylir_data = chg.ChangeDetection('practice_data_lpfentanylir',
    measure=True,
    verbose=True)
    lpfentanylir_data.run()

    ### Here is another example, but it takes a very long time
    ### to run!
    # opioids = chg.ChangeDetection('practice_data_opi%',
    #                                measure=True,
    #                                verbose=True)
    # opioids.run()


