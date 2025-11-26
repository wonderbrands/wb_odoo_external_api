# import pandas as pd
#
#
# def find_differences(file_path, column1, column2):
#     # Leer el archivo de Excel
#     df = pd.read_excel(file_path)
#
#     # Convertir las columnas a conjuntos para encontrar las diferencias
#     set1 = set(df[column1])
#     set2 = set(df[column2])
#
#     # Encontrar las diferencias entre los conjuntos
#     differences1 = set1.symmetric_difference(set2)
#
#     return differences1
#
#
# # Ruta del archivo Excel
# file_path = r'C:\Users\Sergio Gil Guerrero\Downloads\Book1.xlsx'
#
# # Nombres de las columnas que quieres comparar
# columna1 = 'A'
# columna2 = 'B'
#
# # Encontrar las diferencias entre las columnas
# diferencias1 = find_differences(file_path, columna1, columna2)
#
# # Imprimir las diferencias encontradas
# print("Diferencias en Columna1:", diferencias1)
#


import pandas as pd


def find_differences(file_path, column1, column2):
    # Leer el archivo de Excel
    df = pd.read_excel(file_path)

    # Obtener conjuntos de valores únicos de cada columna
    set1 = set(df[column1])
    set2 = set(df[column2])

    # Encontrar las órdenes que están en set1 pero no en set2
    differences = set1 - set2

    return differences


# Ruta del archivo Excel
file_path = r'C:\Users\Sergio Gil Guerrero\Downloads\Book1.xlsx'

# Nombres de las columnas que quieres comparar
columna1 = 'A'
columna2 = 'B'

# Encontrar las órdenes que están en set1 pero no en set2
ordenes_diferentes = find_differences(file_path, columna1, columna2)

# Imprimir las órdenes encontradas
print("Órdenes en set1 pero no en set2:")
print(ordenes_diferentes)
print(len(ordenes_diferentes))