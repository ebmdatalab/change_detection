# Change detection in prescribing data

Detects changes in time series using the R package gets (https://cran.r-project.org/web/packages/gets/index.html). Uses a combination of Google BigQuery and Python to query data, which is then fed to the R change detection code. Outputs a table containing results 

## Requirements:

Python with an associated install of R. I've used Anaconda to do this.

### Python installation requires:
- ebmdatalab library https://github.com/ebmdatalab/datalab-pandas

### R installation requires:
- zoo
- caTools
- gets

## Usage
 See https://github.com/ebmdatalab/prescribing_change_metrics/blob/master/change_speed_metrics.ipynb for example of use

## Data flow
1. Queries data from BigQuery, either by:
    - creating a SQL query in the queries folder, query must produce a table with only the fields `code` `month` `numerator` and `denominator`
    - querying any number of the OpenPrescribing measures
2. Reshapes data with Pandas
3. Splits data into chunks and passes each chunk to the R change detection code
4. The resulting output is then extracted with further R code
5. The R outputs are then concatenated
