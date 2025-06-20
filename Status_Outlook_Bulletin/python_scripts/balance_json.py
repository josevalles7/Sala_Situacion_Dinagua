import pandas as pd

# path of the results
csv_path = "modelling_result_codcuenca_2.csv"

# Read the CSV
df = pd.read_csv(csv_path, encoding="latin1")

# Round the numerical fields to two decimals
for col in df.select_dtypes(include=["float", "int"]).columns:
    df[col] = df[col].map(lambda x: round(x, 2))

# Convert to json
json_data = df.to_json(orient="records", force_ascii=False, indent=2)

# Save the JSON
json_path = "modelling_result_codcuenca_2.json"
with open(json_path, "w", encoding="utf-8") as f:
    f.write(json_data)

print(f"Archivo JSON generado exitosamente: {json_path}")