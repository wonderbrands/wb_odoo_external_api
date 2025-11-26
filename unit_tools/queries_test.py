import datetime
import mysql.connector
import json
import extract_orders as e_o

config_file_name = r'C:\Users\Sergio Gil Guerrero\Documents\WonderBrands\Repos\wb_odoo_external_api\config\config_dev.json'


orders_meli_file_path = 'C:/Users/Sergio Gil Guerrero/Documents/WonderBrands/Finanzas/Marzo/Notas_de_credito_totales_ML.csv'
def get_psql_access():
    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)
    return config['psql']

psql_keys = get_psql_access()

# Connect to MySQL database
mydb = mysql.connector.connect(
    host=psql_keys['dbhost'],
    user=psql_keys['dbuser'],
    password=psql_keys['dbpassword'],
    database=psql_keys['database']
)
mycursor = mydb.cursor()

#FECHAS DEL PERIODO
start_date_str = datetime.date(2024, 3, 1).strftime("%Y-%m-%d")
end_date_str = datetime.date(2024, 3, 24).strftime("%Y-%m-%d")

#QUERIES INDIVIDUALES MELI

def query_ind_meli_hardcode():
    mycursor.execute("""#INDIVIDUALES
                            SELECT c.name,
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
                            LEFT JOIN somos_reyes.odoo_new_sale_order c
                            ON b.invoice_origin = c.name
                            LEFT JOIN (SELECT a.order_id, max(payment_date_last_modified) 'payment_date_last_modified', SUM(paid_amt) 'paid_amt', SUM(refunded_amt) 'refunded_amt', SUM(shipping_amt) 'shipping_amt'
                                       FROM somos_reyes.ml_order_payments a
                                       LEFT JOIN somos_reyes.ml_order_update b
                                       ON a.order_id = b.order_id
                                       WHERE refunded_amt > 0 AND b.pack_id = 'None' AND date(payment_date_last_modified) >= '2024-03-01' AND date(payment_date_last_modified) <= '2024-03-24'
                                       GROUP BY 1) d
                            ON c.channel_order_id = d.order_id
                            LEFT JOIN (SELECT a.pack_id, max(payment_date_last_modified) 'payment_date_last_modified', SUM(b.paid_amt) 'paid_amt', SUM(b.refunded_amt) 'refunded_amt', SUM(shipping_amt) 'shipping_amt'
                            FROM somos_reyes.ml_order_update a
                            LEFT JOIN somos_reyes.ml_order_payments b
                            ON a.order_id = b.order_id
                            WHERE b.refunded_amt > 0 AND a.pack_id <> 'None' AND date(payment_date_last_modified) >= '2024-03-01' AND date(payment_date_last_modified) <= '2024-03-24'
                            GROUP BY 1) dd
                            ON c.yuju_pack_id = dd.pack_id
                            LEFT JOIN (SELECT distinct invoice_origin FROM somos_reyes.odoo_new_account_move_aux WHERE name like '%RINV%') e
                            ON c.name = e.invoice_origin
                            WHERE (d.order_id is not null or dd.pack_id is not null)
                            AND e.invoice_origin is null
                            AND ((ifnull(d.refunded_amt, dd.refunded_amt) - b.amount_total < 1 AND ifnull(d.refunded_amt, dd.refunded_amt) - b.amount_total > -1)
                            OR (ifnull(d.refunded_amt - d.shipping_amt, dd.refunded_amt - dd.shipping_amt) - b.amount_total < 1
                            AND ifnull(d.refunded_amt - d.shipping_amt, dd.refunded_amt - dd.shipping_amt) - b.amount_total > -1))
                            AND c.name in ('SO2813670','SO2770673','SO2807827','SO2797227','SO2815234','SO2770672','SO2823281','SO2764197','SO2748230','SO2787500','SO2831396','SO2797136','SO2709282','SO2753238','SO2770675','SO2770671','SO2711129','SO2765502','SO2802603','SO2799385','SO2816904','SO2792417','SO2792417','SO2784170','SO2830869');
                            """)
    results = mycursor.fetchall()
    for fila in results:
        print(fila)

def query_ind_meli_format():
    type_filter = 'INDIVIDUAL'
    marketplace_filter = 'MERCADO LIBRE'
    list_orders, placeholders, num_records = e_o.filter_orders(orders_meli_file_path, type_filter, marketplace_filter)
    dates_list_params = [start_date_str,end_date_str,start_date_str,end_date_str]
    #print(type(list_orders), tuple(dates_list_params + list_orders))

    mycursor.execute("""#INDIVIDUALES
                            SELECT c.name,
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
                            LEFT JOIN somos_reyes.odoo_new_sale_order c
                            ON b.invoice_origin = c.name
                            LEFT JOIN (SELECT a.order_id, max(payment_date_last_modified) 'payment_date_last_modified', SUM(paid_amt) 'paid_amt', SUM(refunded_amt) 'refunded_amt', SUM(shipping_amt) 'shipping_amt'
                                       FROM somos_reyes.ml_order_payments a
                                       LEFT JOIN somos_reyes.ml_order_update b
                                       ON a.order_id = b.order_id
                                       WHERE refunded_amt > 0 AND b.pack_id = 'None' AND date(payment_date_last_modified) >= %s AND date(payment_date_last_modified) <= %s
                                       GROUP BY 1) d
                            ON c.channel_order_id = d.order_id
                            LEFT JOIN (SELECT a.pack_id, max(payment_date_last_modified) 'payment_date_last_modified', SUM(b.paid_amt) 'paid_amt', SUM(b.refunded_amt) 'refunded_amt', SUM(shipping_amt) 'shipping_amt'
                            FROM somos_reyes.ml_order_update a
                            LEFT JOIN somos_reyes.ml_order_payments b
                            ON a.order_id = b.order_id
                            WHERE b.refunded_amt > 0 AND a.pack_id <> 'None' AND date(payment_date_last_modified) >= %s AND date(payment_date_last_modified) <= %s
                            GROUP BY 1) dd
                            ON c.yuju_pack_id = dd.pack_id
                            LEFT JOIN (SELECT distinct invoice_origin FROM somos_reyes.odoo_new_account_move_aux WHERE name like '%RINV%') e
                            ON c.name = e.invoice_origin
                            WHERE (d.order_id is not null or dd.pack_id is not null)
                            AND e.invoice_origin is null
                            AND ((ifnull(d.refunded_amt, dd.refunded_amt) - b.amount_total < 1 AND ifnull(d.refunded_amt, dd.refunded_amt) - b.amount_total > -1)
                            OR (ifnull(d.refunded_amt - d.shipping_amt, dd.refunded_amt - dd.shipping_amt) - b.amount_total < 1
                            AND ifnull(d.refunded_amt - d.shipping_amt, dd.refunded_amt - dd.shipping_amt) - b.amount_total > -1))
                            AND c.name in ({});
                            """.format(placeholders), tuple(dates_list_params+list_orders))

    results = mycursor.fetchall()
    for fila in results:
        print(fila)

query_ind_meli_hardcode()
print('*****************')
query_ind_meli_format()