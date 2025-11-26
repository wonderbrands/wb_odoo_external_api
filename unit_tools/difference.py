import pandas as pd

# Cargar el archivo de Excel
excel_file = r'C:\Users\Sergio Gil Guerrero\Downloads\POS.xlsx'
df = pd.read_excel(excel_file)

# Obtener los valores únicos de cada columna
valores_columna1 = set(df['columna1'].unique())
valores_columna2 = df['columna2']

# Función para comprobar si el valor está en valores_no_en_columna1
cont = 0
def esta_en_columna1(valor):
    if valor not in valores_columna1:
        print(cont, valor)
        return valor


# Crear la nueva columna con los resultados
df['resultados'] = df['columna2'].apply(esta_en_columna1)

# Guardar el DataFrame actualizado en un nuevo archivo Excel
excel_resultado = r'C:\Users\Sergio Gil Guerrero\Downloads\POS_2.xlsx'
df.to_excel(excel_resultado, index=False)

# Imprimir los valores encontrados
print("Valores en columna2 que no están en columna1:")

