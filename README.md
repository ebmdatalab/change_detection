# Change detection in prescribing data

Detects changes in time series using the R package gets (https://cran.r-project.org/web/packages/gets/index.html). Uses a combination of Google BigQuery and Python to query data, which is then fed to the R change detection code. Outputs a table containing results.


## Usage
See https://github.com/ebmdatalab/change_detection/blob/master/change_speed_metrics.ipynb for examples of use.

## Data flow
1. Get data, by:
    - using a csv in `data/<name>`, which must have only the fields `code`, `month`, `numerator` and `denominator`
    - creating a BigQuery SQL query in the same folder as the notebook that you're using, query must produce a table with only the fields `code`, `month`, `numerator` and `denominator`
    - querying any number of the OpenPrescribing measures in BigQuery
2. Reshapes data with Pandas
3. Splits data into chunks and passes each chunk to the R change detection code
4. The resulting output is then extracted with further R code
5. The R outputs are then concatenated


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

