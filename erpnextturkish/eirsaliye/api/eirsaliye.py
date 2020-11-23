# Copyright (c) 2020, Logedosoft Business Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnextturkish.eirsaliye.api.utlis import to_base64, get_hash_md5, render_template
import requests


@frappe.whitelist()
def send_eirsaliye(delivery_note_name):
    doc = frappe.get_doc("Delivery Note", delivery_note_name)
    eirsaliye_settings = frappe.get_all("E Irsaliye Ayarlar", filters = {"company": doc.company})[0]
    settings_doc = frappe.get_doc("E Irsaliye Ayarlar", eirsaliye_settings)
    # company_doc = frappe.get_doc("Company", doc.company)
    TEMPLATE_FILE = "irsaliye_data.xml"
    hello="hello..... "

    outputText = render_template(TEMPLATE_FILE, hello)  # this is where to put args to the template renderer
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

    x=response.content
    x=str(x,"UTF-8")
    print("-------------------------")
    #print (x)

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



