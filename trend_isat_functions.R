


#####################
####extract trend coefficients and compute coefficient path
########################

x <- islstr.res
trend.var <- function(x, mxfull=NULL, mxbreak="tis"){


  if( length(grep(mxbreak, x$ISnames) ) != 0 ){
    
    if (is.null(mxfull)){
      
      relvar <- grep(mxbreak, names(coefficients(x)))
      
      rel.coefs <- coefficients(x)[relvar]
      end.coef <- sum(rel.coefs)
      
      rel.variance <- x$vcov.mean[relvar, relvar]
      
      coef.var <- data.frame(matrix(NA, length(rel.coefs), 3))
      names(coef.var) <- c("tis", "coef", "se")
      coef.var$tis <- names(coefficients(x)[relvar])
      coef.var$coef <- cumsum(rel.coefs)
      
      ##find the timing:
      rel.mx <- grep(mxbreak, x$ISnames)
      
      if (NCOL(x$aux$mX[,x$ISnames]) > 1 ){
      indic.mat <-  x$aux$mX[,x$ISnames][,rel.mx]
      } else {
      indic.mat <-  x$aux$mX[,x$ISnames]
      }
      
      
      if (!is.null(dim(indic.mat))){
        timing <- apply(indic.mat[,], 2, function(x) min(which(x!=0)))
        
      } else {
        
        timing <- min(which(indic.mat!=0))
      }
      
      
      for (i in 1:length(relvar)){
        
        #i <- 3
        if (length(relvar) > 1){
          cuvar <- sum(rel.variance[1:i, 1:i])
        } else {
          cuvar <- rel.variance[1]
        }
        
        coef.var$se[i] <- sqrt(cuvar)
        
      }
      
      coef.var$t.val <- coef.var$coef/coef.var$se
      coef.var$p.val <- (1-pnorm(abs(coef.var$t.val)))*2
      coef.var$time <- timing

      ###get a coefficient path out
      
      if (length(rel.coefs) > 1){
        indic.fit <- data.frame(indic.mat %*% rel.coefs)
        names(indic.fit) <- c("indic.fit")
      } else {
        indic.fit <- data.frame(indic.mat * rel.coefs)
        names(indic.fit) <- c("indic.fit")
      }
      
      
      indic.fit$coef <- 0
      indic.fit$se <- 0
      indic.fit$t.val <- 0
      indic.fit$p.val <- 0
      
      for (j in 1:length(timing)){
        
        start <- timing[j]
        
        if (j < length(timing)){
          end <- timing[j+1]-1
        } else {
          end <- NROW(indic.fit)
        }
        
        indic.fit$coef[start:end] <- coef.var$coef[j]
        indic.fit$se[start:end] <- coef.var$se[j]
        indic.fit$t.val[start:end] <- coef.var$t.val[j]
        indic.fit$p.val[start:end] <- coef.var$p.val[j]
        
      }
      
    } #if null check closed
    
    
  } else {   #grep check closed else
    
    coef.var <- NULL
    
    indic.fit <- data.frame(matrix(0, nrow=NROW(x$aux$y), ncol=1))
    names(indic.fit) <- c("indic.fit")
    indic.fit$coef <- 0
    indic.fit$se <- 0
    indic.fit$t.val <- 0
    indic.fit$p.val <- 0
    
  } #grep check closed
  
  out <- list(coef.var, indic.fit)
  names(out) <- c("coef.var", "indic.fit")

  return(out)
  
} ###function closed
