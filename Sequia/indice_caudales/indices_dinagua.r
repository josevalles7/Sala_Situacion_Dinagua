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

# iii. Usar Cairo para graficos
options(bitmapType = "cairo")

# iv. Cargar archivo de configuracion YML
config <- yaml::yaml.load_file("configuracion_indices_dinagua.yml")

# v. Cargar archivos de datos diarios
caudales_agregados <- readr::read_csv(file = "work/caudales_agregados.csv") %>%
  # Transformar data frame en tibble
  tibble::as_tibble()
# ------------------------------------------------------------------------------

# -----------------------------------------------------------------------------#
# --- Definicion de funciones ----
# -----------------------------------------------------------------------------#

# Funciones para pasar de tibble a lista y vicecersa
ParametrosATibble <- function(parametros.ajuste) {
  parametros <- tibble::enframe(parametros.ajuste) %>%
    tidyr::unnest() %>%
    dplyr::rename(parametro = name, valor = value) %>%
    tibble::as_tibble()
  return (parametros)
}
ParametrosALista <- function(parametros.ajuste) {
  parametros.lista        <- as.list(parametros.ajuste$valor)
  names(parametros.lista) <- parametros.ajuste$parametro
  return (parametros.lista)
}

# Ajuste de función de distribución Gamma por método de máxima verosimilitud
AjustarMaximaVerosimilitudGamma <- function(x, numero.muestras = NULL, min.tasa.valores.positivos) {
  # Ajuste de la distribución Gamma por metodo de maxima verosimilitud
  # Eliminar los valores = 0 porque está fuera del dominio de la distribución Gamma
  # Verificar si el vector de entrada tiene ceros 
  prob.cero             <- 0 # Probabilidad de valores = 0 segun (Stagge et. al, 2015), eq [2]
  prob.media.mult.ceros <- 0 # Probabilidad de valores = 0 segun (Stagge et. al, 2015), eq [3]
  longitud.inicial      <- length(x) # Cantidad de elementos antes de eliminar 0s
  if (any(x == 0)) {
    # Calcular probabilidad de valores = 0
    n.ceros         <- as.integer(length(x[x == 0]))                             # Numero de ceros en ESTA serie
    largo.con.ceros <- as.integer(length(x))                             # Largo serie ajustada (con ceros)
    prob.cero       <- (n.ceros / (largo.con.ceros + 1))                 # (Stagge et. al, 2015, eq 2)
    prob.media.mult.ceros <- (n.ceros + 1) / (2 * (largo.con.ceros + 1)) # (Stagge et. al, 2015, eq 3)
    x               <- x[which(x > 0)]                                   # Eliminar los ceros presentes
    rm(n.ceros, largo.con.ceros)
  }
  
  # Verificar si hay un minimo numero de valores para estimar parametros
  parametros.ajuste <- list(alpha = NA, beta = NA, prob.0 = prob.cero, prob.media.0 = prob.media.mult.ceros)
  if (length(x) >= (min.tasa.valores.positivos * longitud.inicial)) {
    # Estimar L-momentos para usar como valores iniciales
    lmomco.fit     <- lmomco::pwm2lmom(lmomco::pwm.ub(x))
    gam.pars.guess <- lmomco::pargam(lmomco.fit, checklmom = TRUE)
    start.params   <- list(shape = unname(gam.pars.guess$para['alpha']),
                           scale = unname(gam.pars.guess$para['beta']))
    
    # Realizar estimacion por metodo ML
    gam.mle.fit       <- fitdistrplus::fitdist(data = x,
                                               distr = 'gamma',
                                               method = 'mle',
                                               keepdata = FALSE,
                                               start = start.params)
    if (is.null(numero.muestras)) {
      # Estimar parametros sin remuestreo
      parametros.ajuste$alpha <- unname(gam.mle.fit$estimate['shape'])
      parametros.ajuste$beta  <- unname(gam.mle.fit$estimate['scale'])
    } else {
      # Realizar bootstrap parametrico para los parametros estimados
      bootstrap <- fitdistrplus::bootdist(f = gam.mle.fit,
                                          bootmethod = "param",
                                          niter = numero.muestras,
                                          silent = TRUE)
      
      # Calcular la mediana de cada parametro
      parametros.remuestreo   <- apply(X = bootstrap$estim, MARGIN = 2, FUN = median)
      parametros.ajuste$alpha <- unname(parametros.remuestreo['shape'])
      parametros.ajuste$beta  <- unname(parametros.remuestreo['scale'])
    }
  }
  
  return (parametros.ajuste)
}

# Ajuste de función de distribución por método basado en Logsplines
AjustarNoParametrico <- function(x = NULL, lbound = NULL, min.tasa.valores.positivos = NULL) {
  # Validar parametros de entrada
  base::stopifnot(is.null(lbound) || is.numeric(lbound))
  base::stopifnot(is.null(min.tasa.valores.positivos) || is.numeric(min.tasa.valores.positivos))
  
  # Verificar que x sea un vector numerico
  if (is.null(x)) {
    # Devolver un objeto de ajuste con valor NA
    return (NA)
  } else {
    base::stopifnot(is.numeric(x))
  }
  
  # En caso de estar definida una tasa minima de valores positivos, verificar tal condicion.
  # Si la condicion no se cumple, devolver NA
  longitud.inicial <- length(x) # Cantidad de elementos antes de eliminar 0s
  if (! is.null(min.tasa.valores.positivos) && any(x == 0)) {
    # Eliminar ceros
    x <- x[which(x > 0)]
    
    # Verificar condicion de minima tasa de valores positivos
    if (length(x) < (min.tasa.valores.positivos * longitud.inicial)) {
      # No se cumple la condicion. Devolver NA
      return (NA)
    }
  }
  rm(longitud.inicial)
  
  # Realizar ajuste
  tryCatch({
    objeto.ajuste <- logspline::logspline(x, lbound = ifelse(is.null(lbound), min(x), lbound),
                                          ubound = max(x), silent = TRUE)
    
    # ATENCION: Hay casos en donde se devuelve objeto de ajuste erroneo.
    # Ej: Error in objeto.ajuste$logl[, 2] : incorrect number of dimensions
    # Para ello se controla que el objeto objeto.ajuste$logl sea una matriz.
    # Si esto no se cumple se asume que no hubo ajuste
    if ((class(objeto.ajuste) != "logspline") || ! is.matrix(objeto.ajuste$logl)) {
      return (NA)
    }
    
    # Devolver parametros como data frame
    return (objeto.ajuste)
  }, error = function(e) {
    cat(e$message, "\n")
    return (NA)
  })
}

# Función de normalización de probabilidad cuando está fuera del intervalo 0-1
NormalizarProbabilidad <- function(prob) {
  if (is.na(prob) || is.nan(prob)) {
    return (as.double(NA))
  } else if (prob > 1) {
    return (1)
  } else if (prob < 0) {
    return (0)
  } else {
    return (prob)
  }
}

# Función para normalizar valor del índice dentro de un intervalo de valores
NormalizarIndice <- function(valor, limites = c(-3, 3)) {
  if (! is.na(valor) && ! is.nan(valor)) {
    if (! is.null(limites)) {
      if (valor > limites[2]) {
        return (limites[2])
      } else if (valor < limites[1]) {
        return (limites[1])
      } else {
        return (valor)
      }
    } else {
      return (valor)
    }
  } else {
    return (as.double(NA))
  }
}

# Función de cálculo de SDI
CalcularSDI <- function(valores, parametros) {
  purrr::map_dfr(
    .x = valores, 
    .f = function(x) {
      # Calcular percentil correspondiente al valor de entrada
      prob.gamma <- NA
      if ((nrow(parametros) == 1) && (as.character(parametros$parametro) == "objeto_ajuste")) {
        # Ajuste no paramétrico
        objeto_ajuste <- dplyr::pull(parametros, valor)[[1]]
        if (! is.null(objeto_ajuste)) {
          prob.gamma <- logspline::plogspline(x, objeto_ajuste)
        }
      } else {
        # Ajuste paramétrico
        parametros.gamma <- ParametrosALista(parametros)
        if (! any(is.na(parametros.gamma))) {
          if (parametros.gamma$prob.0 != 0) {
            prob.gamma <- stats::pgamma(x, shape = parametros.gamma$alpha, scale = parametros.gamma$beta)
            prob.gamma <- ifelse(prob.gamma == 0,
                                 parametros.gamma$prob.media.0,
                                 parametros.gamma$prob.0 + ((1 - parametros.gamma$prob.0) * prob.gamma))
          } else {
            # No hay ceros en el periodo de referencia
            # Si x = 0, se toma como valor de entrada 0.01
            y          <- ifelse(x == 0, 0.01, x)
            prob.gamma <- stats::pgamma(y, shape = parametros.gamma$alpha, scale = parametros.gamma$beta)
          }
        }
      }
      
      # Devolver resultados
      prob.gamma <- NormalizarProbabilidad(prob.gamma)
      if (! is.na(prob.gamma)) {
        sdi       <- NormalizarIndice(stats::qnorm(prob.gamma, mean = 0, sd = 1))
        percentil <- 100 * prob.gamma
      } else {
        sdi       <- as.double(NA)
        percentil <- as.double(NA)
      }
      
      return (tibble::tibble(sdi = sdi, percentil = percentil))   
    }
  )
}
# ------------------------------------------------------------------------------

# -----------------------------------------------------------------------------#
# --- Ajuste de PDF para cada estación, ancho de ventana y péntada de fin ----
# -----------------------------------------------------------------------------#

# Parametros para el metodo de ajuste
parametros_metodo_ajuste <- config$metodos_ajuste[[config$metodo_ajuste]]

# Definir el rango de años para período de referencia
anos_referencia <- seq(from = config$periodo_referencia$desde,
                       to = config$periodo_referencia$hasta) %>%
  data.frame(ano_fin = .)

ajustes <- purrr::pmap_dfr(
  .l = dplyr::distinct(caudales_agregados, estacion, ancho_ventana, pentada_fin),
  .f = function(estacion, ancho_ventana, pentada_fin) {
    # Seleccionar datos para ajuste
    caudales_ajuste <- caudales_agregados %>%
      # Filtro por estacion, ancho de ventana y pentada de fin
      dplyr::filter(estacion == !! estacion & ancho_ventana == !! ancho_ventana &
                    pentada_fin == !! pentada_fin) %>%
      # Calculo de ano en base a fecha_hasta
      dplyr::mutate(ano_fin = lubridate::year(fecha_hasta)) %>%
      # Seleccionar datos dentro del período de referencia
      dplyr::inner_join(anos_referencia, by = c("ano_fin")) %>%
      # Eliminar valores nulos
      dplyr::filter(! is.na(caudal_agregado)) %>%
      # Obtener valores de caudales
      dplyr::pull(caudal_agregado)
    
    # Calcular la cantidad mínima de valores necesarios para el ajuste
    minimos_valores_necesarios <- round(nrow(anos_referencia) * (1 - config$periodo_referencia$maxima_proporcion_faltantes))
    if (length(caudales_ajuste) >= minimos_valores_necesarios) {
      if (config$metodo_ajuste == "ML-SinRemuestreo") {
        parametros_ajuste <- AjustarMaximaVerosimilitudGamma(x = caudales_ajuste, 
                                                             min.tasa.valores.positivos = parametros_metodo_ajuste$mimima_tasa_positivos) %>%
          ParametrosATibble()
      } else if (config$metodo_ajuste == "NoParametrico") {
        objeto_ajuste     <- AjustarNoParametrico(x = caudales_ajuste, lbound = parametros_metodo_ajuste$lbound,
                                                  min.tasa.valores.positivos = parametros_metodo_ajuste$mimima_tasa_positivos)
        parametros_ajuste <- tibble::tibble(parametro = "objeto_ajuste", valor = list(objeto_ajuste))
      } else {
        stop(paste0("Método de ajuste desconocido: ", config$metodo_ajuste))
      }
    } else {
      # No hay datos suficientes para ajuste
      if (config$metodo_ajuste == "ML-SinRemuestreo") {
        parametros_ajuste <- list(alpha = as.double(NA), beta = as.double(NA),
                                  prob.0 = as.double(NA), prob.media.0 = as.double(NA)) %>%
          ParametrosATibble()
      } else if (config$metodo_ajuste == "NoParametrico") {
        parametros_ajuste <- tibble::tibble(parametro = "objeto_ajuste", valor = NA)
      } else {
        stop(paste0("Método de ajuste desconocido: ", config$metodo_ajuste))
      }
    }
    
    # Agregado datos de estacion, ancho de ventana y pentada de fin
    parametros_ajuste <- parametros_ajuste %>%
      dplyr::mutate(estacion = estacion, ancho_ventana = ancho_ventana,
                    pentada_fin = pentada_fin) %>%
      dplyr::select(estacion, ancho_ventana, pentada_fin, parametro, valor)
    
  }
)

readr::write_csv(x = ajustes, path = paste0("work/ajustes.csv"))
# ------------------------------------------------------------------------------

# -----------------------------------------------------------------------------#
# --- Cálculo de SDI para cada estación, ancho de ventana y péntada de fin ----
# -----------------------------------------------------------------------------#

indices <- purrr::pmap_dfr(
  .l = dplyr::distinct(caudales_agregados, estacion, ancho_ventana, pentada_fin),
  .f = function(estacion, ancho_ventana, pentada_fin) {
    # Obtener parametros de ajuste
    parametros <- ajustes %>%
      dplyr::filter(estacion == !! estacion & ancho_ventana == !! ancho_ventana &
                      pentada_fin == !! pentada_fin)
    
    # Seleccionar datos para calcular indices
    caudales_calculo <- caudales_agregados %>%
      # Filtro por estacion, ancho de ventana y pentada de fin
      dplyr::filter(estacion == !! estacion & ancho_ventana == !! ancho_ventana &
                      pentada_fin == !! pentada_fin)
    
    # Calcular SDI
    dplyr::bind_cols(
      caudales_calculo,
      CalcularSDI(valores = dplyr::pull(caudales_calculo, caudal_agregado), parametros = parametros)
    )
  }
)
id.estacion <- 1653
ancho.ventana <- 6
serieTemporalSPI <- indices %>% filter(estacion == id.estacion, ancho_ventana == ancho.ventana)
readr::write_csv(x = indices, path = paste0("output/indices.csv"))

# ------------------------------------------------------------------------------
# test <- indices %>% 
#   filter(estacion == 119, ancho_ventana == 6, pentada_fin == 8)
# 
# test2 <- indices %>% 
#   filter(estacion == 133, ancho_ventana == 6)
# 
# a <- ajustes %>% 
#   filter(is.na(valor),estacion == 44, ancho_ventana == 6)
