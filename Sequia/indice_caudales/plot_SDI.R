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

id.estacion =  44
id.ancho_ventaja = 6
d <- indices %>% 
  filter(estacion == id.estacion, ancho_ventana == id.ancho_ventaja)

d$State_sdi <- cut(d$sdi,c(10,0,-1,-1.5,-2,-10),labels = c("Sequía extrema","Sequía severa","Sequía moderada","Sequía leve","No sequía"),right=FALSE)

p <- ggplot(d,aes(x=fecha_hasta,y=sdi)) + 
  geom_bar(aes(fill=State_sdi), stat = "identity",colour = "black", na.rm = TRUE) +
  scale_fill_manual("Simbología",values = c("Sequía extrema" = "#730000",
                                            "Sequía severa" = "#e50100",
                                            "Sequía moderada" = "#e69800",
                                            "Sequía leve" = "#ffff01",
                                            "No sequía" = "white")) + 
  scale_x_date(date_breaks = "1 month", 
               labels = date_format("%Y-%m-%d"),
               #limits = c(d$fecha_hasta[1],tail(d$fecha_hasta,n=1))) +
               limits = c(as.Date("2022-05-01"),as.Date("2023-03-01"))) + 
  scale_y_continuous(breaks = scales::pretty_breaks(n = 20),
                     limits = c(-4,4)) +
  labs(title = "Indice Sequía en Caudales (SDI)",
         subtitle = "Estación: Fray Marcos (44.0) - Escala temporal de 1 Meses",
       x = "Fecha",
       y = "SDI (-)", 
       caption = "Elaborado por: Jose Rodolfo Valles León")

p + theme(plot.title = element_text(size = 15,
                                    face = "bold",
                                    family = "Arial",
                                    hjust = 0.5),
          plot.margin = unit(c(1,1,1,1),"cm"),
          plot.subtitle = element_text(size = 12,
                                       face = "italic",
                                       family = "Cambria",
                                       hjust = 0.5),
          plot.caption = element_text(size = 10,
                                      face = "italic"),
          legend.title = element_text(size = 12,
                                      face = "bold"),
          legend.text = element_text(size = 10,
                                     family = "Cambria"),
          legend.title.align = 0.5,
          axis.title.x = element_text(size = 12,
                                      face = "bold",
                                      family = "Cambria"),
          axis.title.y = element_text(size = 12,
                                      face = "bold",
                                      family = "Cambria"))

