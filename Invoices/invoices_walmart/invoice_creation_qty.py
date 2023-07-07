import time

from flask import Flask, render_template, request, make_response, url_for, session
from os import listdir
from os.path import isfile, join
from datetime import date, datetime, timedelta
import json
import jsonrpc
import jsonrpclib
import random
import urllib.request
import getpass
import http
import requests
from pprint import pprint
import logging
import zipfile
import socket
import os
import xmlrpc.client
import base64
import openpyxl
import xlrd
import pandas as pd
#import MySQLdb
import mysql.connector

#API Configuration
dir_path = os.path.dirname(os.path.realpath(__file__))

#server_url  ='https://wonderbrands.odoo.com'
#db_name = 'wonderbrands-main-4539884'
#username = 'admin'
#password = 'nK738*rxc#nd'

server_url  ='https://wonderbrands-v3-8866939.dev.odoo.com'
db_name = 'wonderbrands-v3-8866939'
username = 'admin'
password = 'nK738*rxc#nd'

print('----------------------------------------------------------------')
print('SCRIPT DE CREACIÓN DE FACTURAS POR ITEM')
print('----------------------------------------------------------------')
print('Conectando API Odoo')
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(server_url))
uid = common.authenticate(db_name, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(server_url))
print(common)
print('Conexión con Odoo establecida')
print('----------------------------------------------------------------')
print('Conectando a Mysql')
print('----------------------------------------------------------------')
# Connect to MySQL database
mydb = mysql.connector.connect(
  host="wonderbrands1.cuwd36ifbz5t.us-east-1.rds.amazonaws.com",
  user="anibal",
  password="Tuy0TEZOcXAwBgtb",
  database="tech"
)
mycursor = mydb.cursor()
print(f"Leyendo query")
print('Este proceso tomará algo de tiempo, le recomendamos ir por un café')
print('----------------------------------------------------------------')
mycursor.execute("""select b.order_id, a.uuid, a.fecha
                    from finance.sr_sat_emitidas a
                    left join somos_reyes.odoo_master_txns_c b
                        on a.folio = b.marketplace_order_id
                    where a.folio in
                        (702235000576,716236901178,350234600546,717235102501,702235000576,351234703312,347234101773,717237103277,351234703312,352234104142,352234300482,350232602407,716235900047,351232401685,718235004113,351234403964,718236702661,352234000811,718235004113,350233901839,350233900449,717236200325,719236800176,352234100414,353232603557,686236901102,353233700844,353233702395,352232400554,353233902929,349234601162,718236601569,354233400027,356232902685,349233400030,720236301156,353234603399,354232401147,354233400027,354233400027,722234904076,354233400027,354233400027,720235000304,354232401147,722234903687,354232403606,354232401147,354232401147,720234802701,355234200712,721237001220,716236502553,355232501428,355234200712,720236500853,350232504356,720236602545,352234202508,351234602252,721237101431,722236200356,354232502380,354232502380,356232500047,719235002693,356234301207,723236602063,356234303188,723235002984,356234501508,720236803280,722236602438,356234203723,357234403846,356234500333,356234600811,720236803280,722236103528,723235303785,354233803282,359234401292,720236201017,354233803282,354233803282,359234401292,691236900716,720236201017,356233703318,354233803282,726234800137,356233703318,720236201017,359233000253,338233901703,726235400539,356234301040,354233803282,717236901619,354232802611,722236601046,714236902329,352234601500,721235001099,351233705735,718235001797,357234104383,723236000710,358232805641,721235001099,359233900057,718236400903,724235305147,357234405023,722234901925,722237102951,359232900920,721235001099,723236804153,723236504662,727236200248,361234501367,722236404136,358234400191,358234400224,361234101671,726236300187,681236500769,722236604583,360234600443,353233703018,357234103214,358234400224,358234400224,700235000487,353234302512,700235000487,106576243975,700235000487,700235000487,700235000487,728236400321,362233900723,721237000391,727235301304,363232601946,356234100447,720234903298,681236500769,726236601039,726236601039,365232700338,726236601039,731235001303,697236501844,356234100059,359234200910,365233900719,732234900096,351233901091,364232400656,361234000800,356233700374,351234602523,714234901092,351234602523,351234602523,720236301822,720236301822,365234401762,731236801815,730236801815,106353414022,723235200071,366234601817,730236801815,106622823296,350234101655,350234101655,356232701890,731236801815,730236801815,730236801815,731236801815,106617799919,730236801815,731235101498,365234401762,731236801815,365233900969,731236801815,736235000775,730236700070,731236401863,730236700070,734237101019,357234101512,364234500419,364234500419,366233800936,734237101019,364234500419,364234500419,360232900096,731236401863,364234500419,366233800936,734235101009,734236400199,730236700070,364234500419,730236200752,360232900096,366233800936,731236401863,364234500419,364234500419,730236700070,364234500419,364234500419,366233800936,724235204125,726236801356,696234900335,371232900994,737234800889,106581530178,359232901399,737236601693,359232700786,357234701553,106648096770,106648096770,106648096770,106648096770,106648096770,371232601375,727235400444,364232602053,364234701871,727235400444,727235400444,727235400444,730235101277,364232602053,730235101235,730235101277,364232701825,730235100661,364232602053,733237000379,730235101277,727235400444,364232701812,725235201104,364232602053,730235100661,364232602053,730235101277,725235201104,730235101277,730235100661,730235100680,730235100661,730235100661,371234401715,739236700330,372234400784,372232701406,372234400784,365233800935,372234400784,737237102388,372234400784,372234400784,738236500664,738236500664,730236702176,737234900708,742235001243,738236600972,738236500664,737234900708,372234100924,737234900708,737234900708,375234501686,369234402023,740236400703,729235500045,372234600170,732237003562,374234401939,740237001625,729235500045,357234604393,374234501016,354233802944,374234401939,371234601146,374234501016,740237001625,729235500045,358234000888,717237003295)
                    group by a.uuid
                    order by b.order_id""")
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
    so_name = row[0]
    xml_name = row[1]
    xml_date = date_year + row[2].strftime("%y-%m-%d %H:%M:%S")

    if so_name not in xml_dict:
        xml_dict[so_name] = []

    xml_dict[so_name].append(xml_name)
    xml_dict[so_name].append(xml_date)
for so_order, xml_files in xml_dict.items():
    value_position = 0
    value_position_date = 1
    so_domain = ['name', '=', so_order]
    for xml_ids in so_order[1]:
        xml_list.append(xml_ids)
    sale_ids = models.execute_kw(db_name, uid, password,'sale.order', 'search_read', [[so_domain]])
    order_name = sale_ids[0]['name']
    order_state = sale_ids[0]['state']
    print(f"Orden de venta encontrada en el sistema")
    try:
        if order_state == 'done':
            if sale_ids:
                invoice_count = sale_ids[0]['invoice_count']
                if invoice_count < 1:
                    # Create invoice for sales order
                    sale_id = int(sale_ids[0]['id'])
                    #for sale_order in sale_ids:
                    #sale_id = int(sale_order['id'])
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
                    # Call to sale order line to get order line data
                    sol_domain = ['id', 'in', sale_order_line_id]
                    sale_order_line = models.execute_kw(db_name, uid, password, 'sale.order.line', 'search_read', [[sol_domain]])
                    for inv_lines in sale_order_line:
                        qty_delivered = round(inv_lines['qty_delivered'])
                        qty_uom = round(inv_lines['product_uom_qty'])
                        if qty_delivered != 0:
                            for qty in range(qty_delivered):
                                print("DATOS DE FACTURA")
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
                                }
                                #line_id = sale_order_line[0]['id']
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
                                create_inv = models.execute_kw(db_name, uid, password, 'account.move', 'create', [invoice])
                                print('La factura de la orden: ', invoice_origin, 'fue creada con ID: ', create_inv)
                                #Busca la factura para agregar mensaje en el chatter
                                print(f"Agregando mensaje a la factura")
                                search_inv = models.execute_kw(db_name, uid, password, 'account.move', 'search_read', [[['id', '=', create_inv]]])
                                inv_ids.append(create_inv)
                                message = {
                                    'body': 'Esta factura fue creada por el equipo de Tech vía API',
                                    'message_type': 'comment',
                                }
                                write_msg_inv = models.execute_kw(db_name, uid, password, 'account.move', 'message_post', [create_inv], message)
                                # Busca el UUID relacionada con la factura
                                if xml_files:
                                    #Obtiene el nombre del XML y la fecha, modifica el nombre del XML y lo pone en mayúsculas
                                    file_name = xml_files[value_position]
                                    file_date = xml_files[value_position_date]
                                    file_name_mayus = file_name.upper()
                                    print(f"AGREGANDO ARCHIVO XML A LA FACTURA")
                                    invoices_folder = 'G:/Mi unidad/xml_sr_mkp_invoices/Junio/'
                                    print(f"El xml {file_name} será agregado a la factura")
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
                                    print('AGREGANDO REGISTRO XML A LA TABLA DOCUMENTOS EDI')
                                    edi_document = models.execute_kw(db_name, uid, password, 'account.edi.document', 'create', values)
                                    print('Registro account.edi.document creado')
                                    #Modifica la fecha de la factura por la del xml
                                    print(f"Se Modifica la fecha de factura: {file_date}")
                                    upd_inv_date = models.execute_kw(db_name, uid, password, 'account.move', 'write',[[create_inv], {'invoice_date': file_date}])
                                    upd_inv_date_term = models.execute_kw(db_name, uid, password, 'account.move', 'write',[[create_inv], {'invoice_payment_term_id': 1}])
                                    #Valida la factura llamando al botón "Confirmar"
                                    upd_invoice_state = models.execute_kw(db_name, uid, password, 'account.move','action_post', [create_inv])
                                    print('Se publica la factura: ', create_inv)
                                    #Agrega el folio fiscal del XML a la factura y al campo de narration (parche realizado momentaneamente)
                                    print(f"Se agrega el folio fiscal: {file_name_mayus}")
                                    upd_folio_fiscal = models.execute_kw(db_name, uid, password, 'account.move','write', [[create_inv], {'l10n_mx_edi_cfdi_uuid': file_name_mayus}])
                                    upd_folio_fiscal_narr = models.execute_kw(db_name, uid, password, 'account.move','write', [[create_inv], {'narration': file_name_mayus}])
                                    #Busca el nombre de la factura una vez publicada meramente infomativo
                                    search_inv_name = models.execute_kw(db_name, uid, password, 'account.move','search_read', [[['id', '=', create_inv]]])
                                    inv_name = search_inv_name[0]['name']
                                    #posiciones de los array
                                    value_position += 2
                                    value_position_date += 2
                                    sales_mod.append(order_name)
                                    inv_names.append(inv_name)
                                    #print(f"ESTE ES LA POSICION DEL ARRAY: {value_position}")
                                    print('-------------------------------------------------------')
                                else:
                                    print(f'La orden: {order_name} no tiene un XML en la carpeta')
                                    sales_no_xml.append(order_name)
                                    continue
                        else:
                            print(f"La cantidad entregada es igual a {qty_delivered}")
                            print(f"Se tomará en cuenta el campo qty_uom")
                            for qty in range(qty_uom):
                                print("DATOS DE FACTURA")
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
                                print('La factura de la orden: ', invoice_origin, 'fue creada con ID: ', create_inv)
                                # Busca la factura para agregar mensaje en el chatter
                                print(f"Agregando mensaje a la factura")
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
                                    file_name = xml_files[value_position]
                                    file_name_mayus = file_name.upper()
                                    print(f"AGREGANDO ARCHIVO XML A LA FACTURA")
                                    # invoices_folder = dir_path + '/xml/'
                                    invoices_folder = 'G:/Mi unidad/xml_sr_mkp_invoices/Junio/'
                                    print(f"El xml {file_name} será agregado a la factura")

                                    xml_file = file_name + '.xml'
                                    xml_file_path = os.path.join(invoices_folder, xml_file)
                                    with open(xml_file_path, 'rb') as f:
                                        xml_data = f.read()
                                    xml_base64 = base64.b64encode(xml_data).decode('utf-8')

                                    attachment_data = {
                                        'name': xml_file,
                                        'datas': xml_base64,
                                        'res_model': 'account.move',
                                        'res_id': create_inv,
                                    }

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
                                    print('AGREGANDO REGISTRO XML A LA TABLA DOCUMENTOS EDI')
                                    edi_document = models.execute_kw(db_name, uid, password, 'account.edi.document',
                                                                     'create', values)
                                    print('Valores para la tabla Documentos EDI: ', values)
                                    print('Registro account.edi.document creado')
                                    # upd_invoice_state = models.execute_kw(db_name, uid, password, 'account.move', 'write',[[create_inv], {'state': 'posted'}])
                                    upd_invoice_state = models.execute_kw(db_name, uid, password, 'account.move', 'action_post', [create_inv])
                                    print(f"Se publica la factura: {create_inv}")
                                    value_position += 1
                                    print(f"Se agrega el folio fiscal: {file_name_mayus}")
                                    upd_folio_fiscal = models.execute_kw(db_name, uid, password, 'account.move','write', [[create_inv], {'l10n_mx_edi_cfdi_uuid': file_name_mayus}])
                                    # print(f"ESTE ES LA POSICION DEL ARRAY: {value_position}")
                                    print('-------------------------------------------------------')
                                else:
                                    print(f'La orden: {order_name} no tiene un XML en la carpeta')
                                    continue
                else:
                    print(f'La orden de venta: {order_name} ya tiene una factura creada')
                    print('----------------------------------------------------------------')
                    sales_w_inv.append(order_name)
                    continue
            else:
                print(f'El ID de la orden: {order_name} no coincide con ninguna venta en Odoo')
                sales_no_exist.append(order_name)
                continue
        else:
            print(f"Revise el estatus de la orden {order_name} se encuentra en estatus {order_state}")
            print(f"Por lo que esta orden no puede ser facturada")
            sales_error_state.append(order_name)
            continue
    except Exception as e:
        print(f"Error al crear la factura de la orden {order_name}: {e}")

print(f"Ordenes que no están en done {sales_error_state}")
print(f"Ordenes que no existen en Odoo {sales_no_exist}")
print(f"Ordenes que ya tenían una factura {sales_w_inv}")
print(f"Ordenes sin XML {sales_no_xml}")
print(f"Ordenes a las que se les creo factura: {sales_mod}")
print(f"Nombre de las facturas creadas: {inv_names}")
print(f"IDs de las facturas creadas: {inv_ids}")

mycursor.close()
mydb.close()
