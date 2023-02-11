# i. Borrar variables del ambiente 
rm(list = objects())
# Libraries
library(ggplot2)
library(scales)
library(tidyverse)
library(extrafont)

loadfonts(device = "win")

indices <- readr::read_csv(file = "output/indices.csv") %>%
  # Transformar data frame en tibble
  tibble::as_tibble()

fray.marcos <- indices %>% filter(estacion == 44, ancho_ventana == 12)
paso.pache <- indices %>% filter(estacion == 59.1, ancho_ventana == 12)
florida <- indices %>% filter(estacion == 53.1, ancho_ventana == 12)
santa.lucia <- indices %>% filter(estacion == 133, ancho_ventana == 12)

data <- Reduce(function(x, y) merge(x, y, by="fecha_hasta",all.x=TRUE), 
               list(fray.marcos, paso.pache, florida,santa.lucia))
data$fecha_hasta <- as.Date(data$fecha_hasta,format = "%Y-%m-%d")
dataPlot <- reshape2::melt(data,id.vars = c("fecha_hasta"),variable.name = c("estacion"),value.name = "sdi")
