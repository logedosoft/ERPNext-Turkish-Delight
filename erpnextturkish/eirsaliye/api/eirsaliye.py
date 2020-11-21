# Copyright (c) 2020, Logedosoft Business Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnextturkish.eirsaliye.api.utlis import to_base64, get_hash_md5, render_template
import requests



def send_eirsaliye(doc=None, method=None):

    TEMPLATE_FILE = "irsaliye_data.xml"
    hello="hello..... "

    outputText = render_template(TEMPLATE_FILE, hello)  # this is where to put args to the template renderer
    veri = to_base64(outputText)
    belgeHash = get_hash_md5(outputText)
    
    endpoint = "https://erpefaturatest.cs.com.tr:8043/efatura/ws/connectorService"
    user = "3340526030"
    password = "irsAliye@2020"

    context = {
        "veri": veri,
        "belgeHash": belgeHash,
        "user": user,
        "password": password
    }
    body = render_template("eirsaliye_body.xml", context)
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
    if belgeOid:
        msg = soup.find('belgeOid').getText()
        print(msg)



