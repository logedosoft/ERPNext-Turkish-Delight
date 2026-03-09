# -*- coding: utf-8 -*-
# LOGEDOSOFT

from __future__ import unicode_literals
import frappe, json
from frappe import msgprint, _

from frappe.model.document import Document
from frappe.utils import cstr, flt, cint, nowdate, add_days, comma_and, now_datetime, ceil, today, formatdate, format_time, encode, get_time

import requests
import base64
import dateutil

from bs4 import BeautifulSoup

def sales_order_before_save(doc, method):
	#Set template item image when saving sales order. https://app.asana.com/0/1199512727558833/1208206221565431/f
	#For each row in items grid, check if item has an image. If image exist, use it or try to get the image from the template
	
	for item in doc.items:
		imgItem, template_item = frappe.db.get_value("Item", item.item_code, ["image", "variant_of"])
		if imgItem is None and template_item is not None:
			imgItem = frappe.db.get_value("Item", template_item, "image")

		if imgItem is not None:
			item.custom_ld_template_image = imgItem

		#Get size and colour attribute values https://app.asana.com/0/1199512727558833/1208206221565437/f
		if template_item is not None:
			size_attribute = frappe.db.get_value("Item", template_item, "custom_ld_size_attribute")
			if size_attribute is not None:
				docItem = frappe.get_doc("Item", item.item_code)
				for attribute in docItem.attributes:
					if attribute.attribute == size_attribute:
						item.custom_ld_variant_attribute_size = attribute.attribute_value
					else:
						item.custom_ld_variant_attribute_colour = attribute.attribute_value

def item_before_save(doc, method):
	#We need to show size chart properly in the printouts. So created a html field and we will fill it in this method.
	#Field custom_size_chart_html and custom_ld_variant_size_chart table https://app.asana.com/0/1199512727558833/1208032071430686/f
	#HTML Template:
	if len(doc.custom_ld_variant_size_chart) > 0:
		strHTML = """<table class="table table-bordered table-condensed"><thead><tr>"""
		strHTML += """<th style="width: 150px;" class="" data-fieldname="custom_ld_variant_size_chart" data-fieldtype="Table">Bedenler</th>"""

		for size in get_template_valid_attributes(doc.name)['attribute_list']:
			strHTML += """<th style="width: 80px;" class="" data-fieldname="custom_ld_variant_size_chart" data-fieldtype="Table">""" + size + """</th>"""

		strHTML += """</tr></thead><tbody>"""

		for row in doc.custom_ld_variant_size_chart:
				strHTML += """<tr>"""
				strHTML += f"""
				<td class="" data-fieldname="custom_ld_variant_size_chart" data-fieldtype="Table">
					<div class="value">{row.part}</div>
				</td>"""

				dSizeIndex = 1
				for size in get_template_valid_attributes(doc.name)['attribute_list']:
					flSize = row.get(f"attr{dSizeIndex}")
					strHTML += f"""<td class="text-right" data-fieldname="custom_ld_variant_size_chart" data-fieldtype="Table"><div class="value">{flSize}</div></td>"""
					dSizeIndex += 1

				strHTML += """</tr>"""

		strHTML += """</tbody></table>"""
			
		doc.custom_size_chart_html_editor = strHTML
		frappe.log_error("ITEM BS 10", doc.custom_size_chart_html_editor)

@frappe.whitelist()
def get_template_valid_attributes(strTemplateItemCode):
	#Will return item attribute of the given template item.
	#Algorithm: Get variant items of given template item. Loop in their attribute list.
	#If attribute name is selected in the Template Item. Size Attribute
	#Add attribute value to the result array.

	result = {
		'op_message': '',
		'op_result': True,
		'attribute_list': []
	}
	strSizeAttributeName = frappe.get_value("Item", strTemplateItemCode, "custom_ld_size_attribute")
	dctVariants = frappe.get_all("Item", filters={"variant_of": strTemplateItemCode}, fields=["name"])

	for variant in dctVariants:
		docItem = frappe.get_doc("Item", variant.name)
		for attribute in docItem.attributes:
			if attribute.attribute == strSizeAttributeName and attribute.attribute_value not in result['attribute_list']:
				dIdx = get_attribute_idx(docItme, strSizeAttributeName)
				result['attribute_list'].append((dIdx, attribute.attribute_value))

	result['attribute_list'].sort(key=lambda x: x)
	result['attribute_list'] = [attr for attr in result['attribute_list']]
	#result['attribute_list'] = sorted(result['attribute_list'])

	return result

def get_attribute_idx(docItem, strSizeAttributeName):
	#Finds item attribute no (idx) for the given variant
	dResult = -1

	for attribute in docItem.attributes:
		if attribute.attribute == strSizeAttributeName:
			docItemAttribute = frappe.get_doc("Item Attribute", attribute.attribute)
			for item_attribute in docItemAttribute.item_attribute_values:
				if attribute.attribute_value == item_attribute.attribute_value:
					dResult = item_attribute.idx

	return dResult

@frappe.whitelist()
def process_variant_json_data(strTemplateItem, jsonData):
	#We will try to find the correct item codes based on Item Template and json data
	#jsonData = [{"attribute_name":"RED","XS":0,"column_attribute_name":"Boyut","row_attribute_name":"Renk","S":0,"M":0,"L":2,"XL":0,"idx":1,"name":"row 1"},{"attribute_name":"GRE","XS":0,"column_attribute_name":"Boyut","row_attribute_name":"Renk","S":0,"M":0,"L":0,"XL":0,"idx":2,"name":"row 2"},{"attribute_name":"BLU","XS":0,"column_attribute_name":"Boyut","row_attribute_name":"Renk","S":5,"M":0,"L":0,"XL":0,"idx":3,"name":"row 3"},{"attribute_name":"BLA","XS":0,"column_attribute_name":"Boyut","row_attribute_name":"Renk","S":0,"M":0,"L":0,"XL":0,"idx":4,"name":"row 4"},{"attribute_name":"WHI","XS":0,"column_attribute_name":"Boyut","row_attribute_name":"Renk","S":0,"M":0,"L":0,"XL":0,"idx":5,"name":"row 5"}]
	#Algorithm: get attribute in info
	result = {
		'op_result': True, 'op_message': '',
		'variant_item_info': [] #{'item_code':'', 'qty':0}
	}

	item_template_info = get_item_template_attributes(strTemplateItem)

	dctVariantInfo = json.loads(jsonData)
	for variant_info in dctVariantInfo:
		docColumnAttribute = frappe.get_doc("Item Attribute", variant_info['column_attribute_name'])
		for column_attr in docColumnAttribute.item_attribute_values:
			if variant_info[column_attr.abbr] > 0:
				
				strItemCode = item_template_info['item_code_info'][0] #GOMLE
				strAttr = item_template_info['item_code_info'][1] #RENK
				if strAttr == variant_info['row_attribute_name']:
					strItemCode += "-" + variant_info['attribute_name']
				
				strItemCode += "-" + column_attr.abbr
				result['variant_item_info'].append({
					'item_code':strItemCode, 'qty':variant_info[column_attr.abbr]
				})

	return result

def get_item_code(strTemplateItem, attr1_name, attr2_name):
	#strTemplateItem = Gomlek Kodu
	 #attr1_name = BLU
	 #attr2_name = M
	  return "{}-{}-{}".format(strTemplateItem, attr1_name, attr2_name)


@frappe.whitelist()
def get_template_item_info(doc, template_data):
	#Variant selector. https://app.asana.com/0/1199512727558833/1206652223240041/f
	#We get selected values from the template data
	 #Find proper item codes
	#Return item array with item code and qty
	#The client side will process it and create new lines
	doc = frappe.get_doc(json.loads(doc))
	template_data = json.loads(template_data)
	result = False
	result_message = ""
	result_data = []

	for item in template_data:
		print(frappe.as_json(item))
		frappe.log_error("VS 0", frappe.as_json(item))

	#frappe.log_error("Hata", item)

	docTemplateItem = frappe.get_doc("Item", item["item_code"])

	return {'result': result, 'result_message': result_message, 'result_data': result_data}

def is_item_exist(attribute_info, strTemplateItem):
	blnResult = False
	print(attribute_info)
	print(strTemplateItem)
	return blnResult

@frappe.whitelist()
def get_item_template_attributes(strTemplateItemCode):
	#Variant selector. https://app.asana.com/0/1199512727558833/1206652223240041/f
	data = []#It will have arrays of attributes with attribute_name, attribute_values, attribute_abbr
	result = False
	result_message = ""
	arrItemCodeInfo = [] #Variant item code info
	
	docItem = frappe.get_doc("Item", strTemplateItemCode)
	arrItemCodeInfo.append(docItem.item_name) #Will add variant abbrv info
	for attribute in docItem.attributes:
		docItemAttribute = frappe.get_doc("Item Attribute", attribute.attribute)
		arrItemCodeInfo.append(attribute.attribute)
		attribute_info = {'attribute_name': docItemAttribute.attribute_name, 'attribute_values': [], 'attribute_abbr': []}
		data.append(attribute_info)
		for attribute_value in docItemAttribute.item_attribute_values:
			attribute_info['attribute_values'].append(attribute_value.attribute_value)
			attribute_info['attribute_abbr'].append(attribute_value.abbr)


	is_item_exist(attribute_info, strTemplateItemCode)

	#Create columns and rows list. Values with higher count should be in rows.
	if len(data) == 2:
		result = True
		if len(data[0]['attribute_values']) > len(data[1]['attribute_values']):
			columns = data[0]
			rows = data[1]
			#column_attribute_name = data[0]['attribute_name']
			#row_attribute_name = data[1]['attribute_name']
		else:
			columns = data[1]
			rows = data[0]
			#column_attribute_name = data[1]['attribute_name']
			#row_attribute_name = data[0]['attribute_name']
	else:
		result = False
		result_message = _("Template must have 2 attributes")
			
	return {
		'columns': columns, 'rows': rows, 'data': data,
		'item_code_info': arrItemCodeInfo,
		#'column_attribute_name': column_attribute_name, 'row_attribute_name': row_attribute_name,
		'op_result': result, 'op_message': result_message
	}

@frappe.whitelist()
def pp_create_wosco(docPP, strType):
	#Create WO, Subassembly WO and SCO from PP. https://app.asana.com/0/1206337061845755/1206535127766803/f
	#strType = ['Work Order', 'Subcontracting Order']
	docPP = frappe.get_doc(json.loads(docPP))

	from erpnext.manufacturing.doctype.work_order.work_order import get_default_warehouse

	wo_list, po_list = [], []
	subcontracted_po = {}
	default_warehouses = get_default_warehouse()

	if strType == "Work Order":
		docPP.make_work_order_for_finished_goods(wo_list, default_warehouses)
	if strType == "Subcontracting Order":
		docPP.make_work_order_for_subassembly_items(wo_list, subcontracted_po, default_warehouses)
		docPP.make_subcontracted_purchase_order(subcontracted_po, po_list)
	docPP.show_list_created_message("Work Order", wo_list)
	docPP.show_list_created_message("Purchase Order", po_list)

	if strType == "Work Order" and not wo_list:
		frappe.msgprint(_("No Work Orders were created!"))
	if strType == "Subcontracting Order" and not po_list:
		frappe.msgprint(_("No Subcontracting Purchase Orders were created!"))

def get_service_xml_for_uyumsoft(strType):
	strResult = ''

	if strType == 'einvoice-body':
		#<s:Header><wsse:Security s:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"><wsse:UsernameToken><wsse:Username>Uyumsoft</wsse:Username><wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">Uyumsoft</wsse:Password><wsse:Nonce EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary">zOBB+xvgK+JpkdzfssWwKg==</wsse:Nonce><wsu:Created>2020-02-17T21:46:40.646Z</wsu:Created></wsse:UsernameToken></wsse:Security></s:Header>
		strResult = """
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">

	<s:Header>
		<wsse:Security s:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
			<wsse:UsernameToken>
				<wsse:Username>{{docEISettings.kullaniciadi}}</wsse:Username>
				<wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{{docEISettings.parola}}</wsse:Password>
			</wsse:UsernameToken>
		</wsse:Security>
	</s:Header>

	<s:Body xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
		<SaveAsDraft xmlns="http://tempuri.org/">
			<invoices>
				<InvoiceInfo LocalDocumentId="{{docSI.name}}">
					<Invoice>
						<ProfileID xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">TICARIFATURA</ProfileID>
						<ID xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"/>
						<CopyIndicator xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">false</CopyIndicator>
						<IssueDate xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.posting_date_formatted}}</IssueDate>
						<IssueTime xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.posting_time_formatted}}</IssueTime>
						<InvoiceTypeCode xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">SATIS</InvoiceTypeCode>
						<Note xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_not1_formul}}</Note>
						<Note xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_not2_formul}}</Note>
						<Note xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_not3_formul}}</Note>
						<Note xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_not4_formul}}</Note>
						<DocumentCurrencyCode xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">TRY</DocumentCurrencyCode>
						<PricingCurrencyCode xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">TRY</PricingCurrencyCode>
						<LineCountNumeric xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.line_count}}</LineCountNumeric>
						
						<AccountingSupplierParty xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
							<Party>
								<PartyIdentification>
									<ID schemeID="VKN" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_vergi_no if docEISettings.td_vergi_no else ''}}</ID>
								</PartyIdentification>
								<PartyIdentification>
									<ID schemeID="MERSISNO" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_mersis_no if docEISettings.td_mersis_no else ''}}</ID>
								</PartyIdentification>
								<PartyIdentification>
									<ID schemeID="TICARETSICILNO" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_ticaret_sicil_no if docEISettings.td_ticaret_sicil_no else ''}}</ID>
								</PartyIdentification>
								<PartyName>
									<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_firma_adi if docEISettings.td_firma_adi else ''}}</Name>
								</PartyName>
								<PostalAddress>
									<Room xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_adres_kapi_no|replace("&", "&#38;") if docEISettings.td_adres_kapi_no else ''}}</Room>
									<StreetName xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_adres_sokak|replace("&", "&#38;") if docEISettings.td_adres_sokak else ''}}</StreetName>
									<BuildingNumber xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_adres_bina_no|replace("&", "&#38;") if docEISettings.td_adres_bina_no else ''}}</BuildingNumber>
									<CitySubdivisionName xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_adres_ilce if docEISettings.td_adres_ilce else ''}}</CitySubdivisionName>
									<CityName xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_adres_il if docEISettings.td_adres_il else ''}}</CityName>
									<Country>
										<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_adres_ulke if docEISettings.td_adres_ulke else ''}}</Name>
									</Country>
								</PostalAddress>
								<PartyTaxScheme>
									<TaxScheme>
										<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_vergi_dairesi if docEISettings.td_vergi_dairesi else ''}}</Name>
									</TaxScheme>
								</PartyTaxScheme>
							</Party>
						</AccountingSupplierParty>

						<AccountingCustomerParty xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
							<Party>
								<PartyIdentification>
									<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCustomer.customer_name}}</Name>
								</PartyName>

								<PostalAddress>
									<StreetName xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCustomerAddress.address_line1|replace("&", "&#38;") if docCustomerAddress.address_line1 else ''}}</StreetName>
									<BuildingNumber xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCustomerAddress.address_line2|replace("&", "&#38;") if docCustomerAddress.address_line2 else ''}}</BuildingNumber>
									<CitySubdivisionName xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCustomerAddress.county|replace("&", "&#38;") if docCustomerAddress.county else ''}}</CitySubdivisionName>
									<CityName xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCustomerAddress.city|replace("&", "&#38;") if docCustomerAddress.city else ''}}</CityName>
									<PostalZone xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCustomerAddress.pincode|replace("&", "&#38;") if docCustomerAddress.pincode else ''}}</PostalZone>
									<Country>
										<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCustomerAddress.country or ''}}</Name>
									</Country>
								</PostalAddress>

								<PartyTaxScheme>
									<TaxScheme>
										<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCustomer.tax_office or ''}}</Name>
									</TaxScheme>
								</PartyTaxScheme>

							</Party>
						</AccountingCustomerParty>

						<TaxTotal xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
							<TaxAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.TaxAmount}}</TaxAmount>
							<TaxSubtotal>
								<TaxAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.TaxAmount}}</TaxAmount>
								<Percent xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.TaxPercent}}</Percent>
								<TaxCategory>
									<TaxScheme>
										<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">KDV</Name>
										<TaxTypeCode xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">0015</TaxTypeCode>
									</TaxScheme>
								</TaxCategory>
							</TaxSubtotal>
						</TaxTotal>

						<LegalMonetaryTotal xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
							<LineExtensionAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.LineExtensionAmount}}</LineExtensionAmount>
							<TaxExclusiveAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.TaxExclusiveAmount}}</TaxExclusiveAmount>
							<TaxInclusiveAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.TaxInclusiveAmount}}</TaxInclusiveAmount>
							<AllowanceTotalAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.AllowanceTotalAmount}}</AllowanceTotalAmount>
							<PayableAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.PayableAmount}}</PayableAmount>
						</LegalMonetaryTotal>

						{{docSI.contentLines}}

					</Invoice>
					<TargetCustomer VknTckn="{{docCustomer.tax_id}}" Alias="{{docCustomer.td_alici_alias}}" Title="{{docCustomer.customer_name}}"/>
					<EArchiveInvoiceInfo DeliveryType="Electronic"/>
					<Scenario>Automated</Scenario>
				</InvoiceInfo>
			</invoices>
		</SaveAsDraft>
	</s:Body>
</s:Envelope>
"""
	elif strType == "einvoice-line":
			strResult = """
	<InvoiceLine xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
		<ID xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.idx}}</ID>
		<Note xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"></Note>
		
		<InvoicedQuantity unitCode="{{docCurrentLine.efatura_birimi}}" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.qty}}</InvoicedQuantity>
		<LineExtensionAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.amount}}</LineExtensionAmount>
		
		<AllowanceCharge>
			<ChargeIndicator xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">false</ChargeIndicator>
			<MultiplierFactorNumeric>0.0</MultiplierFactorNumeric>
			<Amount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.discount_amount}}</Amount>
			<PerUnitAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.qty}}</PerUnitAmount>
			<BaseAmount currencyID="TRL">{{docCurrentLine.AllowanceBaseAmount}}</BaseAmount>
		</AllowanceCharge>

		<TaxTotal>
			<TaxAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.TaxAmount}}</TaxAmount>
			<TaxSubtotal>
				<TaxAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.TaxAmount}}</TaxAmount>
				<Percent xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.TaxPercent}}</Percent>
				<TaxCategory>
					<TaxScheme>
						<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">KDV</Name>
						<TaxTypeCode xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">0015</TaxTypeCode>
					</TaxScheme>
				</TaxCategory>
			</TaxSubtotal>
		</TaxTotal>

		<Item>
			<Description xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"></Description>
			<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docItem.item_code}} {{docItem.item_name}}</Name>
			<BrandName xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"></BrandName>
			<ModelName xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"></ModelName>
			<BuyersItemIdentification>
				<ID xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"></ID>
			</BuyersItemIdentification>
			<SellersItemIdentification>
				<ID xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"></ID>
			</SellersItemIdentification>
			<ManufacturersItemIdentification>
				<ID xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"></ID>
			</ManufacturersItemIdentification>
		</Item>
		<Price>
			<PriceAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.rate}}</PriceAmount>
		</Price>
	</InvoiceLine>
		"""

	elif strType == "einvoice-headers":
		strResult = {
			'Accept-Encoding': 'gzip,deflate',
			'Accept': 'text/xml',
			'Content-Type': 'text/xml;charset=UTF-8',
			'Cache-Control': 'no-cache',
			'Pragma': 'no-cache',
			'SOAPAction': 'http://tempuri.org/IIntegration/SaveAsDraft',
			'Connection': 'Keep-Alive'
		}
	
	elif strType == "login-test-headers":
		strResult = {
			'Accept-Encoding': 'gzip,deflate',
			'Accept': 'text/xml',
			'Content-Type': 'text/xml;charset=UTF-8',
			'Cache-Control': 'no-cache',
			'Pragma': 'no-cache',
			'SOAPAction': 'http://tempuri.org/IIntegration/WhoAmI',
			'Connection': 'Keep-Alive'
		}
	elif strType == "login-test-body":
		strResult = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
   <soapenv:Header>
	  <wsse:Security soapenv:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
		 <wsse:UsernameToken>
			<wsse:Username>{{docEISettings.kullaniciadi}}</wsse:Username>
			<wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{{docEISettings.parola}}</wsse:Password>
		 </wsse:UsernameToken>
	  </wsse:Security>
   </soapenv:Header>
   <soapenv:Body>
	  <tem:WhoAmI/>
   </soapenv:Body>
</soapenv:Envelope>
"""

	elif strType == "query-invoice-status-headers":
		strResult = {
			'Accept-Encoding': 'gzip,deflate',
			'Accept': 'text/xml',
			'Content-Type': 'text/xml;charset=UTF-8',
			'Cache-Control': 'no-cache',
			'Pragma': 'no-cache',
			'SOAPAction': 'http://tempuri.org/IIntegration/QueryOutboxInvoiceStatus',
			'Connection': 'Keep-Alive'
		}
	
	elif strType == "query-invoice-status-body":
		strResult = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
   <soapenv:Header>
	  <wsse:Security soapenv:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
		 <wsse:UsernameToken>
			<wsse:Username>{{docEISettings.kullaniciadi}}</wsse:Username>
			<wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{{docEISettings.parola}}</wsse:Password>
		 </wsse:UsernameToken>
	  </wsse:Security>
	</soapenv:Header>
   <soapenv:Body>
	  <tem:QueryOutboxInvoiceStatus>
		 <tem:invoiceIds>
			<tem:string>{{docSI.td_efatura_uuid}}</tem:string>
		 </tem:invoiceIds>
	  </tem:QueryOutboxInvoiceStatus>
   </soapenv:Body>
</soapenv:Envelope>
"""
	elif strType == "query-get-user-aliasses-headers":
		strResult = {
			'Accept-Encoding': 'gzip,deflate',
			'Accept': 'text/xml',
			'Content-Type': 'text/xml;charset=UTF-8',
			'Cache-Control': 'no-cache',
			'Pragma': 'no-cache',
			'SOAPAction': 'http://tempuri.org/IIntegration/GetUserAliasses',
			'Connection': 'Keep-Alive'
		}

	elif strType == "query-get-user-aliasses-body":
		strResult = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
   <soapenv:Header>
	  <wsse:Security soapenv:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
		 <wsse:UsernameToken>
			<wsse:Username>{{docEISettings.kullaniciadi}}</wsse:Username>
			<wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{{docEISettings.parola}}</wsse:Password>
		 </wsse:UsernameToken>
	  </wsse:Security>
	</soapenv:Header>
   <soapenv:Body>
	  <tem:GetUserAliasses>
		 <tem:vknTckn>{{docCustomer.tax_id}}</tem:vknTckn>
	  </tem:GetUserAliasses>
   </soapenv:Body>
</soapenv:Envelope>
		"""

	return strResult

def get_service_xml_for_bien_teknoloji(strType):
	strResult = ''

	if strType == "inbox-invoice-list-body": 
		#<tem:StatusInList>WaitingForAprovement</tem:StatusInList>
		strResult = """
		<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
			<soapenv:Body>
				<tem:GetInboxInvoiceList>
					<tem:userInfo Username="{{docEISettings.username}}" Password="{{docEISettings.parola}}"/>
					<tem:query PageIndex="1" PageSize="100000">
						<tem:ExecutionStartDate>{{tarih1}}</tem:ExecutionStartDate>
						<tem:ExecutionEndDate>{{tarih2}}</tem:ExecutionEndDate>
						<tem:StatusNotInList>Declined</tem:StatusNotInList>
					</tem:query>
				</tem:GetInboxInvoiceList>
			</soapenv:Body>
		</soapenv:Envelope> 
			"""

	elif strType == "einvoice-tevkifat":
		strResult = """
<WithholdingTaxTotal>
	<TaxAmount currencyID="TRY">{{kdv_tevkifat1}}</TaxAmount>
	<TaxSubtotal>
		<TaxableAmount currencyID="TRY">{{kdv_tam}}</TaxableAmount>
		<TaxAmount currencyID="TRY">{{kdv_tevkifat2}}</TaxAmount>
		<Percent>50</Percent>
		<TaxCategory>
			<TaxScheme>
				<Name>604 YEMEK SERVİS HİZMETİ *GT 117-Bölüm (3.2.4)+</Name>
				<TaxTypeCode>604</TaxTypeCode>
			</TaxScheme>
		</TaxCategory>
	</TaxSubtotal>
</WithholdingTaxTotal>
					"""

	elif strType == 'einvoice-body':
		#<s:Header><wsse:Security s:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"><wsse:UsernameToken><wsse:Username>Uyumsoft</wsse:Username><wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">Uyumsoft</wsse:Password><wsse:Nonce EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary">zOBB+xvgK+JpkdzfssWwKg==</wsse:Nonce><wsu:Created>2020-02-17T21:46:40.646Z</wsu:Created></wsse:UsernameToken></wsse:Security></s:Header>
		strResult = """
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">

	<s:Header>
		<wsse:Security s:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
			<wsse:UsernameToken>
				<wsse:Username>{{docEISettings.kullaniciadi}}</wsse:Username>
				<wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{{docEISettings.parola}}</wsse:Password>
			</wsse:UsernameToken>
		</wsse:Security>
	</s:Header>

	<s:Body xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
		<SaveAsDraft xmlns="http://tempuri.org/">
			<invoices>
				<InvoiceInfo LocalDocumentId="{{docSI.name}}">
					<Invoice>
						<ProfileID xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">TICARIFATURA</ProfileID>
						<ID xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"/>
						<CopyIndicator xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">false</CopyIndicator>
						<IssueDate xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.posting_date_formatted}}</IssueDate>
						<IssueTime xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.posting_time_formatted}}</IssueTime>
						<InvoiceTypeCode xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">SATIS</InvoiceTypeCode>
						<Note xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_not1_formul}}</Note>
						<Note xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_not2_formul}}</Note>
						<Note xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_not3_formul}}</Note>
						<Note xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_not4_formul}}</Note>
						<DocumentCurrencyCode xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">TRY</DocumentCurrencyCode>
						<PricingCurrencyCode xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">TRY</PricingCurrencyCode>
						<LineCountNumeric xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.line_count}}</LineCountNumeric>
						
						<AccountingSupplierParty xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
							<Party>
								<PartyIdentification>
									<ID schemeID="VKN" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_vergi_no if docEISettings.td_vergi_no else ''}}</ID>
								</PartyIdentification>
								<PartyIdentification>
									<ID schemeID="MERSISNO" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_mersis_no if docEISettings.td_mersis_no else ''}}</ID>
								</PartyIdentification>
								<PartyIdentification>
									<ID schemeID="TICARETSICILNO" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_ticaret_sicil_no if docEISettings.td_ticaret_sicil_no else ''}}</ID>
								</PartyIdentification>
								<PartyName>
									<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_firma_adi if docEISettings.td_firma_adi else ''}}</Name>
								</PartyName>
								<PostalAddress>
									<Room xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_adres_kapi_no|replace("&", "&#38;") if docEISettings.td_adres_kapi_no else ''}}</Room>
									<StreetName xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_adres_sokak|replace("&", "&#38;") if docEISettings.td_adres_sokak else ''}}</StreetName>
									<BuildingNumber xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_adres_bina_no|replace("&", "&#38;") if docEISettings.td_adres_bina_no else ''}}</BuildingNumber>
									<CitySubdivisionName xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_adres_ilce if docEISettings.td_adres_ilce else ''}}</CitySubdivisionName>
									<CityName xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_adres_il if docEISettings.td_adres_il else ''}}</CityName>
									<Country>
										<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_adres_ulke if docEISettings.td_adres_ulke else ''}}</Name>
									</Country>
								</PostalAddress>
								<PartyTaxScheme>
									<TaxScheme>
										<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docEISettings.td_vergi_dairesi if docEISettings.td_vergi_dairesi else ''}}</Name>
									</TaxScheme>
								</PartyTaxScheme>
							</Party>
						</AccountingSupplierParty>

						<AccountingCustomerParty xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
							<Party>
								<PartyIdentification>
									<ID schemeID="{{docCustomer.id_scheme}}" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCustomer.tax_id}}</ID>
								</PartyIdentification>

								<PartyName>
									<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCustomer.customer_name}}</Name>
								</PartyName>

								<PostalAddress>
									<StreetName xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCustomerAddress.address_line1|replace("&", "&#38;") if docCustomerAddress.address_line1 else ''}}</StreetName>
									<BuildingNumber xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCustomerAddress.address_line2|replace("&", "&#38;") if docCustomerAddress.address_line2 else ''}}</BuildingNumber>
									<CitySubdivisionName xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCustomerAddress.county|replace("&", "&#38;") if docCustomerAddress.county else ''}}</CitySubdivisionName>
									<CityName xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCustomerAddress.city|replace("&", "&#38;") if docCustomerAddress.city else ''}}</CityName>
									<PostalZone xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCustomerAddress.pincode|replace("&", "&#38;") if docCustomerAddress.pincode else ''}}</PostalZone>
									<Country>
										<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCustomerAddress.country or ''}}</Name>
									</Country>
								</PostalAddress>

								<PartyTaxScheme>
									<TaxScheme>
										<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCustomer.tax_office or ''}}</Name>
									</TaxScheme>
								</PartyTaxScheme>

							</Party>
						</AccountingCustomerParty>

						<TaxTotal xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
							<TaxAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.TaxAmount}}</TaxAmount>
							<TaxSubtotal>
								<TaxAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.TaxAmount}}</TaxAmount>
								<Percent xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.TaxPercent}}</Percent>
								<TaxCategory>
									<TaxScheme>
										<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">KDV</Name>
										<TaxTypeCode xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">0015</TaxTypeCode>
									</TaxScheme>
								</TaxCategory>
							</TaxSubtotal>
						</TaxTotal>

						<LegalMonetaryTotal xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
							<LineExtensionAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.LineExtensionAmount}}</LineExtensionAmount>
							<TaxExclusiveAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.TaxExclusiveAmount}}</TaxExclusiveAmount>
							<TaxInclusiveAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.TaxInclusiveAmount}}</TaxInclusiveAmount>
							<AllowanceTotalAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.AllowanceTotalAmount}}</AllowanceTotalAmount>
							<PayableAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.PayableAmount}}</PayableAmount>
						</LegalMonetaryTotal>

						{{docSI.contentLines}}

					</Invoice>
					<TargetCustomer VknTckn="{{docCustomer.tax_id}}" Alias="{{docCustomer.td_alici_alias}}" Title="{{docCustomer.customer_name}}"/>
					<EArchiveInvoiceInfo DeliveryType="Electronic"/>
					<Scenario>Automated</Scenario>
				</InvoiceInfo>
			</invoices>
		</SaveAsDraft>
	</s:Body>
</s:Envelope>
"""

	elif strType == "einvoice-line":
			strResult = """
	<InvoiceLine xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
		<ID xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.idx}}</ID>
		<Note xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"></Note>
		
		<InvoicedQuantity unitCode="{{docCurrentLine.efatura_birimi}}" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.qty}}</InvoicedQuantity>
		<LineExtensionAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.amount}}</LineExtensionAmount>
		
		<AllowanceCharge>
			<ChargeIndicator xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">false</ChargeIndicator>
			<MultiplierFactorNumeric>0.0</MultiplierFactorNumeric>
			<Amount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.discount_amount}}</Amount>
			<PerUnitAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.qty}}</PerUnitAmount>
			<BaseAmount currencyID="TRL">{{docCurrentLine.AllowanceBaseAmount}}</BaseAmount>
		</AllowanceCharge>

		<TaxTotal>
			<TaxAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.TaxAmount}}</TaxAmount>
			<TaxSubtotal>
				<TaxAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.TaxAmount}}</TaxAmount>
				<Percent xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.TaxPercent}}</Percent>
				<TaxCategory>
					<TaxScheme>
						<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">KDV</Name>
						<TaxTypeCode xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">0015</TaxTypeCode>
					</TaxScheme>
				</TaxCategory>
			</TaxSubtotal>
		</TaxTotal>

		<Item>
			<Description xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"></Description>
			<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docItem.item_code}} {{docItem.item_name}}</Name>
			<BrandName xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"></BrandName>
			<ModelName xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"></ModelName>
			<BuyersItemIdentification>
				<ID xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"></ID>
			</BuyersItemIdentification>
			<SellersItemIdentification>
				<ID xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"></ID>
			</SellersItemIdentification>
			<ManufacturersItemIdentification>
				<ID xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"></ID>
			</ManufacturersItemIdentification>
		</Item>
		<Price>
			<PriceAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.rate}}</PriceAmount>
		</Price>
	</InvoiceLine>
		"""

	elif strType == "einvoice-headers":
		strResult = {
			'Accept-Encoding': 'gzip,deflate',
			'Accept': 'text/xml',
			'Content-Type': 'text/xml;charset=UTF-8',
			'Cache-Control': 'no-cache',
			'Pragma': 'no-cache',
			'SOAPAction': 'http://tempuri.org/IBasicIntegration/SaveAsDraft',
			'Connection': 'Keep-Alive'
		}
	
	elif strType == "login-test-headers":
		strResult = {
			'Accept-Encoding': 'gzip,deflate',
			'Accept': 'text/xml',
			'Content-Type': 'text/xml;charset=UTF-8',
			'Cache-Control': 'no-cache',
			'Pragma': 'no-cache',
			'SOAPAction': 'http://tempuri.org/IBasicIntegration/WhoAmI',
			'Connection': 'Keep-Alive'
		}
	elif strType == "login-test-body":
		strResult = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
	<soapenv:Body>
		<tem:WhoAmI>
			<tem:userInfo Username="{{docEISettings.kullaniciadi}}" Password="{{docEISettings.parola}}"/>
		</tem:WhoAmI>
	</soapenv:Body>
</soapenv:Envelope>
"""

	elif strType == "query-invoice-status-headers":
		strResult = {
			'Accept-Encoding': 'gzip,deflate',
			'Accept': 'text/xml',
			'Content-Type': 'text/xml;charset=UTF-8',
			'Cache-Control': 'no-cache',
			'Pragma': 'no-cache',
			'SOAPAction': 'http://tempuri.org/IBasicIntegration/QueryOutboxInvoiceStatus',
			'Connection': 'Keep-Alive'
		}
	
	elif strType == "query-invoice-status-body":
		strResult = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
   <soapenv:Body>
	  <tem:QueryOutboxInvoiceStatus>
		<tem:userInfo Username="{{docEISettings.kullaniciadi}}" Password="{{docEISettings.parola}}"/>
		 <tem:invoiceIds>
			<tem:string>{{docSI.td_efatura_uuid}}</tem:string>
		 </tem:invoiceIds>
	  </tem:QueryOutboxInvoiceStatus>
   </soapenv:Body>
</soapenv:Envelope>
"""
	elif strType == "query-get-user-aliasses-headers":
		strResult = {
			'Accept-Encoding': 'gzip,deflate',
			'Accept': 'text/xml',
			'Content-Type': 'text/xml;charset=UTF-8',
			'Cache-Control': 'no-cache',
			'Pragma': 'no-cache',
			#'SOAPAction': 'http://tempuri.org/IIntegration/GetUserAliasses',
			'SOAPAction': 'http://tempuri.org/IBasicIntegration/GetUserAliasses',
			'Connection': 'Keep-Alive'
		}

	elif strType == "query-get-user-aliasses-body":
		strResult = """
		<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
			<soapenv:Body>
				<tem:GetUserAliasses>
					<tem:userInfo Username="{{docEISettings.kullaniciadi}}" Password="{{docEISettings.parola}}"/>
					<tem:vknTckn>{{docCustomer.tax_id}}</tem:vknTckn>
				</tem:GetUserAliasses>
			</soapenv:Body>
		</soapenv:Envelope>
		"""

	return strResult

def get_service_xml(strType, strIntegrator):
	if strIntegrator == 'Uyumsoft':
		return get_service_xml_for_uyumsoft(strType)
	elif strIntegrator == "Bien Teknoloji":
		return get_service_xml_for_bien_teknoloji(strType)

@frappe.whitelist()
def get_incoming_invoices(doc):
	#Get incoming invoices
	strResult = ""

	try:
		body = get_service_xml('inbox-invoice-list-body')

		headers = get_service_xml('inbox-invoice-list-headers')

		#e-Fatura Ayarları
		docEISettings = frappe.get_single("eInvoice Settings")
		docEISettings.username = docEISettings.kullanici_adi
		docEISettings.parola = docEISettings.get_password('parola')


		if docEISettings.test_modu:
			strServerURL = docEISettings.test_servis_adresi
		else:
			strServerURL = docEISettings.canli_servis_adresi

		body = frappe.render_template(body, context={"docEISettings": docEISettings, "tarih1": tarih1, "tarih2": tarih2}, is_path=False)
		
		#frappe.log_error(str(body), "Olusan istek")

		response = requests.post(strServerURL, headers=headers, data=body)

		#frappe.log_error("Gelen cevap", "Gelen cevap")

		bsMain = BeautifulSoup(response.text, "lxml")
		if response.status_code == 500:
			strErrorMessage = bsMain.find_all("faultstring")[0].text
			strResult = "İşlem Başarısız! Hata Kodu:500. Detay:"
			strResult += strErrorMessage
			dctEttn = ""
		elif response.status_code == 200:
			frappe.log_error("Olumlu cevap", "Olumlu cevap")
			strResult = "İşlem Başarılı."
			
			dctInvoiceId = bsMain.find_all("invoiceid")
			#frappe.log_error(dctInvoiceId, "Faturano")
			dctEttn = bsMain.find_all("documentid")
			#frappe.log_error(dctEttn, "Ettn")
			dctTitle = bsMain.find_all("targettitle")
			dctAmount = bsMain.find_all("payableamount")
			dctDate = bsMain.find_all("executiondate")
			dctType = bsMain.find_all("type")
			dctIType = bsMain.find_all("invoicetiptype")
			#dctScn = bsMain.find_all("scenario")


			#frappe.log_error(bsMain,"TEST")
			y = []
			for idx, ettn in enumerate(dctEttn):
				#print(idx, ettn.text)
				ctrl = frappe.db.get_value('Purchase Invoice', {'ettn': ettn.text}, ['name']) #daha önce kabul edilmiş mi?
				if not ctrl:
					tip = ""
					if dctType[idx].text=="ComercialInvoice":
						tip = "TICARIFATURA"
					elif dctType[idx].text=="BaseInvoice":
						tip = "TEMELFATURA"

					x = {
						'ettn': ettn.text,
						'invoiceid': dctInvoiceId[idx].text,
						'title': dctTitle[idx].text,
						'amount': dctAmount[idx].text,
						'date': dctDate[idx].text,
						'type': tip,
						'invoicetype': dctIType[idx].text, 
						#'scenario': dctScn[idx].text
					}
					y.append(x)
			print(y)
			strResult = y
			
		else:
			strResult = _("İşlem Başarısız! Hata Kodu:{0}. Detay:").format(response.status_code)
			dctEttn = ""
			strResult += response.text

	except Exception as e:
		strResult = _("Sunucudan gelen mesaj işlenirken hata oluştu! Detay:{0}").format(e)
		frappe.log_error(e, _("E-Fatura (LoginTest) sunucudan gelen mesaj işlenemedi."))

	return {'result':strResult, 'ettn': dctEttn, 'response':response.text}

@frappe.whitelist()
def send_einvoice(strSalesInvoiceName):

	strResult = ""

	try:
		docSI = frappe.get_doc("Sales Invoice", strSalesInvoiceName)
		docCustomer = frappe.get_doc("Customer", docSI.customer)
		#Ayarlari alalim
		docEISettings = frappe.get_single("EFatura Ayarlar")
		docEISettings.parola = docEISettings.get_password('parola')

		strHeaders = frappe.safe_eval(docEISettings.td_efatura_header) #get_service_xml('einvoice-headers')
		strBody = docEISettings.td_efatura_xml_genel #get_service_xml('einvoice-body')
		strLine = docEISettings.td_efatura_xml_satir #get_service_xml('einvoice-line')
		strTaxWithholding = get_service_xml('einvoice-tevkifat', docEISettings.entegrator)

		docCustomerAddress = frappe.get_doc("Address", docSI.customer_address)

		docCustomer.id_scheme = "VKN" if len(docCustomer.tax_id) == 10 else "TCKN"
		#Eger alias tanimli degil ise bulalim
		if not docCustomer.td_alici_alias:
			docCustomer.td_alici_alias = get_user_aliasses(docCustomer=docCustomer)['alias']

		#Vergi dairesi alalim
		if hasattr(docCustomer, 'tax_office'):
			docCustomer.tax_office = docCustomer.tax_office if docCustomer.tax_office is not None else ''
		else:
			raise ValueError('Müşteri kartlarında için vergi dairesi alanı (tax_office) bulunamadı. (Customize Form ile Customer için tax_office alanı eklenmeli).')

		#Satirlari olusturalim
		docSI.contentLines = ""
		flTotalLineDiscountAmount = 0 #Satirlardan gelen toplam iskonto tutari
		for docSILine in docSI.items:
			docItem = frappe.get_doc("Item", docSILine.item_code)

			#Satir KDV orani, KDV Tutari, KDV Matrahi, Iskonto uygulanan rakami bulalim.
			docSILine.TaxPercent = frappe.get_doc("Account", docSI.taxes[0].account_head).tax_rate #docSI.taxes[0].rate #Satir KDV Orani.#TODO:satira bagli item-tax-template altinda ki oranlardan almali.Suan fatura genelinde ki ilk satirdan aliyoruz
			docSILine.TaxableAmount = docSILine.amount
			docSILine.TaxAmount = round((docSILine.TaxPercent/100) * docSILine.amount, 2)
			docSILine.AllowanceBaseAmount = docSILine.rate * docSILine.qty#Iskonto uygulanan rakam #docSILine.AllowanceBaseAmount = docSILine.price_list_rate * docSILine.qty#Iskonto uygulanan rakam			

			flTotalLineDiscountAmount += docSILine.discount_amount * docSILine.qty

			#E-Fatura birimini ayarlardan bulalim
			lstUnitLine = frappe.get_all('TD EFatura Birim Eslestirme',
				fields=['td_efatura_birimi'],
				filters=[['parent', '=', 'EFatura Ayarlar'], ['td_birim', '=', docSILine.uom]])
			
			if not lstUnitLine:
				raise ValueError('{UOM} birimi için E-Fatura Birimi tanımlanmamış. EFatura Ayarlar sayfasından Birim Eşleştirmesi giriniz.'.format(UOM=docSILine.uom))
			else:
				docSILine.efatura_birimi = lstUnitLine[0]['td_efatura_birimi']

			#XML olusturalim
			str_line_xml = frappe.render_template(strLine, context={"docCurrentLine": docSILine, "docItem":docItem}, is_path=False)
			docSI.contentLines = docSI.contentLines + str_line_xml

		#Ozel alanlari hesaplayalim
		docSI.LineExtensionAmount = docSI.net_total + flTotalLineDiscountAmount #Miktar*BirimFiyat (Iskonto dusulmeden onceki hali, vergi haric)
		docSI.TaxExclusiveAmount = docSI.net_total #VergiMatrahi (Vergiler Haric, Iskonto Dahil, Vergiye tabi kisim)
		docSI.TaxInclusiveAmount = docSI.grand_total #Vergiler, iskonto dahil
		docSI.AllowanceTotalAmount = flTotalLineDiscountAmount #Iskonto tutari
		docSI.ChargeTotal = 0 #Artirim tutari.
		docSI.PayableAmount = docSI.grand_total #Toplam odenecek tutar

		docSI.TaxAmount = docSI.total_taxes_and_charges
		docSI.TaxPercent = frappe.get_doc("Account", docSI.taxes[0].account_head).tax_rate #docSI.taxes[0].rate#TODO:satira bagli item-tax-template altinda ki oranlardan almali.Suan fatura genelinde ki ilk satirdan aliyoruz

		docSI.posting_date_formatted = formatdate(docSI.posting_date, "yyyy-MM-dd")
		docSI.posting_time_formatted = get_time(docSI.posting_time).strftime("%H:%M:%S")#format_time(time_string=docSI.posting_time, format_string='HH:mm:ss')#str(dateutil.parser.parse(docSI.posting_time)).strftime("%H-%M-%S")#docSI.posting_time #"03:55:40"# formatdate(docSI.posting_time, "HH:mm")#"HH:mm:ss.SSSSSSSZ")
		docSI.line_count = len(docSI.items)

		tax_withoholding = docSI.TaxAmount / 2
		tax_total = docSI.TaxAmount

		strTaxWithholding = frappe.render_template(strTaxWithholding, context=
		{
			"kdv_tevkifat1": tax_withoholding, 
			"kdv_tevkifat2": tax_withoholding,
			"kdv_tam": tax_total
		}, is_path=False)

		#Ana dokuman dosyamizi olusturalim. Once not parametreleri dolsun sonra asil dokuman.
		strDocXML = frappe.render_template(strBody, context=
		{
			"docSI": docSI, 
			"docCustomer": docCustomer, 
			"docEISettings": docEISettings,
			"docCustomerAddress": docCustomerAddress
		}, is_path=False)
		strDocXML = frappe.render_template(strDocXML, context=
		{
			"docSI": docSI, 
			"docCustomer": docCustomer, 
			"docEISettings": docEISettings,
			"docCustomerAddress": docCustomerAddress
		}, is_path=False)

		if docEISettings.test_modu:
			strServerURL = docEISettings.test_efatura_adresi
			#Test modunda gonderdigimiz xml i  de saklayalim
			frappe.log_error(strDocXML, _("E-Fatura (send_einvoice) gönderilen paket"))
		else:
			strServerURL = docEISettings.efatura_adresi

		#webservisine gonderelim
		#response = requests.post('https://efatura-test.uyumsoft.com.tr/services/integration', headers=strHeaders, data=strDocXML.encode('utf-8'))
		#response = requests.post('https://efatura.uyumsoft.com.tr/services/integration', headers=strHeaders, data=strDocXML.encode('utf-8'))
		if docEISettings.detailed_log == True:
			frappe.log_error("E-Connect SendEInvoice Request", f"URL={strServerURL},\nHeaders={strHeaders},\nData={strDocXML}")
		
		response = requests.post(strServerURL, headers=strHeaders, data=strDocXML.encode('utf-8'))
		if docEISettings.detailed_log == True:
			frappe.log_error("E-Connect SendEInvoice Response", f"Code={response.status_code},\nResponse={response.text}")

		# You can inspect the response just like you did before. response.headers, response.text, response.content, response.status_code

		bsMain = BeautifulSoup(response.text, "lxml")#response.content.decode('utf8')
		if response.status_code == 500:
			strErrorMessage = bsMain.find_all("faultstring")[0].text
			strResult = "İşlem Başarısız! Hata Kodu:500. Detay:"
			strResult += strErrorMessage
			docSI.add_comment('Comment', text="E-Fatura: Belge gönderilemedi! Detay:" + strResult)
		elif response.status_code == 200:
			objSaveResult = bsMain.find_all("saveasdraftresult")[0]#['issucceded']#.get_attribute_list('is_succeddede')
			if objSaveResult['issucceded'] == "false":
				strResult = "Fatura gönderilemedi! Detay:" + objSaveResult['message']
				docSI.add_comment('Comment', text="E-Fatura: Belge gönderilemedi! Detay:" + objSaveResult['message'])
			else:
				strResult = "İşlem Başarılı."
				#Referanslari faturaya geri yazalim
				objSaveResultInfo = bsMain.find_all("value")[0]#['issucceded']#.get_attribute_list('is_succeddede')

				#docSI.td_efatura_senaryosu = objSaveResultInfo['invoicescenario']
				docSI.db_set('td_efatura_senaryosu', objSaveResultInfo['invoicescenario'], notify=True)
				docSI.db_set('td_efatura_uuid', objSaveResultInfo['id'], notify=True)
				docSI.db_set('td_efatura_ettn', objSaveResultInfo['number'], notify=True)

				#Ayarlarda fatura belge numarasi ayarlanmis ise ilgili alani guncelleyelim. https://app.asana.com/0/1129228181996987/1179462249309721/f
				if docEISettings.td_guncellenecek_alan:
					docSI.db_set(docEISettings.td_guncellenecek_alan, objSaveResultInfo['number'], notify=True)

				docSI.add_comment('Comment', text=_('E-Fatura: Belge gönderildi. (Ek Bilgiler:{0}, {1})'.format(objSaveResultInfo['number'], objSaveResultInfo['id'])))

				#Fatura durumunu alalim
				docSI.db_set('td_efatura_durumu', get_invoice_status(docSI)['result'], notify=True)

				docSI.notify_update()
		else:
			strResult = _("İşlem Başarısız! Hata Kodu:{0}. Detay:").format(response.status_code)
			strResult += response.text

	except Exception as e:
		strResult = _("Hata oluştu! Detay:{0}").format(e)
		frappe.log_error(frappe.get_traceback(), _("E-Fatura (send_einvoice) generated an error."))
	
	return {'result':strResult, 'response':response.text if 'response' in locals() else ''}

@frappe.whitelist()
def get_user_aliasses(strCustomerName = None, docCustomer = None):
	#Firma alias bilgilerini alir. strCustomerName = Musteri Kart ID
	strResult = ""
	strResultAlias = ""

	try:
		if docCustomer is None:
			docCustomer = frappe.get_doc("Customer", strCustomerName)

		#Ayarlari alalim
		docEISettings = frappe.get_single("EFatura Ayarlar")		
		docEISettings.kullaniciadi = docEISettings.kullaniciadi 
		docEISettings.parola = docEISettings.get_password('parola')

		body = get_service_xml('query-get-user-aliasses-body', docEISettings.entegrator)
		headers = get_service_xml('query-get-user-aliasses-headers', docEISettings.entegrator)

		body = frappe.render_template(body, context={"docEISettings": docEISettings, "docCustomer": docCustomer}, is_path=False)
		
		if docEISettings.test_modu:
			strServerURL = docEISettings.test_efatura_adresi
			frappe.log_error(body, _("E-Fatura (get_user_aliasses) gönderilen paket"))
		else:
			strServerURL = docEISettings.efatura_adresi

		if docEISettings.detailed_log == True:
			frappe.log_error("E-Connect GetUserAliasses Request", f"URL={strServerURL},\nHeaders={headers},\nBody={body}")

		response = requests.post(strServerURL, headers=headers, data=body)

		if docEISettings.detailed_log == True:
			frappe.log_error("E-Connect GetUserAliasses Response", f"Code={response.status_code},\nResponse={response.text}")

		bsMain = BeautifulSoup(response.text, "lxml")#response.content.decode('utf8')

		if response.status_code == 500:
			strErrorMessage = bsMain.find_all("faultstring")[0].text
			strResult = "İşlem Başarısız! Hata Kodu:500. Detay:"
			strResult += strErrorMessage
		elif response.status_code == 200:
			objSaveResult = bsMain.find_all("getuseraliassesresult")[0]#['issucceded']#.get_attribute_list('is_succeddede')
			if objSaveResult['issucceded'] == "false":
				strResult = "Adres alınamadı! Detay:" + objSaveResult['message']
				docCustomer.add_comment('Comment', text="E-Fatura: Adres alınamadı! Detay:" + objSaveResult['message'])
			else:
				if len(bsMain.find_all("receiverboxaliases")) == 0:
					#EArsiv kullanicisi olmali
					strResult = "E-Arşiv kullanıcısı."
					docCustomer.db_set('td_alici_alias', 'defaultpk', notify=True)
					docCustomer.add_comment('Comment', text="E-Fatura: E-Arşiv kullanıcısı (defaultpk).")
					docCustomer.notify_update()
				else:
					objReceiverboxAliases = bsMain.find_all("receiverboxaliases")[0]
					strCompanyTitle = bsMain.find_all("definition")[0]['title']
					#print(objReceiverboxAliases['alias'])
					strResultAlias = objReceiverboxAliases['alias']
					strResult = _("Adres {0} olarak güncellendi.Firma Adı:{1}").format(objReceiverboxAliases['alias'], strCompanyTitle)
					docCustomer.db_set('td_alici_alias', objReceiverboxAliases['alias'], notify=True)
					docCustomer.add_comment('Comment', text=_("E-Fatura: Adres {0} olarak güncellendi.Firma Adı:{1}").format(objReceiverboxAliases['alias'], strCompanyTitle))
					docCustomer.notify_update()
		else:
			strResult = _("İşlem Başarısız! Hata Kodu:{0}. Detay:").format(response.status_code)
			strResult += response.text

	except Exception as e:
		strResult = _("Sunucudan gelen mesaj işlenirken hata oluştu! Detay:{0}").format(e)
		frappe.log_error(frappe.get_traceback(), _("E-Fatura (GetUserAliasses) sunucudan gelen mesaj işlenemedi."))

	return {'result':strResult, 'response':response.text, 'alias': strResultAlias}

@frappe.whitelist()
def get_invoice_status(docSI = None, strSaleInvoiceName = None):
	strResult = ""

	if docSI is None:
		docSI = frappe.get_doc("Sales Invoice", strSaleInvoiceName)

	try:
		#Ayarlari alalim
		docEISettings = frappe.get_single("EFatura Ayarlar")		
		docEISettings.kullaniciadi = docEISettings.kullaniciadi 
		docEISettings.parola = docEISettings.get_password('parola')

		body = get_service_xml('query-invoice-status-body', docEISettings.entegrator)
		body = frappe.render_template(body, context={"docEISettings": docEISettings, "docSI": docSI}, is_path=False)

		headers = get_service_xml('query-invoice-status-headers', docEISettings.entegrator)

		if docEISettings.test_modu:
			strServerURL = docEISettings.test_efatura_adresi
			frappe.log_error(body, _("E-Fatura (get_invoice_status) gönderilen paket"))
		else:
			strServerURL = docEISettings.efatura_adresi

		if docEISettings.detailed_log == True:
			frappe.log_error("E-Connect GetInvoiceStatus Request", f"URL={strServerURL},\nHeaders={headers},\nBody={body}")

		response = requests.post(strServerURL, headers=headers, data=body)

		if docEISettings.detailed_log == True:
			frappe.log_error("E-Connect GetInvoiceStatus Response", f"Code={response.status_code}, Response={response.text}")

		bsMain = BeautifulSoup(response.text, "lxml")#response.content.decode('utf8')
		if response.status_code == 500:
			strErrorMessage = bsMain.find_all("faultstring")[0].text
			strResult = "İşlem Başarısız! Hata Kodu:500. Detay:"
			strResult += strErrorMessage
		elif response.status_code == 200:
			strResult = bsMain.find_all("value")[0]['status']
		else:
			strResult = _("İşlem Başarısız! Hata Kodu:{0}. Detay:").format(response.status_code)
			strResult += response.text

	except Exception as e:
		strResult = _("Sunucudan gelen mesaj işlenirken hata oluştu! Detay:{0}").format(e)
		frappe.log_error(frappe.get_traceback(), _("E-Fatura (GetInvoiceStatus) sunucudan gelen mesaj işlenemedi."))

	return {'result':strResult, 'response':response.text}

@frappe.whitelist()
def login_test(doc):
	dctResult = {'op_result': False, 'op_message': ''}

	try:
		#Ayarlari alalim
		#docEISettings = frappe.get_single("EFatura Ayarlar")
		docEISettings = frappe.get_doc(json.loads(doc))
		docEISettings.kullaniciadi = docEISettings.kullaniciadi 
		docEISettings.parola = docEISettings.get_password('parola')

		body = get_service_xml('login-test-body', docEISettings.entegrator)
		body = frappe.render_template(body, context={"docEISettings": docEISettings}, is_path=False)

		headers = get_service_xml('login-test-headers', docEISettings.entegrator)

		if docEISettings.test_modu:
			strServerURL = docEISettings.test_efatura_adresi
			frappe.log_error(body, _("E-Fatura (login_test) gönderilen paket"))
		else:
			strServerURL = docEISettings.efatura_adresi

		#response = requests.post('https://efatura-test.uyumsoft.com.tr/services/integration', headers=headers, data=body)
		#response = requests.post('https://efatura.uyumsoft.com.tr/services/integration', headers=headers, data=body)
		if docEISettings.detailed_log == True:
			frappe.log_error("E-Connect Login Request", f"URL={strServerURL}, Headers={headers}, Body={body}")
		
		response = requests.post(strServerURL, headers=headers, data=body)
		if docEISettings.detailed_log == True:
			frappe.log_error("E-Connect Login Response", f"Code={response.status_code}, Response={response.text}")

		bsMain = BeautifulSoup(response.text, "lxml")#response.content.decode('utf8')
		if response.status_code == 500:
			dctResult['op_result'] = False
			strErrorMessage = bsMain.find_all("faultstring")[0].text
			dctResult['op_message'] = "İşlem Başarısız! Hata Kodu:500. Detay:"
			dctResult['op_message'] += strErrorMessage
		elif response.status_code == 200:
			dctResult['op_result'] = True
			dctResult['op_message'] = "İşlem Başarılı."
			strCustomerName = bsMain.find_all("name")[1].text
			dctResult['op_message'] += _("Firma Adı:{0}").format(strCustomerName)
		else:
			dctResult['op_result'] = False
			dctResult['op_message'] = _("İşlem Başarısız! Hata Kodu:{0}. Detay:").format(response.status_code)
			dctResult['op_message'] += response.text

	except Exception as e:
		dctResult['op_result'] = False
		dctResult['op_message'] = _("Sunucu iletişiminde beklenmeyen hata oluştu! Detay:{0}").format(e)
		frappe.log_error(frappe.get_traceback(), _("E-Fatura (LoginTest) hatası"))

	return dctResult

### DOSYA GUNCELLEME MODULU
@frappe.whitelist()
def td_attach_all_docs_from_item(document, strURL):
	from frappe import _, throw
	from frappe.utils import flt
	from frappe.utils.file_manager import save_url, save_file, get_file_name, remove_all, remove_file
	from frappe.utils import get_site_path, get_files_path, random_string, encode
	import json
	#Dokuman icin dosya eklerini ayarlayalim
	document = json.loads(document)
	document2 = frappe._dict(document)

	current_attachments = [] #Icinde oldugumuz dokumanda ki ek dosya bilgilerini tutar
	items = [] #Dokumanda ki malzeme bilgilerini tutar
	item_attachments = [] #Malzemede ki ek dosya bilgilerini tutar
	current_attachments_file_name = [] #Dosya adini saklar
	item_attachments_file_name = [] #Dosya adi

	#Once bulundugumuz dokumanda ki butun ek dosyalari bir dizi icinde (current_attachments) saklayalaim
	for file_info in frappe.db.sql("""select file_url, file_name from `tabFile` where attached_to_doctype = %(doctype)s and attached_to_name = %(docname)s""", {'doctype': document2.doctype, 'docname': document2.name}, as_dict=True ):
			current_attachments.append(file_info.file_url)
			current_attachments_file_name.append(file_info.file_name)
			#frappe.msgprint("Found " + file_info.file_name + " file in this document", "Document Files")

	#Dokumanda ki butun malzeme kartlari icin ek dosya var mi kontrol edelim
	for item in document["items"]:
		#Malzeme kayidina ulasalim
		item_doc = frappe.get_doc('Item', item["item_code"]) #frappe.get_doc("Item",item)
		#frappe.msgprint(str(item_doc["attachments"][0]["file_url"]))
		#frappe.msgprint("Getting " + item_doc.name + " files", "Items")

		#Malzemeye bagli ek dosyalari alalim
		for file_info in frappe.db.sql("""select file_url, file_name from `tabFile` where attached_to_doctype = %(doctype)s and attached_to_name = %(docname)s""", {'doctype': item_doc.doctype, 'docname': item_doc.name}, as_dict=True ):
			item_attachments.append(file_info.file_url)
			item_attachments_file_name.append(file_info.file_name)
			#frappe.msgprint("Found " + file_info.file_name + " file in item " + item_doc.name, "Item Files")

	count = 0
	dIndex = 0
	#frappe.msgprint("Starting to add attachments")
	for attachment in item_attachments:
		# Check to see if this file is attached to the one we are looking for
		if not attachment in current_attachments:
			count = count + 1
			#frappe.msgprint(attachment)
			myFile = save_url(attachment, item_attachments_file_name[dIndex], document2.doctype, document2.name, "Home/Attachments", 0)
			myFile.file_name = item_attachments_file_name[dIndex] #attachment
			myFile.save()
			current_attachments.append(attachment)
		dIndex = dIndex + 1

	frappe.msgprint("{0} adet dosya eklendi".format(count))


import frappe
import zipfile
import io
import base64
import requests
import uuid
import json


def get_settings_for_company(company):
	"""Şirkete göre ayar döner, yoksa None döner"""
	if not company:
		return None

	settings_list = frappe.get_all("TD EInvoice Settings", filters={"company": company}, limit=1)
	if not settings_list:
		return None

	settings_name = settings_list[0].name
	settings = frappe.get_doc("TD EInvoice Settings", settings_name)
	return settings

@frappe.whitelist()
def check_profile(receiver_id=None, company=None):
	"""Profile sorgulama fonksiyonu"""
	if not receiver_id:
		return {"status": "fail", "error": "Receiver ID is required"}

	try:
		if company:
			settings = get_settings_for_company(company)
		else:
			settings = frappe.get_single("TD EInvoice Settings")

		if not settings.integrator:
			return {"status": "fail", "error": "Integrator not configured"}
		
		integrator = frappe.get_doc("TD EInvoice Integrator", settings.integrator)
		if not integrator.td_enable:
			return {"status": "fail", "error": "Integration is disabled"}

		soap_body = create_profile_check_soap(receiver_id, integrator)
		url = integrator.test_efatura_url if integrator.td_test else integrator.efatura_url
		headers = {"Content-Type": 'application/soap+xml; charset=utf-8; action="http://tempuri.org/IEBelge/checkProfile"'}

		resp = requests.post(url, data=soap_body.encode("utf-8"), headers=headers, timeout=60)

		if resp.status_code != 200:
			return {"status": "fail", "error": f"HTTP {resp.status_code}"}

		return_code = extract_return_code_from_response(resp.text)
		if return_code and return_code not in [300, 400]:
			return {"status": "fail", "error": f"ReturnCode: {return_code}"}

		profile_type = extract_profile_from_response(resp.text)
		
		return {
			"status": "success",
			"http_status": resp.status_code,
			"profile": profile_type,
			"return_code": return_code
		}

	except Exception as e:
		return {"status": "fail", "error": str(e)}


@frappe.whitelist()
def send_invoice_to_finalizer(invoice_name=None):
	if not invoice_name:
		return {"status": "fail", "error": "Invoice name is required"}

	try:
		company = frappe.get_value("Sales Invoice", invoice_name, "company")
		settings = get_settings_for_company(company)
		
		if not settings.integrator:
			return {"status": "fail", "error": "Integrator not configured"}
		
		integrator = frappe.get_doc("TD EInvoice Integrator", settings.integrator)
		if not integrator.td_enable:
			return {"status": "fail", "error": "Integration is disabled"}

		doc_si = frappe.get_doc("Sales Invoice", invoice_name)
		customer = frappe.get_doc("Customer", doc_si.customer)

		if integrator.td_enable:
			missing_fields = []

			if not customer.tax_id:
				missing_fields.append("Tax ID (tax_id)")
			if not customer.custom_tax_office:
				missing_fields.append("Tax Office (custom_tax_office)")
			if not doc_si.customer_address:
				missing_fields.append("Billing Address (customer_address)")

			if missing_fields:
				frappe.throw(
					"E-Invoice integration is enabled. The following fields are missing in the customer record:<br><ul><li>" +
					"</li><li>".join(missing_fields) +
					"</li></ul>"
				)

		# VKN/TC numarasını al
		receiver_id = customer.tax_id or doc_si.tax_id or doc_si.customer_name
		if not receiver_id:
			return {"status": "fail", "error": "Tax ID (receiver_id) is required"}

		profile_result = check_profile(receiver_id, company)

		# Log full profile result
		frappe.log_error(
			title=f"Profile Check Result - {invoice_name}",
			message=json.dumps(profile_result, indent=2, ensure_ascii=False)
		)

		if profile_result.get("status") != "success":
			return {"status": "fail", "error": f"Profile check failed: {profile_result.get('error')}"}

		profile_type = profile_result.get("profile", "EARSIVFATURA")

		frappe.db.set_value("Sales Invoice", invoice_name, "custom_profile_type", profile_type)
		frappe.db.commit()

		# Alıcı bilgilerini getir
		customer_address = frappe.get_doc("Address", doc_si.customer_address) if doc_si.customer_address else None
		receiver_info = get_receiver_info(doc_si, customer, customer_address, profile_type)

		# Log alıcı bilgileri
		frappe.log_error(
			title=f"Receiver Info Log - {invoice_name}",
			message=json.dumps(receiver_info, indent=2, ensure_ascii=False)
		)

		# XML üretimi
		xml_content = generate_invoice_xml(doc_si, profile_type, settings)

		# ZIP'e çevir
		mem = io.BytesIO()
		with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
			zf.writestr(f"{doc_si.name}.xml", xml_content)
		zip_base64 = base64.b64encode(mem.getvalue()).decode()

		# SOAP body oluştur
		soap_body = create_soap_body(zip_base64, integrator, f"{doc_si.name}.zip", receiver_id)
		url = integrator.test_efatura_url if integrator.td_test else integrator.efatura_url

		headers = {
			"Content-Type": 'application/soap+xml; charset=utf-8; action="http://tempuri.org/IEBelge/sendData"'
		}
		resp = requests.post(url, data=soap_body.encode("utf-8"), headers=headers, timeout=60)

		# Geniş log
		if integrator.detailed_log:
			mem_check = io.BytesIO()
			with zipfile.ZipFile(mem_check, "w", zipfile.ZIP_DEFLATED) as zf:
				zf.writestr(f"{doc_si.name}.xml", xml_content)

			mem_check.seek(0)
			with zipfile.ZipFile(mem_check, "r") as zf:
				zip_content = zf.read(f"{doc_si.name}.xml").decode('utf-8')

			frappe.log_error(
				f"""🧾 Profile: {profile_type}
🏷️  Receiver ID used: {receiver_id}
🔍 Profile Check Result:
{json.dumps(profile_result, indent=2, ensure_ascii=False)}

SOAP BODY
{soap_body}

SOAP BODY ENCODED
{soap_body.encode("utf-8")}

📁 ZIP içeriği:
{zip_content}

📄 Sent XML:
{xml_content}

📤 Finalizer Response:
HTTP {resp.status_code}
{resp.text}""",
				f"Finalizer SOAP Result - {invoice_name}"
			)

		add_comment_to_invoice(invoice_name, resp.text, resp.status_code)

		is_success = check_response_success(resp.status_code, resp.text)

		return {
			"status": "success" if is_success else "fail",
			"http_status": resp.status_code,
			"profile_used": profile_type,
			"response": resp.text
		}

	except Exception as e:
		frappe.log_error(str(e), f"Finalizer Send Error - {invoice_name}")
		return {"status": "fail", "error": str(e)}

@frappe.whitelist(allow_guest=False)
def download_pdf(invoice_name):
	import email #multipart response
	from email import policy #multipart response

	# Download and attach PDF of the invoice via getPdfDocument method
	dctResult = frappe._dict({
		'op_result': False,
		'op_message': '',
	})

	docSI = frappe.get_doc("Sales Invoice", invoice_name)
	if not docSI.get("custom_td_efatura_id"):
		dctResult.op_result = False
		dctResult.op_message = _("E-Fatura ID olmadığı için işlem yapılmadı!")
	else:
		docTDEInvoiceSettings = get_settings_for_company(docSI.company)
		docIntegrator = frappe.get_doc("TD EInvoice Integrator", docTDEInvoiceSettings.integrator)
		docIntegrator.password = docIntegrator.get_password('password')

		request_url = docIntegrator.test_efatura_url if docIntegrator.td_test else docIntegrator.efatura_url

		headers = {
			'Content-Type': 'application/soap+xml;charset=UTF-8;action="http://tempuri.org/IEBelge/getPdfDocument"',
			'SOAPAction': 'http://tempuri.org/IEBelge/getPdfDocument',
			'Accept-Encoding': 'gzip,deflate'
		}

		soap_body = """<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:tem="http://tempuri.org/" xmlns:ns="http://schemas.datacontract.org/2004/07/">
		<soap:Header/>
		<soap:Body>
			<tem:getPdfDocument>
				<tem:document>
					<ns:DocumentID>{{ docSI.custom_td_efatura_id }}</ns:DocumentID>
					<ns:DocumentVariable></ns:DocumentVariable>
					<ns:IsRead>false</ns:IsRead>
					<ns:ReceiverID></ns:ReceiverID>
					<ns:ReturnCode></ns:ReturnCode>
					<ns:ReturnText></ns:ReturnText>
					<ns:SenderID></ns:SenderID>
					<ns:UUID>{{ docSI.td_efatura_uuid }}</ns:UUID>
					<ns:UserID>{{ docIntegrator.username }}</ns:UserID>
					<ns:UserPassword>{{ docIntegrator.password }}</ns:UserPassword>
					<ns:binaryData></ns:binaryData>
					<ns:fileName></ns:fileName>
				</tem:document>
			</tem:getPdfDocument>
		</soap:Body>
	</soap:Envelope>"""

		soap_body = frappe.render_template(soap_body, context={'docSI': docSI, 'docIntegrator': docIntegrator})

		try:
			frappe.log_error("getPdfDocument SOAP Body", f"{soap_body}")

			response = requests.post(
				request_url,
				data=soap_body.encode('utf-8'),
				headers=headers,
				timeout=60
			)

			frappe.log_error("getPdfDocument Response", f"Status:{response.status_code}\nBody:{response.text[:500]}")

			if response.status_code == 200:
				# Parse multipart response
				content_type = response.headers.get('Content-Type', '')
				header = f"Content-Type: {content_type}\r\n\r\n".encode('utf-8')
				full_message = header + response.content
				msg = email.message_from_bytes(full_message, policy=policy.default)

				pdf_bytes = None
				return_text = None

				# First part: SOAP envelope — extract ReturnText to confirm success
				# Second part: octet-stream — the actual PDF bytes
				if msg.is_multipart():
					parts = list(msg.iter_parts())
					for part in parts:
						ct = part.get_content_type()
						if 'application/xop+xml' in ct or 'application/soap+xml' in ct:
							soap_xml = part.get_payload(decode=True).decode('utf-8')
							soup = BeautifulSoup(soap_xml, 'xml')
							rt = soup.find('ReturnText')
							if rt:
								return_text = rt.text
						elif 'application/octet-stream' in ct:
							pdf_bytes = part.get_payload(decode=True)

				if pdf_bytes and pdf_bytes.startswith(b'%PDF'):
					file_name = f"{invoice_name}.pdf"
					# Attach PDF to the Sales Invoice
					file_doc = frappe.get_doc({
						'doctype': 'File',
						'file_name': file_name,
						'attached_to_doctype': 'Sales Invoice',
						'attached_to_name': invoice_name,
						'content': pdf_bytes,
						'is_private': 1
					})
					file_doc.save(ignore_permissions=True)

					dctResult['op_result'] = True
					dctResult['op_message'] = _('PDF indirildi ve eklendi.')
					dctResult['file_url'] = file_doc.file_url
				else:
					dctResult['op_message'] = return_text or _("PDF verisi alınamadı.")
			else:
				dctResult['op_message'] = f"HTTP Error {response.status_code}: {response.text}"

		except Exception as e:
			dctResult['op_result'] = False
			dctResult['op_message'] = f"Exception: {str(e)}"
			frappe.log_error("getPdfDocument Exception", frappe.get_traceback())

	docSI.add_comment(
		comment_type='Comment',
		text=_("PDF İndirme İşlem Sonucu: {0} - {1}").format(dctResult.op_result, dctResult.op_message)
	)

	return dctResult

@frappe.whitelist(allow_guest=False)
def update_invoice_status(invoice_name):
	import email #multipart response
	from email import policy #multipart response

	#Check invoice status and write back to GIB DURUM
	dctResult = {
		'op_result': False,
		'op_message': '',
	}

	docSI = frappe.get_doc("Sales Invoice", invoice_name)
	docTDEInvoiceSettings = get_settings_for_company(docSI.company)
	docIntegrator = frappe.get_doc("TD EInvoice Integrator", docTDEInvoiceSettings.integrator)
	docIntegrator.password = docIntegrator.get_password('password') #docIntegrator.username
	docCustomer = frappe.get_doc("Customer", docSI.customer)

	docSI.posting_date_str = formatdate(docSI.posting_date, "dd.mm.yyyy")

	request_url = docIntegrator.test_efatura_url if docIntegrator.td_test else docIntegrator.efatura_url

	headers = {
		'Content-Type': 'application/soap+xml;charset=UTF-8;action="http://tempuri.org/IEBelge/viewDocumentList"',
		'SOAPAction': 'http://tempuri.org/IEBelge/viewDocumentList',
		'Accept-Encoding': 'gzip,deflate'
	}

	soap_body = """<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:tem="http://tempuri.org/" xmlns:ns="http://schemas.datacontract.org/2004/07/">
	<soap:Header/>
	<soap:Body>
		<tem:viewDocumentList>
			<tem:listQuery>
				<ns:DocumentCount>50</ns:DocumentCount>
				<ns:DocumentType>EFATURA</ns:DocumentType>
				<ns:DocumentViewType>GİDEN</ns:DocumentViewType>
				<ns:EndDate>{{ docSI.posting_date_str }}</ns:EndDate>
				<ns:ListRead>true</ns:ListRead>
				<ns:ReceiverID>{{ docCustomer.tax_id }}</ns:ReceiverID>
				<ns:ReplyStatus></ns:ReplyStatus>
				<ns:SenderID></ns:SenderID>
				<ns:StartDate>{{ docSI.posting_date_str }}</ns:StartDate>
				<ns:UserID>{{ docIntegrator.username }}</ns:UserID>
			  <ns:UserPassword>{{ docIntegrator.password }}</ns:UserPassword>
			</tem:listQuery>
		</tem:viewDocumentList>
	</soap:Body>
</soap:Envelope>"""

	soap_body = frappe.render_template(soap_body, context={'docSI': docSI, 'docIntegrator': docIntegrator, 'docCustomer': docCustomer })

	try:
		frappe.log_error("ViewDocumentList SOAP Body", f"{soap_body}")

		response = requests.post(
			request_url,
			data=soap_body.encode('utf-8'),
			headers=headers,
			timeout=60
		)
		
		frappe.log_error("ViewDocumentList Response", f"Status:{response.status_code}\nBody:{response.text}")

		if response.status_code == 200:
			# Parse multipart response
			content_type = response.headers.get('Content-Type', '')
			# Add Content-Type header to response body for email parser
			header = f"Content-Type: {content_type}\r\n\r\n".encode('utf-8')
			full_message = header + response.content
			# Parse as multipart message
			msg = email.message_from_bytes(full_message, policy=policy.default)

			document_list_xml = None
			# Iterate through multipart sections
			if msg.is_multipart():
				for part in msg.iter_parts():
					# Look for the XML part containing DocumentList
					content_type_part = part.get_content_type()
					if 'application/octet-stream' in content_type_part or \
					   'text/xml' in content_type_part:
						# Get content as bytes and decode with UTF-8
						document_list_xml = part.get_payload(decode=True).decode('utf-8')
						break

			if document_list_xml:
				# Parse the XML response to find the StatusDetail for the UUID
				soup = BeautifulSoup(document_list_xml, 'xml')

				# Extract the DocumentList section
				document_list = soup.find('DocumentList')
				#frappe.log_error("ViewDocumentList TMP 1", frappe.as_json(document_list))
				if document_list:
					# Find the Document with the matching UUID
					for document in document_list.find_all('Document'):
						uuid_element = document.find('UUID')
						if uuid_element and uuid_element.text == docSI.td_efatura_uuid:
							status_detail = document.find('StatusDetail')
							if status_detail:
								# Update the invoice status with the StatusDetail
								#docSI.db_set('gib_status', status_detail.text, update_modified=False)
								status_code = document.find('StatusCode')
								#docSI.db_set('custom_gib_status_code', status_code.text, update_modified=False)
								invoice_id = document.find('InvoiceID')
								docSI.gib_status = status_detail.text
								docSI.custom_gib_status_code = status_code.text
								docSI.custom_td_efatura_id = invoice_id.text
								docSI.save()
								dctResult['op_result'] = True
								dctResult['op_message'] = status_detail.text
								break
					else:
						dctResult['op_message'] = _("UUID not found in response")
				else:
					dctResult['op_message'] = _("DocumentList not found in response")
			else:
				dctResult['op_message'] = _("Could not extract DocumentList from multipart response")
		else:
			# Handle error responses
			dctResult['op_result'] = False
			dctResult['op_message'] = f"HTTP Error for ViewDocumentList {response.status_code}: {response.text}"

	except Exception as e:
		dctResult['op_result'] = False
		dctResult['op_message'] = f"Exception: {str(e)}"
		frappe.log_error(f"ViewDocumentList Exception: {str(e)}")

	#Add a comment if it is failed.
	if dctResult['op_result'] == False:
		docSI.add_comment(
				comment_type='Comment',
				text=_("Fatura Durum Güncelleme Hatası: {0}").format(dctResult['op_message'])
			)

	return dctResult

def update_invoice_statuses():
	# Update invoice statuses. Get invoice list which doesn't have status codes in skip_codes.
	# Call update_invoice_status for each invoice, run hourly.
	
	frappe.log_error("update_invoice_statuses started")

	skip_codes = [
		'1300',  # OK
		# Error codes
		'1110', '1115', '1120', '1125', '1130', '1135',
		'1140', '1145', '1150', '1155', '1160', '1165',
		'1170', '1175', '1180', '1185', '1190', '1195',
		'1215', '1230'
	]

	filters = {
		'docstatus': 1,
		'td_efatura_uuid': ['!=', ''],
		'posting_date': ['>=', frappe.utils.add_days(frappe.utils.today(), -8)]
	}
	
	or_filters = [
		['custom_gib_status_code', 'is', 'not set'],
		['custom_gib_status_code', '=', ''],
		['custom_gib_status_code', 'not in', skip_codes]
	]
	
	dctInvoices = frappe.db.get_list(
		'Sales Invoice',
		filters=filters,
		or_filters=or_filters,
		fields=['name', 'custom_gib_status_code', 'posting_date'],
		order_by='creation desc',
		limit=50,
		as_list=False
	)

	for invoice in dctInvoices:
		frappe.enqueue(
			method='erpnextturkish.td_utils.update_invoice_status',
			queue='short',
			timeout=120,
			invoice_name=invoice.name,
			job_name="LOGEDO.UpdInvStatus",
			enqueue_after_commit=True
		)

	frappe.log_error("update_invoice_statuses finished", "Processed " + str(len(dctInvoices)) + " invoices.\n" + frappe.as_json(dctInvoices))


def check_response_success(status_code, response_text):
	"""Response başarı kontrolü"""
	if status_code != 200:
		return False
	
	if "ReturnCode" in response_text:
		try:
			import re
			return_code_match = re.search(r'<.*?ReturnCode.*?>(\d+)</', response_text)
			if return_code_match:
				return_code = int(return_code_match.group(1))
				return return_code == 300
		except:
			pass
	return True


def add_comment_to_invoice(invoice_name, response_text, status_code):
	"""Faturaya yorum ekle"""
	try:
		comment_text = f"Finalizer Response (HTTP {status_code}):\n{response_text[:1000]}..."
		frappe.get_doc({
			"doctype": "Comment",
			"comment_type": "Comment",
			"reference_doctype": "Sales Invoice",
			"reference_name": invoice_name,
			"content": comment_text
		}).insert(ignore_permissions=True)
	except:
		pass


def extract_return_code_from_response(response_text):
	"""Response'dan ReturnCode çıkar"""
	try:
		import re
		patterns = [
			r'<a:ReturnCode>(\d+)</a:ReturnCode>',
			r'<.*?ReturnCode.*?>(\d+)</',
			r'<ReturnCode>(\d+)</ReturnCode>',
			r'<d4p1:ReturnCode>(\d+)</d4p1:ReturnCode>'
		]
		
		for pattern in patterns:
			match = re.search(pattern, response_text, re.IGNORECASE)
			if match:
				return int(match.group(1))
		return None
	except:
		return None


def extract_profile_from_response(response_text):
	"""Response'dan profile tipini çıkar"""
	try:
		import re
		patterns = [
			r'<a:ReturnText>(.*?)</a:ReturnText>',
			r'<.*?ReturnText.*?>(.*?)</',
			r'<ReturnText>(.*?)</ReturnText>',
			r'<d4p1:ReturnText>(.*?)</d4p1:ReturnText>'
		]
		
		for pattern in patterns:
			match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
			if match:
				return match.group(1).strip()
		
		if "EFATURA" in response_text.upper():
			return "EFATURA"
		elif "EARSIV" in response_text.upper():
			return "EARSIVFATURA"
			
		return "EARSIVFATURA"
	except:
		return "EARSIVFATURA"


def create_profile_check_soap(receiver_id, integrator):
	password = integrator.get_password('password') if hasattr(integrator, 'get_password') else integrator.password
	user_id = integrator.username
	return f"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
				 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
				 xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Header/>
  <soap12:Body>
	<checkProfile xmlns="http://tempuri.org/">
	  <document xmlns:d4p1="http://schemas.datacontract.org/2004/07/">
		<d4p1:ReceiverID>{receiver_id}</d4p1:ReceiverID>
		<d4p1:UserID>{user_id}</d4p1:UserID>
		<d4p1:UserPassword>{password}</d4p1:UserPassword>
		<d4p1:DocumentVariable>efaturaozel</d4p1:DocumentVariable>
	  </document>
	</checkProfile>
  </soap12:Body>
</soap12:Envelope>"""



def get_sender_info(settings):
	"""Gönderici bilgilerini al (her zaman string döner, None asla dönmez)"""
	try:
		company_doc = frappe.get_doc("Company", settings.company) if getattr(settings, "company", None) else None

		def safe_get(obj, field):
			return str(getattr(obj, field, "") or "").strip() if obj else ""

		return {
			'tax_id': safe_get(settings, "central_registration_system") or safe_get(company_doc, "tax_id"),
			'company_name': safe_get(settings, "company_name") or safe_get(company_doc, "company_name"),
			'phone': safe_get(settings, "phone") or safe_get(company_doc, "phone_no"),
			'fax': safe_get(settings, "fax") or safe_get(company_doc, "fax"),
			'website': safe_get(settings, "website") or safe_get(company_doc, "website"),
			'email': safe_get(settings, "email") or safe_get(company_doc, "email"),
			'tax_office': safe_get(settings, "tax_office"),
			'country': safe_get(settings, "country"),
			'city': safe_get(settings, "city"),
			'district': safe_get(settings, "district"),
			'address': safe_get(settings, "address")
		}
	except Exception as e:
		frappe.log_error(f"get_sender_info error: {str(e)}", "Sender Info Error")
		return {
			'tax_id': "",
			'company_name': "",
			'phone': "",
			'fax': "",
			'website': "",
			'email': "",
			'tax_office': "",
			'country': "",
			'city': "",
			'district': "",
			'address': ""
		}

def get_receiver_info(doc, customer_doc, customer_address, profile_type):
	"""Alıcı bilgilerini al (güvenli, sade versiyon)"""
	try:
		# Vergi numarası: önce müşteri, sonra belge
		tax_id = getattr(customer_doc, "tax_id", "") or getattr(doc, "tax_id", "") or ""

		# İsim ve soyisim ayrıştır
		full_name = getattr(customer_doc, "customer_name", "") or getattr(doc, "customer_name", "")
		first_name, last_name = "", ""
		if full_name:
			parts = full_name.strip().split(None, 1)
			first_name = parts[0]
			last_name = parts[1] if len(parts) > 1 else ""

		# Eğer e-Arşiv ise ve bireysel isim varsa sahıs bilgilerini hazırla
		individual_fields = ""
		if profile_type == "EARSIVFATURA" and first_name:
			individual_fields = f"\n    <SahisAd>{first_name}</SahisAd>"
			if last_name:
				individual_fields += f"\n    <SahisSoyad>{last_name}</SahisSoyad>"

		# Güvenli getter
		def safe_get(obj, field):
			return getattr(obj, field, "") or ""

		return {
			'id_type': "VKN" if len(tax_id) == 10 else "TC",
			'id_number': tax_id,
			'phone': safe_get(customer_address, "phone"),
			'email': safe_get(customer_address, "email_id"),
			'tax_office': safe_get(customer_doc, "custom_tax_office"),
			'country': safe_get(customer_address, "country") if customer_address else "Türkiye",
			'city': safe_get(customer_address, "city") if customer_address else "",
			'district': safe_get(customer_address, "county") if customer_address else "",
			'address': f"{safe_get(customer_address, 'address_line1')} {safe_get(customer_address, 'address_line2')}".strip() if customer_address else "",
			'individual_fields': individual_fields,
			'company_name': full_name
		}

	except:
		return {
			'id_type': "TC",
			'id_number': "",
			'phone': "",
			'email': "",
			'tax_office': "",
			'country': "Türkiye",
			'city': "",
			'district': "",
			'address': "",
			'individual_fields': "",
			'company_name': ""
		}


def get_mapped_unit(settings, original_unit):
	"""
	Unit mapping tablosundan orijinal birime karşılık gelen einvoice_unit'i bulur
	"""
	if not settings or not hasattr(settings, 'unit_mapping'):
		return original_unit
	
	for mapping in settings.unit_mapping:
		if hasattr(mapping, 'unit_name') and mapping.unit_name == original_unit:
			return mapping.einvoice_unit

	return original_unit
def render_jinja_template(template_str, doc):
	"""Jinja template'ini render et"""
	if not template_str:
		return ""
	
	try:
		import re
		import html
		from bs4 import BeautifulSoup

		pattern = r'\{\{\s*doc(?:SI)?\.([\w_]+)\s*\}\}'

		def clean_html(value):
			"""HTML içeriğini temizle ve düz metin olarak döndür"""
			try:
				if not value:
					return ""
				
				# Eğer HTML içeriyorsa BeautifulSoup ile temizle
				if isinstance(value, str) and ('<' in value and '>' in value):
					soup = BeautifulSoup(value, "html.parser")
					
					# Her <p> etiketini yeni satır ile değiştir
					for p in soup.find_all('p'):
						p.insert_after('\n')
					
					# <br> etiketlerini yeni satır ile değiştir
					for br in soup.find_all('br'):
						br.replace_with('\n')
					
					# Tüm metni al
					text = soup.get_text()
					
					# Satır sonlarını düzenle
					lines = []
					for line in text.split('\n'):
						line = line.strip()
						if line:  # Boş satırları atla
							lines.append(line)
					
					return '\n'.join(lines)
				else:
					return str(value)
			except Exception as e:
				# Hata durumunda orijinal değeri döndür
				return str(value) if value else ""

		def replace_var(match):
			field_name = match.group(1)
			try:
				value = getattr(doc, field_name, '')
				if value:
					# HTML temizleme işlemini her zaman uygula
					cleaned_value = clean_html(value)
					return cleaned_value
				return ''
			except Exception as e:
				return ''
		
		result = re.sub(pattern, replace_var, template_str)
		return result

	except Exception as e:
		frappe.log_error(f"Jinja template error: {str(e)}", "Jinja Template Error")
		return template_str

def generate_notes_block(doc, settings):
	"""Not bloğunu oluştur (satır satır Aciklama olarak yaz)"""
	try:
		notes_xml = ""

		siparis_tarih = getattr(doc, "td_siparis_tarihi", "") or str(doc.posting_date)
		belge_no = getattr(doc, "td_belge_no", "") or doc.name
		belge_tarih = getattr(doc, "td_belge_tarihi", "") or str(doc.posting_date)

		# <Siparis> bloğu yalnızca bir kez yazılmalı
		notes_xml += f"""
  <Siparis>
	<SiparisTarihi>{siparis_tarih}</SiparisTarihi>
	<BelgeNo>{belge_no}</BelgeNo>
	<BelgeTarihi>{belge_tarih}</BelgeTarihi>
  </Siparis>"""

		aciklama_satirlar = []

		# 4 adet not formül alanını kontrol et (td_not1_formul - td_not4_formul)
		for i in range(1, 5):
			field_name = f"td_not{i}_formul"
			formula = getattr(settings, field_name, None)

			if formula:
				rendered_value = render_jinja_template(formula, doc)
				if rendered_value:
					# Satır satır böl ve boş olmayanları listeye ekle
					lines = rendered_value.split('\n')
					for line in lines:
						line = line.strip()
						if line:  # Boş satırları atla
							aciklama_satirlar.append(line)

		# Eğer açıklama varsa <AciklamaSatir> bloğunu oluştur
		if aciklama_satirlar:
			notes_xml += "\n  <AciklamaSatir>"
			for line in aciklama_satirlar:
				notes_xml += f"\n    <Aciklama>{line}</Aciklama>"
			notes_xml += "\n  </AciklamaSatir>"

		return notes_xml

	except Exception as e:
		frappe.log_error(f"Notes block error: {str(e)}", "Notes Block Error")
		return ""
def generate_invoice_xml(doc, profile_type, settings):
	import html
	import uuid
	import json
	import io
	from decimal import Decimal, ROUND_HALF_UP

	def round_currency(amount, precision=2):
		return float(Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

	try:
		uuid_str = str(uuid.uuid4()).upper()
		frappe.db.set_value("Sales Invoice", doc.name, "td_efatura_uuid", uuid_str)

		if profile_type == "EARSIVFATURA":
			xml_profile = "EARSIVFATURA"
			scenario = "SATIS"
		else:
			xml_profile = "EFATURA"
			scenario = doc.custom_scenario_type or "SATIS"

		invoice_type = doc.custom_invoice_type or "SATIS"
		conversion_rate = float(doc.conversion_rate or 1.0)

		customer_doc = frappe.get_doc("Customer", doc.customer)
		customer_address = None
		if doc.customer_address:
			try:
				customer_address = frappe.get_doc("Address", doc.customer_address)
			except Exception as e:
				frappe.log_error(message=str(e), title="Address fetch error")

		sender_info = get_sender_info(settings)
		receiver_info = get_receiver_info(doc, customer_doc, customer_address, profile_type)

		sender_info['country'] = "Türkiye"
		receiver_info['country'] = "Türkiye"
		receiver_info['individual_fields'] = receiver_info.get('individual_fields', "")

		item_tax_map = {}
		for tax in doc.taxes:
			if tax.item_wise_tax_detail:
				try:
					parsed = json.loads(tax.item_wise_tax_detail)
					for item_code, tax_data in parsed.items():
						if isinstance(tax_data, list) and len(tax_data) >= 2:
							rate = float(tax_data[0] or 0)
							amount = float(tax_data[1] or 0)
						elif isinstance(tax_data, dict):
							rate = float(tax_data.get('rate', 0))
							amount = float(tax_data.get('amount', 0))
						else:
							continue
						item_tax_map.setdefault(item_code, []).append({
							"rate": rate,
							"amount": amount,
							"tax_name": tax.account_head
						})
				except Exception as e:
					frappe.log_error(message=f"Error parsing tax details: {e}", title="Tax parse error")

		if all(not v for v in item_tax_map.values()) and doc.taxes:
			default_tax_rate = float(doc.taxes[0].rate or 0)
			for item in doc.items:
				tax_amount = (item.amount * default_tax_rate) / 100
				item_tax_map[item.item_code] = [{
					"rate": default_tax_rate,
					"amount": tax_amount,
					"tax_name": "Varsayılan KDV"
				}]

		if doc.currency != "TRY" and conversion_rate != 1.0:
			for item_code in item_tax_map:
				for tax in item_tax_map[item_code]:
					tax["amount"] = round_currency(tax["amount"] / conversion_rate)

		net_total = round_currency(float(doc.net_total or 0))
		grand_total = round_currency(float(doc.grand_total or 0))
		toplam_iskonto = round_currency(float(doc.discount_amount or 0))

		def get_vergi_detaylari(item_code, matrah_tutar):
			"""Generate tax detail XML for an invoice line item.
			
			Args:
				item_code: The item code to look up tax information
				matrah_tutar: The taxable base amount (gross amount before discount = price_list_rate * qty)
			
			Returns:
				XML string containing tax details including FaturaVergiDetay for all tax entries.
				Even items with 100% discount (0 tax amount) must have FaturaVergiDetay section.
			"""
			vergi_satirlari = item_tax_map.get(item_code, [])

			# Always include all tax entries, even with 0 amount (required by e-Fatura integration)
			toplam_vergi = sum(round_currency(v["amount"]) for v in vergi_satirlari)

			detay_xml = f'<ToplamVergiTutar ParaBirimi="{doc.currency}">{toplam_vergi:.2f}</ToplamVergiTutar>'
			for vergi in vergi_satirlari:
				vergi_tutari = round_currency(vergi["amount"])
				detay_xml += f'''
		 <FaturaVergiDetay>
		<MatrahTutar ParaBirimi="{doc.currency}">{matrah_tutar:.2f}</MatrahTutar>
		<VergiTutar ParaBirimi="{doc.currency}">{vergi_tutari:.2f}</VergiTutar>
		<VergiOran>{vergi["rate"]:.2f}</VergiOran>
		<Kategori>
		  <VergiAdi>KDV</VergiAdi>
		  <VergiKodu>0015</VergiKodu>
		</Kategori>
		 </FaturaVergiDetay>'''
			return detay_xml

		def generate_normal_satir(i, item):
			mapped_unit = get_mapped_unit(settings, item.uom)

			iskonto_orani = float(item.discount_percentage or 0)
			iskonto_tutari = round_currency(float(item.discount_amount or 0) * item.qty)
			item_amount = round_currency(float(item.amount or 0))
			
			# MatrahTutar: Gross amount before discount (price_list_rate * qty)
			# This is required by e-Fatura integration - must show the taxable base amount
			# even for items with 100% discount where tax amount is 0
			gross_amount = round_currency(flt(item.price_list_rate) * flt(item.qty))

			# LOG SATIRI: Discount ve hesaplama detayları
			frappe.log_error(
				title=f"İskonto Satır Logu - {doc.name} - Satır {i+1}",
				message=f"""🧾 Satır: {i+1}
Item Code: {item.item_code}
Item Name: {item.item_name}
Qty: {item.qty}
Rate: {item.rate}
Price List Rate: {item.price_list_rate}
Amount: {item.amount}
Discount %: {item.discount_percentage}
Discount Amount: {item.discount_amount}
➡️ Kullanılan İskonto Oranı: {iskonto_orani}
➡️ Kullanılan İskonto Tutarı: {iskonto_tutari}
➡️ MatrahTutar (Gross Amount): {gross_amount}
"""
			)

			# Pass gross_amount for MatrahTutar (taxable base before discount)
			vergi_xml = get_vergi_detaylari(item.item_code, gross_amount)

			#Create the item line
			effective_price_list_rate = flt(item.price_list_rate) or flt(item.rate)
			effective_rate = flt(item.rate)
			qty = flt(item.qty)

			# Ensure no negative discounts
			if effective_price_list_rate > effective_rate:
				# Normal case: discount calculation
				final_price_list_rate = effective_price_list_rate
			else:
				# Edge case: rate > price list rate, avoid negative discount
				iskonto_orani = 0.0
				iskonto_tutari = 0.0
				final_price_list_rate = effective_rate

			return f'''
  <FaturaSatir>
	<SatirNo>{i+1}</SatirNo>
	<UrunAdi>{html.escape(item.item_name)}</UrunAdi>
	<UrunKodu>{html.escape(item.item_code)}</UrunKodu>
	<OlcuBirimi>{mapped_unit}</OlcuBirimi>
	<BirimFiyati ParaBirimi="{doc.currency}">{final_price_list_rate}</BirimFiyati>
	<Miktar>{item.qty}</Miktar>
	<Vergi>
	  {vergi_xml}
	</Vergi>
	<IskontoOrani>{iskonto_orani:.2f}</IskontoOrani>
	<IskontoTutari ParaBirimi="{doc.currency}">{iskonto_tutari:.2f}</IskontoTutari>
  </FaturaSatir>'''

		satirlar = "".join([generate_normal_satir(i, item) for i, item in enumerate(doc.items)])
		posting_time = str(doc.posting_time or '12:00:00').split('.')[0]
		notes_block = generate_notes_block(doc, settings)

		if abs(net_total - round_currency(doc.net_total or 0)) > 0.05:
			frappe.log_error(
				message=f"Net total mismatch: calculated={net_total}, doc={doc.net_total}",
				title="Invoice Total Warning"
			)

		if abs(grand_total - round_currency(doc.grand_total or 0)) > 0.05:
			frappe.log_error(
				message=f"Grand total mismatch: calculated={grand_total}, doc={doc.grand_total}",
				title="Invoice Total Warning"
			)

		xml_template = f"""<?xml version="1.0"?>
<Fatura xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Profil>{xml_profile}</Profil>
  <Senaryo>{scenario}</Senaryo>
  <No></No>
  <UUID>{uuid_str}</UUID>
  <Tarih>{doc.posting_date}</Tarih>
  <Zaman>{posting_time}</Zaman>
  <Tip>{invoice_type}</Tip>
  <ParaBirimi>{doc.currency}</ParaBirimi>
  <SatirSayisi>{len(doc.items)}</SatirSayisi>
  <FaturaSahibi>
	<VknTc>VKN</VknTc>
	<VknTcNo>{sender_info['tax_id']}</VknTcNo>
	<Unvan>{html.escape(sender_info['company_name'])}</Unvan>
	<Tel>{sender_info['phone']}</Tel>
	<Eposta>{sender_info['email']}</Eposta>
	<VergiDairesi>{sender_info.get('tax_office', 'Türk Vergi Dairesi')}</VergiDairesi>
	<Ulke>{sender_info['country']}</Ulke>
	<Sehir>{sender_info['city']}</Sehir>
	<Ilce>{sender_info['district']}</Ilce>
	<AdresMahCad>{sender_info['address']}</AdresMahCad>
  </FaturaSahibi>
  <FaturaAlici>
	<VknTc>{receiver_info.get('id_type', 'VKN')}</VknTc>
	<VknTcNo>{receiver_info.get('id_number', '')}</VknTcNo>
	<Unvan>{html.escape(receiver_info.get('company_name', ''))}</Unvan>
	<Tel>{receiver_info['phone']}</Tel>
	<Eposta>{receiver_info['email']}</Eposta>
	<VergiDairesi>{receiver_info.get('tax_office', '')}</VergiDairesi>
	<Ulke>{receiver_info['country']}</Ulke>
	<Sehir>{receiver_info['city']}</Sehir>
	<Ilce>{receiver_info.get('district') or ''}</Ilce>
	<AdresMahCad>{receiver_info['address']}</AdresMahCad>{receiver_info['individual_fields']}
  </FaturaAlici>{notes_block}
{satirlar}
  <ToplamVergiHaricTutar ParaBirimi="{doc.currency}">{net_total:.2f}</ToplamVergiHaricTutar>
  <ToplamVergiDahilTutar ParaBirimi="{doc.currency}">{grand_total:.2f}</ToplamVergiDahilTutar>
  <ToplamIskontoTutar ParaBirimi="{doc.currency}">{toplam_iskonto:.2f}</ToplamIskontoTutar>
  <OdenecekTutar ParaBirimi="{doc.currency}">{grand_total:.2f}</OdenecekTutar>
  <DovizKuru>{conversion_rate}</DovizKuru>
</Fatura>"""

		return xml_template

	except Exception as e:
		frappe.log_error(message=str(e), title="generate_invoice_xml hata")
		raise

def create_soap_body(zip_base64, integrator, file_name="invoice.zip", receiver_id="22222222222"):
	password = integrator.get_password('password') if hasattr(integrator, 'get_password') else integrator.password
	user_id = integrator.username
	return f"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
				 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
				 xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
	<sendData xmlns="http://tempuri.org/">
	  <document xmlns:d4p1="http://schemas.datacontract.org/2004/07/" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
		<d4p1:DocumentID i:nil="true" />
		<d4p1:DocumentVariable>efaturaozel</d4p1:DocumentVariable>
		<d4p1:IsRead>false</d4p1:IsRead>
		<d4p1:ReceiverID>{receiver_id}</d4p1:ReceiverID>
		<d4p1:ReturnCode i:nil="true" />
		<d4p1:ReturnText i:nil="true" />
		<d4p1:SenderID i:nil="true" />
		<d4p1:UUID i:nil="true" />
		<d4p1:UserID>{user_id}</d4p1:UserID>
		<d4p1:UserPassword>{password}</d4p1:UserPassword>
		<d4p1:binaryData>
		  <d4p1:FileByte>{zip_base64}</d4p1:FileByte>
		  <d4p1:FileName>{file_name}</d4p1:FileName>
		</d4p1:binaryData>
		<d4p1:fileName>{file_name}</d4p1:fileName>
	  </document>
	</sendData>
  </soap12:Body>
</soap12:Envelope>"""




import frappe
import zipfile
import io
import base64
import requests
import uuid
import json
import html
@frappe.whitelist()
def send_delivery_note_to_finalizer(delivery_note_name=None):
	"""E-İrsaliye gönderme fonksiyonu"""
	if not delivery_note_name:
		return {"status": "fail", "error": "Delivery Note name is required"}

	try:
		# Delivery Note'u al
		doc_dn = frappe.get_doc("Delivery Note", delivery_note_name)
		
		# Delivery Note'taki company'ye göre TD EWayBill Settings'i bul
		ewaybill_settings = frappe.get_value("TD EWayBill Settings", 
										   {"company": doc_dn.company}, 
										   "*")
		
		if not ewaybill_settings:
			return {"status": "fail", "error": f"TD EWayBill Settings not found for company: {doc_dn.company}"}
			
		# Dict'e çevir
		ewaybill_settings = frappe.get_doc("TD EWayBill Settings", ewaybill_settings.name)
		
		if not ewaybill_settings.integrator:
			return {"status": "fail", "error": "Integrator not configured in TD EWayBill Settings"}
		
		integrator = frappe.get_doc("TD EInvoice Integrator", ewaybill_settings.integrator)
		if not integrator.td_enable:
			return {"status": "fail", "error": "Integration is disabled"}

		# Müşteri bilgilerini kontrol et
		customer = frappe.get_doc("Customer", doc_dn.customer)
		if integrator.td_enable:
			missing_fields = []
			if not customer.tax_id:
				missing_fields.append("Tax ID")
			if not customer.custom_tax_office:
				missing_fields.append("Tax Office")
			if not doc_dn.customer_address:
				missing_fields.append("Customer Address")

			if missing_fields:
				fields_str = ", ".join(_(missing_fields))
				frappe.throw(_("E-İrsaliye entegrasyonu aktif. Aşağıdaki zorunlu alanlar eksik: ") + f"{fields_str}.")

		# Posta kodu validasyonu
		validate_postal_codes(doc_dn, ewaybill_settings)

		receiver_id = customer.tax_id or doc_dn.customer_name
		if not receiver_id:
			return {"status": "fail", "error": "Tax ID (receiver_id) is required"}

		# E-İrsaliye XML oluştur (ewaybill_settings'i geçir)
		xml_content = generate_delivery_note_xml(doc_dn, ewaybill_settings)

		# ZIP dosyası oluştur
		mem = io.BytesIO()
		with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
			zf.writestr(f"{doc_dn.name}.xml", xml_content)
		zip_base64 = base64.b64encode(mem.getvalue()).decode()

		# SOAP body oluştur
		soap_body = create_eirsaliye_soap_body(zip_base64, integrator, f"{doc_dn.name}.zip", receiver_id)
		url = integrator.test_efatura_url if integrator.td_test else integrator.efatura_url

		headers = {
			"Content-Type": 'application/soap+xml; charset=utf-8; action="http://tempuri.org/IEBelge/sendData"'
		}
		
		resp = requests.post(url, data=soap_body.encode("utf-8"), headers=headers, timeout=60)

		# 🔽 Sadece detailed_log aktifse log kaydet
		if integrator.detailed_log:
			frappe.log_error(
				f"""📦 E-İrsaliye Gönderildi
📄 Sent XML:\n{xml_content}

📤 Finalizer Response:
HTTP {resp.status_code}
{resp.text}""",
				f"E-İrsaliye Result - {delivery_note_name}"
			)

		# Yorum ekle
		add_comment_to_delivery_note(delivery_note_name, resp.text, resp.status_code)

		is_success = check_response_success(resp.status_code, resp.text)

		return {
			"status": "success" if is_success else "fail",
			"http_status": resp.status_code,
			"response": resp.text
		}

	except Exception as e:
		frappe.log_error(str(e), f"E-İrsaliye Send Error - {delivery_note_name}")
		return {"status": "fail", "error": str(e)}


def validate_postal_codes(doc_dn, ewaybill_settings=None):
	"""Sadece müşteri adresi için posta kodu kontrolü yapar"""
	missing_postal_codes = []
	
	# Müşteri posta kodu kontrolü
	if doc_dn.customer_address:
		try:
			customer_address = frappe.get_doc("Address", doc_dn.customer_address)
			if not customer_address.pincode or not str(customer_address.pincode).strip():
				missing_postal_codes.append("Müşteri adresi posta kodu")
		except:
			missing_postal_codes.append("Müşteri adresi posta kodu")
	else:
		missing_postal_codes.append("Müşteri adresi posta kodu")
	
	if missing_postal_codes:
		fields_str = ", ".join(missing_postal_codes)
		frappe.throw(f"E-İrsaliye için zorunlu posta kodu alanları eksik: {fields_str}")


def get_einvoice_unit(item_uom, ewaybill_settings):
	"""
	Delivery Note'daki UOM'u e-fatura için uygun birime çevirir
	ewaybill_settings'deki unit_mapping tablosundan karşılığını bulur
	"""
	try:
		# unit_mapping tablosunda unit_name'e karşılık gelen einvoice_unit'i bul
		if hasattr(ewaybill_settings, 'unit_mapping') and ewaybill_settings.unit_mapping:
			for mapping in ewaybill_settings.unit_mapping:
				if mapping.unit_name == item_uom:
					return mapping.einvoice_unit
		
		# Eğer mapping bulunamazsa orijinal UOM'u döndür
		return item_uom
		
	except Exception as e:
		frappe.log_error(f"get_einvoice_unit error: {str(e)}", "Unit Mapping Error")
		return item_uom

def generate_delivery_note_xml(doc, ewaybill_settings):
	"""E-İrsaliye XML oluştur"""
	import uuid
	import html

	uuid_str = str(uuid.uuid4()).upper()
	doc.custom_td_eirsaliye_uuid = uuid_str
	doc.save()

	customer_doc = frappe.get_doc("Customer", doc.customer)
	customer_address = None
	if doc.customer_address:
		try:
			customer_address = frappe.get_doc("Address", doc.customer_address)
		except:
			pass

	# Sevkiyat adresi için ayrı address alma
	shipping_address = None
	if doc.shipping_address_name:
		try:
			shipping_address = frappe.get_doc("Address", doc.shipping_address_name)
		except:
			pass

	def safe_get(obj, field):
		return getattr(obj, field, "") or ""

	# Country alanlarını Turkey - Türkiye dönüştürme fonksiyonu falan filan
	def convert_country(country):
		return "Türkiye" if country == "Turkey" else country

	sender_info = get_sender_info_from_ewaybill_settings(ewaybill_settings)

	receiver_info = {
		'tax_id': customer_doc.tax_id,
		'company_name': customer_doc.customer_name,
		'phone': safe_get(customer_address, "phone"),
		'email': safe_get(customer_address, "email_id"),
		'tax_office': customer_doc.custom_tax_office,
		'city': safe_get(customer_address, "city"),
		'district': safe_get(customer_address, "county"),
		'address': f"{safe_get(customer_address, 'address_line1')} {safe_get(customer_address, 'address_line2')}".strip(),
		'country': convert_country(safe_get(customer_address, "country")),
		'pincode': safe_get(customer_address, "pincode")
	}

	shipping_info = {
		'city': safe_get(shipping_address, "city") if shipping_address else receiver_info['city'],
		'district': safe_get(shipping_address, "county") if shipping_address else receiver_info['district'],
		'address': f"{safe_get(shipping_address, 'address_line1')} {safe_get(shipping_address, 'address_line2')}".strip() if shipping_address else receiver_info['address'],
		'country': convert_country(safe_get(shipping_address, "country")) if shipping_address else receiver_info['country'],
		'pincode': safe_get(shipping_address, "pincode") if shipping_address else receiver_info['pincode']
	}

	#testttt
	# Şoför bilgileri
	sofor_adi = ""
	sofor_soyadi = ""
	sofor_tc = ""
	plaka = ""

	if doc.driver_name:
		parts = doc.driver_name.strip().split()
		if len(parts) >= 2:
			sofor_adi = " ".join(parts[:-1])
			sofor_soyadi = parts[-1]
		elif len(parts) == 1:
			sofor_adi = parts[0]

	if doc.driver:
		try:
			driver_doc = frappe.get_doc("Driver", doc.driver)
			sofor_tc = str(getattr(driver_doc, "custom_driver_id", "") or "")
			plaka = str(getattr(driver_doc, "license_number", "") or
						getattr(driver_doc, "license_plate", "") or
						getattr(driver_doc, "custom_license_plate", "") or
						getattr(driver_doc, "vehicle_no", "") or "")
		except Exception as e:
			print(f"Driver bilgisi alınırken hata: {e}")

	# Şoför bilgileri validasyonu
	if not sofor_adi or not sofor_soyadi or not sofor_tc:
		frappe.throw("Şoför bilgileri eksik! Şoför Adı, Soyadı ve TC No alanları dolu olmalıdır.")

	# Taşıyıcı bilgileri
	tasiyici_vkn = sender_info['tax_id']
	tasiyici_unvan = sender_info['company_name']
	
	if doc.transporter:
		try:
			transporter_supplier = frappe.get_doc("Supplier", doc.transporter)
			tasiyici_vkn = transporter_supplier.tax_id
			tasiyici_unvan = doc.transporter_name
		except:
			pass
	
	
	tasiyici_vkn_tc = "TC" if len(str(tasiyici_vkn)) == 11 else "VKN"

	sevk_info = {
		'tarih': doc.posting_date or frappe.utils.today(),
		'zaman': str(doc.posting_time or "12:00:00").split('.')[0],
		'siparis_tarihi': doc.posting_date or frappe.utils.today(),
		'siparis_no': doc.name,
		'belge_tarihi': doc.posting_date or frappe.utils.today(),
		'belge_no': doc.name,
		'posta_kodu': shipping_info['pincode']  # Sevkiyat adresinden posta kodu
	}

	satirlar = ""
	for i, item in enumerate(doc.items):
		einvoice_unit = get_einvoice_unit(item.uom, ewaybill_settings)
		satirlar += f'''
  <FaturaSatir>
	<SatirNo>{i+1}</SatirNo>
	<UrunAdi>{html.escape(item.item_name)}</UrunAdi>
	<UrunKodu>{html.escape(item.item_code)}</UrunKodu>
	<OlcuBirimi>{einvoice_unit}</OlcuBirimi>
	<BirimFiyati ParaBirimi="{doc.currency or 'TRY'}">{item.rate}</BirimFiyati>
	<Miktar>{item.qty}</Miktar>
  </FaturaSatir>'''

	net_total = getattr(doc, 'net_total', 0) or getattr(doc, 'total', 0) or 0
	grand_total = getattr(doc, 'grand_total', 0) or getattr(doc, 'rounded_total', 0) or net_total
	discount_amount = getattr(doc, 'discount_amount', 0) or 0

	# Sender VknTc kontrolü
	sender_vkn_tc = "TC" if len(str(sender_info['tax_id'])) == 11 else "VKN"
	
	# Receiver VknTc kontrolü
	receiver_vkn_tc = "TC" if len(str(receiver_info['tax_id'])) == 11 else "VKN"
	
	# TC için isim soyisim ayırma
	receiver_sahis_ad = ""
	receiver_sahis_soyad = ""
	if receiver_vkn_tc == "TC":
		# customer_name alanından direkt olarak al
		name_parts = customer_doc.customer_name.strip().split()
		if len(name_parts) >= 2:
			receiver_sahis_ad = " ".join(name_parts[:-1])
			receiver_sahis_soyad = name_parts[-1]
		elif len(name_parts) == 1:
			receiver_sahis_ad = name_parts[0]
	
	# FaturaAlici kısmı için TC kontrolü ile dinamik XML oluşturma
	fatura_alici_xml = f"""  <FaturaAlici>
	<VknTc>{receiver_vkn_tc}</VknTc>
	<VknTcNo>{receiver_info['tax_id']}</VknTcNo>
	<Unvan>{html.escape(receiver_info['company_name'])}</Unvan>
	<Tel>{receiver_info['phone']}</Tel>
	<Eposta>{receiver_info['email']}</Eposta>
	<VergiDairesi>{receiver_info['tax_office']}</VergiDairesi>
	<Ulke>{receiver_info['country']}</Ulke>
	<Sehir>{receiver_info['city']}</Sehir>
	<Ilce>{receiver_info['district']}</Ilce>
	<AdresMahCad>{receiver_info['address']}</AdresMahCad>"""
	
	# TC ise SahisAd ve SahisSoyad alanlarını ekle
	if receiver_vkn_tc == "TC":
		fatura_alici_xml += f"""
	<SahisAd>{html.escape(receiver_sahis_ad)}</SahisAd>
	<SahisSoyad>{html.escape(receiver_sahis_soyad)}</SahisSoyad>"""
	
	fatura_alici_xml += "\n  </FaturaAlici>"
	
	xml_template = f"""<?xml version="1.0"?>
<Fatura xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Profil>EIRSALIYE</Profil>
  <Senaryo>TEMELIRSALIYE</Senaryo>
  <No></No>
  <UUID>{uuid_str}</UUID>
  <Tarih>{doc.posting_date}</Tarih>
  <Zaman>{sevk_info['zaman']}</Zaman>
  <Tip>SEVK</Tip>
  <ParaBirimi>{doc.currency or 'TRY'}</ParaBirimi>
  <SatirSayisi>{len(doc.items)}</SatirSayisi>
  <FaturaSahibi>
	<VknTc>{sender_vkn_tc}</VknTc>
	<VknTcNo>{sender_info['tax_id']}</VknTcNo>
	<Unvan>{html.escape(sender_info['company_name'])}</Unvan>
	<Tel>{sender_info['phone']}</Tel>
	<Eposta>{sender_info['email']}</Eposta>
	<VergiDairesi>{sender_info['tax_office']}</VergiDairesi>
	<Ulke>{convert_country(sender_info['country'])}</Ulke>
	<Sehir>{sender_info['city']}</Sehir>
	<Ilce>{sender_info['district']}</Ilce>
	<AdresMahCad>{sender_info['address']}</AdresMahCad>
  </FaturaSahibi>
{fatura_alici_xml}
  <Irsaliye>
	<Tasiyici>
	  <VknTc>{tasiyici_vkn_tc}</VknTc>
	  <VknTcNo>{tasiyici_vkn}</VknTcNo>
	  <Unvan>{html.escape(tasiyici_unvan)}</Unvan>
	  <Plaka>{plaka}</Plaka>
	  <SoforAdi>{sofor_adi}</SoforAdi>
	  <SoforSoyadi>{sofor_soyadi}</SoforSoyadi>
	  <SoforTcNo>{sofor_tc}</SoforTcNo>
	</Tasiyici>
	<Sevk>
	  <SevkTarihi>{sevk_info['tarih']}</SevkTarihi>
	  <SevkZamani>{sevk_info['zaman']}</SevkZamani>
	  <SiparisTarihi>{sevk_info['siparis_tarihi']}</SiparisTarihi>
	  <SiparisNo>{sevk_info['siparis_no']}</SiparisNo>
	  <BelgeTarihi>{sevk_info['belge_tarihi']}</BelgeTarihi>
	  <BelgeNo>{sevk_info['belge_no']}</BelgeNo>
	  <Ulke>{shipping_info['country']}</Ulke>
	  <Sehir>{shipping_info['city']}</Sehir>
	  <Ilce>{shipping_info['district']}</Ilce>
	  <AdresMahCad>{shipping_info['address']}</AdresMahCad>
	  <PostaKodu>{sevk_info['posta_kodu']}</PostaKodu>
	</Sevk>   
 </Irsaliye>
{satirlar}
  <ToplamVergiHaricTutar ParaBirimi="{doc.currency or 'TRY'}">{net_total}</ToplamVergiHaricTutar>
  <ToplamVergiDahilTutar ParaBirimi="{doc.currency or 'TRY'}">{grand_total}</ToplamVergiDahilTutar>
  <ToplamIskontoTutar ParaBirimi="{doc.currency or 'TRY'}">{discount_amount}</ToplamIskontoTutar>
  <OdenecekTutar ParaBirimi="{doc.currency or 'TRY'}">{grand_total}</OdenecekTutar>
  <DovizKuru>1</DovizKuru>
</Fatura>"""

	return xml_template

def get_sender_info_from_ewaybill_settings(ewaybill_settings):
	"""TD EWayBill Settings'den gönderici bilgilerini al"""
	try:
		# Company doc'u al
		company_doc = frappe.get_doc("Company", ewaybill_settings.company) if ewaybill_settings.company else None

		# company_name öncelikli olarak settings içinden alınır, yoksa Company doc'tan
		company_name = getattr(ewaybill_settings, "company_name", None) or (company_doc.company_name if company_doc else None)

		return {
			'tax_id': ewaybill_settings.central_registration_system or (company_doc.tax_id if company_doc else None),
			'company_name': company_name,
			'phone': getattr(ewaybill_settings, "phone", None) or "",
			'email': getattr(ewaybill_settings, "email", None) or "",
			'fax': getattr(ewaybill_settings, "fax", None) or "",
			'website': getattr(ewaybill_settings, "website", None) or "",
			'tax_office': ewaybill_settings.tax_office or "",
			'country': ewaybill_settings.country or "",
			'city': ewaybill_settings.city or "",
			'district': ewaybill_settings.district or "",
			'address': ewaybill_settings.address or "",
			'postal_code': getattr(ewaybill_settings, 'postal_code', None) or ""
		}

	except Exception as e:
		frappe.log_error(f"get_sender_info_from_ewaybill_settings error: {str(e)}", "EWayBill Sender Info Error")
		return {
			'tax_id': None, 
			'company_name': getattr(ewaybill_settings, "company_name", None) or "",
			'phone': "",
			'email': "",
			'fax': "",
			'website': "",
			'tax_office': "", 
			'country': "", 
			'city': "", 
			'district': "", 
			'address': "",
			'postal_code': ""
		}


def create_eirsaliye_soap_body(zip_base64, integrator, file_name="delivery.zip", receiver_id="3881416132"):
	"""E-İrsaliye SOAP body oluştur"""
	password = integrator.get_password('password') if hasattr(integrator, 'get_password') else integrator.password
	user_id = integrator.username
	
	return f"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
				 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
				 xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
	<sendData xmlns="http://tempuri.org/">
	  <document xmlns:d4p1="http://schemas.datacontract.org/2004/07/" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
		<d4p1:DocumentID i:nil="true" />
		<d4p1:DocumentVariable>eirsaliyeozel</d4p1:DocumentVariable>
		<d4p1:IsRead>false</d4p1:IsRead>
		<d4p1:ReceiverID>{receiver_id}</d4p1:ReceiverID>
		<d4p1:ReturnCode i:nil="true" />
		<d4p1:ReturnText i:nil="true" />
		<d4p1:SenderID i:nil="true" />
		<d4p1:UUID i:nil="true" />
		<d4p1:UserID>{user_id}</d4p1:UserID>
		<d4p1:UserPassword>{password}</d4p1:UserPassword>
		<d4p1:binaryData>
		  <d4p1:FileByte>{zip_base64}</d4p1:FileByte>
		  <d4p1:FileName>{file_name}</d4p1:FileName>
		</d4p1:binaryData>
		<d4p1:fileName>{file_name}</d4p1:fileName>
	  </document>
	</sendData>
  </soap12:Body>
</soap12:Envelope>"""


def add_comment_to_delivery_note(delivery_note_name, response_text, status_code):
	"""Delivery Note'a yorum ekle"""
	try:
		comment_text = f"E-İrsaliye Response (HTTP {status_code}):\n{response_text[:1000]}..."
		frappe.get_doc({
			"doctype": "Comment",
			"comment_type": "Comment",
			"reference_doctype": "Delivery Note",
			"reference_name": delivery_note_name,
			"content": comment_text
		}).insert(ignore_permissions=True)
	except:
		pass


def check_response_success(status_code, response_text):
	"""Response başarı kontrolü"""
	if status_code != 200:
		return False
	
	if "ReturnCode" in response_text:
		try:
			import re
			return_code_match = re.search(r'<.*?ReturnCode.*?>(\d+)</', response_text)
			if return_code_match:
				return_code = int(return_code_match.group(1))
				return return_code == 300
		except:
			pass
	return True

import frappe
import xml.etree.ElementTree as ET
import json
import traceback

@frappe.whitelist()
def parse_xml_and_fill_table(xml_string, docname):
	# XML başını temizle
	lines = xml_string.strip().splitlines()
	for i, line in enumerate(lines):
		if line.strip().startswith("<?xml"):
			xml_string = "\n".join(lines[i:])
			break

	try:
		root = ET.fromstring(xml_string)
	except ET.ParseError as e:
		frappe.throw(f"XML parse edilemedi: {str(e)}")

	doc = frappe.get_doc("TD EInvoice Inbox", docname)

	invoice_number = root.findtext("No")
	invoice_date = root.findtext("Tarih")
	invoice_type = root.findtext("Tip")
	supplier_name = root.findtext("FaturaSahibi/Unvan")
	total = root.findtext("ToplamVergiHaricTutar")
	general_total = root.findtext("OdenecekTutar")

	# Vergi bilgisi
	tax_node = root.find("FaturaSatir/Vergi/FaturaVergiDetay/VergiTutar")
	tax = float(tax_node.text) if tax_node is not None else 0

	# Ürün bilgilerini topla
	items = []
	for item_node in root.findall("FaturaSatir"):
		item_name = item_node.findtext("UrunAdi") or "XML Ürün"
		item_code = item_node.findtext("UrunKodu") or item_name
		qty = float(item_node.findtext("Miktar") or 1)
		rate = float(item_node.findtext("BirimFiyati") or 0)

		items.append({
			"item_code": item_code,
			"item_name": item_name,
			"qty": qty,
			"rate": rate
		})

	# Tabloya yalnızca fatura özeti yaz
	doc.append("invoices_received", {
		"invoice_number": invoice_number,
		"date": invoice_date,
		"invoice_type": invoice_type,
		"supplier": supplier_name,
		"total": float(total or 0),
		"tax": tax,
		"general_total": float(general_total or 0),
		"custom_invoice_type": invoice_type,
		"custom_selected": 0
	})
	doc.save()

	# Ürünleri cache'e yaz (1 saat geçerli)
	cache_key = f"xml_cache::{docname}::{invoice_number}"
	frappe.cache().set_value(cache_key, json.dumps(items), expires_in_sec=3600)

	return {"status": "ok"}


@frappe.whitelist()
def create_invoices_from_selected(rows):
	rows = json.loads(rows) if isinstance(rows, str) else rows
	created = []

	try:
		for row in rows:
			invoice_number = row.get("invoice_number")
			docname = row.get("parent")
			cache_key = f"xml_cache::{docname}::{invoice_number}"
			items_data = frappe.cache().get_value(cache_key)

			if not items_data:
				frappe.throw(f"Faturanın ürün bilgisi cache'de yok. Lütfen XML'i yeniden yükleyin. ({invoice_number})")

			items = json.loads(items_data)
			supplier = get_or_create_supplier(row.get("supplier"))

			pi = frappe.new_doc("Purchase Invoice")
			pi.supplier = supplier
			pi.posting_date = row.get("date")
			pi.bill_no = invoice_number
			pi.custom_invoice_type = row.get("custom_invoice_type")
			pi.currency = "TRY"

			for item in items:
				item_code = get_or_create_item_code(item["item_code"], item["item_name"])
				pi.append("items", {
					"item_code": item_code,
					"qty": item["qty"],
					"rate": item["rate"]
				})

			pi.insert(ignore_permissions=True)
			pi.submit()
			created.append(pi.name)

	except Exception as e:
		frappe.log_error(f"Hata: {str(e)}\n{traceback.format_exc()}", "Fatura Oluşturma Hatası")
		frappe.throw("Fatura oluşturulurken hata oluştu. Logları kontrol edin.")

	return created


def get_or_create_supplier(supplier_name):
	if frappe.db.exists("Supplier", supplier_name):
		return supplier_name

	supplier = frappe.new_doc("Supplier")
	supplier.supplier_name = supplier_name
	supplier.supplier_type = "Company"
	supplier.insert(ignore_permissions=True)
	return supplier.name


def get_or_create_item_code(item_code, item_name):
	if frappe.db.exists("Item", item_code):
		return item_code

	item = frappe.new_doc("Item")
	item.item_code = item_code
	item.item_name = item_name
	item.item_group = "All Item Groups"  # Gerekirse özelleştir
	item.stock_uom = "Nos"
	item.expense_account = "Expenses - Expenses"  # Gerçek hesaplarla değiştir
	item.income_account = "Sales - Income"
	item.insert(ignore_permissions=True)
	return item.item_code