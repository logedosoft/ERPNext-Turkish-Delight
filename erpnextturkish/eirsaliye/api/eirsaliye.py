# Copyright (c) 2020, Logedosoft Business Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnextturkish.eirsaliye.api.utlis import to_base64, get_hash_md5, render_template
from frappe.contacts.doctype.address.address import get_default_address
import requests
import uuid


@frappe.whitelist()
def send_eirsaliye(delivery_note_name):
    doc = frappe.get_doc("Delivery Note", delivery_note_name)
    doc.db_update()
    frappe.db.commit()
    doc.reload()

    eirsaliye_settings = frappe.get_all("E Irsaliye Ayarlar", filters = {"company": doc.company})[0]
    settings_doc = frappe.get_doc("E Irsaliye Ayarlar", eirsaliye_settings)
    
    set_warehouse_address_doc = frappe.get_doc("Address", get_default_address("Warehouse", doc.set_warehouse))
    set_warehouse_address_doc = set_missing_address_values(set_warehouse_address_doc)

    customer_doc = frappe.get_doc("Customer", doc.customer)
    customer_address_doc = frappe.get_doc("Address", doc.shipping_address_name)
    customer_address_doc = set_missing_address_values(customer_address_doc)
    
    doc.eirsaliye_uuid = uuid.uuid1()

    doc = set_driver_name(doc)
    
    user = {}
    user["full_name"] = frappe.get_value("User",frappe.session.user,"full_name")

    for item in doc.items:
        td_eirsaliye_birimi = frappe.get_list("TD EIrsaliye Birim Eslestirme",
            filters={
                "parent": settings_doc.name,
                "td_birim": item.uom,    
            },
            fields = ["td_eirsaliye_birimi"]
        )[0]["td_eirsaliye_birimi"]
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
    frappe.msgprint(str(body))
    session = requests.session()
    session.headers = {"Content-Type": "text/xml; charset=utf-8"}
    session.headers.update({"Content-Length": str(len(body))})
    response = session.post(url=endpoint, data=body, verify=False)

    x=response.content
    x=str(x,"UTF-8")
    print("-------------------------")

    from bs4 import BeautifulSoup
    xml = response.content
    # print(xml)
    soup = BeautifulSoup(xml, 'xml')
    error = soup.find_all('Fault')
    belgeOid = soup.find_all('belgeOid')
    if error:
        faultcode = soup.find('faultcode').getText()
        faultstring = soup.find('faultstring').getText()
        print(faultcode, faultstring)
        return str(faultcode) + " " + str(faultstring)
    if belgeOid:
        msg = soup.find('belgeOid').getText()
        print(msg)
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