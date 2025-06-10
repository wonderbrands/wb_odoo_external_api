# Miguel Alejandro Sánchez Acosta
# alex@wonderbrands.co
# Data
# Qiseth
# Script that gets and stores everyday's invoices from SAT website. It only needs manual credentials.

from datetime import datetime, date, timedelta

start_date = datetime.now()

print('')
print('Process started at:')
print(start_date)
print('')

print(
    '------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------')
print('Importing libraries.')
print('')

import time

start_time = time.time()
import zipfile
import os, glob
import xml.etree.cElementTree as ET
import MySQLdb

import random
import sys
import set666 as creds

import prepare_folders as prep

print(
    '------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------')
print('Connect to MySQL db.')
print(time.time() - start_time)
print('')

db = MySQLdb.connect(creds.wbh, creds.wbu, creds.wbp, 'finance', local_infile=True)
cursor = db.cursor()

db.set_character_set('utf8mb4')
cursor.execute('SET NAMES utf8mb4;')
cursor.execute('SET CHARACTER SET utf8mb4;')
cursor.execute('SET character_set_connection=utf8mb4;')

print(
    '------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------')
print('Insert downloaded items in db.')
print(time.time() - start_time)
print('')

yday = 20250401
dbfore = 20250430
search_date = yday

# ******************
# MES DE EJECUCIÓN
month, year = prep.get_dates()
year = str(year)
# ******************

# ----------------------------------------------------------------
### Mes y año manual si se ejecuta en el mes posterior pero para efecto contable del mes anterior.
month = "Mayo"
year = "2025"
# ----------------------------------------------------------------

print('******************')
print(month, year)
print('******************')

# REVISAR QUE EXISTA LA RUTA DE LOS XML'S !!!
os.chdir(f'C:/Users/Sergio Gil Guerrero/Documents/WonderBrands/Finanzas/{year}/{month}/Walmart/xmls_walmart')

for file in glob.glob("*.xml")[0:]:
    try:
        tree = ET.parse(file)
    except Exception as e:
        print(f"Error en archivo {file}: {e}")

    root = tree.getroot()

    fecha = root.get('Fecha')
    lugar = root.get('LugarExpedicion')
    folio = root.get('Folio')
    serie = root.get('Serie')
    tipo = root.get('TipoDeComprobante')
    metodo_de_pago = root.get('MetodoPago')
    condiciones_de_pago = root.get('CondicionesDePago')
    forma_de_pago = root.get('FormaPago')
    moneda = root.get('Moneda')
    tipo_de_cambio = root.get('TipoCambio')
    subtotal = root.get('SubTotal')
    total = root.get('Total')

    try:
        rfc = root.find('{http://www.sat.gob.mx/cfd/3}Emisor').get('Rfc')
        nombre = root.find('{http://www.sat.gob.mx/cfd/3}Emisor').get('Nombre')
        uso = root.find('{http://www.sat.gob.mx/cfd/3}Receptor').get('UsoCFDI')
        rfc_rec = root.find('{http://www.sat.gob.mx/cfd/3}Receptor').get('Rfc')
        nombre_rec = root.find('{http://www.sat.gob.mx/cfd/3}Receptor').get('Nombre')

    except AttributeError:
        rfc = root.find('{http://www.sat.gob.mx/cfd/4}Emisor').get('Rfc')
        nombre = root.find('{http://www.sat.gob.mx/cfd/4}Emisor').get('Nombre')
        uso = root.find('{http://www.sat.gob.mx/cfd/4}Receptor').get('UsoCFDI')
        rfc_rec = root.find('{http://www.sat.gob.mx/cfd/4}Receptor').get('Rfc')
        nombre_rec = root.find('{http://www.sat.gob.mx/cfd/4}Receptor').get('Nombre')
    uuid = file.replace('.xml', '')

    data = uuid, file, fecha, lugar, folio, serie, rfc, nombre, uso, tipo, metodo_de_pago, condiciones_de_pago, forma_de_pago, moneda, tipo_de_cambio, subtotal, total, rfc_rec, nombre_rec, search_date

    try:
        cursor.execute(
            "insert into finance.sr_sat_emitidas (uuid, file, fecha, lugar, folio, serie, rfc, nombre, uso, tipo, metodo_de_pago, condiciones_de_pago, forma_de_pago, moneda, tipo_de_cambio, subtotal, total, rfc_rec, nombre_rec, search_date) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ",
            (uuid, file, fecha, lugar, folio, serie, rfc, nombre, uso, tipo, metodo_de_pago, condiciones_de_pago,
             forma_de_pago, moneda, tipo_de_cambio, subtotal, total, rfc_rec, nombre_rec, search_date))
        db.commit()

        try:
            for item in root.find('{http://www.sat.gob.mx/cfd/3}Conceptos'):
                descr = item.get('Descripcion')
                q = item.get('Cantidad')
                valor = item.get('ValorUnitario')
                importe = item.get('Importe')
                descuento = item.get('Descuento')
                uuid = file.replace('.xml', '')

                data = uuid, file, descr, q, valor, importe, descuento, fecha, rfc, nombre, search_date

                cursor.execute(
                    "insert into finance.sr_sat_emitidas_desc (uuid, file, descr, q, valor, importe, descuento, fecha, rfc, nombre, search_date) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ",
                    (uuid, file, descr, q, valor, importe, descuento, fecha, rfc, nombre, search_date))
                db.commit()

        except TypeError:
            for item in root.find('{http://www.sat.gob.mx/cfd/4}Conceptos'):
                descr = item.get('Descripcion')
                q = item.get('Cantidad')
                valor = item.get('ValorUnitario')
                importe = item.get('Importe')
                descuento = item.get('Descuento')
                uuid = file.replace('.xml', '')

                data = uuid, file, descr, q, valor, importe, descuento, fecha, rfc, nombre, search_date

                cursor.execute(
                    "insert into finance.sr_sat_emitidas_desc (uuid, file, descr, q, valor, importe, descuento, fecha, rfc, nombre, search_date) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ",
                    (uuid, file, descr, q, valor, importe, descuento, fecha, rfc, nombre, search_date))
            db.commit()

    except MySQLdb.IntegrityError:
        print(file + ' is already in the DB.')

print(
    '------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------')
print('Update year, ym and date.')
print(time.time() - start_time)
print('')

q_u = "update finance.sr_sat_emitidas set year = year(fecha), yearmonth = extract(year_month from fecha), date = date(fecha)"
cursor.execute(q_u)

db.commit()

print('')
print(
    '****** ****** ****** ********************************************************************** ****** ****** ******')
print('****** ****** ******  With -' + str(dbfore) + ' days from today, ' + str(
    yday) + ' was extracted and inserted in DB. ****** ****** ******')
print(
    '****** ****** ****** ********************************************************************** ****** ****** ******')
print('')

print(
    '------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------ ------')
print("That's all folks!")
print('')
print('The process lasted:')
print("--- %s seconds ---" % (time.time() - start_time))
print('')
print('Process finished at:')
print(datetime.now())
print('')

NdGT = 'Being able to adapt our behviour to challenges is as good a definition of intelligence as any I know. -- Neil deGrasse Tyson'
RL = 'It is good to travel with hope and courage but it is better to travel with knowledge. -- Ragnar Lothbrok'
JP = 'Every bit of learning is a little death. Every bit of new information challenges a previous conception, forcing it to dissolve into chaos before it can be reborn as something better. -- Jordan Peterson'
RD = 'Evidence is the only good reason to believe anything. -- Richard Dawkins'
RF = 'Know how to solve every problem that has been solved. -- Richard Feynman'
CS = 'Absence of evidence is not evidence of absence. -- Carl Sagan'

closing = [RL, NdGT, JP, RD, RF, CS]
print('')
print(random.choice(closing))

# QUERY DE VERIFICACION DE XML EN BASE DE DATOS

# select date(fecha), count(1)
# from finance.sr_sat_emitidas
# where year(fecha) = 2024
# group by 1
# order by 1 desc