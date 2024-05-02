# -*- coding: utf-8 -*-
# LOGEDOSOFT

from __future__ import unicode_literals
import frappe, json
from frappe import msgprint, _

from frappe.model.document import Document
from frappe.utils import cstr, flt, cint, nowdate, add_days, comma_and, now_datetime, ceil, today, formatdate, format_time, encode, get_time

#import requests
#import base64
#import dateutil

#from bs4 import BeautifulSoup


@frappe.whitelist()
def kur_guncelle():
    flUSDCurrRate = guncel_kur_getir("USD","Döviz Satış")   #32.0000
    flEURCurrRate = guncel_kur_getir("EUR","Döviz Satış")   #35.0000

    getUSD = frappe.db.get_list('Currency Exchange',
        filters={
            'date': today(),
            'from_currency':'USD',
        },
        fields=['name','exchange_rate']
    )

    getEUR = frappe.db.get_list('Currency Exchange',
        filters={
            'date': today(),
            'from_currency':'EUR',
        },
        fields=['name','exchange_rate']
    )

    #frappe.msgprint(str(getUSD[0].name) + "test")

    if not getUSD:
        doc = frappe.get_doc({
            'doctype': 'Currency Exchange',
            'date': today(),
            'from_currency':'USD',
            'to_currency':'TRY',
            'exchange_rate': flUSDCurrRate,
            'for_buying': 1,
            'for_selling': 1,   
        })
        doc.insert()
    elif getUSD[0].exchange_rate != flUSDCurrRate:
        doc = frappe.get_doc('Currency Exchange', getUSD[0].name)
        doc.exchange_rate = flUSDCurrRate
        doc.db_update()

    if not getEUR:
        doc = frappe.get_doc({
            'doctype': 'Currency Exchange',
            'date': today(),
            'from_currency':'EUR',
            'to_currency':'TRY',
            'exchange_rate': flEURCurrRate,
            'for_buying': 1,
            'for_selling': 1,   
        })
        doc.insert()
    elif getEUR[0].exchange_rate != flEURCurrRate:
        doc = frappe.get_doc('Currency Exchange', getEUR[0].name)
        doc.exchange_rate = flEURCurrRate
        doc.db_update()

    #"Currency Exchange" , buying selling


def guncel_kur_getir(paraBirimi : str, kurTipi : str):
    from xml.etree.ElementTree import fromstring,ElementTree as ET
    import requests
    r = requests.get("https://www.tcmb.gov.tr/kurlar/today.xml")
    response_text = r.text
    response_text = response_text.replace('<?xml version="1.0" encoding="UTF-8"?>','')
    response_text = response_text.replace('<?xml-stylesheet type="text/xsl" href="isokur.xsl"?>','')
    
    kurTipleri = {
        "Döviz Alış": 3,
        "Döviz Satış":4,
        "Efektif Alış":5,
        "Efektif Satış":6
    }

    tree = ET(fromstring(response_text))
    root = tree.getroot()
    for children in root:
        if paraBirimi == children.attrib["Kod"]:
            return float(children[kurTipleri[kurTipi]].text)