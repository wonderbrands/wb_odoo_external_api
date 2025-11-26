import os
import shutil
from concurrent.futures import ThreadPoolExecutor
import time
from tqdm import tqdm
from datetime import datetime, timedelta

__description__ = """
        Este script realiza la reubicacion de archivos xml de la carpeta root del drive compartido (en la cual se tienen sub
        carpetas las cuales coresponden a cada dia) a una carpeta general. Estas carpetas son credas por un script que crewlea 
        al sat y descarga los xml.
        
        Este script solo se utiliza cuando esten todas las sub carpetas con los xml.
"""

def copy_file(file_path, destination_directory, pbar):
    """
    Toma la ruta de un archivo, la carpeta de destino y una barra de progreso (tqdm),
     luego copia el archivo a la carpeta de destino y actualiza la barra de progreso.
    """
    file_name = os.path.basename(file_path)
    shutil.copy(file_path, os.path.join(destination_directory, file_name))
    #if pbar != True:
    pbar.update(1)  # Actualizamos la barra de progreso cada vez que se copia un archivo
    #print(f"Archivo '{file_name}' copiado a la carpeta raíz.")

def generate_date_range(dates):
    """
    Genera una lista de fechas dentro de un rango dado.
    Esto se utiliza para verificar si una subcarpeta está dentro del rango de fechas especificado.
    """
    # Convertir las fechas de texto a objetos de fecha
    start_date = datetime.strptime(dates[0], '%Y%m%d')
    end_date = datetime.strptime(dates[1], '%Y%m%d')

    # Lista para almacenar las fechas dentro del rango
    date_range = []

    # Generar las fechas dentro del rango
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date.strftime('%Y%m%d'))
        current_date += timedelta(days=1)

    return date_range

def stay_in(string, dates):
    """
    Verifica si una cadena (en este caso, el nombre de una subcarpeta) está dentro del rango de fechas especificado.
    """
    lst = generate_date_range(dates)
    return any(string in element for element in lst)

def copy_files_into_root_parallel(root_directory, dates):
    """
    Recorre todas las subcarpetas en la carpeta raíz. Si una subcarpeta está dentro del rango de fechas especificado,
    agrega todos los archivos XML de esa subcarpeta a una lista. Luego, utiliza un ThreadPoolExecutor para copiar estos
    archivos en paralelo a la carpeta raíz, mostrando una barra de progreso.
    """
    files_to_copy = []
    in_range = False
    # Obtener todas las rutas completas de los archivos en las subcarpetas
    for root_path, _, files in os.walk(root_directory): #Acceder a los elentos de la tupla (se les resta y suma una unidad por los rangos en python)
        if stay_in(os.path.basename(root_path), dates):  #La ruta actual esta en el rango de fechas? /  dates -> Rango de fechas
            for file in files:
                if file != 'desktop.ini':  # Verificar si el archivo no es desktop.ini
                    full_file_path = os.path.join(root_path, file)
                    files_to_copy.append(full_file_path)
        #else:
         #   pass

    # Crear una única barra de progreso para el total de archivos
    with tqdm(total=len(files_to_copy), desc="Extracting files", unit="file") as pbar:
        with ThreadPoolExecutor() as executor:
            for file in files_to_copy:
                executor.submit(copy_file, file, root_directory, pbar)
def copy_files_into_root(root_directory):
    """
    Realiza la misma operación que copy_files_into_root_parallel, pero de forma secuencial, sin utilizar paralelismo.
    """
    # Obtener todas las rutas completas de los archivos en las subcarpetas
    files_to_copy = []
    for root_path, directories, files in os.walk(root_directory):
        for file in files:
            if file != 'desktop.ini':  # Verificar si el archivo no es desktop.ini
                # Ruta completa del archivo
                full_file_path = os.path.join(root_path, file)
                files_to_copy.append(full_file_path)

    # Crear una única barra de progreso para el total de archivos
    with tqdm(total=len(files_to_copy), desc="Extracting files", unit="file") as pbar:
                for file in files_to_copy:
                    copy_file(file, root_directory, pbar)

def remove_files(directory):
    """
    Elimina todos los archivos en una carpeta dada.
    :param directory: Ruta de donde se eliminaran todos los archivos
    """
    # Iterar sobre todos los elementos en la carpeta
    for element in os.listdir(directory):
        element_path = os.path.join(directory, element)
        # Verificar si es un archivo
        if os.path.isfile(element_path):
            # Eliminar el archivo
            os.remove(element_path)
            print(f"File '{element}' removed.")
        # Si es una carpeta, no hacer nada
        elif os.path.isdir(element_path):
            continue

if __name__ == "__main__":

    # Carpeta raíz (ruta completa)
    root_directory = r'G:\.shortcut-targets-by-id\1vsZk0-0Cd1FnEKNQlXzq3EuSgg6ZRgtP\2024\202402'
    dates = ('20240201','20240227') #Rango de fechas (inicio:fin)

    # Llamar a la función para mover los archivos de las subcarpetas a la carpeta raíz
    start = time.time()
    copy_files_into_root_parallel(root_directory, dates) #avg = 78 files/seg
    #copy_files_into_root(root_directory) #avg = 45 files/seg      NO esta actualizada para los rangos, extrae los archivos de todas las carpetas
    end = time.time()
    print(f"Tiempo de ejecución: {end-start} segundos")

    # Ruta de la carpeta a limpiar
    folder_to_clean = r'G:\.shortcut-targets-by-id\1vsZk0-0Cd1FnEKNQlXzq3EuSgg6ZRgtP\2024\202402'
    #remove_files(folder_to_clean)

    #UPDATE 13-03
