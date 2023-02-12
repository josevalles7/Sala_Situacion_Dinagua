library(ggplot2)
library(tidyverse)
library(RColorBrewer)
library(scales)
library(reshape2)
library(extrafont)
  
loadfonts(device = "win")
  
filename_01 <- "output/6-month_CompleteSDI_pasoroldan.txt"
filename_02 <- "output/6-month_CompleteSDI_fraymarcos.txt"
filename_03 <- "output/6-month_CompleteSDI_pasopache.txt"
filename_04 <- "output/6-month_CompleteSDI_santalucia.txt"
  
station.pasoroldan <- read.csv(filename_01,header = TRUE)
station.pasoroldan = subset(station.pasoroldan, select = -c(Año_hidrologico,Escala,SDI,LogSDI))
colnames(station.pasoroldan) <- c("Fecha", "pasoroldan")

station.fraymarcos <- read.csv(filename_02,header = TRUE)
station.fraymarcos = subset(station.fraymarcos, select = -c(Año_hidrologico,Escala,SDI,LogSDI))
colnames(station.fraymarcos) <- c("Fecha", "fraymarcos")

station.pasopache <- read.csv(filename_03,header = TRUE)
station.pasopache = subset(station.pasopache, select = -c(Año_hidrologico,Escala,SDI,LogSDI))
colnames(station.pasopache) <- c("Fecha", "pasopache")

station.santalucia <- read.csv(filename_04,header = TRUE)
station.santalucia = subset(station.santalucia, select = -c(Año_hidrologico,Escala,SDI,LogSDI))
colnames(station.santalucia) <- c("Fecha", "santalucia")
  
  
data <- Reduce(function(x, y) merge(x, y, by="Fecha",all.x=TRUE),
               list(station.pasoroldan, station.fraymarcos, station.pasopache, station.santalucia))
  
data$Fecha <- as.Date(data$Fecha,format = "%Y-%m-%d")
dataPlot <- melt(data,id.vars = c("Fecha"),variable.name = c("Estacion"),value.name = "SDI")
dataPlot$Estacion <- factor(dataPlot$Estacion, 
                            levels = c("pasoroldan",
                                       "fraymarcos",
                                       "pasopache",
                                       "santalucia"))
  
dataPlot$categoria_sequia <- factor(cut(dataPlot$SDI,
                                        c(Inf,0,-1,-1.5,-2,-Inf),
                                        labels = c("Sequia extrema",
                                                   "Sequia severa",
                                                   "Sequia moderada",
                                                   "Sequia leve",
                                                   "No sequia"),
                                        right=FALSE))
  
colors <- c("#730000", "#e50100", "#e69800","#ffff01","white")
  
theme_set(theme_bw())
p <- ggplot(dataPlot, aes(x = Fecha, y = Estacion)) + 
geom_tile(aes(fill = categoria_sequia, ratio = 1)) + 
  labs(title = "Matriz de caracterización espacio-temporal de sequía hidrológica en Cuenca Río Santa Lucía",
       subtitle = "Escala temporal de 6-Meses",
       x = "Año",
       y = NULL, 
       caption = "Elaborado por: Jose Rodolfo Valles León")
  
p + scale_fill_manual("Categoria de Sequía",values=colors,
                      na.value = "grey90",
                      labels = c("Sequía Extrema",
                                 "Sequía Severa",
                                 "Sequía Moderada",
                                 "Sequía Leve",
                                 "No seco",
                                 "Faltante")) +
  scale_x_date(date_breaks = "5 year", 
                 labels = date_format("%Y"),
                 limits = c(as.Date("1980-01-01"),Sys.Date()),
                 expand = c(0,0),
                 date_minor_breaks = "5 months") + 
  scale_y_discrete(labels = c("pasoroldan",
                                "fraymarcos",
                                "pasopache",
                                "santalucia")) +
  theme(plot.title = element_text(size = 15,
                                      face = "bold",
                                      family = "Cambria",
                                      hjust = 0.5),
        plot.subtitle = element_text(size = 12,
                                       face = "italic",
                                       family = "Cambria",
                                       hjust = 0.5),
        plot.caption = element_text(size = 10,
                                      face = "italic"),
        legend.title = element_text(size = 12,
                                      face = "bold",
                                      family = "Cambria"),
        legend.text = element_text(size = 10,
                                     family = "Cambria"),
        legend.title.align = 0.5,
        axis.title.x = element_text(size = 12,
                                      face = "bold",
                                      family = "Cambria"),
        axis.text.x = element_text(size = 10,
                                     family ="Cambria"),
        axis.text.y = element_text(size = 10,
                                     family = "Cambria"))
  
                          