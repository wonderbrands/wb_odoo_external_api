import time
import xmlrpc.client
import os
import logging
# from dotenv import load_dotenv
from datetime import datetime, timedelta
# load_dotenv()
now = datetime.now()
import json
import time as tm

__description__ = """
Script para solucionar problema en ordenes que no se actualizaron y por ende no se les colocaron
sus 3 movimientos en el caso de Almacen General.

Obtiene las ordenes con el mensaje de 'not serialize' encontradas en el mes presente.
Para cada una de ellas, revisa si no estan hechas.
Almacena los productos y cantidades, pone en borrador la orden, despues elimina las lineas de productos
en cada orden, vuelve a colocar los prodcutos y cantidades conrrectas, confirma la orden nuevamente. 
 
Autor: Will Colin
"""

if not os.path.exists("logs"):
    os.makedirs("logs")
log_filename = f"{datetime.now().strftime('%Y-%m-%d')}.log"
log_path = os.path.join('logs', log_filename)
logging.basicConfig(filename=log_path, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def search_sales_with_message(start_day, end_day):
    try:
        # Obtener el primer día y el último día del mes actual
        today = datetime.today()
        today = today - timedelta(days=30)
        print(today)
        first_day_of_month = today.replace(day=1)
        last_day_of_month = today.replace(day=1, month=today.month+1) - timedelta(days=1)

        # Filtrar ventas del mes actual con mensaje "could not serialize"
        domain = [
            ('state', '!=', 'cancel'), # ('state', '!=', 'cancel'),('state', '=', 'sale')
            ('create_date', '>=', (start_day + ' 00:00:00')),
            ('create_date', '<=', (end_day + ' 23:59:59')),
            ('message_ids.body', 'ilike', 'insufficient stock 0'),
            # ('create_date', '>=', first_day_of_month.strftime('%Y-%m-%d 00:00:00')),
            # ('create_date', '<=', last_day_of_month.strftime('%Y-%m-%d 23:59:59')),
            # ('message_ids.body', 'ilike', 'serialize'),
            ('name', '=', 'SO3340927')
        ]

        # Buscar órdenes de venta que cumplan con los criterios
        sales_orders = models.execute_kw(odoo_db, uid, odoo_password,
                                          'sale.order', 'search_read',
                                          [domain],
                                          {'fields': ['id', 'name','state','delivery_count','warehouse_id'], 'limit':0})
        return sales_orders
    except Exception as e:
        print("Error al buscar las órdenes de venta:", e)
        return None
def search_order_line(sale_id):
    try:
        # Buscar orden de venta por nombre
        order_line = models.execute_kw(odoo_db, uid, odoo_password, 'sale.order.line', 'search_read',
                                       [[['order_id', '=', sale_id]]], {'limit': 1})
        if order_line:
            return order_line
        else:
            print("No se encontró ninguna linea de la orden de venta con ese nombre.")
            return None
    except Exception as e:
        print("Error al buscar la linea de la orden de venta:", e)
        return None
def update_order_line(sale_id, product_id, price_unit,quantity):
    try:
        # Eliminar la línea de pedido
        order_line_ids = models.execute_kw(odoo_db, uid, odoo_password, 'sale.order.line', 'search', [[['order_id', '=', sale_id], ['product_id', '=', product_id]]])
        if order_line_ids:
            delete_result = models.execute_kw(odoo_db, uid, odoo_password, 'sale.order.line', 'unlink', [order_line_ids])
            if delete_result:
                print("Línea de pedido eliminada exitosamente.")
            else:
                print("Error al eliminar la línea de pedido.")
                return None
        else:
            print("No se encontró ninguna línea de pedido con el producto especificado.")
            return None
        # Actualizar la orden de venta
        update_result = models.execute_kw(odoo_db, uid, odoo_password, 'sale.order', 'write', [[sale_id], {'order_line': [(0, 0, {'product_id': product_id,'price_unit': price_unit,'product_uom_qty': quantity,})]}])
        if update_result:
            print("Orden de venta actualizada exitosamente.")
            return update_result
        else:
            print("Error al actualizar la orden de venta.")
            return None
    except Exception as e:
        print("Error al actualizar la orden de venta:", e)
        return None
def cancel_order(sale_id):
    try:
        # Buscar orden de venta por nombre
        cancel = models.execute_kw(odoo_db, uid, odoo_password, 'sale.order', 'action_cancel',[[sale_id]])
        if cancel:
            return cancel
        else:
            print("No se pudo cancelar la orden de venta.")
            return None
    except Exception as e:
        print("Error al cancelar la orden de venta:", e)
        return None
def confirm_order(sale_id):
    try:
        # Buscar orden de venta por nombre
        confirm = models.execute_kw(odoo_db, uid, odoo_password, 'sale.order', 'action_confirm',[[sale_id]])
        if confirm:
            return confirm
        else:
            print("No se pudo cancelar la orden de venta.")
            return None
    except Exception as e:
        print("Error al cancelar la orden de venta:", e)
        return None
def draft_order(sale_id):
    try:
        # Buscar orden de venta por nombre
        draft = models.execute_kw(odoo_db, uid, odoo_password, 'sale.order', 'action_draft',[[sale_id]])
        if draft:
            return draft
        else:
            print("No se pudo cambiar a borrador la orden de venta.")
            return None
    except Exception as e:
        print("Error al cambiar a borrador  la orden de venta:", e)
        return None

def get_odoo_access():
    config_file = 'config.json'
    config_file_name = rf'C:\Users\Sergio Gil Guerrero\Documents\WonderBrands\Repos\wb_odoo_external_api\config\{config_file}'

    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)
    return config['odoo']

if __name__ == "__main__":

    # RANGO DE FECHAS
    start_day = '2024-08-01'
    end_day = '2024-11-27'

    try:

        odoo_keys = get_odoo_access()

        # Obtener los datos de conexión
        odoo_url = odoo_keys['odoourl']
        odoo_db = odoo_keys['odoodb']
        odoo_user = odoo_keys['odoouser']
        odoo_password = odoo_keys['odoopassword']
        json_endpoint = "%s/jsonrpc" % odoo_url
        headers = {"Content-Type": "application/json"}
        user_id = 2

        print('----------------------------------------------------------------')
        print('Conectando API Odoo')
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(odoo_url))
        uid = common.authenticate(odoo_db, odoo_user, odoo_password, {})
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(odoo_url))
        print('Conexión con Odoo establecida')
        print('----------------------------------------------------------------')

        # Buscar órdenes de venta con mensaje "could not serialize"
        sales_orders = search_sales_with_message(start_day, end_day)
        print(len(sales_orders))
        for order in sales_orders:
            sale_id = order['id']
            sale_name = order['name']
            status_order = order['state']
            print(sale_id, sale_name)
        tm.sleep(1)
        if sales_orders:
            for order in sales_orders:
                sale_id = order['id']
                sale_name = order['name']
                state = order["state"]
                delivery_count = order['delivery_count']
                warehouse = order["warehouse_id"][1]

                if delivery_count == 1:
                    # Ejecutar acciones sobre la orden de venta
                    print("----------------------------------------------------------")
                    order_lines = search_order_line(sale_id)
                    if order_lines:
                            for line in order_lines:
                                product_id = line['product_id'][0]
                                price_unit = line['price_unit']
                                quantity = line['product_uom_qty']
                                qty_delivered = line['qty_delivered']
                                if qty_delivered == 0:
                                    # Eliminar la línea existente y agregar una nueva con los mismos valores
                                    cancel_order(sale_id)
                                    draft_order(sale_id)
                                    update_order_line(sale_id, product_id, price_unit, quantity)
                                    confirm_order(sale_id)
                                    print(f"Se actualizo la {sale_name} con estado: {state} y almacen: {warehouse}")
                                    logging.info(f"Se actualizo la {sale_name} con estado: {state} y almacen: {warehouse}")
                                else:
                                    print(f"La venta {sale_name} {state} {warehouse} tiene {qty_delivered} piezas entregada(s), no se modificara")
                                    logging.info(f"La {sale_name} {state} {warehouse} tiene {qty_delivered} piezas entregada(s), no se modificara")
                                    pass
                    print("----------------------------------------------------------")
                    print("")
                else:
                    pass

                break

    except Exception as e:
        print("Error:", e)

    end = datetime.now()
    duration = end - now
    print(f'Duracion del script: {duration}')
    logging.info(f'Duracion del script: {duration}')