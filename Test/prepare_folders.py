import os
from datetime import datetime


def print_info(fnc):
    def wrapper(*args, **kwargs):
        print('---------------------------------------------------')
        print('Proceso de creación de carpetas para cierre contable')
        print('---------------------------------------------------')
        # Ejecuta la función decorada
        resultado = fnc(*args, **kwargs)
        print('---------------------------------------------------')
        print('Terminó el proceso de creación de carpetas')
        print('---------------------------------------------------')
        return resultado
    return wrapper

def create_folder(path):
    # Crea la carpeta en el path absoluto
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Carpeta '{path}' creada con éxito.")
    else:
        print(f"La carpeta '{path}' ya existe.")

def get_dates():
    month_dic = {
        "january": "Enero",
        "february": "Febrero",
        "march": "Marzo",
        "april": "Abril",
        "may": "Mayo",
        "june": "Junio",
        "july": "Julio",
        "august": "Agosto",
        "september": "Septiembre",
        "october": "Octubre",
        "november": "Noviembre",
        "december": "Diciembre"
    }
    now = datetime.now()
    month_ = now.strftime('%B').lower()
    month_ = month_dic[month_]
    year_ = now.year

    return (month_,year_)

def get_month_number():
    return datetime.now().strftime('%m')
@print_info
def create_folders(device='dell'):  # mac, dell, rog
    dates_ = get_dates()

    if device == 'dell':
        year_path = fr'C:\Users\Sergio Gil Guerrero\Documents\WonderBrands\Finanzas\{dates_[1]}'
        month_path = fr'C:\Users\Sergio Gil Guerrero\Documents\WonderBrands\Finanzas\{dates_[1]}\{dates_[0]}'
        conciled_path = fr'C:\Users\Sergio Gil Guerrero\Documents\WonderBrands\Finanzas\{dates_[1]}\{dates_[0]}\Conciliadas'
        walmart_path = fr'C:\Users\Sergio Gil Guerrero\Documents\WonderBrands\Finanzas\{dates_[1]}\{dates_[0]}\Walmart'
        xmls_path = fr'C:\Users\Sergio Gil Guerrero\Documents\WonderBrands\Finanzas\{dates_[1]}\{dates_[0]}\Walmart\xmls_walmart'
    elif device == 'mac':
        year_path = f'/Users/sergio/Documents/Trabajo/Wonderbrands/Finanzas/{dates_[1]}'
        month_path = f'/Users/sergio/Documents/Trabajo/Wonderbrands/Finanzas/{dates_[1]}/{dates_[0]}'
        conciled_path = f'/Users/sergio/Documents/Trabajo/Wonderbrands/Finanzas/{dates_[1]}/{dates_[0]}/Conciliadas'
        walmart_path = f'/Users/sergio/Documents/Trabajo/Wonderbrands/Finanzas/{dates_[1]}/{dates_[0]}/Walmart'
        xmls_path = f'/Users/sergio/Documents/Trabajo/Wonderbrands/Finanzas/{dates_[1]}/{dates_[0]}/Walmart/xmls_walmart'
    elif device == 'rog': # PENDIENTE DE CAMBIO
        year_path = fr'C:\Users\Sergio Gil Guerrero\Documents\WonderBrands\Finanzas\{dates_[1]}'
        month_path = fr'C:\Users\Sergio Gil Guerrero\Documents\WonderBrands\Finanzas\{dates_[1]}\{dates_[0]}'
        conciled_path = fr'C:\Users\Sergio Gil Guerrero\Documents\WonderBrands\Finanzas\{dates_[1]}\{dates_[0]}\Conciliadas'
        walmart_path = fr'C:\Users\Sergio Gil Guerrero\Documents\WonderBrands\Finanzas\{dates_[1]}\{dates_[0]}\Walmart'
        xmls_path = fr'C:\Users\Sergio Gil Guerrero\Documents\WonderBrands\Finanzas\{dates_[1]}\{dates_[0]}\Walmart\xmls_walmart'

    create_folder(year_path)
    create_folder(month_path)
    create_folder(conciled_path)
    create_folder(walmart_path)
    create_folder(xmls_path)

if __name__ == '__main__':
    create_folders()


