# Change detection in prescribing data

Detects changes in time series with a python wrapper around the R package gets (https://cran.r-project.org/web/packages/gets/index.html). Uses a combination of Google BigQuery and Python to query data, which is then fed to the R change detection code. Outputs a table containing results.

## Installation
`pip install change_detection`

Anaconda users may have to `conda install rpy2` and `conda install geopandas` if not already installed.

## Usage
See https://github.com/ebmdatalab/change_detection/blob/master/examples/examples.ipynb for examples of use.

## Data flow
1. Get data, by:
    - using a csv in `data/<name>`, which must have only the fields `code`, `month`, `numerator` and `denominator`
    - creating a BigQuery SQL query in the same folder as the notebook that you're using, query must produce a table with only the fields `code`, `month`, `numerator` and `denominator`
    - querying any number of the OpenPrescribing measures in BigQuery
2. Reshapes data with Pandas
3. Splits data into chunks and passes each chunk to the R change detection code
4. The resulting output is then extracted with further R code
5. The R outputs are then concatenated

### Options
- `name` specifies either the name of the custom SQL file, or the name of the BigQuery measure to be queried
- `verbose` makes the R output more verbose to help with bug fixing _default = False_
- `sample` for testing purposes, takes a random sample of 100 entities, to reduce processing time _default = False_
- `measure` specifies that the `name` specified refers to a measure, rather than custom SQL _default = False_
- `direction` specifies which direction to look for changes, may be `'up'`, `'down'`, or `'both'`, _default = 'both'_
- `use_cache` passes the `use_cache` option to `bq.cached_read` _default = True_
- `csv_name` to specify a .csv file to be used in the change detection, rather than getting the data from BigQuery
- `overwrite` forces reprocessing of the change detection, default behaviour is to not re-run if the output files exist _default = False_
- `draw_figures` draw an R plot for each of the time-series, along with plotting regression lines/breaks. These are stored in the `figures` folder. Options are `'no'` or `'yes'` _default = 'no'_

## Output table

### Timing Measures
`is.tfirst` First negative break
`is.tfirst.pknown` First negative break after a known intervention date
`is.tfirst.pknown.offs` First negative break after a known intervention date not offset by a XX% increase
`is.tfirst.offs` First negative break not offset by a XX% increase
`is.tfirst.big` Steepest break as identified by `is.slope.ma`

### Slope Measures
`is.slope.ma` Average slope over steepest segment contributing at least XX% of total drop
`is.slope.ma.prop` Average slope as proportion to prior level
`is.slope.ma.prop.lev` Percentage of the total drop the segment used to evaluate the slope makes up

### Level Measures
`is.intlev.initlev` Pre-drop level
`is.intlev.finallev` End level
`is.intlev.levd` Difference between pre and end level
`is.intlev.levdprop` Proportion of drop


## Requirements

Python with an associated install of R. Python dependencies should be dealt with on installation (though for my install, I had to install rpy2 separately. R packages should be installed with the package is first loaded.

### Python installation requires:
- ebmdatalab library https://github.com/ebmdatalab/datalab-pandas
- rpy2 (to install R and the below libraries)
- pandas
- pandas-gbq
- numpy

### R installation requires:
- zoo
- caTools
- gets

