print("Extracting and classifying changes")

library(caTools)
library(gets) ### main package for break detection - see Pretis, Reade, and Sucarrat, Journal of Stat. Software, in press.

##### Retrive arguments from Python command
arguments <- commandArgs(trailingOnly = TRUE)

###################################################################
#######################################
########### B: Extract Trend-Break Results
#######################################
####################################################################

#rm(list = ls())  #clear the workspace

#setwd("C:\\Users\\ajwalker\\Documents\\GitHub\\prescribing_change_metrics\\data\\testing") # for testing only
setwd(arguments[1])

#load("r_intermediate_2.RData")
load(arguments[2])
vars.list <- length(result.list)

arguments <- commandArgs(trailingOnly = TRUE)

#### additional source code for trend functions for analysis
source(file.path(arguments[4], "trend_isat_functions.R"))
#source("C:\\Users\\ajwalker\\Documents\\GitHub\\prescribing_change_metrics\\trend_isat_functions.R")

####################
########## Calibration of Analysis
###################

saveplots_analysis <- FALSE ###save plots of output of analysis
if (arguments[6] == 'yes'){
  saveplots_analysis <- TRUE
}
fig_path_tis_analysis <- paste(arguments[1], "/figures/", sep = "") ###set path to store analysis figures
#fig_path_tis_analysis <- "C:\\Users\\ajwalker\\Documents\\GitHub\\prescribing_change_metrics\\data\\testing\\figures\\" ###set path to store analysis figures

###### Timing Measures
known.t <- 0 ### Time of known intervention in the sample, e.g. medication became available as generic at observation t=18
break.t.lim <- .8 ### Proportion offset after negative break 

###### Slope Measures
slope.lim <- 0.5   ### Proportion of slope drop for construction of slope measure

#########################
#########################

############### to store results
results <- data.frame(name=names.rel)

### Number of Detected Breaks
results$is.nbreak <- NA ### Number of breaks

### Timing Measures
results$is.tfirst <- NA ### First negative break
results$is.tfirst.pknown <- NA  ### First negative break after a known intervention date
results$is.tfirst.pknown.offs <- NA  ### First negative break after a known intervention date not offset by a XX% increase
results$is.tfirst.offs <- NA  ###First negative break not offset by a XX% increase
results$is.tfirst.big <- NA ###steepest break as identified by is.slope.ma

### Slope Measures
results$is.slope.ma <- NA ### Average slope over steepest segment contributing at least XX% of total drop
results$is.slope.ma.prop <- NA ### Average slope as proportion to prior level
results$is.slope.ma.prop.lev <- NA ### Percentage of the total drop the segment used to evaluate the slope makes up

### Level Measures
results$is.intlev.initlev <- NA  ### Pre-drop level
results$is.intlev.finallev <- NA ### End level
results$is.intlev.levd <- NA ### Difference between pre and end level
results$is.intlev.levdprop <- NA ### Proportion of drop

########################################
################### Loop over different series

for (i in 1:(vars.list)) 

{
  #print(names.rel[i])
  y <- data.pick[names.rel[i]]
  results$name[i] <- names.rel[i]
  islstr.res <- result.list[[i]]

  ### Number of trend breaks
  nbreak <- NROW(grep("tis", islstr.res$ISnames))  
  results$is.nbreak[i] <-  nbreak #number of breaks
  
  ###coefficient path 
  tis.path <- trend.var(islstr.res)
  
  #############################################
  ##### Measure 1: Timing of Breaks
  ################################################
  
  if (nbreak > 0){ ##if there are any relevant breaks
    
    #trend break names:
    tnames <- islstr.res$ISnames[grep("tis", islstr.res$ISnames)]
    if (NCOL(islstr.res$aux$mX[,tnames]) > 1){
      tdates <-  apply(islstr.res$aux$mX[,tnames],2,function(x) (which(x>0))[1])  ##finds first non-zero index
    } else {
      tdates <-  min(which(islstr.res$aux$mX[,tnames] > 0))
    }
    
    ###coefficients and fitted values
    rel.coef.num <- islstr.res$specific.spec[tnames]
    rel.coef <- islstr.res$coefficients[rel.coef.num]
    mconst.res <- islstr.res$coefficients[islstr.res$specific.spec["mconst"]]
    fit.res <- fitted(islstr.res) ##fitted values
    fit.res <- fit.res[!fit.res<0]
    
    #### Measure 1.1: the first breaks where the coefficient path is also downward sloping
    if (arguments[5] == 'both'){
      direction <- 'min(which(tis.path$indic.fit$coef != 0))'
    }
    else if (arguments[5] == 'up'){
      direction <- 'min(which(tis.path$indic.fit$coef > 0))'
    }
    else if (arguments[5] == 'down'){
      direction <- 'min(which(tis.path$indic.fit$coef < 0))'
    }
    is.first <- eval(parse(text=direction)) 
    results$is.tfirst[i] <- is.first
    
    ### Measure 1.2: first negative break after the known break-date intervention
    if (arguments[5] == 'both'){
      direction <- 'min( tdates[which(tis.path$indic.fit$coef[tdates] != 0)][tdates[which(tis.path$indic.fit$coef[tdates] != 0)] > known.t] )'
    }
    else if (arguments[5] == 'up'){
      direction <- 'min( tdates[which(tis.path$indic.fit$coef[tdates] > 0)][tdates[which(tis.path$indic.fit$coef[tdates] > 0)] > known.t] )'
    }
    else if (arguments[5] == 'down'){
      direction <- 'min( tdates[which(tis.path$indic.fit$coef[tdates] < 0)][tdates[which(tis.path$indic.fit$coef[tdates] < 0)] > known.t] )'
    }
    
    is.first.pknown <- eval(parse(text=direction))
    results$is.tfirst.pknown[i] <- is.first.pknown
    
    #### Measure 1.3: the first negative break where there is no subsequent offset of at least break.t.lim 
    offset <- array(NA, dim=NROW(tdates))
    levels <- array(NA, dim=NROW(tdates))
    
    for (j in 1:NROW(tdates)){
      
      ###for each break, compute the total change
      date <- tdates[j]
      
      if (j < NROW(tdates)){
        enddate <- tdates[j+1]
      } else {
        enddate <- NROW(tis.path$indic.fit$indic.fit)
      }
      startlev <- tis.path$indic.fit$indic.fit[date-1]
      endlev <- tis.path$indic.fit$indic.fit[enddate-1]
      levchange <- endlev - startlev
      
      levels[j] <- levchange
      
    }
    
    ratios <- array(NA, dim= (NROW(levels)-1))
    
    if ( NROW(levels) > 1){
      
      for (j in 1: (NROW(levels)-1)){
        
        ratios[j] <-  levels[j+1]/levels[j]
        
        if (ratios[j] < -break.t.lim & !is.na(ratios[j])){     
          offset[j] <- TRUE 
        } else {
          offset[j] <- FALSE 
        }
        
        offset[NROW(levels)] <- FALSE
      }
      
    } else {
      offset <- FALSE 
    } 
    ############ FUTURE - ADD IN OFFSETS *BEFORE* BREAK TOO ###############
    ### Store first negative break which is not offset and which occurs after known break date
    if (arguments[5] == 'both'){
      direction <- 'min(tdates[rel.coef != 0 & tdates >= known.t & tis.path$indic.fit$coef[tdates] != 0 & offset == FALSE])'
    }
    else if (arguments[5] == 'up'){
      direction <- 'min(tdates[rel.coef > 0 & tdates >= known.t & tis.path$indic.fit$coef[tdates] > 0 & offset == FALSE])'
    }
    else if (arguments[5] == 'down'){
      direction <- 'min(tdates[rel.coef < 0 & tdates >= known.t & tis.path$indic.fit$coef[tdates] < 0 & offset == FALSE])'
    }
    
    is.first.pknown.offs <- eval(parse(text=direction))
    results$is.tfirst.pknown.offs[i] <- is.first.pknown.offs
    
    ### Store first negative break which is not offset  (regardless of known break date)
    if (arguments[5] == 'both'){
      direction <- 'min(tdates[rel.coef != 0  & tis.path$indic.fit$coef[tdates] != 0 & offset == FALSE])'
    }
    else if (arguments[5] == 'up'){
      direction <- 'min(tdates[rel.coef > 0  & tis.path$indic.fit$coef[tdates] > 0 & offset == FALSE])'
    }
    else if (arguments[5] == 'down'){
      direction <- 'min(tdates[rel.coef < 0  & tis.path$indic.fit$coef[tdates] < 0 & offset == FALSE])'
    }
    
    is.first.offs <- eval(parse(text=direction))
    results$is.tfirst.offs[i] <- is.first.offs
    
    #############################################
    ##### Measure 2 Steepness/Slope: average slope of the steepest contiguous segment contributing to at least XX% of the total level change
    ################################################
#    print(!is.first==Inf)
    if (!is.first==Inf)  #first break not to lie before the known break date
    {
      
      coefp.dif <- tis.path$indic.fit$coef
      const.path <-  tis.path$indic.fit$indic.fit
      
      first.index <-  which(tdates==is.first.pknown )
      interval <- const.path[tdates[first.index:length(tdates)]-1]
      #predrop <- fit.res[is.first.pknown-1] #changed: FP Sept 13th.
      predrop <- fit.res[is.first.pknown]
      
      #totaldif  <- sum(coefp.dif[(is.first.pknown-1):(NROW(coefp.dif))]) # total drop, change in every period, i.e. the slope #changed: FP Sept 13th.
      totaldif  <- sum(coefp.dif[(is.first.pknown):(NROW(coefp.dif))]) # total drop, change in every period, i.e. the slope
      
      max_interval <- NROW(const.path) - is.first.pknown + 1
      
      
      grid_sum <- matrix(NA, ncol=max_interval, nrow=max_interval)
      grid_mean <- matrix(NA, ncol=max_interval, nrow=max_interval)
      
      #####Grid Search:
      
      for (j in 1:max_interval){
        grid_sum[,j] <- runmean(coefp.dif[(is.first.pknown):NROW(coefp.dif)], j, align="left", endrule="NA")*j  #sum over every length (columns) at every point (rows)
        grid_mean[,j] <-  runmean(coefp.dif[(is.first.pknown):NROW(coefp.dif)], j, align="left", endrule="NA") #take the running mean of the slope, corresponding to the values above
        
      }
      
      grid_prop <- grid_sum*(as.numeric(totaldif))^(-1)
      
      maxc <- apply(grid_prop,2,max, na.rm=TRUE)
      min_index <- min(which(maxc>slope.lim))
      
      #Find the steepest slope that falls within this shortest interval and satisfies the XX% requirement:
      minslopgrid <- which(grid_prop[,min_index] > slope.lim)
      slopeval <- grid_mean[minslopgrid[which.max(abs(grid_mean[minslopgrid, min_index]))], min_index] ###find the maximum slope, on the shortest interval, that yields over XX% drop
      
      interval.full <- const.path[c(tdates[first.index:length(tdates)]-1, NROW(const.path))]
      
      if(length(tdates[first.index:length(tdates)])>1){   #if more than one break
        slopindex <- minslopgrid[which.max(abs(grid_mean[minslopgrid, min_index]))]
      } else { #if just one break
        slopindex <- 1   #start at the beginning
      }
      
      
      coef.p <- const.path
      coefp.dif.hl <- coefp.dif*NA
      coefp.dif.hl[(is.first.pknown+slopindex-2):((is.first.pknown+slopindex)+min_index-3) ] <- coefp.dif[(is.first.pknown+slopindex-2):((is.first.pknown+slopindex)+min_index-3) ]
      
      ### Store the part of the slope segment evaluated for plotting
      coef.p.hl <- coef.p*NA
      coef.p.hl[(is.first.pknown+slopindex-2):((is.first.pknown+slopindex)+min_index-2)] <- const.path[(is.first.pknown+slopindex-2):((is.first.pknown+slopindex)+min_index-2)]
      result.list[[i]]$is.results$coef.p.hl <- coef.p.hl
      
      
      big.break.index <- which(round(tis.path$coef.var$coef, digits = 4)==round(slopeval, digits = 4))
      
      ###Store Slope Results
      results$is.slope.ma[i] <- slopeval    #slope over the contiguous segment
      results$is.slope.ma.prop[i] <- slopeval/predrop #slope over the contiguous segment as proportion of prior level
      results$is.slope.ma.prop.lev[i] <- grid_prop[slopindex,min_index ] #percentage of total drop that the contiguous segment contributes
      
      ###Biggest break
      big.break <- is.first.pknown+slopindex-1 ### which(round(tis.path$coef.var$coef, digits = 4)==round(slopeval, digits = 4))
      results$is.tfirst.big[i] <- big.break      
    }
    
    
    #############################################
    ##### Measure 3: Magnitude of Change
    ################################################
    
    start.lev <- is.first.pknown-1
    init.lev <- fit.res[start.lev]
    end.lev <- fit.res[NROW(fit.res)]
    
    ### Store Magnitude Results
    results$is.intlev.initlev[i] <- init.lev
    results$is.intlev.finallev[i] <- end.lev
    results$is.intlev.levd[i] <- as.numeric(init.lev) - as.numeric(end.lev)   #absulte change
    results$is.intlev.levdprop[i] <-  (as.numeric(init.lev) - as.numeric(end.lev))/as.numeric(init.lev)         #percentage change
    
    print(paste(round((i / vars)*100,1), "%"))
  } ## if there are breaks closed
  
  #### Save analysis plots      
  if (saveplots_analysis){
    filename <- paste(fig_path_tis_analysis, results$name[i], ".png", sep="")
    wid <- 500
    hei <- 500
    png(filename)
    par(mfrow=c(1,1))
    islstr.res$aux$y[islstr.res$aux$y == 99] <- NA
    plot(islstr.res$aux$y, col="black", ylab="Numerator over denominator", xlab="Time series months", type="l",las=1) ##
    trendline <- tis.path$indic.fit$indic.fit+islstr.res$coefficients[islstr.res$specific.spec["mconst"]]
    lines(trendline,  col="red", lwd=2) ###fitted lines
    if (nbreak > 0){
        if (!is.first==Inf){
        abline(h=fit.res[is.first.pknown-1], lty=3, col="purple", lwd=2)### start value
        abline(h=fit.res[NROW(fit.res)], lty=3, col="purple", lwd=2)### end value
        lines(coef.p.hl+mconst.res, col=rgb(red = 1, green = 0.4118, blue = 0, alpha = 0.5), lwd=15) ###section used to evaluate slope
        #print(big.break.index)
        if (length(big.break.index) != 0){
          abline(v=tdates[min(big.break.index)], lty=2, col="blue", lwd=2) ## first negative break after intervention which is not off-set
        }
      }
    }
    #abline(v=known.t, lty=1, col="blue", lwd=2)### known intervention, blue dottedwarnings()
    
    #print(names.rel[i])
    dev.copy(png,filename=filename, width=wid, height=hei)
    dev.off()
    dev.off()
  }

} #loop over i closed 

write.csv(results, file = arguments[3])
print("Done extracting results")
