import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches
import pandas as pd

# Configuración de rutas
folder = r"C:\Dinagua\1_estado_espejos_agua\1_Laguna_Merin"
input_file = f"{folder}\\fecha_area.csv"

# Cargar datos
df = pd.read_csv(input_file, sep=",")
df["fecha"] = pd.to_datetime(df["fecha"], format="%Y-%m")
df = df.dropna(subset=["area"])

# Definir percentiles y colores
percentiles = [10, 25, 40, 60, 75, 90]
colors = [
    "#C90000",         # < percentil 10
    "#EB8B13",      # < percentil 25
    "#FFF94F",      # < percentil 40
    "#EBEBEB",        # < percentil 60
    "#57E9FF",      # < percentil 75
    "#137BEB",        # < percentil 90
    "#0000C9"       # >= percentil 90
]

# Calcular valores de percentiles
values = np.percentile(df["area"], percentiles)

# Asignar color a cada fila según el percentil
def get_color(area):
    if area < values[0]:
        return colors[0]
    elif area < values[1]:
        return colors[1]
    elif area < values[2]:
        return colors[2]
    elif area < values[3]:
        return colors[3]
    elif area < values[4]:
        return colors[4]
    elif area < values[5]:
        return colors[5]
    else:
        return colors[6]

df["color"] = df["area"].apply(get_color)

# Crear gráfico
fig, ax = plt.subplots(figsize=(10, 6))

# Pintar el fondo según los percentiles
bounds = [df["area"].min()] + list(values) + [df["area"].max()]
for i in range(len(colors)):
    ax.axhspan(bounds[i], bounds[i+1], facecolor=colors[i], alpha=0.2)

# Graficar línea de trayectoria del área
ax.plot(df["fecha"], df["area"], color="black", linewidth=1)

# Graficar observaciones
ax.scatter(df["fecha"], df["area"], c=df["color"], s=20, edgecolor="white", linewidth=0.5)


# Líneas horizontales para los percentiles
for v in values:
    ax.axhline(y=v, color="black", linestyle="--", linewidth=0.5, alpha=0.5)


percentil_labels = [
    "< 10%", "< 25%", "< 40%", "< 60%", "< 75%", "< 90%", "≥ 90%"
][::-1] 

handles = [
    mpatches.Patch(color=colors[i], label=percentil_labels[i])
    for i in range(len(colors))
]

# Configuración de gráfico
ax.set_title("Área a lo largo del tiempo")
ax.set_xlabel("Fecha")
ax.set_ylabel("Área (m²)")
ax.legend(handles=handles, title="Color por percentil", loc="upper left")
ax.grid(False)
plt.tight_layout()
plt.show()