# -*- coding: utf-8 -*-
# LOGEDOSOFT

from __future__ import unicode_literals
import frappe, json
from frappe import msgprint, _

from frappe.model.document import Document
from frappe.utils import cstr, flt, cint, nowdate, add_days, comma_and, now_datetime, ceil, today, formatdate, format_time, encode, get_time

from erpnextturkish import console
from pprint import pprint

@frappe.whitelist()
def get_work_order_items(strSalesOrder):
    #Returns sales order items with BOM info
    docSO = frappe.get_doc("Sales Order", strSalesOrder)

    return docSO.get_work_order_items(for_raw_material_request = 1)#It won't check existing WOs

@frappe.whitelist()
def create_manufacture_se_for_so(items, company, sales_order, s_warehouse, t_warehouse):
    #Creates manufacture stock entries with given BOM and qty
    lstSE = [] #Olusturulan uretim fislerini tutar
    lstSETransfer = [] #Olusturulacak ambar fisinde ki malzemeleri tutar

    items = json.loads(items).get('items')

    for dctItem in items:
        docItem = frappe.get_doc("Item", dctItem['item_code']) # Item kodlarını getirdik

        #print("Item Group Fonksiyonu Başlangıç")
        docParent_Item_Group = get_main_parent_item_group(docItem.item_group)

        if(docParent_Item_Group == "GRUP-Hazir Mamuller"):
            dctSE = create_manufacture_se(dctItem['bom'], dctItem['required_qty'], company, s_warehouse, t_warehouse, sales_order)
            docSE = frappe.get_doc(dctSE)
            docSE.insert()
            docSE.submit()
        
            lstSE.append(docSE.name)
        elif(docParent_Item_Group == "GRUP-Malzemeler"):
            lstSETransfer.append({'item_code': docItem.item_code, 'uom': docItem.stock_uom, 'qty': dctItem['required_qty']})

    #Ambtar transferi yapilacak malzemeler icin fis olusturalim
    if len(lstSETransfer) > 0:   #lstSETransfer.count() 
        print("AMBAR TR BASLATILIYOR")
        dctSETransfer = create_transfer_se(lstSETransfer, company, sales_order, s_warehouse, t_warehouse)
        docSETransfer = frappe.get_doc(dctSETransfer)
        docSETransfer.insert()
        docSETransfer.submit()
        print("AMBAR AYIT TAMAM")

        lstSE.append(docSETransfer.name)

    return lstSE

def create_transfer_se(lstSETransfer, company, sales_order, s_warehouse, t_warehouse):
    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.purpose = "Material Transfer"
    stock_entry.company = company
    stock_entry.from_bom = 0
    stock_entry.ld_sales_order = sales_order

    stock_entry.from_warehouse = s_warehouse
    stock_entry.to_warehouse = t_warehouse

    stock_entry.set_stock_entry_type()
    for item in lstSETransfer:
        row = stock_entry.append('items', {})
        print(item)
        row.item_code = item['item_code']
        row.qty = item['qty']
        row.uom = item['uom']

    stock_entry.set_actual_qty()
    stock_entry.calculate_rate_and_amount(raise_error_if_no_rate=False)
	
    return stock_entry.as_dict()

def create_manufacture_se(bom_no, qty, company, s_warehouse, t_warehouse, sales_order):
    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.purpose = "Manufacture"
    stock_entry.company = company
    stock_entry.from_bom = 1
    stock_entry.bom_no = bom_no
    #stock_entry.use_multi_level_bom = work_order.use_multi_level_bom
    stock_entry.fg_completed_qty = qty
    stock_entry.ld_sales_order = sales_order

    stock_entry.from_warehouse = s_warehouse
    stock_entry.to_warehouse = t_warehouse
    #stock_entry.project = project

    stock_entry.set_stock_entry_type()
    stock_entry.get_items()

    stock_entry.set_actual_qty()
    stock_entry.calculate_rate_and_amount(raise_error_if_no_rate=False)
	
    return stock_entry.as_dict()

def get_main_parent_item_group(strItemGroup):
    #item group en başa kadar gidecek
    blnControl= True

    lstItemGroup =[]

    while (blnControl == True):
        docItem_group = frappe.get_doc("Item Group", strItemGroup) 
        if(docItem_group.parent_item_group != ""):
            strItemGroup = docItem_group.parent_item_group
            lstItemGroup.append(strItemGroup)
        else:
            blnControl =False
    
    if (blnControl ==False):
        strItemGroup = lstItemGroup[(len(lstItemGroup)-2)]

    return strItemGroup