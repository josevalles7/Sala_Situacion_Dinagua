# %% [markdown]
# # Automatic Dinagua's Flood Report

# %%
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Cm, Inches, Mm, Emu
import xlwings as xw
from jinja2 import Environment, BaseLoader
import locale

# %%
# Configura la configuración regional para español
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

# %%
excel_file = 'database_report.xlsx' 
template_file = 'doc_master.docx'

# %%
doc = DocxTemplate(template_file)
# placeholder_1 = InlineImage(doc,'Placeholders/Placeholder_1.png',Inches(8.62))

# %%
# Open the excel file using xlwings
wb = xw.Book(excel_file)
# select the excel sheet that contains the data
sheet = wb.sheets['INICIO']
# From the Excel Sheet select the cell range 
# context = sheet.range('B2').options(dict,expand='table',numbers=float).value
entero = int(sheet.range('C2').value)
fecha_emision = sheet.range('C3').value
fecha_ayer = sheet.range('C4').value
fecha_anteayer = sheet.range('C5').value
fecha_pronos1 = sheet.range('C6').value
fecha_pronos2 = sheet.range('C7').value
fecha_pronos3 = sheet.range('C8').value
titulo = sheet.range('C9').value


# %%
# Ajusta el formato de las fechas
fecha_emision = fecha_emision.strftime('%A, %d de %B de %Y').encode('latin-1').decode('utf-8')
fecha_ayer = fecha_ayer.strftime('%A, %d de %B de %Y').encode('latin-1').decode('utf-8')
fecha_anteayer = fecha_anteayer.strftime('%A, %d de %B de %Y').encode('latin-1').decode('utf-8')

fecha_pronos1 = fecha_pronos1.strftime('%A, %d de %B de %Y').encode('latin-1').decode('utf-8')
fecha_pronos2 = fecha_pronos2.strftime('%A, %d de %B de %Y').encode('latin-1').decode('utf-8')
fecha_pronos3 = fecha_pronos3.strftime('%A, %d de %B de %Y').encode('latin-1').decode('utf-8')

# %%
# Río Yí
sheet_yi = wb.sheets['YI']
context_yi = sheet_yi.range('B2').options(dict,expand='table',numbers=float).value
# Río Cuareim
sheet_cuareim = wb.sheets['CUAREIM']
context_cuareim = sheet_cuareim.range('B2').options(dict,expand='table',numbers=float).value
# Río Santa Lucia
sheet_lucia = wb.sheets['SANTALUCIA']
context_lucia = sheet_lucia.range('B2').options(dict,expand='table',numbers=float).value
# Río Uruguay
sheet_uy = wb.sheets['URUGUAY']
context_uy = sheet_uy.range('B2').options(dict,expand='table',numbers=float).value
# Río Negro
sheet_negro = wb.sheets['NEGRO']
context_negro = sheet_negro.range('B2').options(dict,expand='table',numbers=float).value

# %%
context = {
    'numero_id': entero,
    'fecha_emision': fecha_emision,
    'fecha_48': fecha_ayer,
    'fecha_72': fecha_anteayer,
    'fecha_pronos_24': fecha_pronos1,
    'fecha_pronos_48': fecha_pronos2,
    'fecha_pronos_72': fecha_pronos3,
    'titulo': titulo
    }
context.update(context_yi)
context.update(context_cuareim)
context.update(context_lucia)
context.update(context_uy)
context.update(context_negro)
print(context)

# %%
doc.replace_pic('placeholder_1.png','pronostico_hidro.png')

# %%
# Renderiza la plantilla con el formato adecuado
env = Environment(loader=BaseLoader())
env.filters['strftime'] = lambda dt, fmt: dt.strftime(fmt)
doc.render(context, jinja_env=env)

# %%
output_file = f'Informe_Situacion_Pronostico_{entero}.docx'
print(output_file)

# %%
# Guarda el documento resultante
doc.save(output_file)
wb.close()

