import xmlrpc.client
host = "https://wonderbrands-v2-13556540.dev.odoo.com"
db = "wonderbrands-v2-13556540"
username = "admin"
password = "9Lh5Z0x*bCqV"
url = '%s/xmlrpc/' % (host)
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(host))
uid = common.authenticate(db, username, password, {})


# common_proxy = xmlrpclib.ServerProxy(url+'common')
# object_proxy = xmlrpclib.ServerProxy(url+'object')
# uid = common_proxy.login(db,username,password)
print(uid)
