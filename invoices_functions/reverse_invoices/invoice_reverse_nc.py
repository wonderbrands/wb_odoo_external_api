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
import jsonrpclib
import random
import urllib.request
import getpass
import http
import requests
import logging
import zipfile
import socket
import os
import locale
import xmlrpc.client
import base64
import openpyxl
import xlrd
import pandas as pd
import MySQLdb
import mysql.connector
import smtplib
import ssl
import email
import datetime

print('================================================================')
print('BIENVENIDO AL PROCESO DE NOTAS DE CRÉDITO PARA MARKETPLACES')
print('================================================================')
print('SCRIPT DE CREACIÓN DE NOTAS DE CRÉDITO INDIVIDUALES')
print('================================================================')
today_date = datetime.datetime.now()
dir_path = os.path.dirname(os.path.realpath(__file__))
print('Fecha:' + today_date.strftime("%Y-%m-%d %H:%M:%S"))
#Archivo de configuración - Use config_dev.json si está haciendo pruebas
#Archivo de configuración - Use config.json cuando los cambios vayan a producción
config_file_name = r'C:\Dev\wb_odoo_external_api\config\config_dev.json'

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
def reverse_invoice_meli():
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
    print('NOTAS DE CRÉDITO MELI')
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
    print('----------------------------------------------------------------')
    print('Vaya por un tecito o un café porque este proceso tomará algo de tiempo')

    mycursor.execute("""SELECT c.name,
                               b.id 'account_move_id',
                               ifnull(d.payment_date_last_modified, dd.payment_date_last_modified) 'payment_date_last_modified'/*,
                               ifnull(d.order_id, dd.pack_id) 'order_id_or_pack_id',
                               b.amount_total 'total_factura',
                               b.amount_untaxed 'subtotal_factura',
                               ifnull(d.refunded_amt, dd.refunded_amt) 'ml_refunded_amount',
                               b.invoice_partner_display_name 'cliente',
                               b.name,
                               'INDIVIDUAL' as type,
                               'MERCADO LIBRE' as marketplace*/
                        FROM somos_reyes.odoo_new_account_move_aux b
                        LEFT JOIN odoo_new_sale_order c
                        ON b.invoice_origin = c.name
                        LEFT JOIN (SELECT a.order_id, max(payment_date_last_modified) 'payment_date_last_modified', SUM(paid_amt) 'paid_amt', SUM(refunded_amt) 'refunded_amt', SUM(shipping_amt) 'shipping_amt'
                                   FROM ml_order_payments a
                                   LEFT JOIN ml_order_update b
                                   ON a.order_id = b.order_id
                                   WHERE refunded_amt > 0 AND b.pack_id = 'None' AND date(payment_date_last_modified) >= '2023-01-01' AND date(payment_date_last_modified) <= '2023-10-31'
                                   GROUP BY 1) d
                        ON c.channel_order_id = d.order_id
                        LEFT JOIN (SELECT a.pack_id, max(payment_date_last_modified) 'payment_date_last_modified', SUM(b.paid_amt) 'paid_amt', SUM(b.refunded_amt) 'refunded_amt', SUM(shipping_amt) 'shipping_amt'
                        FROM ml_order_update a
                        LEFT JOIN ml_order_payments b
                        ON a.order_id = b.order_id
                        WHERE b.refunded_amt > 0 AND a.pack_id <> 'None' AND date(payment_date_last_modified) >= '2023-01-01' AND date(payment_date_last_modified) <= '2023-10-31'
                        GROUP BY 1) dd
                        ON c.yuju_pack_id = dd.pack_id
                        LEFT JOIN (SELECT distinct invoice_origin FROM odoo_new_account_move_aux WHERE name like '%RINV%') e
                        ON c.name = e.invoice_origin
                        WHERE (d.order_id is not null or dd.pack_id is not null)
                        AND e.invoice_origin is null
                        AND ((ifnull(d.refunded_amt, dd.refunded_amt) - b.amount_total < 1 AND ifnull(d.refunded_amt, dd.refunded_amt) - b.amount_total > -1)
                        OR (ifnull(d.refunded_amt - d.shipping_amt, dd.refunded_amt - dd.shipping_amt) - b.amount_total < 1
                        AND ifnull(d.refunded_amt - d.shipping_amt, dd.refunded_amt - dd.shipping_amt) - b.amount_total > -1))
                        AND c.name not in ('SO2407057', 'SO2162491', 'SO2260535', 'SO2225912', 'SO2199035', 'SO2176440', 'SO2138635', 'SO2243457', 'SO2212581', 'SO2082929', 'SO2217050','SO2398691','SO2233863','SO2335461','SO2334456','SO2250305','SO2218057','SO2067163','SO2260567','SO2261845','SO2275451','SO2237778','SO2278358','SO2243521','SO2295236','SO2382150','SO2240357','SO2130288','SO2367994','SO2242962','SO2404954','SO2287697','SO2424911','SO2424911','SO2235963','SO2296843','SO2248501','SO2287080','SO2286215','SO2481024','SO2481024','SO2314119','SO2487577','SO2206450','SO2362974','SO2384135','SO2341296','SO2299763','SO2198874','SO2230459','SO2251197','SO2285219','SO2288855','SO2358585','SO2329682','SO2410821','SO2407957','SO2221166','SO2228818','SO2431157','SO2333103','SO2479113','SO2377104','SO2381383','SO2319963','SO2438542','SO2438542','SO2467477','SO2333570','SO2250823','SO2255819','SO2317962','SO2419708','SO2201212','SO2254711','SO2241024','SO2366791','SO2178744','SO2197317','SO2311391','SO2444958','SO2505334','SO2235619','SO2260482','SO2181573','SO2401370','SO2416549','SO2240799','SO2483357','SO2312224','SO2376686','SO2376686','SO2240768','SO2304683','SO2234700','SO2449633','SO2368835','SO2381969','SO2159352','SO2239719','SO2307389','SO2474554','SO2369068','SO2373028','SO2289219','SO2340941','SO2409149','SO2466236','SO2394770','SO2245277','SO2209053','SO2314784','SO2395439','SO2328726','SO2264062','SO2200879','SO2368652','SO2203913','SO2463747','SO2322431','SO2441359','SO2429718','SO2307981','SO2302131','SO2288302','SO2335215','SO2385492','SO2272609','SO2474334','SO2171731','SO2366461','SO2228483','SO2306618','SO2459608','SO2188937','SO2209102','SO2233045','SO2281715','SO2465627','SO2466504');""")
    invoice_records = mycursor.fetchall()
    # Lista de SO a las que se les creó una credit_notes
    so_modified = []
    # Lista de las facturas enlazadas a la SO y no existen
    inv_no_exist = []
    # Lista de SO que ya contaban con credit_notes antes del script
    so_with_refund = []
    # Lista de nombres de las notas de crédito creadas
    nc_created = []
    # Lista de facturas origen
    so_origin_invoice = []
    # Lista de referencias MKP para cada SO
    so_mkp_reference = []
    # Lista de total de la NC
    nc_amount_total = []
    print('----------------------------------------------------------------')
    print('Creando notas de crédito')
    print('Este proceso tomará unos minutos')
    # Creación de notas de crédito
    try:
        progress_bar = tqdm(total=len(invoice_records), desc="Procesando")
        for each in invoice_records:
            inv_origin_name = each[0]
            inv_id = each[1]
            nc_date = each[2].strftime("%Y-%m-%d %H:%M:%S")
            #Busca la factura que contenga el nombre de la SO
            invoice = models.execute_kw(db_name, uid, password, 'account.move', 'search_read', [[['invoice_origin', '=', inv_origin_name]]])
            if invoice:
                # Se verifica si ya existe una nota de crédito para esta orden de venta
                existing_credit_note = models.execute_kw(db_name, uid, password, 'account.move', 'search', [[['invoice_origin', '=', inv_origin_name], ['move_type', '=', 'out_refund']]])
                if not existing_credit_note:
                #if 'out_refund' not in inv_move_types:
                    for inv in invoice:
                        inv_id = inv['id'] # ID de la factura
                        inv_name = inv['name'] # Nombre de la factura
                        inv_origin = inv['invoice_origin'] # Nombre de la SO ligada a la factura
                        #inv_narration = inv['narration']
                        #inv_uuid = inv_narration[3:-4]
                        inv_uuid = inv['l10n_mx_edi_cfdi_uuid'] # Folio fiscal de la factura
                        inv_journal_id = inv['journal_id'][0] #Diario de la factura
                        inv_state = inv['state']

                        if inv_state == 'posted':
                            #Se hace una llamada al wizard de creación de notas de crédito
                            credit_note_wizard = models.execute_kw(db_name, uid, password, 'account.move.reversal', 'create',
                                                                   [{
                                'refund_method': 'refund',
                                'reason': 'Por efectos de devolución o retorno de una orden',
                                'journal_id': inv_journal_id, }],
                                           {'context': {
                                               'active_ids': [inv_id],
                                               'active_id': inv_id,
                                               'active_model': 'account.move',
                                           }}
                                        )
                            #Se crea la nota de crédito con la info anterior y se usa la función reverse_moves del botón revertir en el wizard
                            nc_inv_create = models.execute_kw(db_name, uid, password, 'account.move.reversal', 'reverse_moves',[credit_note_wizard])
                            nc_id = nc_inv_create['res_id'] # Obtiene el id de la nota de crédito
                            # Agrega un mensaje al chatter de la nota de crédito
                            message = {
                                'body': f"Esta nota de crédito fue creada a partir de la factura: {inv_name}, de la órden {inv_origin}, con folio fiscal {inv_uuid}, a solicitud del equipo de Contabilidad, por el equipo de Tech mediante API.",
                                'message_type': 'comment',
                            }
                            write_msg_tech = models.execute_kw(db_name, uid, password, 'account.move', 'message_post',[nc_id], message)
                            #Confirma la nota de crédito
                            upd_nc_state = models.execute_kw(db_name, uid, password, 'account.move', 'action_post',[nc_id])
                            # Timbramos la nota de crédito
                            # upd_nc_stamp = models.execute_kw(db_name, uid, password, 'account.move', 'button_process_edi_web_services',[nc_id])
                            #buscamos el nombre de la nota creada
                            search_nc_name = models.execute_kw(db_name, uid, password, 'account.move', 'search_read',[[['id', '=', nc_id]]])
                            nc_name = search_nc_name[0]['name']
                            nc_total = search_nc_name[0]['amount_total']
                            sale_order = models.execute_kw(db_name, uid, password, 'sale.order', 'search_read',[[['name', '=', inv_origin_name]]])[0]
                            sale_ref = sale_order['channel_order_reference']
                            #Agregamos a las listas
                            nc_created.append(nc_name)
                            nc_amount_total.append(nc_total)
                            so_modified.append(inv_origin)
                            so_origin_invoice.append(inv_name)
                            so_mkp_reference.append(sale_ref)
                            progress_bar.update(1)
                        else:
                            print(f"La factura de la órden {inv_origin_name} no está confirmada")
                            progress_bar.update(1)
                            continue
                else:
                    print(f"La órden {inv_origin_name} ya tiene una nota de crédito creada")
                    so_with_refund.append(inv_origin_name)
                    progress_bar.update(1)
                    continue
            else:
                print(f"No hay una factura en la SO {inv_origin_name} por la cual se pueda crear una nota de crédito")
                inv_no_exist.append(inv_origin_name)
                progress_bar.update(1)
                continue
    except Exception as e:
        print(f"Error: no se pudo crear la nota de crédito: {e}")
    # Excel
    try:
        # Crear el archivo Excel y agregar los nombres de los arrays y los resultados
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet['A1'] = 'so_modified'
        sheet['B1'] = 'so_mkp_reference'
        sheet['C1'] = 'nc_created'
        sheet['D1'] = 'nc_amount_total'
        sheet['E1'] = 'so_origin_invoice'
        sheet['F1'] = 'inv_no_exist'
        sheet['G1'] = 'so_with_refund'

        # Agregar los resultados de los arrays
        for i in range(len(so_modified)):
            sheet['A{}'.format(i + 2)] = so_modified[i]
        for i in range(len(so_mkp_reference)):
            sheet['B{}'.format(i + 2)] = so_mkp_reference[i]
        for i in range(len(nc_created)):
            sheet['C{}'.format(i + 2)] = nc_created[i]
        for i in range(len(nc_amount_total)):
            sheet['D{}'.format(i + 2)] = nc_amount_total[i]
        for i in range(len(so_origin_invoice)):
            sheet['E{}'.format(i + 2)] = so_origin_invoice[i]
        for i in range(len(inv_no_exist)):
            sheet['F{}'.format(i + 2)] = inv_no_exist[i]
        for i in range(len(so_with_refund)):
            sheet['G{}'.format(i + 2)] = so_with_refund[i]

        # Guardar el archivo Excel en disco
        excel_file = 'notas_credito_individuales_meli_' + today_date.strftime("%Y%m%d") + '.xlsx'
        workbook.save(excel_file)

        # Leer el contenido del archivo Excel
        with open(excel_file, 'rb') as file:
            file_data = file.read()
        file_data_encoded = base64.b64encode(file_data).decode('utf-8')
    except Exception as a:
        print(f"Error: no se pudo crear el archivo de excel: {a}")
    # Correo
    try:
        msg = MIMEMultipart()
        body = '''\
                <html>
                  <head></head>
                  <body>
                    <p>Buenas</p>
                    <p>Hola a todos, espero que estén muy bien. Les comento que acabamos de correr el script de notas de crédito.</p>
                    <p>Adjunto encontrarán el archivo generado por el script en el cual se encuentran las órdenes a las cuales 
                    se les creó una nota de crédito, órdenes que no se les pudo crear una credit_notes, nombre de las notas de crédito 
                    creadas, órdenes que ya contaban con una nota de crédito antes de correr el script y órdenes que tuvieron 
                    algún error, por ejemplo que no existieran dentro de la factura global o no tuvieran una factura creada por la cual se pueda emitir una nota de crédito.</p>
                    </br>
                    <p>Sin más por el momento quedo al pendiente para resolver cualquier duda o comentario.</p>
                    </br>
                    <p>Muchas gracias</p>
                    </br>
                    <p>Un abrazo</p>
                  </body>
                </html>
                '''
        # Define remitente y destinatario
        msg = MIMEMultipart()
        msg['From'] = 'Tech anibal@wonderbrands.co'
        msg['To'] = ', '.join(
            ['anibal@wonderbrands.co', 'rosalba@wonderbrands.co', 'natalia@wonderbrands.co', 'greta@somos-reyes.com',
             'contabilidad@somos-reyes.com', 'alex@wonderbrands.co', 'will@wonderbrands.co'])
        msg['Subject'] = 'Script Automático Meli - Creación de notas de crédito para facturas individuales'
        # Adjuntar el cuerpo del correo
        msg.attach(MIMEText(body, 'html'))
        # Adjuntar el archivo Excel al mensaje
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(file_data)
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment', filename=excel_file)
        msg.attach(attachment)
        print("Enviando correo")
        smtpObj = smtplib.SMTP(smtp_server, smtp_port)
        smtpObj.starttls()
        smtpObj.login(smtp_username, smtp_password)
        smtpObj.sendmail(smtp_username, msg['To'], msg.as_string())
    except Exception as i:
        print(f"Error: no se pudo enviar el correo: {i}")

    print('----------------------------------------------------------------')
    print('PROCESO NC PARA MERCADO LIBRE COMPLETADO :)')
    print('----------------------------------------------------------------')

    # Cierre de conexiones
    progress_bar.close()
    smtpObj.quit()
    mycursor.close()
    mydb.close()
def reverse_invoice_amazon():
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
    print('NOTAS DE CRÉDITO AMAZON')
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
    print('----------------------------------------------------------------')
    print('Vaya por un tecito o un café porque este proceso tomará algo de tiempo')

    mycursor.execute("""SELECT c.name,
                               b.id 'account_move_id',
                               d.refund_date as 'payment_date_last_modified'/*,
                               d.order_id 'order_id',
                               b.amount_total 'total_factura',
                               b.amount_untaxed 'subtotal_factura',
                               d.refunded_amt,
                               b.invoice_partner_display_name 'cliente',
                               b.name,
                               'INDIVIDUAL' as type,
                               'AMAZON' as marketplace*/
                        FROM somos_reyes.odoo_new_account_move_aux b
                        LEFT JOIN odoo_new_sale_order c
                        ON b.invoice_origin = c.name
                        LEFT JOIN (SELECT a.order_id, max(STR_TO_DATE(fecha, '%d/%m/%Y')) 'refund_date', SUM(total - tarifas_de_amazon) * (-1) 'refunded_amt'
                                   FROM somos_reyes.amazon_payments_refunds a
                                   WHERE (total - tarifas_de_amazon) * (-1) > 0 AND STR_TO_DATE(fecha, '%d/%m/%Y') >= '2023-01-01' AND STR_TO_DATE(fecha, '%d/%m/%Y') <= '2023-10-31'
                                   GROUP BY 1) d
                        ON c.channel_order_id = d.order_id
                        LEFT JOIN (SELECT distinct invoice_origin FROM odoo_new_account_move_aux WHERE name like '%RINV%') e
                        ON c.name = e.invoice_origin
                        WHERE d.order_id is not null
                        AND e.invoice_origin is null
                        AND d.refunded_amt - b.amount_total < 1 AND d.refunded_amt - b.amount_total > -1;""")
    invoice_records = mycursor.fetchall()
    # Lista de SO a las que se les creó una credit_notes
    so_modified = []
    # Lista de las facturas enlazadas a la SO y no existen
    inv_no_exist = []
    # Lista de SO que ya contaban con credit_notes antes del script
    so_with_refund = []
    # Lista de nombres de las notas de crédito creadas
    nc_created = []
    # Lista de facturas origen
    so_origin_invoice = []
    # Lista de referencias MKP para cada SO
    so_mkp_reference = []
    # Lista de total de la NC
    nc_amount_total = []
    print('----------------------------------------------------------------')
    print('Creando notas de crédito')
    print('Este proceso tomará unos minutos')
    # Creación de notas de crédito
    try:
        progress_bar = tqdm(total=len(invoice_records), desc="Procesando")
        for each in invoice_records:
            inv_origin_name = each[0]
            inv_id = each[1]
            nc_date = each[2].strftime("%Y-%m-%d %H:%M:%S")
            inv_move_types = [] # Lista en la que se almacenan los tipos de factura para la orden en curso
            #Busca la factura que contenga el nombre de la SO
            invoice = models.execute_kw(db_name, uid, password, 'account.move', 'search_read', [[['invoice_origin', '=', inv_origin_name]]])
            if invoice:
                for type in invoice:
                    exist_nc_type = type['move_type']
                    inv_move_types.append(exist_nc_type)

                # Se verifica si ya existe una nota de crédito para esta orden de venta
                existing_credit_note = models.execute_kw(db_name, uid, password, 'account.move', 'search', [[['invoice_origin', '=', inv_origin_name], ['move_type', '=', 'out_refund']]])
                if not existing_credit_note:
                #if 'out_refund' not in inv_move_types:
                    for inv in invoice:
                        inv_id = inv['id'] # ID de la factura
                        inv_name = inv['name'] # Nombre de la factura
                        inv_origin = inv['invoice_origin'] # Nombre de la SO ligada a la factura
                        #inv_narration = inv['narration']
                        #inv_uuid = inv_narration[3:-4]
                        inv_uuid = inv['l10n_mx_edi_cfdi_uuid'] # Folio fiscal de la factura
                        inv_journal_id = inv['journal_id'][0] #Diario de la factura
                        #Se hace una llamada al wizard de creación de notas de crédito
                        credit_note_wizard = models.execute_kw(db_name, uid, password, 'account.move.reversal', 'create',
                                                               [{
                            'refund_method': 'refund',
                            'reason': 'Por efectos de devolución o retorno de una orden',
                            'journal_id': inv_journal_id, }],
                                       {'context': {
                                           'active_ids': [inv_id],
                                           'active_id': inv_id,
                                           'active_model': 'account.move',
                                       }}
                                    )
                        #Se crea la nota de crédito con la info anterior y se usa la función reverse_moves del botón revertir en el wizard
                        nc_inv_create = models.execute_kw(db_name, uid, password, 'account.move.reversal', 'reverse_moves',[credit_note_wizard])
                        nc_id = nc_inv_create['res_id'] # Obtiene el id de la nota de crédito
                        # Agrega un mensaje al chatter de la nota de crédito
                        message = {
                            'body': f"Esta nota de crédito fue creada a partir de la factura: {inv_name}, de la órden {inv_origin}, con folio fiscal {inv_uuid}, a solicitud del equipo de Contabilidad, por el equipo de Tech mediante API.",
                            'message_type': 'comment',
                        }
                        write_msg_tech = models.execute_kw(db_name, uid, password, 'account.move', 'message_post',[nc_id], message)
                        #Confirma la nota de crédito
                        upd_nc_state = models.execute_kw(db_name, uid, password, 'account.move', 'action_post',[nc_id])
                        # Timbramos la nota de crédito
                        # upd_nc_stamp = models.execute_kw(db_name, uid, password, 'account.move', 'button_process_edi_web_services',[nc_id])
                        #buscamos el nombre de la nota creada
                        search_nc_name = models.execute_kw(db_name, uid, password, 'account.move', 'search_read',[[['id', '=', nc_id]]])
                        nc_name = search_nc_name[0]['name']
                        nc_total = search_nc_name[0]['amount_total']
                        sale_order = models.execute_kw(db_name, uid, password, 'sale.order', 'search_read',[[['name', '=', inv_origin_name]]])[0]
                        sale_ref = sale_order['channel_order_reference']
                        #Agregamos a las listas
                        nc_created.append(nc_name)
                        nc_amount_total.append(nc_total)
                        so_modified.append(inv_origin)
                        so_origin_invoice.append(inv_name)
                        so_mkp_reference.append(sale_ref)
                        progress_bar.update(1)
                else:
                    print(f"La órden {inv_origin_name} ya tiene una nota de crédito creada")
                    so_with_refund.append(inv_origin_name)
                    progress_bar.update(1)
                    continue
            else:
                print(f"No hay una factura en la SO {inv_origin_name} por la cual se pueda crear una nota de crédito")
                inv_no_exist.append(inv_origin_name)
                progress_bar.update(1)
                continue
    except Exception as e:
        print(f"Error: no se pudo crear la nota de crédito: {e}")
    # Excel
    try:
        # Crear el archivo Excel y agregar los nombres de los arrays y los resultados
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet['A1'] = 'so_modified'
        sheet['B1'] = 'so_mkp_reference'
        sheet['C1'] = 'nc_created'
        sheet['D1'] = 'nc_amount_total'
        sheet['E1'] = 'so_origin_invoice'
        sheet['F1'] = 'inv_no_exist'
        sheet['G1'] = 'so_with_refund'

        # Agregar los resultados de los arrays
        for i in range(len(so_modified)):
            sheet['A{}'.format(i + 2)] = so_modified[i]
        for i in range(len(so_mkp_reference)):
            sheet['B{}'.format(i + 2)] = so_mkp_reference[i]
        for i in range(len(nc_created)):
            sheet['C{}'.format(i + 2)] = nc_created[i]
        for i in range(len(nc_amount_total)):
            sheet['D{}'.format(i + 2)] = nc_amount_total[i]
        for i in range(len(so_origin_invoice)):
            sheet['E{}'.format(i + 2)] = so_origin_invoice[i]
        for i in range(len(inv_no_exist)):
            sheet['F{}'.format(i + 2)] = inv_no_exist[i]
        for i in range(len(so_with_refund)):
            sheet['G{}'.format(i + 2)] = so_with_refund[i]

        # Guardar el archivo Excel en disco
        excel_file = 'notas_credito_individuales_amazon_' + today_date.strftime("%Y%m%d") + '.xlsx'
        workbook.save(excel_file)

        # Leer el contenido del archivo Excel
        with open(excel_file, 'rb') as file:
            file_data = file.read()
        file_data_encoded = base64.b64encode(file_data).decode('utf-8')
    except Exception as a:
        print(f"Error: no se pudo crear el archivo de excel: {a}")
    # Correo
    try:
        msg = MIMEMultipart()
        body = '''\
                <html>
                  <head></head>
                  <body>
                    <p>Buenas</p>
                    <p>Hola a todos, espero que estén muy bien. Les comento que acabamos de correr el script de notas de crédito.</p>
                    <p>Adjunto encontrarán el archivo generado por el script en el cual se encuentran las órdenes a las cuales 
                    se les creó una nota de crédito, órdenes que no se les pudo crear una credit_notes, nombre de las notas de crédito 
                    creadas, órdenes que ya contaban con una nota de crédito antes de correr el script y órdenes que tuvieron 
                    algún error, por ejemplo que no existieran dentro de la factura global o no tuvieran una factura creada por la cual se pueda emitir una nota de crédito.</p>
                    </br>
                    <p>Sin más por el momento quedo al pendiente para resolver cualquier duda o comentario.</p>
                    </br>
                    <p>Muchas gracias</p>
                    </br>
                    <p>Un abrazo</p>
                  </body>
                </html>
                '''
        # Define remitente y destinatario
        msg = MIMEMultipart()
        msg['From'] = 'Tech anibal@wonderbrands.co'
        msg['To'] = ', '.join(
            ['anibal@wonderbrands.co', 'rosalba@wonderbrands.co', 'natalia@wonderbrands.co', 'greta@somos-reyes.com',
             'contabilidad@somos-reyes.com', 'alex@wonderbrands.co', 'will@wonderbrands.co'])
        msg['Subject'] = 'Script Automático Amazon - Creación de notas de crédito para facturas individuales'
        # Adjuntar el cuerpo del correo
        msg.attach(MIMEText(body, 'html'))
        # Adjuntar el archivo Excel al mensaje
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(file_data)
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment', filename=excel_file)
        msg.attach(attachment)
        print("Enviando correo")
        smtpObj = smtplib.SMTP(smtp_server, smtp_port)
        smtpObj.starttls()
        smtpObj.login(smtp_username, smtp_password)
        smtpObj.sendmail(smtp_username, msg['To'], msg.as_string())
    except Exception as i:
        print(f"Error: no se pudo enviar el correo: {i}")

    print('----------------------------------------------------------------')
    print('PROCESO NC PARA AMAZON COMPLETADO :)')
    print('----------------------------------------------------------------')

    # Cierre de conexiones
    progress_bar.close()
    smtpObj.quit()
    mycursor.close()
    mydb.close()

if __name__ == "__main__":
    reverse_invoice_meli()
    #reverse_invoice_amazon()
    print('Listo')
    print('Este arroz ya se coció :)')