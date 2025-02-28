from email.message import EmailMessage
from email.utils import make_msgid
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from pprint import pprint
from email import encoders
from tqdm import tqdm
import time
import json
import jsonrpc
#import jsonrpclib
import random
import urllib.request
import getpass
import http
# import requests
import logging
import zipfile
import socket
import os
import locale
import xmlrpc.client
import base64
import openpyxl
# import xlrd
import pandas as pd
import MySQLdb
import mysql.connector
import smtplib
import ssl
import email
import datetime
from concurrent.futures import ThreadPoolExecutor

from Test import extract_orders as e_o

from Test import prepare_folders as prep

print('================================================================')
print('BIENVENIDO AL PROCESO DE FACTURACIÓN WALMART')
print('================================================================')
print('SCRIPT DE CREACIÓN DE FACTURAS GLOBALES')
print('================================================================')
today_date = datetime.datetime.now()
dir_path = os.path.dirname(os.path.realpath(__file__))
print('Fecha:' + today_date.strftime("%Y-%m-%d %H:%M:%S"))
#Archivo de configuración - Use config_dev.json si está haciendo pruebas
#Archivo de configuración - Use config.json cuando los cambios vayan a producción

# ***********************************************
# ARCHIVO DE CONFIGURACIÓN
config_file = 'config.json'
# ***********************************************

def get_odoo_access():
    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)

    return config['odoo']
def get_psql_access():
    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)

    return config['psql']
def get_email_access():
    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)

    return config['email']
def invoice_create_global(excel_file_path, execution_number):
    # Obtener credenciales
    odoo_keys = get_odoo_access()
    psql_keys = get_psql_access()
    email_keys = get_email_access()
    # odoo
    server_url = odoo_keys['odoourl']
    db_name = odoo_keys['odoodb']
    username = odoo_keys['odoouser']
    password = odoo_keys['odoopassword']
    # correo
    smtp_server = email_keys['smtp_server']
    smtp_port = email_keys['smtp_port']
    smtp_username = email_keys['smtp_username']
    smtp_password = email_keys['smtp_password']

    print('----------------------------------------------------------------')
    print('Conectando API Odoo')
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(server_url))
    uid = common.authenticate(db_name, username, password, {})
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(server_url))
    print('Conexión con Odoo establecida')
    print('----------------------------------------------------------------')
    print('Conectando a Mysql')
    # Connect to MySQL database
    mydb = mysql.connector.connect(
        host=psql_keys['dbhost'],
        user=psql_keys['dbuser'],
        password=psql_keys['dbpassword'],
        database=psql_keys['database']
    )
    mycursor = mydb.cursor()
    print(f"Leyendo query")
    print('----------------------------------------------------------------')
    print('Vaya por un tecito o un café porque este proceso tomará algo de tiempo')
    print('----------------------------------------------------------------')
    #mycursor.execute("SELECT so_name FROM sr_so_global_invoice")
    #mycursor.execute("""SELECT txn_id
    #                    FROM bi.sr_master_orders
    #                    WHERE out_ym = 202305
    #                        AND team_name like '%walmart%'
    #                        AND txn_id NOT IN (SELECT b.order_id
    #                                            FROM finance.sr_sat_emitidas a
    #                                            LEFT JOIN somos_reyes.odoo_master_txns_c b
    #                                                ON a.folio = b.marketplace_order_id
    #                                            WHERE a.serie = 'PGA'
    #                                                AND date(a.fecha) BETWEEN '2023-04-01' AND '2023-05-30'
    #                                            GROUP BY b.order_id)
    #                    GROUP BY txn_id
    #                    ORDER BY out_timestamp_local asc
    #                    limit 10""")
    #excel_file_path = r'C:\Users\Sergio Gil Guerrero\Documents\WonderBrands\Repos\wb_odoo_external_api\invoices_functions\files\invoices\so_invoices.xlsx'
    sale_file = pd.read_excel(excel_file_path, usecols=['so_name'])
    sales_order_records = sale_file['so_name'].tolist()
    #sales_order_records = mycursor.fetchall()
    order_names = []
    order_add_to_inv = []
    order_diff_status = []
    order_w_inv = []
    order_no_exist = []
    progress_bar = tqdm(total=len(sales_order_records), desc=f"Procesando hilo {str(execution_number)}")
    try:
        #for rec in sales_order_records:
        #    order_id = models.execute_kw(db_name, uid, password, 'sale.order', 'search_read', [[['name', '=', rec]]])
        #    order_names.append(order_id[0]['name'])
        #Se crea el cuerpo de la factura con los campos necesarios
        #so_domain = ['name', 'in', order_names]
        print('----------------------------------------------------------------')
        print('Definiendo valores de la factura global')
        print('----------------------------------------------------------------')
        print('Vaya por otro tecito u otro café porque este proceso tomará unos minutos')
        print('----------------------------------------------------------------')
        invoice_vals = {
            'ref': '',
            'move_type': 'out_invoice',
            'partner_id': 140530,
            'invoice_origin': ', '.join(sales_order_records),
            'invoice_line_ids': [],
            'team_id': 30, # Equipo de ventas Walmart
            #'invoice_date': '2024-11-30' # FECHA DE FACTURA manual si se ejecuta para mes anterior
        }
        # Consultamos a sale.order para obtener los campos requeridos de cada orden de venta
        for sale_order in sales_order_records:

            # COLOCAR UN TRY AQUI
            so_domain = ['name', '=', sale_order]
            order = models.execute_kw(db_name, uid, password, 'sale.order', 'search_read', [[so_domain]])
            if order:
                # print(f"Orden de venta encontrada")
                order_line_id = order[0]['order_line']
                order_name = order[0]['name']
                order_state = order[0]['state']
                order_inv_count = order[0]['invoice_count']
                if order_state == 'done':
                    if order_inv_count < 2: # 1 Si es la primer factura, 2 cuando se requiere volver a facturar si la primer factura nacio mal
                        #for line in order_line_id:
                        #print(f"Tomando las lineas de la orden")
                        sale_order_line = models.execute_kw(db_name, uid, password, 'sale.order.line', 'search_read', [[['id', '=', order_line_id]]])
                        for line in sale_order_line:
                            line_id = line['id']
                            invoice_line_vals = {
                                'display_type': line['display_type'],
                                'sequence': int(line['sequence']),
                                'name': line['name'],
                                'product_uom_id': line['product_uom'][0],
                                'product_id': line['product_id'][0],
                                'quantity': line['qty_delivered'],
                                'discount': line['discount'],
                                'price_unit': line['price_unit'],
                                'tax_ids': [(6, 0, [line['tax_id'][0]])],
                                'analytic_tag_ids': [(6, 0, line['analytic_tag_ids'])],
                                'sale_line_ids': [(4, line_id)],
                            }
                            invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))
                        order_add_to_inv.append(order_name)
                        order_names.append(order_name)
                        progress_bar.update(1)
                    else:
                        print(f"La factura {order_name} ya tiene una factura creada")
                        order_w_inv.append(order_name)
                        progress_bar.update(1)
                        continue
                else:
                    print(f"La orden de venta {order_name} se encuentra en estatus {order_state}")
                    print(f"Por lo que esta orden no puede ser facturada")
                    order_diff_status.append(order_name)
                    progress_bar.update(1)
                    continue
            else:
                print(f"No existe una SO que corresponda a {sale_order}")
                order_no_exist.append(sale_order)
                progress_bar.update(1)
                continue

        invoice_id = models.execute_kw(db_name, uid, password, 'account.move', 'create', [invoice_vals])
        print(f"Agregando mensaje a la factura")
        #Mensaje con ordenes de venta como referencia en el chatter
        message_so = {
            'body': order_names,
            'message_type': 'comment',
        }
        write_msg_inv = models.execute_kw(db_name, uid, password, 'account.move', 'message_post', [invoice_id], message_so)
        #Mensaje de creación por API
        message = {
            'body': 'Esta factura fue creada por el equipo de Tech vía API : Facturación global',
            'message_type': 'comment',
        }
        write_msg_tech = models.execute_kw(db_name, uid, password, 'account.move', 'message_post', [invoice_id], message)
    except Exception as e:
        print(f"Error al crear la factura con error: {e}")

    finally:
        progress_bar.close()
        mycursor.close()
        mydb.close()

    #Envío de correo
    msg = MIMEMultipart()
    body = '''\
    <html>
      <head></head>
      <body>
        <p>Buenas noches</p>
        <p>Hola a todos, espero que estén muy bien. Les comento que acabamos de correr el script para creación de facturas 
        globales de Walmart.</p>
        <p>Adjunto encontrarán el archivo generado por el script en el cual se encuentran las órdenes que se agregaron a la 
        factura global, órdenes que no se pudieron facturar debido a un estatus diferente de Done, órdenes que ya tienen una 
        factura creada y órdenes que no se encontraron.</p>
        </br>
        <p>Sin más por el momento quedo al pendiente para resolver cualquier duda o comentario.</p>
        </br>
        <p>Muchas gracias</p>
        </br>
        <p>Un abrazo</p>
      </body>
    </html>
    '''
    print('Creando archivo Excel')
    print('----------------------------------------------------------------')
    # Crear el archivo Excel y agregar los nombres de los arrays y los resultados
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet['A1'] = 'order_add_to_inv'
    sheet['B1'] = 'order_diff_status'
    sheet['C1'] = 'order_w_inv'
    sheet['D1'] = 'order_no_exist'

    # Agregar los resultados de los arrays
    for i in range(len(order_add_to_inv)):
        sheet['A{}'.format(i+2)] = order_add_to_inv[i]
    for i in range(len(order_diff_status)):
        sheet['B{}'.format(i+2)] = order_diff_status[i]
    for i in range(len(order_w_inv)):
        sheet['C{}'.format(i+2)] = order_w_inv[i]
    for i in range(len(order_no_exist)):
        sheet['D{}'.format(i+2)] = order_no_exist[i]
    # Guardar el archivo Excel en disco
    excel_file = 'factura_global_' + today_date.strftime("%Y%m%d") + '-' + str(execution_number) + '.xlsx'
    workbook.save(excel_file)
    # Leer el contenido del archivo Excel
    with open(excel_file, 'rb') as file:
        file_data = file.read()
    file_data_encoded = base64.b64encode(file_data).decode('utf-8')
    #Define el encabezado y las direcciones del remitente y destinatarios
    print('Definiendo remitente y destinatarios')
    print('----------------------------------------------------------------')
    msg = MIMEMultipart()
    msg['From'] = 'sergio@wonderbrands.co'
    msg['To'] = ', '.join(['sergio@wonderbrands.co''eric@wonderbrands.co','rosalba@wonderbrands.co','carlos.hinojosa@wonderbrands.co','greta@somos-reyes.com','contabilidad@somos-reyes.com','alex@wonderbrands.co','will@wonderbrands.co'])
    msg['Subject'] = 'Resultados de facturas Walmart'
    # Adjuntar el cuerpo del correo
    msg.attach(MIMEText(body, 'html'))
    # Adjuntar el archivo Excel al mensaje
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(file_data)
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment', filename=excel_file)
    msg.attach(attachment)

    #Define variables del servidor de correo
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'sergio@wonderbrands.co'
    smtp_password = 'lwbwgygovuhcyjnk'
    print('Enviando correo con listas de ordenes y factura')
    print('----------------------------------------------------------------')
    try:
       smtpObj = smtplib.SMTP(smtp_server, smtp_port)
       smtpObj.starttls()
       smtpObj.login(smtp_username, smtp_password)
       #smtpObj.sendmail(smtp_username, msg['To'], msg.as_string())
       smtpObj.send_message(msg)
       print("Correo enviado correctamente")
    except Exception as e:
       print(f"Error: no se pudo enviar el correo: {e}")

    print('----------------------------------------------------------------')
    print(f"Se creó la factura correctamente")
    print(f"El ID de la factura es el siguiente: {invoice_id}")
    print('----------------------------------------------------------------')

    progress_bar.close()
    mycursor.close()
    mydb.close()
    smtpObj.quit()

    print(f'\nHa terminado la ejecución {execution_number}\n')

    print('----------------------------------------------------------------')


def execute_invoice_create_global(runs_numbs, global_path):
    """
    Esta función ejecuta la función invoice_create_global en paralelo para cada archivo en global_path.

    :param runs_numbs: Número de corridas (numero de hilos) (es igual al número de archivos csv)
    :param global_path: La ruta base donde se encuentran los archivos
    """
    with ThreadPoolExecutor(max_workers=runs_numbs) as executor:
        futures = []
        for num in range(1, runs_numbs + 1):
            file_path = f"{global_path}/so_invoices{num}.xlsx"
            print(f"\n\n********* Corrida {num} **********\n\n")
            futures.append(executor.submit(invoice_create_global, file_path, num))

        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"Error al procesar el archivo: {e}")


if __name__ == "__main__":

    # TAREAS PENDIENTES! :
    # Hacer que al finalizar la función invoice_create_global, cree el archivo de salida, lo guarde (revisar como lo ahce hasta ahora)
    # y cuando terminen todos los hilos y todos los archivos, enviar un solo correo con los archivos adjuntos y
    # añadir el nombre de la ejecucion al archivo de salida.

    device = 'mac' # mac, dell, rog
    # ***********************************************
    # MES Y ANIO DE EJECUCION
    month, year = prep.get_dates()
    year_executed = str(year)
    print('******************')
    print(month, year)
    print('******************')

    # ----------------------------------------------------------------
    # Mes y año manual si se ejecuta en el mes posterior pero para efecto contable del mes anterior.
    #month = "Enero"
    #year_executed = "2025"
    # ----------------------------------------------------------------

    order_lines_in_invoice = 800 #Numero de lienas de orden de la factura, el limite esta al rededor de 1300 (comun = 999)
    # ***********************************************

    start_time = datetime.datetime.now()


    if device == 'dell':
        excel_files_dir = f'C:/Users/Sergio Gil Guerrero/Documents/WonderBrands/Repos/wb_odoo_external_api/invoices_functions/files/invoices'
        file_path_walmart = f'C:/Users/Sergio Gil Guerrero/Documents/WonderBrands/Finanzas/{year_executed}/{month}/Walmart/facturacion_global.csv'

        config_file_name = rf'C:\Users\Sergio Gil Guerrero\Documents\WonderBrands\Repos\wb_odoo_external_api\config\{config_file}'

    elif device == 'mac':
        excel_files_dir = f'/Users/sergio/Documents/Trabajo/WonderBrands/Repos/wb_odoo_external_api/invoices_functions/files/invoices'
        file_path_walmart = f'/Users/sergio/Documents/Trabajo/WonderBrands/Finanzas/{year_executed}/{month}/Walmart/facturacion_global.csv'

        config_file_name = f'/Users/sergio/Documents/Trabajo/Wonderbrands/Repos/wb_odoo_external_api/config/{config_file}'

    elif device == 'rog':
        pass # PENDIENTES
    # Limpia la carpeta 'invoices' de los archivos antiguos
    e_o.delete_files(excel_files_dir)

    # Separa en n archivos de acuerdo al numero de ordenes y los guarda en la carpeta 'invoices'
    num_of_runs = e_o.split_csv_to_excel(file_path_walmart, order_lines_in_invoice, excel_files_dir)
    execute_invoice_create_global(num_of_runs, excel_files_dir)

    end_time = datetime.datetime.now()
    duration = end_time - start_time
    print(f"Duración total del script: {duration}")
    print("Listo")
    print("Este arroz ya se coció :)")