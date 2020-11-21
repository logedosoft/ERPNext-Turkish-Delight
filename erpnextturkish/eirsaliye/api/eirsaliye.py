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
    print(belgeHash)
    endpoint = "https://erpefaturatest.cs.com.tr:8043/efatura/ws/connectorService"
    user = "3340526030"
    password = "irsAliye@2020"

    body="""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="http://service.connector.uut.cs.com.tr/">
        <soapenv:Header> 
        <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"> 
        <wsse:UsernameToken>
        <wsse:Username>{user}</wsse:Username>
        <wsse:Password>{password}</wsse:Password>
        </wsse:UsernameToken>
        </wsse:Security>
        </soapenv:Header>
        <soapenv:Body>
            <ser:belgeGonderExt>
                <parametreler>
                    <belgeHash>{belgeHash}</belgeHash>
                    <belgeNo>del-1243</belgeNo>
                    <belgeTuru>IRSALIYE_UBL</belgeTuru>
                    <belgeVersiyon>1.0</belgeVersiyon>
                    <erpKodu>LDS30822</erpKodu>
                    <mimeType>application/xml</mimeType>
                    <vergiTcKimlikNo>3340526030</vergiTcKimlikNo>
                    <veri>{veri}</veri>
                </parametreler>
            </ser:belgeGonderExt>
        </soapenv:Body>
        </soapenv:Envelope>"""

    
    
    body = body.format(user=user, password=password, veri=veri, belgeHash=belgeHash)
    body = body.encode('utf-8')
    session = requests.session()
    session.headers = {"Content-Type": "text/xml; charset=utf-8"}
    session.headers.update({"Content-Length": str(len(body))})
    response = session.post(url=endpoint, data=body, verify=False)

    x=response.content
    x=str(x,"UTF-8")

    print("-------------------------")
    #print (x)

    # from bs4 import BeautifulSoup
    xml = response.content
    print(xml)
    # soup = BeautifulSoup(xml, 'xml')
    # if soup.find_all('Result', text='0'):
    #     print("door opened")
    # else:
    #     print("door not opened")



