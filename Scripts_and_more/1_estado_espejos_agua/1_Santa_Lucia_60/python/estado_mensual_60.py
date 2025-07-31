
import ee
import geemap
import geopandas as gpd
import sys
from datetime import datetime
import calendar

ee.Authenticate()
ee.Initialize(project='ee-t-pohren')

# Definir área de estudio
gdf = gpd.read_file(r"C:\Dinagua\3_Archivos espaciales\CuencasNivel2\c098Polygon.shp")
geom = gdf[gdf["codcuenca"].astype(int) == 60].geometry.iloc[0]
table = ee.Geometry(geom.simplify(100).buffer(0).__geo_interface__)

# Recibir fecha como YYYY-MM
fecha_str = sys.argv[1]  # Ej: '2025-07'

# Calcular primer y último día del mes
anio, mes = map(int, fecha_str.split('-'))
primer_dia = datetime(anio, mes, 1).strftime('%Y-%m-%d')
ultimo_dia = datetime(anio, mes, calendar.monthrange(anio, mes)[1]).strftime('%Y-%m-%d')

# Seteos básicos
start_date = primer_dia
end_date = ultimo_dia
year = ee.Date(start_date).get('year')

# Colección de imágenes Sentinel-2
inicial_filter = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                  .filterDate(start_date, end_date)
                  .filterBounds(table)
                  .map(lambda img: img.clip(table)))

# Colección de probabilidad de nubes
sentinel_clouds = (ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
                  .filterDate(start_date, end_date)
                  .filterBounds(table)
                  .map(lambda img: img.clip(table)))

#Calcula el porcentaje de nubes en la región de interés.
def cloud_percent(image):
    # Recortar imagen a la región de interés
    image_interest = image

    # Crear máscara de nubes basada en el umbral
    is_cloud = image_interest.gt(cloud_probability_threshold).rename('cloud_mask')

    # Contar píxeles con nubes
    cloud_pixels = is_cloud.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=table,
        scale=10,
        maxPixels=1e9
    ).get('cloud_mask')

    # Contar total de píxeles válidos
    total_pixels = is_cloud.reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=table,
        scale=10,
        maxPixels=1e9
    ).get('cloud_mask')

    # Calcular porcentaje de nubes
    cloud_percentage = ee.Number(cloud_pixels).divide(total_pixels).multiply(100)

    return image.set('cloudPercentage', cloud_percentage)
# Asocia el porcentaje de nubes a las imágenes ópticas Sentinel-2.
def add_cloud_percentage_property(image):
    # Obtener el índice de la imagen
    index = image.get('system:index')

    # Buscar la imagen correspondiente de probabilidad de nubes
    cloud_image = (percent_cloud_collection
                   .filterMetadata('system:index', 'equals', index)
                   .first())

    # Obtener el porcentaje de nubes calculado
    cloud_percentage = ee.Number(cloud_image.get('cloudPercentage'))

    return image.set('cloudPercentage', cloud_percentage)

    # Contar píxeles válidos usando banda B4 como referencia
    valid_pixels = (image.select('B4')
                    .unmask(-9999)
                    .neq(-9999)
                    .reduceRegion(
                        reducer=ee.Reducer.sum(),
                        geometry=table,
                        scale=10,
                        maxPixels=1e9
                    ).get('B4'))

    # Contar total de píxeles en la región
    total_pixels = (ee.Image(1)
                    .reduceRegion(
                        reducer=ee.Reducer.sum(),
                        geometry=table,
                        scale=10,
                        maxPixels=1e9
                    ).get('constant'))

    # Calcular porcentaje de cobertura
    coverage = ee.Number(valid_pixels).divide(total_pixels).multiply(100)

    return image.set('coverage_percent', coverage)

def add_area_properties(feature):
    """
    Función auxiliar para calcular áreas de polígonos de agua.
    Debe estar definida fuera de calcular_espejos para evitar problemas de serialización.
    """
    area_m2 = feature.geometry().area(1)
    area_ha = area_m2.divide(10000)
    return feature.set({
        'area_m2': area_m2,
        'area_ha': area_ha
    })

def procesar_composite(image):
    # === 1. Calcular cobertura de píxeles válidos ===
    valid_pixels = (image.select('B4')
                    .unmask(-9999)
                    .neq(-9999)
                    .reduceRegion(
                        reducer=ee.Reducer.sum(),
                        geometry=table,
                        scale=10,
                        maxPixels=1e9
                    ).get('B4'))

    total_pixels = (ee.Image(1)
                    .reduceRegion(
                        reducer=ee.Reducer.sum(),
                        geometry=table,
                        scale=10,
                        maxPixels=1e9
                    ).get('constant'))

    coverage = ee.Number(valid_pixels).divide(total_pixels).multiply(100)
    image = image.set('coverage_percent', coverage)

    # === 2. Calcular cuerpos de agua ===
    image = image.clip(table)

    awei = image.expression(
        '4*(GREEN - SWIR1) - (0.25*NIR + 2.75*SWIR2)', {
            'GREEN': image.select('B3').multiply(0.0001),
            'NIR': image.select('B8').multiply(0.0001),
            'SWIR1': image.select('B11').multiply(0.0001),
            'SWIR2': image.select('B12').multiply(0.0001)
        })

    ndwi = image.normalizedDifference(['B3', 'B8'])
    mndwi = image.normalizedDifference(['B3', 'B11'])

    NDWI = ndwi.lt(0)
    MNDWI = mndwi.lt(0)
    AWEI = awei.lt(0)

    water_combine = AWEI.And(NDWI).And(MNDWI).rename('w')
    water = water_combine.updateMask(water_combine.eq(0))

    water_vectors = water.reduceToVectors(
        geometry=table,
        crs='EPSG:32721',
        maxPixels=1e10,
        scale=20,
        geometryType='polygon',
        eightConnected=True
    )

    water_vectors_con_area = water_vectors.map(add_area_properties)

    grandes = water_vectors_con_area.filter(ee.Filter.gt('area_ha', 10))

    area_total_ha = ee.Algorithms.If(
        grandes.size().gt(0),
        grandes.aggregate_sum('area_ha'),
        -999
    )

    return image.set('areaTotal_ha', area_total_ha)
    # Calcular índice AWEI (Automated Water Extraction Index)
    awei = image.expression(
        '4*(GREEN - SWIR1) - (0.25*NIR + 2.75*SWIR2)', {
            'GREEN': image.select('B3').multiply(0.0001),
            'NIR': image.select('B8').multiply(0.0001),
            'SWIR1': image.select('B11').multiply(0.0001),
            'SWIR2': image.select('B12').multiply(0.0001)
        })
    # Calcular índices normalizados
    ndwi = image.normalizedDifference(['B3', 'B8'])    # Normalized Difference Water Index
    mndwi = image.normalizedDifference(['B3', 'B11'])  # Modified NDWI

    # Crear máscaras binarias (agua = valores negativos)
    NDWI = ndwi.lt(0)
    MNDWI = mndwi.lt(0) 
    AWEI = awei.lt(0)

    # Combinar las tres máscaras (agua debe cumplir los 3 criterios)
    water_combine = AWEI.And(NDWI).And(MNDWI).rename('w')
    water = water_combine.updateMask(water_combine.eq(0))

    # Vectorizar los cuerpos de agua
    water_vectors = water.reduceToVectors(
        geometry=table,
        crs='EPSG:32721',
        maxPixels=1e10,
        scale=20,
        geometryType='polygon',
        eightConnected=True
    )

    # Agregar propiedades de área a cada polígono
    water_vectors_con_area = water_vectors.map(add_area_properties)

    # Filtrar cuerpos de agua grandes
    grandes = water_vectors_con_area.filter(ee.Filter.gt('area_ha', 10))

    # Calcular área total, retornar -999 si no hay cuerpos grandes
    area_total_ha = ee.Algorithms.If(
        grandes.size().gt(0),
        grandes.aggregate_sum('area_ha'),
        -999
    )

    return image.set('areaTotal_ha', area_total_ha)


# Procesamiento de colecciones - Aplicación de filtros de nubosidad
cloud_probability_threshold = 70
percent_cloud_collection = sentinel_clouds.map(cloud_percent)

sentinel_collection_with_cloud_percentage = inicial_filter.map(add_cloud_percentage_property)

cloud_threshold = 5
sentinel_filter_collection = (sentinel_collection_with_cloud_percentage
                              .filter(ee.Filter.lt('cloudPercentage', cloud_threshold)))

print("\n=== RESULTADOS DEL PROCESAMIENTO ===")
print(f"Imágenes originales encontradas: {inicial_filter.size().getInfo()}")
print(f"Imágenes de probabilidad de nubes: {sentinel_clouds.size().getInfo()}")
print(f"Imágenes con nubosidad < {cloud_threshold}%: {sentinel_filter_collection.size().getInfo()}")

# Crear lista de meses (1 a 12)
months = ee.List.sequence(1, 12)

def create_monthly_composite(m):
    # Filtrar imágenes del mes específico
    filtered = sentinel_filter_collection.filter(ee.Filter.calendarRange(m, m, 'month'))

    # Crear composite solo si hay imágenes disponibles
    return ee.Algorithms.If(
        filtered.size().gt(0),
        filtered.median()
                .set('month', m)
                .set('imageCount', filtered.size())
                .set('system:time_start', ee.Date.fromYMD(year, m, 15).millis()),
        None
    )

# Generar composites mensuales
monthly = ee.ImageCollection.fromImages(
    months.map(create_monthly_composite)
).filter(ee.Filter.notNull(['month']))

#print(f"Composites mensuales creados: {monthly.size().getInfo()}")

# Configurar umbral mínimo de cobertura
coverage_threshold = 90  # AJUSTAR <------------------

resultado = monthly.map(procesar_composite).filter(
    ee.Filter.gt('coverage_percent', coverage_threshold)
)

# Obtener fechas en formato legible
fechas = resultado.aggregate_array('system:time_start').map(
    lambda timestamp: ee.Date(timestamp).format('YYYY-MM')
)

# Obtener áreas totales de agua por mes
areas = resultado.aggregate_array('areaTotal_ha')

# Mostrar resultados
print('\n=== RESULTADOS MENSUALES ===')
fechas_list = fechas.getInfo()
areas_list = areas.getInfo()

print('Fechas:     ', fechas_list)
print('Áreas (ha): ', areas_list)

# Mostrar información detallada por mes
"""print(f"\n=== DETALLE POR MES ===")
for i, (fecha, area) in enumerate(zip(fechas_list, areas_list)):
    # Obtener información adicional del composite
    img = ee.Image(resultado.toList(resultado.size()).get(i))
    coverage = img.get('coverage_percent').getInfo()
    img_count = img.get('imageCount').getInfo()

    status = "SIN AGUA DETECTADA" if area == -999 else f"{area:.2f} ha"
    print(f"Mes {fecha}: {status} (Cobertura: {coverage:.1f}%, Imágenes: {img_count})")"""

# Abrir el archivo CSV y agregar la última línea con Fecha y Área
import csv

csv_file_path = r'C:\Dinagua\1_estado_espejos_agua\1_Santa_Lucia_60\fecha_area.csv'

# Abrir el archivo en modo de escritura (append)
with open(csv_file_path, mode='a', newline='', encoding='utf-8') as csv_file:
    csv_writer = csv.writer(csv_file)
    for fecha, area in zip(fechas_list, areas_list):
        csv_writer.writerow([fecha, area])

print(f"\nDatos agregados al archivo CSV: {csv_file_path}")