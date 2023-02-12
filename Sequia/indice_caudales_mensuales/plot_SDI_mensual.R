# Libraries
library(ggplot2)
library(scales)
library(extrafont)

loadfonts(device = "win")

# Definir parametros de entrada
name.station <- "paso roldan"
codigo.station <- 117
scale.sdi <- 6

filename <- paste0("output/",scale.sdi,"-month","_CompleteSDI_",gsub(" ","",name.station),".txt")

# leer el archvio de salida del codigo
d <- read.csv(filename,sep = ",",header = TRUE)
d$Fecha <- as.Date(d$Fecha,format = "%Y-%m-%d")
# agregar severidad de sequia en base a los valores de SDI mensual
d$State_sdi <- cut(d$GammaSDI,c(10,0,-1,-1.5,-2,-10),labels = c("Sequía extrema","Sequía severa","Sequía moderada","Sequía leve","No sequía"),right=FALSE)
# Plotear
p <- ggplot(d,aes(x=Fecha,y=GammaSDI)) + 
  geom_bar(aes(fill=State_sdi), stat = "identity",colour = "black", na.rm = TRUE) +
  scale_fill_manual("Simbología",values = c("Sequía extrema" = "#730000",
                                            "Sequía severa" = "#e50100",
                                            "Sequía moderada" = "#e69800",
                                            "Sequía leve" = "#ffff01",
                                            "No sequía" = "white")) + 
  scale_x_date(date_breaks = "1 month", 
               labels = date_format("%b.%Y"),
               #limits = c(d$fecha_hasta[1],tail(d$fecha_hasta,n=1))) +
               limits = c(as.Date("2021-01-01"),as.Date("2023-02-01"))) + 
  scale_y_continuous(breaks = scales::pretty_breaks(n = 20),
                     limits = c(-4,4)) +
  theme(axis.text.x = element_text(angle = 45, hjust = 1)) + 
  labs(title = "Indice Sequía en Caudales (SDI)",
       subtitle = paste0("Estación:", name.station, " ", codigo.station, "- Escala temporal de ", scale.sdi, " Meses"),
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


