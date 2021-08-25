
import logging
import multiprocessing
import sys

sys.path.append('../')

from change_detection import functions as chg

if __name__ == '__main__':
    multiprocessing.log_to_stderr()
    logger = multiprocessing.get_logger()
    logger.setLevel(logging.INFO)
    
    csv_test = chg.ChangeDetection('csv_test',
                               csv_name='csv_test_file.csv')
    
    csv_test.run()

# # %% [markdown]
# # ### Test single SQL query

# # %%
# bq_test = chg.ChangeDetection('bq_test')
# bq_test.run()

# # %% [markdown]
# # ### Single measure

# # %%
# lp = chg.ChangeDetection('practice_data_lpfentanylir',
#                          measure=True)
# lp.run()

# # %% [markdown]
# # ### Measures - low-priority CCG level

# # %%
# from change_detection import *
# lp = chg.ChangeDetection('ccg_data_lp%',
#                         measure=True)
# lp.run()

# # %% [markdown]
# # ### Measures - low-priority practice level

# # %%
# lp = chg.ChangeDetection('practice_data_lp%',
#                         measure=True)
# lp.run()

# # %% [markdown]
# # ### Measures - opioids practice level

# # %%
# from change_detection import *
# opioids = chg.ChangeDetection('practice_data_opi%',
#                               measure=True)
# opioids.run()


# # %%
# opioids.concatenate_outputs()


