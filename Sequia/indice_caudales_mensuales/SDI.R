####################################
## Created on 10/May/2020         ##
## @author: Jose Valles - DINAGUA ##
####################################

# Libraries ---------------------------------------------------------------

# Remove workspace object
rm(list = ls())

# Shut-down the warning of the NA gamma fit function
defaultW <- getOption("warn") 
options(warn = -1)

#Libraries
library(zoo)
library(lubridate)
library(EnvStats)
library(lfstat)
library(reshape2)


# Import data -------------------------------------------------------------

#Importing and converting the csv input file
codcuenca = "SL"
filename = paste0("input/",codcuenca,"_monthly_pasopache.csv")
data <- read.csv(filename,header = TRUE)
data$Fecha <- as.Date(data$Fecha,format = "%d/%m/%Y")
station_name <- tools::file_path_sans_ext(basename(filename))

# Importing the reference period (scale). Type the Time Scale (1 to 12)
k <- 6
# Define the month in which the Hydrological Year starts (1 to 12). In Uruguay, starts in April (4)
m <- 4 
m <- month.abb[month(m)]

data$StartMonth <- month.abb[month(data$Fecha - months(k-1))]
data$EndMonth <- month.abb[month(data$Fecha)]
data$ScaleMonth <- paste0(data$StartMonth,"-",data$EndMonth)
data$cumCaudal <- rollsum(data$Caudal,k,fill = NA,align = "right")
data$lnCaudal <- log(data$cumCaudal)

iteration <- unique(data$ScaleMonth)
statsOutput <- matrix(ncol = 4, nrow=length(iteration))
rw = 1


# Calculate the SDI  ------------------------------------------------------

for (i in iteration){
  # extract the data based on the scale month column
  extracted_data <- data[data[,5]==i,]
  # Calculate metrics (avg, std) of the cumCaudal and cumLnCaudal
  statsOutput[rw,1] <- mean(extracted_data$cumCaudal,na.rm=TRUE)
  statsOutput[rw,2] <- sd(extracted_data$cumCaudal, na.rm = TRUE)
  statsOutput[rw,3] <- mean(extracted_data$lnCaudal,na.rm=TRUE)
  statsOutput[rw,4] <- sd(extracted_data$lnCaudal, na.rm = TRUE)
  # calculate the SDI
  data$SDI[data$ScaleMonth==i] <- (data$cumCaudal[data$ScaleMonth==i] - statsOutput[rw,1])/statsOutput[rw,2]
  # calculate the SDI with a two-parameter log-normal distribution 
  data$log_SDI[data$ScaleMonth==i] <- (data$lnCaudal[data$ScaleMonth==i] - statsOutput[rw,3])/statsOutput[rw,4]
  # calculate the SDI with a Gamma distribution
  fitGamma <- egamma(extracted_data$cumCaudal)
  cdfVal <- pgamma(extracted_data$cumCaudal,shape = fitGamma$parameter[1],scale = fitGamma$parameters[2])
  InvNormal <- qnorm(cdfVal)
  data$Gamma_SDI[data$ScaleMonth==i] <- InvNormal
  # Row counter
  rw = rw + 1
}

statsOutput <- data.frame(iteration,statsOutput)
colnames(statsOutput) <- c("ScaleMonth", "avgCumCaudal","stdCumCaudal","avgLnCumCaudal","stdLnCumCaudal")
data$WYear <- year(as.Date(water_year(data$Fecha,origin = m),"%Y"))
data$hydroYear <- paste0(data$WYear,"-",data$WYear+1)


# Exporting to CSV the Complete Results -----------------------------------

dataExport <- subset(data,select=-c(Caudal,StartMonth,EndMonth,cumCaudal,WYear,lnCaudal))
dataExport <- dataExport[,c(1,6,2,3,4,5)]
dataExport$SDI <- round(dataExport$SDI,digits = 2)
dataExport$log_SDI <- round(dataExport$log_SDI,digits = 2)
dataExport$Gamma_SDI <- round(dataExport$Gamma_SDI,digits = 2)
colnames(dataExport) <- c("Fecha", "Año_hidrologico","Escala","SDI","LogSDI","GammaSDI")

SDI_Filename <- paste0("output/",k,"-month","_CompleteSDI_",sub(".*monthly_", "", station_name),".txt")
write.table(dataExport,SDI_Filename,na = "",row.names = FALSE,sep=",")


# # Exporting individual text file for different distribution ---------------
# 
# # SDI with no transformation
# SDI <- dcast(dataExport, Año_hidrologico ~ factor(Escala, levels = unique(Escala)), value.var = "SDI")
# # SDI Log-Normal transformation
# logSDI <- dcast(dataExport, Año_hidrologico ~ factor(Escala, levels = unique(Escala)), value.var = "LogSDI")
# # SDI Gamma transformation
# gammaSDI <- dcast(dataExport, Año_hidrologico ~ factor(Escala, levels = unique(Escala)), value.var = "GammaSDI")
# 
# # Exporting specific csv files for each SDI
# SDI_Filename_gamma <- paste0(outputfolder,k,"-month","_GammaSDI_",station_name,".txt")
# SDI_Filename_log <- paste0(outputfolder,k,"-month","_logSDI_",station_name,".txt")
# SDI_Filename_noTrans <- paste0(outputfolder,k,"-month","_RegularSDI_",station_name,".txt")
# 
# write.table(SDI,SDI_Filename_noTrans,na = "",row.names = FALSE,sep=",")
# write.table(logSDI,SDI_Filename_log,na = "",row.names = FALSE,sep=",")
# write.table(gammaSDI,SDI_Filename_gamma,na = "",row.names = FALSE,sep=",")
# 
# options(warn = defaultW)
# 
# # Test the gamma function -------------------------------------------------
# 
# # Testing the gamma function
# 
# sw.gamma <- gofTest(extracted_data$cumCaudal,dist="gamma",data.name = "Discharge")
# dev.new()
# plot(sw.gamma, digits = 3)
