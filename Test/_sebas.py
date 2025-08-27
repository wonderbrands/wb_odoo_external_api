import MySQLdb # mysqlclient
import set666 as creds
from datetime import datetime
import pandas as pd

__description__ = """
        Este script obtiene los resultados de las queries de Mercado Libre y Amazon tanto totales como parciales (Individuales y Globales),
        los guarda en documentos CSV. 

        La información que se obtiene son las órdenes que generan reembolsos (notas de crédito) que deben ser cotejadas por el qeuipo de finanzas.

        Se deben modificar los parámetros de fechas de inicio y fin (start_date y end_date), el anio y el mes.
"""


def fetch_data(query_name, query_template, csv_path):
    try:
        connection = MySQLdb.connect(creds.wbh, creds.wbu, creds.wbp, 'somos_reyes', local_infile=True)
        print('\n', 'Conexión iniciada para Query: ', query_name)

        query = query_template
        data_frame = pd.read_sql(query, connection)
        data_frame.to_csv(csv_path, index=False)
        print(f"Consulta ejecutada y resultados guardados en '{csv_path}'")

    except MySQLdb.Error as e:
        print("Error al conectar a la base de datos", e)

    finally:
        if connection:
            connection.close()
            print("Conexión cerrada")


def init_process(start_date,end_date, month, year):

    _start_date = datetime.strptime(start_date, '%d-%m-%Y')
    _end_date = datetime.strptime(end_date, '%d-%m-%Y')

    _start_date = _start_date.strftime('%Y-%m-%d')
    _end_date = _end_date.strftime('%Y-%m-%d')

    # -----------------------------------------------------------------------------------------------------------------------------------------
    # -----------------------------------------------------------------------------------------------------------------------------------------
    csv_path_ML_Totales = f'/Users/sergio/Documents/Trabajo/Wonderbrands/Finanzas/{year}/{month}/Notas_de_credito_totales_ML.csv'
    csv_path_ML_Parciales = f'/Users/sergio/Documents/Trabajo/Wonderbrands/Finanzas/{year}/{month}/Notas_de_credito_parciales_ML.csv'
    csv_path_AMZ_Totales = f'/Users/sergio/Documents/Trabajo/Wonderbrands/Finanzas/{year}/{month}/Notas_de_credito_totales_AMAZON.csv'
    csv_path_AMZ_Parciales = f'/Users/sergio/Documents/Trabajo/Wonderbrands/Finanzas/{year}/{month}/Notas_de_credito_parciales_AMAZON.csv'
    # -----------------------------------------------------------------------------------------------------------------------------------------
    # -----------------------------------------------------------------------------------------------------------------------------------------


    # MERCADO-LIBRE TOTALES
    query_template_ML_Totales = f"""
    #MERCADO-LIBRE TOTALES
    #INDIVIDUALES
    SELECT c.name,
           ifnull(d.order_id, dd.pack_id) 'order_id_or_pack_id',
           c.channel_order_reference 'marketplace reference',
           b.amount_total 'total_factura',
           b.amount_untaxed 'subtotal_factura',
           ifnull(d.refunded_amt, dd.refunded_amt) 'ml_refunded_amount',
           ifnull(d.payment_date_last_modified, dd.payment_date_last_modified) 'payment_date_last_modified',
           b.invoice_partner_display_name 'cliente',
           b.name,
           b.id 'account_move_id',
           'INDIVIDUAL' as type,
           'MERCADO LIBRE' as marketplace
    FROM somos_reyes.odoo_new_account_move_aux b
    LEFT JOIN somos_reyes.odoo_new_sale_order c
    ON b.invoice_origin = c.name
    LEFT JOIN (SELECT a.order_id, max(payment_date_last_modified) 'payment_date_last_modified', SUM(paid_amt) 'paid_amt', SUM(refunded_amt) 'refunded_amt', SUM(shipping_amt) 'shipping_amt'
               FROM somos_reyes.ml_order_payments a
               LEFT JOIN somos_reyes.ml_order_update b
               ON a.order_id = b.order_id
               WHERE refunded_amt > 0 AND b.pack_id = 'None' AND date(payment_date_last_modified) >= '{_start_date}' AND date(payment_date_last_modified) <= '{_end_date}'
               GROUP BY 1) d
    ON c.channel_order_id = d.order_id
    LEFT JOIN (SELECT a.pack_id, max(payment_date_last_modified) 'payment_date_last_modified', SUM(b.paid_amt) 'paid_amt', SUM(b.refunded_amt) 'refunded_amt', SUM(shipping_amt) 'shipping_amt'
    FROM somos_reyes.ml_order_update a
    LEFT JOIN somos_reyes.ml_order_payments b
    ON a.order_id = b.order_id
    WHERE b.refunded_amt > 0 AND a.pack_id <> 'None' AND date(payment_date_last_modified) >= '{_start_date}' AND date(payment_date_last_modified) <= '{_end_date}'
    GROUP BY 1) dd
    ON c.yuju_pack_id = dd.pack_id
    LEFT JOIN (SELECT distinct invoice_origin FROM somos_reyes.odoo_new_account_move_aux WHERE name like '%RINV%') e
    ON c.name = e.invoice_origin
    WHERE (d.order_id is not null or dd.pack_id is not null)
    AND e.invoice_origin is null
    AND ((ifnull(d.refunded_amt, dd.refunded_amt) - b.amount_total < 1 AND ifnull(d.refunded_amt, dd.refunded_amt) - b.amount_total > -1)
    OR (ifnull(d.refunded_amt - d.shipping_amt, dd.refunded_amt - dd.shipping_amt) - b.amount_total < 1
    AND ifnull(d.refunded_amt - d.shipping_amt, dd.refunded_amt - dd.shipping_amt) - b.amount_total > -1))

    UNION ALL
    #GLOBALES
    SELECT c.name,
           ifnull(d.order_id, dd.pack_id) 'order_id_or_pack_id',
           c.channel_order_reference 'marketplace reference',
           b.amount_total 'total_factura',
           b.amount_untaxed 'subtotal_factura',
           ifnull(d.refunded_amt, dd.refunded_amt) 'ml_refunded_amount',
           ifnull(d.payment_date_last_modified, dd.payment_date_last_modified) 'payment_date_last_modified',
           b.invoice_partner_display_name 'cliente',
           b.name,
           b.id 'account_move_id',
           'GLOBAL' as type,
           'MERCADO LIBRE' as marketplace
    FROM somos_reyes.odoo_new_account_move_aux b
    LEFT JOIN somos_reyes.odoo_new_sale_order c
    ON SUBSTRING_INDEX(SUBSTRING_INDEX(invoice_ids, ']', 1), '[', -1) = b.id
    LEFT JOIN (SELECT a.order_id, max(payment_date_last_modified) 'payment_date_last_modified', SUM(paid_amt) 'paid_amt', SUM(refunded_amt) 'refunded_amt', SUM(shipping_amt) 'shipping_amt'
               FROM somos_reyes.ml_order_payments a
               LEFT JOIN somos_reyes.ml_order_update b
               ON a.order_id = b.order_id
               WHERE refunded_amt > 0 AND b.pack_id = 'None' AND date(payment_date_last_modified) >= '{_start_date}' AND date(payment_date_last_modified) <= '{_end_date}'
               GROUP BY 1) d
    ON c.channel_order_id = d.order_id
    LEFT JOIN (SELECT a.pack_id, max(payment_date_last_modified) 'payment_date_last_modified', SUM(b.paid_amt) 'paid_amt', SUM(b.refunded_amt) 'refunded_amt', SUM(shipping_amt) 'shipping_amt'
    FROM somos_reyes.ml_order_update a
    LEFT JOIN somos_reyes.ml_order_payments b
    ON a.order_id = b.order_id
    WHERE b.refunded_amt > 0 AND a.pack_id <> 'None' AND date(payment_date_last_modified) >= '{_start_date}' AND date(payment_date_last_modified) <= '{_end_date}'
    GROUP BY 1) dd
    ON c.yuju_pack_id = dd.pack_id
    LEFT JOIN (SELECT distinct invoice_origin FROM somos_reyes.odoo_new_account_move_aux WHERE name like '%RINV%') e
    ON c.name = e.invoice_origin
    WHERE (d.order_id is not null or dd.pack_id is not null)
    AND e.invoice_origin is null
    AND invoice_partner_display_name = 'PÚBLICO EN GENERAL'
    AND (ifnull(d.refunded_amt, dd.refunded_amt) - b.amount_total > 1 OR ifnull(d.refunded_amt, dd.refunded_amt) - b.amount_total < -1)
    AND (ifnull(d.refunded_amt - d.shipping_amt, dd.refunded_amt - dd.shipping_amt) - b.amount_total > 1 OR ifnull(d.refunded_amt - d.shipping_amt, dd.refunded_amt - dd.shipping_amt) - b.amount_total < -1)
    AND ((ifnull(d.refunded_amt, dd.refunded_amt) - c.amount_total < 1 AND ifnull(d.refunded_amt, dd.refunded_amt) - c.amount_total > -1)
    OR (ifnull(d.refunded_amt - d.shipping_amt, dd.refunded_amt - dd.shipping_amt) - c.amount_total < 1
    AND ifnull(d.refunded_amt - d.shipping_amt, dd.refunded_amt - dd.shipping_amt) - c.amount_total > -1))
    """

    query_name = 'MERCADO-LIBRE TOTALES'
    fetch_data(query_name, query_template_ML_Totales, csv_path_ML_Totales)

    # MERCADO-LIBRE PARCIALES
    query_template_ML_Parciales = f"""
    #MERCADO-LIBRE PARCIALES
    #INDIVIDUALES
    SELECT c.name,
           ifnull(d.order_id, dd.pack_id) 'order_id_or_pack_id',
           c.channel_order_reference 'marketplace reference',
           b.amount_total 'total_factura',
           b.amount_untaxed 'subtotal_factura',
           ifnull(d.refunded_amt, dd.refunded_amt) 'total_so',
           ifnull(d.shipping_amt, dd.shipping_amt) 'ml_refunded_amount',
           ifnull(d.payment_date_last_modified, dd.payment_date_last_modified) 'payment_date_last_modified',
           b.invoice_partner_display_name 'cliente',
           b.name,
           b.id 'account_move_id',
           f.product_id,
           ROUND(ifnull(d.refunded_amt, dd.refunded_amt) / unit_price, 2) 'qty_refunded',
           'INDIVIDUAL' as type,
           'MERCADO LIBRE' as marketplace
    FROM somos_reyes.odoo_new_account_move_aux b

    LEFT JOIN somos_reyes.odoo_new_sale_order c
    ON b.invoice_origin = c.name

    LEFT JOIN (SELECT a.order_id, sku_id,
                      max(payment_date_last_modified) 'payment_date_last_modified',
                      SUM(paid_amt) 'paid_amt',
                      SUM(refunded_amt) 'refunded_amt',
                      SUM(shipping_amt) 'shipping_amt',
                      SUM(refunded_amt) / SUM(sku_unit_price) 'division',
                      ROUND(SUM(refunded_amt) / SUM(sku_unit_price)) 'redondeo'
               FROM somos_reyes.ml_order_payments a
               LEFT JOIN somos_reyes.ml_order_update b
               ON a.order_id = b.order_id
               WHERE refunded_amt > 0 AND b.pack_id = 'None' AND date(payment_date_last_modified) >= '{_start_date}' AND date(payment_date_last_modified) <= '{_end_date}'
               GROUP BY 1, 2
               ) d
    ON c.channel_order_id = d.order_id

    LEFT JOIN (SELECT a.pack_id, sku_id,
                      max(payment_date_last_modified) 'payment_date_last_modified',
                      SUM(b.paid_amt) 'paid_amt',
                      SUM(b.refunded_amt) 'refunded_amt',
                      SUM(shipping_amt) 'shipping_amt',
                      SUM(refunded_amt) / SUM(sku_unit_price) 'division',
                      ROUND(SUM(refunded_amt) / SUM(sku_unit_price)) 'redondeo'
    FROM somos_reyes.ml_order_update a
    LEFT JOIN somos_reyes.ml_order_payments b
    ON a.order_id = b.order_id
    WHERE b.refunded_amt > 0 AND a.pack_id <> 'None' AND date(payment_date_last_modified) >= '{_start_date}' AND date(payment_date_last_modified) <= '{_end_date}'
    GROUP BY 1, 2
    ) dd
    ON c.yuju_pack_id = dd.pack_id

    LEFT JOIN (SELECT distinct invoice_origin FROM somos_reyes.odoo_new_account_move_aux WHERE name like '%RINV%') e
    ON c.name = e.invoice_origin

    LEFT JOIN (SELECT order_name, default_code, product_id, SUM(product_qty) 'product_qty', ROUND(SUM(price_total) / SUM(product_qty), 2) 'unit_price'
               FROM somos_reyes.odoo_new_sale_order_line a
               LEFT JOIN somos_reyes.odoo_new_product_product_bis b
               ON a.product_id = b.id
               WHERE product_id <> '1'
               GROUP BY 1, 2, 3) f
    ON c.name = f.order_name AND ifnull(d.sku_id, dd.sku_id) = f.default_code

    LEFT JOIN (SELECT a.order_id,
                      SUM(refunded_amt) 'refunded_amt',
                      SUM(shipping_amt) 'shipping_amt'
               FROM somos_reyes.ml_order_payments a
               LEFT JOIN somos_reyes.ml_order_update b
               ON a.order_id = b.order_id
               WHERE refunded_amt > 0 AND b.pack_id = 'None' AND date(payment_date_last_modified) >= '{_start_date}' AND date(payment_date_last_modified) <= '{_end_date}'
               GROUP BY 1) t
    ON c.channel_order_id = t.order_id

    LEFT JOIN (SELECT a.pack_id,
                      SUM(b.refunded_amt) 'refunded_amt',
                      SUM(shipping_amt) 'shipping_amt'
    FROM somos_reyes.ml_order_update a
    LEFT JOIN somos_reyes.ml_order_payments b
    ON a.order_id = b.order_id
    WHERE b.refunded_amt > 0 AND a.pack_id <> 'None' AND date(payment_date_last_modified) >= '{_start_date}' AND date(payment_date_last_modified) <= '{_end_date}'
    GROUP BY 1
    ) tt
    ON c.yuju_pack_id = tt.pack_id

    WHERE (d.order_id is not null or dd.pack_id is not null) #QUE TENGA REEMBLSO
    AND e.invoice_origin is null #QUE NO TENGA NOTA DE CREDITO
    AND b.invoice_partner_display_name <> 'PÚBLICO EN GENERAL'
    AND c.amount_total - ifnull(t.refunded_amt, tt.refunded_amt) > 1 #QUE EL MONTO DEL REEMBOLSO SEA MENOR AL MONTO DE LA VENTA
    AND c.amount_total - ifnull(t.refunded_amt - t.shipping_amt, tt.refunded_amt - tt.shipping_amt) > 1 #QUE EL MONTO DEL REEMBOLSO SEA MENOR AL MONTO DE LA VENTA, CONSIDERANDO ENVIO
    AND (b.amount_total - c.amount_total < 1 AND b.amount_total - c.amount_total > (-1)) #QUE SEA INNDIVIDUAL
    AND f.order_name is not null #QUE LA SO TENGA UN SOLO SKU
    AND ROUND(ifnull(d.refunded_amt, dd.refunded_amt) / unit_price, 2) in (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20)

    UNION ALL
    #GLOBALES
    SELECT c.name,
           ifnull(d.order_id, dd.pack_id) 'order_id_or_pack_id',
           c.channel_order_reference 'marketplace reference',
           b.amount_total 'total_factura',
           b.amount_untaxed 'subtotal_factura',
           c.amount_total 'total_so',
           ifnull(d.refunded_amt, dd.refunded_amt) 'ml_refunded_amount',
           ifnull(d.payment_date_last_modified, dd.payment_date_last_modified) 'payment_date_last_modified',
           b.invoice_partner_display_name 'cliente',
           b.name,
           b.id 'account_move_id',
           f.product_id,
           ROUND(ifnull(d.refunded_amt, dd.refunded_amt) / unit_price, 2) 'qty_refunded',
           'GLOBAL' as type,
           'MERCADO LIBRE' as marketplace

    FROM somos_reyes.odoo_new_account_move_aux b
    LEFT JOIN somos_reyes.odoo_new_sale_order c
    ON SUBSTRING_INDEX(SUBSTRING_INDEX(invoice_ids, ']', 1), '[', -1) = b.id
    LEFT JOIN (SELECT a.order_id, sku_id,
                      max(payment_date_last_modified) 'payment_date_last_modified',
                      SUM(paid_amt) 'paid_amt',
                      SUM(refunded_amt) 'refunded_amt',
                      SUM(shipping_amt) 'shipping_amt',
                      SUM(refunded_amt) / SUM(sku_unit_price) 'division',
                      ROUND(SUM(refunded_amt) / SUM(sku_unit_price)) 'redondeo'
               FROM somos_reyes.ml_order_payments a
               LEFT JOIN somos_reyes.ml_order_update b
               ON a.order_id = b.order_id
               WHERE refunded_amt > 0 AND b.pack_id = 'None' AND date(payment_date_last_modified) >= '{_start_date}' AND date(payment_date_last_modified) <= '{_end_date}'
               GROUP BY 1, 2
               ) d
    ON c.channel_order_id = d.order_id
    LEFT JOIN (SELECT a.pack_id, sku_id,
                      max(payment_date_last_modified) 'payment_date_last_modified',
                      SUM(b.paid_amt) 'paid_amt',
                      SUM(b.refunded_amt) 'refunded_amt',
                      SUM(shipping_amt) 'shipping_amt',
                      SUM(refunded_amt) / SUM(sku_unit_price) 'division',
                      ROUND(SUM(refunded_amt) / SUM(sku_unit_price)) 'redondeo'
    FROM somos_reyes.ml_order_update a
    LEFT JOIN somos_reyes.ml_order_payments b
    ON a.order_id = b.order_id
    WHERE b.refunded_amt > 0 AND a.pack_id <> 'None' AND date(payment_date_last_modified) >= '{_start_date}' AND date(payment_date_last_modified) <= '{_end_date}'
    GROUP BY 1, 2
    ) dd
    ON c.yuju_pack_id = dd.pack_id
    LEFT JOIN (SELECT distinct invoice_origin FROM somos_reyes.odoo_new_account_move_aux WHERE name like '%RINV%') e
    ON c.name = e.invoice_origin
    LEFT JOIN (SELECT order_name, default_code, product_id, SUM(product_qty) 'product_qty', ROUND(SUM(price_total) / SUM(product_qty), 2) 'unit_price'
               FROM somos_reyes.odoo_new_sale_order_line a
               LEFT JOIN somos_reyes.odoo_new_product_product_bis b
               ON a.product_id = b.id
               WHERE product_id <> '1'
               GROUP BY 1, 2, 3) f
    ON c.name = f.order_name AND ifnull(d.sku_id, dd.sku_id) = f.default_code
    LEFT JOIN (SELECT a.order_id,
                      SUM(refunded_amt) 'refunded_amt',
                      SUM(shipping_amt) 'shipping_amt'
               FROM somos_reyes.ml_order_payments a
               LEFT JOIN somos_reyes.ml_order_update b
               ON a.order_id = b.order_id
               WHERE refunded_amt > 0 AND b.pack_id = 'None' AND date(payment_date_last_modified) >= '{_start_date}' AND date(payment_date_last_modified) <= '{_end_date}'
               GROUP BY 1) t
    ON c.channel_order_id = t.order_id

    LEFT JOIN (SELECT a.pack_id,
                      SUM(b.refunded_amt) 'refunded_amt',
                      SUM(shipping_amt) 'shipping_amt'
    FROM somos_reyes.ml_order_update a
    LEFT JOIN somos_reyes.ml_order_payments b
    ON a.order_id = b.order_id
    WHERE b.refunded_amt > 0 AND a.pack_id <> 'None' AND date(payment_date_last_modified) >= '{_start_date}' AND date(payment_date_last_modified) <= '{_end_date}'
    GROUP BY 1
    ) tt
    ON c.yuju_pack_id = tt.pack_id
    WHERE (d.order_id is not null or dd.pack_id is not null)
    AND e.invoice_origin is null
    AND invoice_partner_display_name = 'PÚBLICO EN GENERAL'
    AND c.amount_total - ifnull(t.refunded_amt, tt.refunded_amt) > 1
    AND c.amount_total - ifnull(t.refunded_amt - t.shipping_amt, tt.refunded_amt - tt.shipping_amt) > 1
    AND (b.amount_total - c.amount_total > 1 OR b.amount_total - c.amount_total < (-1))
    AND f.order_name is not null
    AND ROUND(ifnull(d.refunded_amt, dd.refunded_amt) / unit_price, 2) in (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20)
    """

    query_name = 'MERCADO-LIBRE PARCIALES'
    fetch_data(query_name, query_template_ML_Parciales, csv_path_ML_Parciales)

    # AMAZON TOTALES
    query_template_AMZ_Totales = f"""
    #AMAZON TOTALES
    #INDIVIDUALES
    SELECT c.name,
           d.order_id 'order_id',
           c.channel_order_reference 'marketplace reference',
           b.amount_total 'total_factura',
           b.amount_untaxed 'subtotal_factura',
           d.refunded_amt,
           d.refund_date,
           b.invoice_partner_display_name 'cliente',
           b.name,
           b.id 'account_move_id',
           'INDIVIDUAL' as type,
           'AMAZON' as marketplace
    FROM somos_reyes.odoo_new_account_move_aux b

    LEFT JOIN somos_reyes.odoo_new_sale_order c
    ON b.invoice_origin = c.name

    LEFT JOIN (SELECT a.order_id, max(STR_TO_DATE(fecha, '%m/%d/%Y')) 'refund_date', SUM(total - tarifas_de_amazon) * (-1) 'refunded_amt'
               FROM somos_reyes.amazon_payments_refunds a
               WHERE (total - tarifas_de_amazon) * (-1) > 0 AND STR_TO_DATE(fecha, '%m/%d/%Y') >= '{_start_date}' AND STR_TO_DATE(fecha, '%m/%d/%Y') <= '{_end_date}'
               GROUP BY 1) d
    ON c.channel_order_id = d.order_id

    LEFT JOIN (SELECT distinct invoice_origin FROM somos_reyes.odoo_new_account_move_aux WHERE name like '%RINV%') e
    ON c.name = e.invoice_origin

    WHERE d.order_id is not null
    AND e.invoice_origin is null
    AND d.refunded_amt - b.amount_total < 1 AND d.refunded_amt - b.amount_total > -1

    UNION ALL

    #GLOBALES
    SELECT c.name,
           d.order_id,
           c.channel_order_reference 'marketplace reference',
           b.amount_total 'total_factura',
           b.amount_untaxed 'subtotal_factura',
           d.refunded_amt,
           refund_date,
           b.invoice_partner_display_name 'cliente',
           b.name,
           b.id 'account_move_id',
           'GLOBAL' as type,
           'AMAZON' as marketplace
    FROM somos_reyes.odoo_new_account_move_aux b
    LEFT JOIN somos_reyes.odoo_new_sale_order c
    ON SUBSTRING_INDEX(SUBSTRING_INDEX(invoice_ids, ']', 1), '[', -1) = b.id
    LEFT JOIN (SELECT a.order_id, max(STR_TO_DATE(fecha, '%m/%d/%Y')) 'refund_date', SUM(total - tarifas_de_amazon) * (-1) 'refunded_amt'
               FROM somos_reyes.amazon_payments_refunds a
               WHERE (total - tarifas_de_amazon) * (-1) > 0 AND STR_TO_DATE(fecha, '%m/%d/%Y') >= '{_start_date}' AND STR_TO_DATE(fecha, '%m/%d/%Y') <= '{_end_date}'
               GROUP BY 1) d
    ON c.channel_order_id = d.order_id
    LEFT JOIN (SELECT distinct invoice_origin FROM somos_reyes.odoo_new_account_move_aux WHERE name like '%RINV%') e
    ON c.name = e.invoice_origin
    WHERE d.order_id is not null
    AND e.invoice_origin is null
    AND invoice_partner_display_name = 'PÚBLICO EN GENERAL'
    AND (d.refunded_amt - b.amount_total > 1 OR d.refunded_amt - b.amount_total < -1)
    AND d.refunded_amt - c.amount_total < 1 AND d.refunded_amt - c.amount_total > -1;
    """

    query_name = 'AMAZON TOTALES'
    fetch_data(query_name, query_template_AMZ_Totales, csv_path_AMZ_Totales)

    # AMAZON PARCIALES
    query_template_AMZ_Parciales = f"""
    #AMAZON PARCIALES
    #INDIVIDUALES
    SELECT c.name,
           d.order_id 'order_id',
           c.channel_order_reference 'marketplace reference',
           b.amount_total 'total_factura',
           b.amount_untaxed 'subtotal_factura',
           d.refunded_amt,
           d.refund_date,
           b.invoice_partner_display_name 'cliente',
           b.name,
           b.id 'account_move_id',
           f.product_id,
           ROUND(d.refunded_amt / unit_price, 2) 'qty_refunded',
           'INDIVIDUAL' as type,
           'AMAZON' as marketplace
    FROM somos_reyes.odoo_new_account_move_aux b

    LEFT JOIN somos_reyes.odoo_new_sale_order c
    ON b.invoice_origin = c.name

    LEFT JOIN (SELECT a.order_id, max(STR_TO_DATE(fecha, '%m/%d/%Y')) 'refund_date', SUM(total - tarifas_de_amazon) * (-1) 'refunded_amt'
               FROM somos_reyes.amazon_payments_refunds a
               WHERE (total - tarifas_de_amazon) * (-1) > 0 AND STR_TO_DATE(fecha, '%m/%d/%Y') >= '{_start_date}' AND STR_TO_DATE(fecha, '%m/%d/%Y') <= '{_end_date}'
               GROUP BY 1) d
    ON c.channel_order_id = d.order_id

    LEFT JOIN (SELECT distinct invoice_origin FROM somos_reyes.odoo_new_account_move_aux WHERE name like '%RINV%') e
    ON c.name = e.invoice_origin

    LEFT JOIN (SELECT order_name, MAX(product_id) 'product_id', SUM(product_qty) 'product_qty', COUNT(distinct product_id) 'cuenta', SUM(price_total) / SUM(product_qty) 'unit_price'
               FROM somos_reyes.odoo_new_sale_order_line a
               LEFT JOIN somos_reyes.odoo_new_product_product_bis b
               ON a.product_id = b.id
               WHERE product_id <> '1'
               GROUP BY 1
               HAVING cuenta = 1) f
    ON c.name = f.order_name

    WHERE d.order_id is not null
    AND e.invoice_origin is null

    AND c.amount_total - d.refunded_amt > 1 #QUE EL REEMBOLSO SEA MENOR A LA SO
    AND (b.amount_total - c.amount_total < 1 AND b.amount_total - c.amount_total > (-1)) #QUE SEA INDIVIDUAL
    AND f.order_name is not null
    AND ROUND(d.refunded_amt / unit_price, 2) in (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20)

    UNION ALL
    #GLOBALES
    SELECT c.name,
           d.order_id,
           c.channel_order_reference 'marketplace reference',
           b.amount_total 'total_factura',
           b.amount_untaxed 'subtotal_factura',
           d.refunded_amt,
           refund_date,
           b.invoice_partner_display_name 'cliente',
           b.name,
           b.id 'account_move_id',
           f.product_id,
           ROUND(d.refunded_amt / unit_price, 2) 'qty_refunded',
           'GLOBAL' as type,
           'AMAZON' as marketplace
    FROM somos_reyes.odoo_new_account_move_aux b
    LEFT JOIN somos_reyes.odoo_new_sale_order c
    ON SUBSTRING_INDEX(SUBSTRING_INDEX(invoice_ids, ']', 1), '[', -1) = b.id
    LEFT JOIN (SELECT a.order_id, max(STR_TO_DATE(fecha, '%m/%d/%Y')) 'refund_date', SUM(total - tarifas_de_amazon) * (-1) 'refunded_amt'
               FROM somos_reyes.amazon_payments_refunds a
               WHERE (total - tarifas_de_amazon) * (-1) > 0 AND STR_TO_DATE(fecha, '%m/%d/%Y') >= '{_start_date}' AND STR_TO_DATE(fecha, '%m/%d/%Y') <= '{_end_date}'
               GROUP BY 1) d
    ON c.channel_order_id = d.order_id
    LEFT JOIN (SELECT distinct invoice_origin FROM somos_reyes.odoo_new_account_move_aux WHERE name like '%RINV%') e
    ON c.name = e.invoice_origin
    LEFT JOIN (SELECT order_name, MAX(product_id) 'product_id', SUM(product_qty) 'product_qty', COUNT(distinct product_id) 'cuenta', SUM(price_total) / SUM(product_qty) 'unit_price'
               FROM somos_reyes.odoo_new_sale_order_line
               WHERE product_id <> '1'
               GROUP BY 1
               HAVING cuenta = 1) f
    ON c.name = f.order_name
    WHERE d.order_id is not null
    AND e.invoice_origin is null
    AND invoice_partner_display_name = 'PÚBLICO EN GENERAL'
    AND c.amount_total - d.refunded_amt > 1
    AND (b.amount_total - c.amount_total > 1 OR b.amount_total - c.amount_total < (-1))
    AND f.order_name is not null
    AND ROUND(d.refunded_amt / unit_price, 2) in (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20)
    """

    query_name = 'AMAZON PARCIALES'
    fetch_data(query_name, query_template_AMZ_Parciales, csv_path_AMZ_Parciales)




if __name__ == '__main__':
    # FECHAS   dia-mes-año

    start_date = '29-05-2025'
    end_date = '26-06-2025'
    month_ = 'Julio'
    year_ = '2025'

    # ************************************

    init_process(start_date,end_date, month_, year_)



