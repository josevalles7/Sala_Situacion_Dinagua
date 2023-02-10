# -----------------------------------------------------------------------------#
# --- Inicializar ambiente ----
# -----------------------------------------------------------------------------#

# i. Borrar variables del ambiente 
rm(list = objects())

# ii. Cargar paquetes
require(Cairo)
require(tidyverse)
require(yaml)
require(zoo)
library(scales)
library(lubridate)
library(ggplot2)
library(extrafont)

# iii. Usar Cairo para graficos
options(bitmapType = "cairo")

# iv. Cargar archivo de configuracion YML
config <- yaml::yaml.load_file("configuracion_caudales_mensuales.yml")

# v. Cargar archivo de datos diarios
caudales_diarios <- list.files(path = "input/", pattern = "*.csv", full.names = TRUE) %>%
  # Para cada archivo csv, efectua lectura del mismo
  purrr::map_dfr(.x = ., .f = readr::read_csv) %>%
  # Transformar fecha a formato Date
  dplyr::mutate(Fecha = as.Date(Fecha, format = "%d/%m/%Y")) %>%
  # Transformar data frame a tibble
  tibble::as_tibble()

# ------------------------------------------------------------------------------
# Caudales mensuales 
# ------------------------------------------------------------------------------
id.station = 1653
number.month = 01

estacion.seleccion <- caudales_diarios %>% 
  filter(Estacion == id.station) %>% 
  mutate(Fecha = floor_date(Fecha, unit = "month")) %>% 
  group_by(Fecha) %>%
  summarise(
    n = n(),
    Qtotal = sum(Q),
    Qprom = mean(Q),
    Qmax = max(Q),
    Qmin = min(Q),
    .groups = "drop"
  ) %>%
  filter(month(Fecha) == number.month)


estacion.seleccion$Ano = year(estacion.seleccion$Fecha)
estacion.seleccion <- na.omit(estacion.seleccion)
    
ggplot(estacion.seleccion,
       aes(x= reorder(Ano,-Qprom),
           Qprom,
           fill = ifelse(Ano == 2023, "Highlighted", "Normal"))) + 
  geom_bar(stat ="identity") + 
  labs(title = "Caudales mensuales",
       subtitle = paste0("Estación: ",id.station),
       x = "Año",
       y = "Caudal (m3/s)", 
       caption = "Elaborado por: Jose Rodolfo Valles León") + 
  theme(plot.title = element_text(size = 15,
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
          legend.position = "none",
          axis.title.x = element_text(size = 12,
                                      face = "bold",
                                      family = "Cambria"),
          axis.title.y = element_text(size = 12,
                                      face = "bold",
                                      family = "Cambria"))

# ------------------------------------------------------------------------------
# Caudales mensuales bandas
# ------------------------------------------------------------------------------

# Determina a qué pentada del año corresponde una fecha (1-72)
# FechaAPentadaAno <- function(fecha) {
#   dia         <- lubridate::day(fecha)
#   mes         <- lubridate::month(fecha)
#   pentada.mes <- ifelse(dia > 25, 6, ((dia - 1) %/% 5) + 1)
#   return (pentada.mes + 6 * (mes - 1))
# }
# 
# # Determina a qué pentada del mes corresponde una fecha (1-6)
# FechaAPentadaMes <- function(fecha) {
#   pentada.ano <- FechaAPentadaAno(fecha)
#   return (((pentada.ano - 1) %% 6) + 1)
# }
# 
# # Devuelve la fecha de inicio de una péntada de un añó determinado
# PentadaAnoAFechaInicio <- function(pentada.ano, ano) {
#   pentada.mes <- ((pentada.ano - 1) %% 6) + 1
#   dia         <- 1 + 5 * (pentada.mes - 1)
#   mes         <- ((pentada.ano - 1) %/% 6) + 1
#   return (as.Date(sprintf("%d-%d-%d", ano, mes, dia)))
# }
# 
# # Obtener la fecha de inicio de péntada de una fecha determinada
# FechaInicioPentada <- function(fecha) {
#   pentada.mes <- FechaAPentadaMes(fecha)
#   dia.inicio  <- 1 + 5 * (pentada.mes - 1)
#   return (as.Date(sprintf("%d-%d-%d", lubridate::year(fecha), lubridate::month(fecha), dia.inicio)))
# }
# 
# # Obtener la fecha de fin de péntada de una fecha determinada
# FechaFinPentada <- function(fecha) {
#   pentada.mes <- FechaAPentadaMes(fecha)
#   dia.fin     <- ifelse(pentada.mes < 6, 5 + 5 * (pentada.mes - 1), lubridate::days_in_month(fecha))
#   return (as.Date(sprintf("%d-%d-%d", lubridate::year(fecha), lubridate::month(fecha), dia.fin)))
# }
# 
# # Suma una cantidad de pentadas a una fecha determinada
# SumarPentadas <- function(fecha.inicio.pentada, cantidad.pentadas) {
#   pentada.ano       <- FechaAPentadaAno(fecha.inicio.pentada)
#   nueva.pentada.ano <- pentada.ano + cantidad.pentadas
#   anos.agregados    <- (nueva.pentada.ano - 1) %/% 72
#   pentada.ano       <- ((nueva.pentada.ano - 1) %% 72) + 1
#   return (PentadaAnoAFechaInicio(pentada.ano, lubridate::year(fecha.inicio.pentada) + anos.agregados))
# }
# 
# # Indica si una serie de valores tiene una cantidad de valores faltantes aceptables
# TieneFaltantesAceptables <- function(valores, max_faltantes) {
#   cantidad_faltantes <- length(which(is.na(valores)))
#   return (cantidad_faltantes <= max_faltantes)
# }
# 
# # Agrega los valores de caudales segun el ancho de ventana seleccionado
# AgregarDatosEstacion <- function(fechas, valores, ancho_ventana, max_faltantes) {
#   # Obtener de secuencia de fechas de fin de pentada para las fechas a procesar
#   fechas_hasta       <- unique(FechaFinPentada(seq(from = min(fechas), to = max(fechas), by = 'days')))
#   
#   # Para cada fecha de fin de pentada, obtener la fecha inicio de pentada segun el ancho de la ventana
#   fechas_desde       <- SumarPentadas(fechas_hasta, -ancho_ventana + 1) 
#   
#   # Generar un data.frame de caudales diarios para todas las fechas del intervalo
#   # Donde haya faltantes, indicarlo con NA
#   caudales_estacion  <- data.frame(fecha = fechas, caudal = valores) %>%
#     dplyr::right_join(data.frame(fecha = seq(from = min(fechas_desde), to = max(fechas_hasta), by = 'days')), by = "fecha")
#   
#   # Calcular caudales agregados. 
#   # Se inicia realizando todos los cruces posibles entre los periodos (fecha_desde / fecha_hasta)
#   # y los datos de caudales diarios de la estacion
#   caudales_agregados <- tidyr::crossing(data.frame(fecha_desde = fechas_desde, fecha_hasta = fechas_hasta),
#                                         caudales_estacion) %>%
#     # Filtrar los datos de modo de las fechas de diarios coincidan con los periodos de agregacion
#     dplyr::filter(fecha >= fecha_desde & fecha <= fecha_hasta) %>%
#     # Agrupar por periodo (fecha_desde / fecha_hasta)
#     dplyr::group_by(fecha_desde, fecha_hasta) %>%
#     # Agregar caudal. Si tiene una cantidad de faltantes aceptable, entonces usar na.rm = TRUE para eliminarlos.
#     # Caso contrario, dejar el parametro en FALSE para que la suma devuelva NA
#     dplyr::summarise(caudal_agregado = mean(caudal, na.rm = TieneFaltantesAceptables(caudal, max_faltantes))) %>%
#     # dplyr::summarise(caudal_agregado = sum(caudal, na.rm = TieneFaltantesAceptables(caudal, max_faltantes))) %>%
#     # Agregar ancho de ventana para facilitar futuras busquedas
#     # Tambien calcular la pentada asociada a la fecha de fin del periodo
#     dplyr::mutate(ancho_ventana = ancho_ventana,
#                   pentada_fin = FechaAPentadaAno(fecha_hasta)) %>%
#     # Seleccionar y ordenar columnas a devolver
#     dplyr::select(ancho_ventana, pentada_fin, fecha_desde, fecha_hasta, caudal_agregado)
#   
#   return (caudales_agregados)
# }
# # ------------------------------------------------------------------------------
# 
# # -----------------------------------------------------------------------------#
# # --- Generar datos estadisticos con caudales para distintas escalas ----
# # -----------------------------------------------------------------------------#
# 
# caudales_agregados <- purrr::pmap_dfr(
#   # Generar posibles combinaciones de estaciones y escalas temporales
#   .l = tidyr::crossing(estacion = unique(caudales_diarios$Estacion),
#                        ancho_ventana = config$anchos_ventana),
#   .f = function(estacion, ancho_ventana) {
#     # Buscar maxima cantidad faltantes para ancho de ventana seleccionado
#     max_faltantes <- purrr::map(
#       .x = config$faltantes,
#       .f = function(faltante) {
#         if (faltante$ancho_ventana == ancho_ventana) {
#           return (faltante$max_faltantes)
#         }
#         return (NULL)
#       }
#     ) %>% purrr::discard(.x = ., .p = is.null) %>% unlist()
#     
#     # Seleccionar datos de estacion
#     caudales_diarios_estacion <- caudales_diarios %>%
#       dplyr::filter(Estacion == estacion)
#     
#     # Efectuar agregacion
#     AgregarDatosEstacion(fechas = caudales_diarios_estacion$Fecha, 
#                          valores = caudales_diarios_estacion$Q, 
#                          ancho_ventana = ancho_ventana,
#                          max_faltantes = max_faltantes) %>%
#       dplyr::mutate(estacion = estacion) %>%
#       dplyr::select(estacion, ancho_ventana, pentada_fin, fecha_desde, fecha_hasta, caudal_agregado)
#   }
# )
# 
# 
# estacion.seleccion.monthly <- caudales_agregados %>% 
#   filter(estacion == id.station)
