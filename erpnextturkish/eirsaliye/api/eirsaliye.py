# Copyright (c) 2020, Logedosoft Business Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnextturkish.eirsaliye.api.utlis import to_base64, get_hash_md5, render_template
from frappe.contacts.doctype.address.address import get_default_address
import requests
import uuid
from erpnextturkish import console


@frappe.whitelist()
def send_eirsaliye(delivery_note_name):
    doc = frappe.get_doc("Delivery Note", delivery_note_name)
    validate_delivery_note(doc)

    if not doc.eirsaliye_uuid:
        doc.eirsaliye_uuid = str(uuid.uuid1())
        doc.db_update()
        frappe.db.commit()
        doc.reload()

    eirsaliye_settings = frappe.get_all("E Irsaliye Ayarlar", filters = {"company": doc.company})[0]
    settings_doc = frappe.get_doc("E Irsaliye Ayarlar", eirsaliye_settings)
    validate_settings_doc(settings_doc)
    
    set_warehouse_address_doc = frappe.get_doc("Address", get_default_address("Warehouse", doc.set_warehouse))
    set_warehouse_address_doc = set_missing_address_values(set_warehouse_address_doc)
    validate_address(set_warehouse_address_doc)

    customer_doc = frappe.get_doc("Customer", doc.customer)
    validate_customer(customer_doc)
    customer_address_doc = frappe.get_doc("Address", doc.shipping_address_name)
    customer_address_doc = set_missing_address_values(customer_address_doc)
    validate_address(customer_address_doc)
    
    doc = set_driver_name(doc)
    
    user = {}
    user["full_name"] = frappe.get_value("User",frappe.session.user,"full_name")

    for item in doc.items:
        eirsaliye_birimi_list = frappe.get_list("TD EIrsaliye Birim Eslestirme",
            filters={
                "parent": settings_doc.name,
                "td_birim": item.uom,    
            },
            fields = ["td_eirsaliye_birimi"]
        )
        if len(eirsaliye_birimi_list) == 0:
            frappe.throw(_("There is no equivalent to the unit of measure: {0} in E Irsaliye Ayarlar: {1}").format(item.uom, eirsaliye_settings))
        td_eirsaliye_birimi = eirsaliye_birimi_list[0]["td_eirsaliye_birimi"]
        item.td_eirsaliye_birimi = td_eirsaliye_birimi


    data_context = {
        "delivery_note_doc" : doc,
        "settings_doc": settings_doc,
        "set_warehouse_address_doc" : set_warehouse_address_doc,
        "customer_doc": customer_doc,
        "customer_address_doc": customer_address_doc,
        "user": user,
    }
    TEMPLATE_FILE = "irsaliye_data.xml"
    outputText = render_template(TEMPLATE_FILE, data_context)  # this is where to put args to the template renderer
    console(outputText)
    veri = to_base64(outputText)
    belgeHash = get_hash_md5(outputText)
    
    endpoint = settings_doc.test_eirsaliye_url if settings_doc.test_modu else settings_doc.eirsaliye_url
    user = settings_doc.user_name
    password = settings_doc.get_password('password')

    body_context = {
        "delivery_note_name": doc.name,
        "veri": veri,
        "belgeHash": belgeHash,
        "user": user,
        "password": password,
        "erp_kodu": settings_doc.erp_kodu,
        "td_vergi_no": settings_doc.td_vergi_no,
    }
    body = render_template("eirsaliye_body.xml", body_context)
    body = body.encode('utf-8')
    session = requests.session()
    session.headers = {"Content-Type": "text/xml; charset=utf-8"}
    session.headers.update({"Content-Length": str(len(body))})
    response = session.post(url=endpoint, data=body, verify=False)
    xml = response.content

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(xml, 'xml')
    error = soup.find_all('Fault')
    belgeOid = soup.find_all('belgeOid')
    if error:
        faultcode = soup.find('faultcode').getText()
        faultstring = soup.find('faultstring').getText()
        frappe.msgprint(str(faultcode) + " " + str(faultstring))
        return str(faultcode) + " " + str(faultstring)
    if belgeOid:
        msg = soup.find('belgeOid').getText()
        doc.belgeno = msg
        doc.db_update()
        frappe.db.commit()
        doc.reload()
        frappe.msgprint(str(msg))
        validate_eirsaliye(doc.name)
        return str(msg)


def set_missing_address_values(address_doc):
    city_subdivision_name = ""
    city_name = ""
    if address_doc.city:
        if "/" in address_doc.city:
            city_split = address_doc.city.split('/')
            city_subdivision_name = city_split[1]
            city_name = city_split[0]
        else:
            city_name = address_doc.city
    
    address_doc.city_subdivision_name = city_subdivision_name
    address_doc.city_name = city_name

    return address_doc


def set_driver_name(doc):
    driver_first_name = ""
    driver_family_name = ""
    if doc.driver_name:
        driver_name_split = doc.driver_name.split(' ')
        if len(driver_name_split) == 1:
            driver_first_name = doc.driver_name
        elif len(driver_name_split) == 2:
            driver_first_name = driver_name_split[0]
            driver_family_name = driver_name_split[1]
        elif len(driver_name_split) == 3:
            driver_first_name = "{0} {1}".format(driver_name_split[0], driver_name_split[1]) 
            driver_family_name = driver_name_split[2]
        else:
            driver_first_name = "{0} {1}".format(driver_name_split[0], driver_name_split[1]) 
            driver_family_name = "{0} {1}".format(driver_name_split[2], driver_name_split[3])
        
    doc.driver_first_name = driver_first_name
    doc.driver_family_name = driver_family_name

    return doc
    

def validate_settings_doc(doc):
    field_list = ["vergi_no", "td_vergi_no", "td_adres_sokak", "td_adres_bina_no",
     "td_adres_ilce", "td_adres_il", "td_posta_kodu", "td_adres_ulke", "vergi_no",
     "td_firma_adi"]
    for field in field_list:
        if not doc.get(field):
            frappe.throw(_("Field: '{0}' can not be emtpy in DocType: {1} {2}").format(field, doc.doctype, doc.name))


def validate_delivery_note(doc):
    field_list = ["set_warehouse", "eirsaliye_uuid", "driver_name", "vehicle_no"]
    for field in field_list:
        if not doc.get(field):
            frappe.throw(_("Field: '{0}' can not be emtpy in DocType: {1} {2}").format(field, doc.doctype, doc.name))


def validate_address(doc):
    field_list = ["address_line1", "city", "pincode", "country", "phone",
     "fax", "email_id"]
    for field in field_list:
        if not doc.get(field):
            frappe.throw(_("Field: '{0}' can not be emtpy in DocType: {1} {2}").format(field, doc.doctype, doc.name))


def validate_customer(doc):
    field_list = ["tax_id", "ld_tax_office"]
    for field in field_list:
        if not doc.get(field):
            frappe.throw(_("Field: '{0}' can not be emtpy in DocType: {1} {2}").format(field, doc.doctype, doc.name))


@frappe.whitelist()
def validate_eirsaliye(delivery_note_name):
    doc = frappe.get_doc("Delivery Note", delivery_note_name)
    eirsaliye_settings = frappe.get_all("E Irsaliye Ayarlar", filters = {"company": doc.company})[0]
    settings_doc = frappe.get_doc("E Irsaliye Ayarlar", eirsaliye_settings)
    endpoint = settings_doc.test_eirsaliye_url if settings_doc.test_modu else settings_doc.eirsaliye_url
    user = settings_doc.user_name
    password = settings_doc.get_password('password')
    body_context = {
        "user": user,
        "password": password,
        "td_vergi_no": settings_doc.td_vergi_no,
        "belgeno": doc.belgeno,
    }
    body = render_template("validate_eirsaliye.xml", body_context)
    body = body.encode('utf-8')
    session = requests.session()
    session.headers = {"Content-Type": "text/xml; charset=utf-8"}
    session.headers.update({"Content-Length": str(len(body))})
    response = session.post(url=endpoint, data=body, verify=False)
    xml = response.content
    # console(str(xml))
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(xml, 'xml')
    error = soup.find_all('Fault')
    belgeOid = soup.find_all('belgeOid')
    msg_return = soup.find_all('return')

    if error:
        faultcode = soup.find('faultcode').getText()
        faultstring = soup.find('faultstring').getText()
        # console(faultcode, faultstring)
        return str(faultcode) + " " + str(faultstring)
    if belgeOid:
        msg = soup.find('belgeOid').getText()
        # console(msg)
        return str(msg)
    if msg_return:
        msg = {}
        if soup.find_all('aciklama'):
            msg["aciklama"] = soup.find('aciklama').getText()
        msg["durum"] = soup.find('durum').getText()
        msg["gonderimCevabiKodu"] = soup.find('gonderimCevabiKodu').getText()
        msg["gonderimDurumu"] = soup.find('gonderimDurumu').getText()
        msg["yanitDurumu"] = soup.find('yanitDurumu').getText()
        msg["ulastiMi"] = soup.find('ulastiMi').getText()
        msg["yenidenGonderilebilirMi"] = soup.find('yenidenGonderilebilirMi').getText()
        msg["yerelBelgeOid"] = soup.find('yerelBelgeOid').getText()
        # console(msg)
        frappe.msgprint(str(msg))
        return(msg)

