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
#import requests
import logging
import zipfile
import socket
import os
import locale
import xmlrpc.client
import base64
import openpyxl
#import xlrd
import pandas as pd
import MySQLdb
import mysql.connector
import smtplib
import ssl
import email
import datetime
import time as tm

from unit_tools import extract_orders as e_o
from unit_tools import prepare_folders as prep

print('================================================================')
print('BIENVENIDO AL PROCESO DE AUTOFACTURACIÓN WALMART')
print('================================================================')
print('SCRIPT DE CREACIÓN DE FACTURAS POR ITEM')
print('================================================================')
today_date = datetime.datetime.now()
dir_path = os.path.dirname(os.path.realpath(__file__))
print('Fecha:' + today_date.strftime("%Y-%m-%d %H:%M:%S"))
#Archivo de configuración - Use config_dev.json si está haciendo pruebas
#Archivo de configuración - Use config.json cuando los cambios vayan a producción

# ***********************************************
device ='dell' # mac, dell, rog
# ***********************************************
# ARCHIVO DE CONFIGURACIÓN
config_file = 'config.json'

# MES Y ANIO DE EJECUCION
month_executed, year_executed = prep.get_dates()
year_executed = str(year_executed)

# FECHAS PARA CARPETA DRIVE en str
month_ = str(prep.get_month_number()) # Número del mes. Ejemplo para enero: '01'


# ----------------------------------------------------------------
### Mes y año MANUAL si se ejecuta en el mes posterior pero para efecto contable del mes anterior.

year_executed = '2025'
month_executed = "Octubre"
month_ = "10"
invoice_date = '2025-10-31'
# ----------------------------------------------------------------

if device == 'dell':
    config_file_name = rf'C:\Users\Sergio Gil Guerrero\Documents\WonderBrands\Repos\wb_odoo_external_api\config\{config_file}'
    #PATH del archivo de ordenes conciliadas
    orders_walmart_file_path = f'C:/Users/Sergio Gil Guerrero/Documents/WonderBrands/Finanzas/{year_executed}/{month_executed}/Walmart/autofacturacion.csv'
    # PATH de XMLs (susituimos estos archivos desde que nosotros tomamos los xmls en local)
    invoices_folder = rf'C:\Users\Sergio Gil Guerrero\Documents\WonderBrands\Finanzas\{year_executed}\{month_executed}\Walmart\xmls_walmart'

elif device == 'mac':
    config_file_name = f'/Users/sergio/Documents/Trabajo/WonderBrands/Repos/wb_odoo_external_api/config/{config_file}'
    # PATH del archivo de ordenes conciliadas
    orders_walmart_file_path = f'/Users/sergio/Documents/Trabajo/WonderBrands/Finanzas/{year_executed}/{month_executed}/Walmart/autofacturacion.csv'
elif device == 'rog':
    pass

print('******************')
print(month_executed, year_executed)
print('******************')


print(f'Carpeta: {month_}, Mes: {month_executed}, Año: {year_executed}')

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
def invoice_create_qty():
    # Formato para query
    marketplace_refs_list, placeholders, num_records = e_o.marketplace_references(orders_walmart_file_path)
    date_list_param = [year_executed+month_]
    print(marketplace_refs_list)

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
    print('Este proceso tomará algo de tiempo, le recomendamos ir por un café')
    print('----------------------------------------------------------------')
    mycursor.execute("""SELECT b.name, a.uuid, a.fecha
                        FROM finance.sr_sat_emitidas a
                        LEFT JOIN somos_reyes.odoo_new_sale_order b
                        ON a.folio LIKE CONCAT(CAST(b.channel_order_reference AS CHAR), '%')
                        WHERE EXTRACT(YEAR_MONTH FROM a.fecha) = %s
                          AND b.channel LIKE '%walmart%' 
                          AND b.team_name LIKE '%walmart%'
                          AND b.state NOT IN ('draft','sent','cancel')
                          AND b.channel_order_reference IN  ({})
                        group by a.uuid
                        order by a.fecha
                        """.format(placeholders), tuple(date_list_param + marketplace_refs_list))
    sales_order_records = mycursor.fetchall()
    xml_dict = {}
    xml_list = []
    inv_list = []
    sales_error_state = []
    sales_no_exist = []
    sales_w_inv = []
    sales_no_xml = []
    sales_mod = []
    inv_names = []
    inv_ids = []
    date_year = '20'
    for row in sales_order_records:
        so_name = row[0] #Del query obtiene el nombre de la SO
        xml_name = row[1] #Del query obtiene el nombre del XML o UUID
        xml_date = date_year + row[2].strftime("%y-%m-%d %H:%M:%S") #Del query obtiene también la fecha de la factura

        if so_name not in xml_dict:
            xml_dict[so_name] = [] #si una SO está repetida le agrega multiples xml y fechas correspondientes

        xml_dict[so_name].append(xml_name) #agrega el nombre del xml a una tabla
        xml_dict[so_name].append(xml_date) #agrega la fecha de factura a una tabla

    progress_bar = tqdm(total=len(sales_order_records), desc="Procesando")
    for so_order, xml_files in xml_dict.items():
        value_position = 0
        value_position_date = 1
        so_domain = ['name', '=', so_order]
        for xml_ids in so_order[1]:
            xml_list.append(xml_ids)
        #busca la orden de venta y obtiene el nombre y el estado de SO
        sale_ids = models.execute_kw(db_name, uid, password,'sale.order', 'search_read', [[so_domain]])
        try:
            #Si existe una orden de venta
            if sale_ids:
                order_name = sale_ids[0]['name']
                order_state = sale_ids[0]['state']
                #Si la orden está en Done o bloqueada
                if order_state == 'done':
                    invoice_count = sale_ids[0]['invoice_count']
                    #Si la cantidad de facturas es menor a 1, ya que si tiene más podría presentar un retorno
                    if invoice_count < 1:
                        #Crea una factura para cada orden y para cada item
                        #Obtiene los datos necesarios directo de la SO
                        sale_id = int(sale_ids[0]['id'])
                        currency_id = sale_ids[0]['currency_id'][0]
                        narration = sale_ids[0]['note']
                        campaign_id = False
                        medium_id = sale_ids[0]['medium_id']
                        source_id = sale_ids[0]['source_id']
                        user_id = sale_ids[0]['user_id'][0]
                        invoice_user_id = sale_ids[0]['user_id'][0]
                        team_id = sale_ids[0]['team_id'][0]
                        partner_id = sale_ids[0]['partner_id'][0]
                        partner_shipping_id = sale_ids[0]['partner_shipping_id'][0]
                        fiscal_position_id = sale_ids[0]['fiscal_position_id']
                        partner_bank_id = 1
                        journal_id = 1
                        invoice_origin = sale_ids[0]['name']
                        invoice_payment_term_id = sale_ids[0]['payment_term_id']
                        payment_reference = sale_ids[0]['reference']
                        transaction_ids = sale_ids[0]['transaction_ids']
                        company_id = 1
                        sale_order_line_id = sale_ids[0]['order_line']
                        #sale_order_line_change =  sale_ids[0]['order_line'][0]
                        #Busca el sale_order_line para obtener los datos
                        sol_domain = ['id', 'in', sale_order_line_id]
                        sale_order_line = models.execute_kw(db_name, uid, password, 'sale.order.line', 'search_read', [[sol_domain]])
                        for inv_lines in sale_order_line:
                            qty_delivered = round(inv_lines['qty_delivered'])
                            qty_uom = round(inv_lines['product_uom_qty'])
                            #Si al cantidad entregada es diferente de 0
                            if qty_delivered != 0:
                                # Inicia un ciclo para cada item en la columna qty_delivered
                                for qty in range(qty_delivered):
                                    if 'invoice_date' in globals():
                                        invoice = {
                                            'ref': '',
                                            'move_type': 'out_invoice',
                                            'currency_id': currency_id,
                                            'narration': narration,
                                            'campaign_id': campaign_id,
                                            'medium_id': medium_id,
                                            'source_id': source_id,
                                            'user_id': user_id,
                                            'invoice_user_id': invoice_user_id,
                                            'team_id': team_id,
                                            'partner_id': partner_id,
                                            'partner_shipping_id': partner_shipping_id,
                                            'fiscal_position_id': fiscal_position_id,
                                            'partner_bank_id': partner_bank_id,
                                            'journal_id': journal_id,  # company comes from the journal
                                            'invoice_origin': invoice_origin,
                                            'invoice_payment_term_id': invoice_payment_term_id,
                                            'payment_reference': payment_reference,
                                            'transaction_ids': [(6, 0, transaction_ids)],
                                            'invoice_line_ids': [],
                                            'invoice_date': invoice_date # FECHA DE FACTURA manual si se ejecuta para mes anterior
                                        }
                                    else:
                                        invoice = {
                                            'ref': '',
                                            'move_type': 'out_invoice',
                                            'currency_id': currency_id,
                                            'narration': narration,
                                            'campaign_id': campaign_id,
                                            'medium_id': medium_id,
                                            'source_id': source_id,
                                            'user_id': user_id,
                                            'invoice_user_id': invoice_user_id,
                                            'team_id': team_id,
                                            'partner_id': partner_id,
                                            'partner_shipping_id': partner_shipping_id,
                                            'fiscal_position_id': fiscal_position_id,
                                            'partner_bank_id': partner_bank_id,
                                            'journal_id': journal_id,  # company comes from the journal
                                            'invoice_origin': invoice_origin,
                                            'invoice_payment_term_id': invoice_payment_term_id,
                                            'payment_reference': payment_reference,
                                            'transaction_ids': [(6, 0, transaction_ids)],
                                            'invoice_line_ids': []
                                        }
                                    line_id = inv_lines['id']
                                    invoice_lines = {'display_type': inv_lines['display_type'],
                                                     'sequence': inv_lines['sequence'],
                                                     'name': inv_lines['name'],
                                                     'product_id': inv_lines['product_id'][0],
                                                     'product_uom_id': inv_lines['product_uom'][0],
                                                     #'quantity': sale_order_line[0]['product_qty'],
                                                     'quantity': 1,
                                                     'discount': inv_lines['discount'],
                                                     'price_unit': inv_lines['price_unit'],
                                                     'tax_ids': [(6, 0, [inv_lines['tax_id'][0]])],
                                                     'analytic_tag_ids': [(6, 0, inv_lines['analytic_tag_ids'])],
                                                     'sale_line_ids': [(4, line_id)],
                                                     }
                                    invoice['invoice_line_ids'].append((0, 0, invoice_lines))
                                    #Crea la factura con el SKU del line_id
                                    create_inv = models.execute_kw(db_name, uid, password, 'account.move', 'create', [invoice])
                                    #print('La factura de la orden: ', invoice_origin, 'fue creada con ID: ', create_inv)
                                    #Busca la factura para agregar mensaje en el chatter
                                    #print(f"Agregando mensaje a la factura")
                                    search_inv = models.execute_kw(db_name, uid, password, 'account.move', 'search_read', [[['id', '=', create_inv]]])
                                    #agrega el id de la factura creada a una tabla
                                    inv_ids.append(create_inv)
                                    message = {
                                        'body': 'Esta factura fue creada por el equipo de Tech vía API: Autofacturación',
                                        'message_type': 'comment',
                                    }
                                    write_msg_inv = models.execute_kw(db_name, uid, password, 'account.move', 'message_post', [create_inv], message)
                                    # Busca el UUID relacionada con la factura
                                    #si existe un archivo XML
                                    if xml_files:
                                        #Obtiene el nombre del XML y la fecha, modifica el nombre del XML y lo pone en mayúsculas
                                        file_name = xml_files[value_position] #utliza la posición que asignamos anteriormente
                                        file_date = xml_files[value_position_date] #utliza la posición que asignamos anteriormente
                                        file_name_mayus = file_name.upper() #Pone en mayúsculas el nombre del XML
                                        #invoices_folder = 'G:/.shortcut-targets-by-id/1vsZk0-0Cd1FnEKNQlXzq3EuSgg6ZRgtP/{}/{}'.format(year_executed,year_executed+month_) #carpeta en la que se encuentran los xmls
                                        #invoices_folder = 'G:/My Drive/Compartido/{}/{}'.format(year_executed,year_executed+month_)
                                        #invoices_folder = rf'C:\Users\Sergio Gil Guerrero\Documents\WonderBrands\Finanzas\{year_executed}\{month_executed}\Walmart\xmls_walmart'
                                        xml_file = file_name + '.xml'
                                        xml_file_path = os.path.join(invoices_folder, xml_file)
                                        with open(xml_file_path, 'rb') as f:
                                            xml_data = f.read()
                                        xml_base64 = base64.b64encode(xml_data).decode('utf-8')
                                        #Define los valores del attachment para agregarl el XML
                                        attachment_data = {
                                            'name': xml_file,
                                            'datas': xml_base64,
                                            'res_model': 'account.move',
                                            'res_id': create_inv,
                                        }
                                        #Busca el id del attachment relacionado a la factura
                                        attachment_ids = models.execute_kw(db_name, uid, password, 'ir.attachment', 'create', [attachment_data])
                                        attachment_id = int(attachment_ids)
                                        values = [{
                                            'move_id': create_inv,
                                            'edi_format_id': 2,
                                            'attachment_id': attachment_id,
                                            'state': 'sent',
                                            'create_uid': 1,
                                            'write_uid': 2,
                                        }]
                                        #Agrega el nombre de la factura a la tabla documentos EDI (solo se ve con debug, conta no la usa)
                                        edi_document = models.execute_kw(db_name, uid, password, 'account.edi.document', 'create', values)
                                        #Valida la factura llamando al botón "Confirmar"
                                        upd_invoice_state = models.execute_kw(db_name, uid, password, 'account.move','action_post', [create_inv])
                                        #Agrega el folio fiscal del XML a la factura y al campo de narration (parche realizado momentaneamente)
                                        upd_folio_fiscal = models.execute_kw(db_name, uid, password, 'account.move','write', [[create_inv], {'l10n_mx_edi_cfdi_uuid': file_name_mayus}])
                                        upd_folio_fiscal_narr = models.execute_kw(db_name, uid, password, 'account.move','write', [[create_inv], {'narration': file_name_mayus}])
                                        # Modifica la fecha de la factura por la del xml y la fecha vencida por "Pago único"
                                        upd_inv_date = models.execute_kw(db_name, uid, password, 'account.move', 'write',[[create_inv], {'invoice_date': file_date}])
                                        upd_inv_date_term = models.execute_kw(db_name, uid, password, 'account.move','write', [[create_inv],{'invoice_payment_term_id': 1}])
                                        #Busca el nombre de la factura una vez publicada meramente infomativo
                                        search_inv_name = models.execute_kw(db_name, uid, password, 'account.move','search_read', [[['id', '=', create_inv]]])
                                        int_id = search_inv_name[0]['id']
                                        inv_name = search_inv_name[0]['name']
                                        inv_edi_state = search_inv_name[0]['edi_state']

                                        #UPDATE Diciembre-2023
                                        attachment = models.execute_kw(db_name, uid, password, 'ir.attachment', 'search_read',[[['res_id', '=', create_inv]]])[0]
                                        edi_document_fix = models.execute_kw(db_name, uid, password, 'account.edi.document','search_read', [[['move_id', '=', create_inv]]])

                                        if inv_edi_state != 'sent':
                                            if attachment:
                                                att_id = attachment['id']
                                                for edi in edi_document_fix:
                                                    edi_id = edi['id']  # ID del registro en la tabla EDI
                                                    edi_name = edi['edi_format_name']  # Nombre del registro en la tabla EDI
                                                    edi_state = edi['state']  # Estado del registro en la tabla EDI
                                                    if edi_name == 'CFDI (3.3)':
                                                        # Elimina el registro de la tabla EDI.DOCUMENT
                                                        del_edi_document = models.execute_kw(db_name, uid, password,'account.edi.document','unlink', [[edi_id]])
                                                        # Crea una lista para insertar un nuevo registro en la tabla EDI.DOCUMENT
                                                        values = [{
                                                            'move_id': int_id,
                                                            'edi_format_id': 2,
                                                            'attachment_id': att_id,
                                                            'state': 'sent',
                                                            'create_uid': 1,
                                                            'write_uid': 2,
                                                        }]
                                                        # Crea un nuevo registro con el UUID correcto de la tabla EDI.DOCUMENT
                                                        new_edi_document = models.execute_kw(db_name, uid, password,'account.edi.document','create', values)
                                                    else:
                                                        continue
                                            else:
                                                print(f'La orden: {order_name} no tiene un XML adjunto')
                                                continue
                                        else:
                                            print(f'La orden: {order_name} no está en estado "Por enviar"')
                                            continue

                                        #posiciones de los array
                                        value_position += 2
                                        value_position_date += 2
                                        sales_mod.append(order_name) #agrega el nombre de la orden a otra tabla
                                        inv_names.append(inv_name) #agrega el nombre que se le asignó a la factura
                                        progress_bar.update(1)
                                        #print(f"ESTE ES LA POSICION DEL ARRAY: {value_position}")
                                    else:
                                        print(f'La orden: {order_name} no tiene un XML en la carpeta')
                                        sales_no_xml.append(order_name)
                                        progress_bar.update(1)
                                        continue
                            else:
                                print("Se encontró una factura con cantidad entregada en 0, se tomará en cuenta solo la cantidad")
                                #Inicia un ciclo para cada item en la columna qty_uom
                                for qty in range(qty_uom):
                                    if 'invoice_date' in globals():
                                        invoice = {
                                            'ref': '',
                                            'move_type': 'out_invoice',
                                            'currency_id': currency_id,
                                            'narration': narration,
                                            'campaign_id': campaign_id,
                                            'medium_id': medium_id,
                                            'source_id': source_id,
                                            'user_id': user_id,
                                            'invoice_user_id': invoice_user_id,
                                            'team_id': team_id,
                                            'partner_id': partner_id,
                                            'partner_shipping_id': partner_shipping_id,
                                            'fiscal_position_id': fiscal_position_id,
                                            'partner_bank_id': partner_bank_id,
                                            'journal_id': journal_id,  # company comes from the journal
                                            'invoice_origin': invoice_origin,
                                            'invoice_payment_term_id': invoice_payment_term_id,
                                            'payment_reference': payment_reference,
                                            'transaction_ids': [(6, 0, transaction_ids)],
                                            'invoice_line_ids': [],
                                            'company_id': company_id,
                                            'invoice_date': invoice_date # FECHA DE FACTURA manual si se ejecuta para mes anterior
                                        }
                                    else:
                                        invoice = {
                                            'ref': '',
                                            'move_type': 'out_invoice',
                                            'currency_id': currency_id,
                                            'narration': narration,
                                            'campaign_id': campaign_id,
                                            'medium_id': medium_id,
                                            'source_id': source_id,
                                            'user_id': user_id,
                                            'invoice_user_id': invoice_user_id,
                                            'team_id': team_id,
                                            'partner_id': partner_id,
                                            'partner_shipping_id': partner_shipping_id,
                                            'fiscal_position_id': fiscal_position_id,
                                            'partner_bank_id': partner_bank_id,
                                            'journal_id': journal_id,  # company comes from the journal
                                            'invoice_origin': invoice_origin,
                                            'invoice_payment_term_id': invoice_payment_term_id,
                                            'payment_reference': payment_reference,
                                            'transaction_ids': [(6, 0, transaction_ids)],
                                            'invoice_line_ids': [],
                                            'company_id': company_id
                                        }
                                    # line_id = sale_order_line[0]['id']
                                    line_id = inv_lines['id']
                                    invoice_lines = {'display_type': inv_lines['display_type'],
                                                     'sequence': inv_lines['sequence'],
                                                     'name': inv_lines['name'],
                                                     'product_id': inv_lines['product_id'][0],
                                                     'product_uom_id': inv_lines['product_uom'][0],
                                                     # 'quantity': sale_order_line[0]['product_qty'],
                                                     'quantity': 1,
                                                     'discount': inv_lines['discount'],
                                                     'price_unit': inv_lines['price_unit'],
                                                     'tax_ids': [(6, 0, [inv_lines['tax_id'][0]])],
                                                     'analytic_tag_ids': [(6, 0, inv_lines['analytic_tag_ids'])],
                                                     'sale_line_ids': [(4, line_id)],
                                                     }
                                    invoice['invoice_line_ids'].append((0, 0, invoice_lines))
                                    create_inv = models.execute_kw(db_name, uid, password, 'account.move', 'create',
                                                                   [invoice])
                                    # Busca la factura para agregar mensaje en el chatter
                                    search_inv = models.execute_kw(db_name, uid, password, 'account.move', 'search_read',
                                                                   [[['id', '=', create_inv]]])
                                    message = {
                                        'body': 'Esta factura fue creada por el equipo de Tech vía API',
                                        'message_type': 'comment',
                                    }
                                    write_msg_inv = models.execute_kw(db_name, uid, password, 'account.move',
                                                                      'message_post', [create_inv], message)
                                    # Busca si hay un UUID relacionada con la factura
                                    if xml_files:
                                        # Obtiene el nombre del XML y la fecha, modifica el nombre del XML y lo pone en mayúsculas
                                        file_name = xml_files[value_position]
                                        file_date = xml_files[value_position_date]
                                        file_name_mayus = file_name.upper()
                                        #invoices_folder = 'G:/.shortcut-targets-by-id/1vsZk0-0Cd1FnEKNQlXzq3EuSgg6ZRgtP/{}/{}'.format(year_executed,year_executed+month_) #carpeta en la que se encuentran los xmls
                                        #invoices_folder = 'G:/My Drive/Compartido/{}/{}'.format(year_executed,year_executed+month_)
                                        #invoices_folder = rf'C:\Users\Sergio Gil Guerrero\Documents\WonderBrands\Finanzas\{year_executed}\{month_executed}\Walmart\xmls_walmart'
                                        xml_file = file_name + '.xml'
                                        xml_file_path = os.path.join(invoices_folder, xml_file)
                                        with open(xml_file_path, 'rb') as f:
                                            xml_data = f.read()
                                        xml_base64 = base64.b64encode(xml_data).decode('utf-8')
                                        # Define los valores del attachment para agregarl el XML
                                        attachment_data = {
                                            'name': xml_file,
                                            'datas': xml_base64,
                                            'res_model': 'account.move',
                                            'res_id': create_inv,
                                        }
                                        # Busca el id del attachment relacionado a la factura
                                        attachment_ids = models.execute_kw(db_name, uid, password, 'ir.attachment',
                                                                           'create', [attachment_data])
                                        attachment_id = int(attachment_ids)
                                        values = [{
                                            'move_id': create_inv,
                                            'edi_format_id': 2,
                                            'attachment_id': attachment_id,
                                            'state': 'sent',
                                            'create_uid': 1,
                                            'write_uid': 2,
                                        }]
                                        # Agrega el nombre de la factura a la tabla documentos EDI (solo se ve con debug, conta no la usa)
                                        edi_document = models.execute_kw(db_name, uid, password, 'account.edi.document','create', values)
                                        # Valida la factura llamando al botón "Confirmar"
                                        upd_invoice_state = models.execute_kw(db_name, uid, password, 'account.move','action_post', [create_inv])
                                        # Agrega el folio fiscal del XML a la factura y al campo de narration (parche realizado momentaneamente)
                                        upd_folio_fiscal = models.execute_kw(db_name, uid, password, 'account.move','write', [[create_inv], {'l10n_mx_edi_cfdi_uuid': file_name_mayus}])
                                        upd_folio_fiscal_narr = models.execute_kw(db_name, uid, password, 'account.move','write', [[create_inv],{'narration': file_name_mayus}])
                                        # Modifica la fecha de la factura por la del xml y la fecha vencida por "Pago único"
                                        upd_inv_date = models.execute_kw(db_name, uid, password, 'account.move', 'write',[[create_inv], {'invoice_date': file_date}])
                                        upd_inv_date_term = models.execute_kw(db_name, uid, password, 'account.move','write', [[create_inv],{'invoice_payment_term_id': 1}])
                                        # Busca el nombre de la factura una vez publicada meramente infomativo
                                        search_inv_name = models.execute_kw(db_name, uid, password, 'account.move','search_read', [[['id', '=', create_inv]]])
                                        int_id = search_inv_name[0]['id']
                                        inv_name = search_inv_name[0]['name']
                                        inv_edi_state = search_inv_name[0]['edi_state']

                                        # UPDATE Diciembre-2023
                                        attachment = models.execute_kw(db_name, uid, password, 'ir.attachment', 'search_read',[[['res_id', '=', create_inv]]])[0]
                                        edi_document_fix = models.execute_kw(db_name, uid, password,'account.edi.document', 'search_read',[[['move_id', '=', create_inv]]])

                                        if inv_edi_state != 'sent':
                                            if attachment:
                                                att_id = attachment['id']
                                                for edi in edi_document_fix:
                                                    edi_id = edi['id']  # ID del registro en la tabla EDI
                                                    edi_name = edi['edi_format_name']  # Nombre del registro en la tabla EDI
                                                    edi_state = edi['state']  # Estado del registro en la tabla EDI
                                                    if edi_name == 'CFDI (3.3)':
                                                        # Elimina el registro de la tabla EDI.DOCUMENT
                                                        del_edi_document = models.execute_kw(db_name, uid, password,'account.edi.document','unlink', [[edi_id]])
                                                        # Crea una lista para insertar un nuevo registro en la tabla EDI.DOCUMENT
                                                        values = [{
                                                            'move_id': int_id,
                                                            'edi_format_id': 2,
                                                            'attachment_id': att_id,
                                                            'state': 'sent',
                                                            'create_uid': 1,
                                                            'write_uid': 2,
                                                        }]
                                                        # Crea un nuevo registro con el UUID correcto de la tabla EDI.DOCUMENT
                                                        new_edi_document = models.execute_kw(db_name, uid, password,
                                                                                             'account.edi.document',
                                                                                             'create', values)
                                                    else:
                                                        continue
                                            else:
                                                print(f'La orden: {order_name} no tiene un XML adjunto')
                                                continue
                                        else:
                                            print(f'La orden: {order_name} no está en estado "Por enviar"')
                                            continue
                                        # posiciones de los array
                                        value_position += 2
                                        value_position_date += 2
                                        sales_mod.append(order_name)
                                        inv_names.append(inv_name)
                                        progress_bar.update(1)
                                        # print(f"ESTE ES LA POSICION DEL ARRAY: {value_position}")
                                    else:
                                        print(f'La orden: {order_name} no tiene un XML en la carpeta')
                                        progress_bar.update(1)
                                        continue
                    else:
                        print(f'La orden de venta: {order_name} ya tiene una factura creada')
                        print('----------------------------------------------------------------')
                        sales_w_inv.append(order_name)
                        progress_bar.update(1)
                        continue
                else:
                    print(f"Revise el estatus de la orden {order_name} se encuentra en estatus {order_state}")
                    print(f"Por lo que esta orden no puede ser facturada")
                    sales_error_state.append(order_name)
                    progress_bar.update(1)
                    continue
            else:
                print(f'El ID de la orden: {order_name} no coincide con ninguna venta en Odoo')
                sales_no_exist.append(order_name)
                progress_bar.update(1)
                continue
        except Exception as e:
            print(f"Error al crear la factura de la orden {order_name}: {e}")

    print('Definiendo correo para contabilidad')
    msg = MIMEMultipart()
    body = '''\
    <html>
      <head></head>
      <body>
        <p>Buen día</p>
        <p>Hola a todos, espero que estén muy bien. Les comento que acabamos de correr el script de autofacturación Walmart.</p>
        <p>Adjunto encontrarán el archivo generado por el script en el cual se encuentran las órdenes a las cuales se les creó una factura, órdenes que no se pudieron facturar, nombre de las facturas creadas y su ids correspondientes.</p>
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
    sheet['A1'] = 'sales_error_state'
    sheet['B1'] = 'sales_no_exist'
    sheet['C1'] = 'sales_w_inv'
    sheet['D1'] = 'sales_no_xml'
    sheet['E1'] = 'sales_mod'
    sheet['F1'] = 'inv_names'
    sheet['G1'] = 'inv_ids'
    # Agregar los resultados de los arrays
    for i in range(len(sales_error_state)):
        sheet['A{}'.format(i+2)] = sales_error_state[i]
    for i in range(len(sales_no_exist)):
        sheet['B{}'.format(i+2)] = sales_no_exist[i]
    for i in range(len(sales_w_inv)):
        sheet['C{}'.format(i+2)] = sales_w_inv[i]
    for i in range(len(sales_no_xml)):
        sheet['D{}'.format(i+2)] = sales_no_xml[i]
    for i in range(len(sales_mod)):
        sheet['E{}'.format(i+2)] = sales_mod[i]
    for i in range(len(inv_names)):
        sheet['F{}'.format(i+2)] = inv_names[i]
    for i in range(len(inv_ids)):
        sheet['G{}'.format(i+2)] = inv_ids[i]
    # Guardar el archivo Excel en disco
    excel_file = 'ordenes_autofacturadas_' + today_date.strftime("%Y%m%d") + '.xlsx'
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
    msg['To'] = ', '.join(['sergio@wonderbrands.co', 'eric@wonderbrands.co', 'rosalba@wonderbrands.co','carlos.hinojosa@wonderbrands.co','greta@somos-reyes.com','contabilidad@somos-reyes.com','alex@wonderbrands.co','will@wonderbrands.co'])
    msg['Subject'] = 'Cierre de facturación de órdenes autofacturadas - Walmart'
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
    print('Enviando correo con listas de ordenes y facturas')
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

    progress_bar.close()
    mycursor.close()
    mydb.close()
    smtpObj.quit()

if __name__ == "__main__":
    invoice_create_qty()
    end_time = datetime.datetime.now()
    duration = end_time - today_date
    print(f'Duraciòn del script: {duration}')
    print('Listo')
    print('Este arroz ya se coció :)')