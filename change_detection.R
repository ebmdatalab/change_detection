print("Change detection running...")

##### Retrive arguments from Python command
arguments <- commandArgs(trailingOnly = TRUE)

#rm(list = ls())  #clear the workspace
setwd(arguments[1]) ### Set working directory

########################
####### Load required packages (install needed first time)
#######################
library(caTools)
library(gets) ### main package for break detection - see Pretis, Reade, and Sucarrat, Journal of Stat. Software, in press.

##########################
####### Parameters
#########################

plot_show <- FALSE ###show plots during break detection

#### Break detection calibration
p_alpha <- 0.0000001 ## level of significance for the detection of breaks (main calibration choice)

### Computational
parallel <- NULL ### set as integer (=number of cores-1) if selection should run in parallel (may increase speed for longer time series)
# recommended to set to "NULL" unless datasets are very large.

######### Input Data
variable <- "ratio_quantity" ###choose relevant variable name in the sample
data.pick <- read.csv(arguments[2], header=TRUE)   #load raw input data

#############################################
############################################

pick.rel <- grep(variable , names(data.pick)) 

month.c  <-  as.POSIXct(as.numeric(as.character(data.pick$month)),origin="1970-01-01",tz="GMT")

data.pick <- data.frame(month.c, data.pick[,pick.rel]) 

names.rel <- names(data.pick)[pick.rel]
vars <- length(pick.rel)


#############################################################################
################################################
###################### A: Break Detection Loop
################################################
##############################################################################

result.list <- list()

withCallingHandlers({
  for (i in 1:vars) 
    
  {
    
    #print(paste(round((i / vars)*100,1), "%"))
    print(names.rel[i])
    print(data.pick[names.rel[i]])
    y <- as.matrix(data.pick[names.rel[i]])
    
    ###############################################
    ###Main Break Detection Function (tis=TRUE searches for trend breaks) - called from "gets" package
    islstr.res <- isat(y, t.pval=p_alpha, sis = FALSE, tis = TRUE, iis = FALSE, plot=plot_show, parallel.options = parallel, max.block.size = 15)
    ##########################################
    
    result.list[i] <- list(islstr.res)
    names(result.list)[i] <- names.rel[i]
    
  }  
}, warning = function(w){
  results$warn[i] <<- w$message
  invokeRestart("muffleWarning")
  
}) ###withCalling closed

#save(result.list, file=arguments[3])
save.image(file=arguments[3])

print("Break detection done")