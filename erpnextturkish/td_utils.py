# -*- coding: utf-8 -*-
# LOGEDOSOFT

from __future__ import unicode_literals
import frappe, json
from frappe import msgprint, _

from frappe.model.document import Document
from frappe.utils import cstr, flt, cint, nowdate, add_days, comma_and, now_datetime, ceil, today, formatdate, encode

import requests
import base64

from bs4 import BeautifulSoup

@frappe.whitelist()
def send_einvoice(strSalesInvoiceName):

	strResult = ""

	try:
#<s:Header><wsse:Security s:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"><wsse:UsernameToken><wsse:Username>Uyumsoft</wsse:Username><wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">Uyumsoft</wsse:Password><wsse:Nonce EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary">zOBB+xvgK+JpkdzfssWwKg==</wsse:Nonce><wsu:Created>2020-02-17T21:46:40.646Z</wsu:Created></wsse:UsernameToken></wsse:Security></s:Header>
		strBody = """
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
				<InvoiceInfo LocalDocumentId="">
					<Invoice>
						<ProfileID xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">TICARIFATURA</ProfileID>
						<ID xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"/>
						<CopyIndicator xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">false</CopyIndicator>
						<IssueDate xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.posting_date_formatted}}</IssueDate>
						<IssueTime xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.posting_time_formatted}}</IssueTime>
						<InvoiceTypeCode xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">SATIS</InvoiceTypeCode>
						<Note xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">Fatura Notu1111</Note>
						<Note xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">Fatura Notu2222</Note>
						<Note xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">Bayi No: 112221</Note>
						<Note xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">Test Not alanı 3</Note>
						<DocumentCurrencyCode xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">TRY</DocumentCurrencyCode>
						<PricingCurrencyCode xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">TRY</PricingCurrencyCode>
						<AccountingSupplierParty xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
							<Party>
								<PartyIdentification>
									<ID schemeID="VKN" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSettings.vergi_no}}</ID>
								</PartyIdentification>
								<PartyIdentification>
									<ID schemeID="MERSISNO" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSettings.mersis_no}}</ID>
								</PartyIdentification>
								<PartyIdentification>
									<ID schemeID="TICARETSICILNO" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSettings.ticaret_sicil_no}}</ID>
								</PartyIdentification>
								<PartyName>
									<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSettings.firma_adi}}</Name>
								</PartyName>
								<PostalAddress>
									<Room xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSettings.adres_kapi_no}}</Room>
									<StreetName xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSettings.adres_sokak}}</StreetName>
									<BuildingNumber xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSettings.adres_bina_no}}</BuildingNumber>
									<CitySubdivisionName xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSettings.adres_ilce}}</CitySubdivisionName>
									<CityName xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSettings.adres_il}}</CityName>
									<Country>
										<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSettings.adres_ulke}}</Name>
									</Country>
								</PostalAddress>
								<PartyTaxScheme>
									<TaxScheme>
										<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSettings.vergi_dairesi}}</Name>
									</TaxScheme>
								</PartyTaxScheme>
							</Party>
						</AccountingSupplierParty>
						<AccountingCustomerParty xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
							<Party>
								<PartyIdentification>
									<ID schemeID="VKN" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCustomer.tax_id}}</ID>
								</PartyIdentification>

								<PartyName>
									<Name xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCustomer.customer_name}}</Name>
								</PartyName>


							</Party>
						</AccountingCustomerParty>

						<LegalMonetaryTotal xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
							<LineExtensionAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.total}}</LineExtensionAmount>
							<TaxExclusiveAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.net_total}}</TaxExclusiveAmount>
							<TaxInclusiveAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.rounded_total}}</TaxInclusiveAmount>
							<AllowanceTotalAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.discount_amount}}</AllowanceTotalAmount>
							<PayableAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.rounded_total}}</PayableAmount>
						</LegalMonetaryTotal>
						{{docSI.contentLines}}
					</Invoice>
					<TargetCustomer VknTckn="{{docCustomer.tax_id}}" Alias="defaultpk" Title="{{docCustomer.customer_name}}"/>
					<EArchiveInvoiceInfo DeliveryType="Electronic"/>
					<Scenario>Automated</Scenario>
				</InvoiceInfo>
			</invoices>
		</SaveAsDraft>
	</s:Body>
</s:Envelope>
"""
		strLine = """
		<InvoiceLine xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
		<ID xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.idx}}</ID>
		<Note xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"></Note>
		<InvoicedQuantity unitCode="{{docUnit.td_efatura_birimi}}" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.qty}}</InvoicedQuantity>
		<LineExtensionAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.amount}}</LineExtensionAmount>
		<AllowanceCharge>
			<ChargeIndicator xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">false</ChargeIndicator>
			<Amount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.discount_amount}}</Amount>
		</AllowanceCharge>
		<TaxTotal>

			<TaxSubtotal>

				<Percent xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">18</Percent>
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

		strHeaders = {
			'Accept-Encoding': 'gzip,deflate',
			'Accept': 'text/xml',
			'Content-Type': 'text/xml;charset=UTF-8',
			'Cache-Control': 'no-cache',
			'Pragma': 'no-cache',
			'SOAPAction': 'http://tempuri.org/IIntegration/SaveAsDraft',
			'Connection': 'Keep-Alive'
		}

		docSI = frappe.get_doc("Sales Invoice", strSalesInvoiceName)
		docCustomer = frappe.get_doc("Customer", docSI.customer)
		docSI.posting_date_formatted = formatdate(docSI.posting_date, "yyyy-MM-dd")
		docSI.posting_time_formatted = "03:55:40"# formatdate(docSI.posting_time, "HH:mm")#"HH:mm:ss.SSSSSSSZ")
		docSettings = {
			'vergi_no': 9000068418,
			'vergi_dairesi': 'asd',
			'mersis_no': '12345669-111',
			'ticaret_sicil_no': '12345669-111',
			'firma_adi' :'Uyumsoft Bilgi Sistemleri ve Teknolojileri A.Ş.',
			'adres_kapi_no' : '1',
			'adres_sokak' : 'TEST',
			'adres_bina_no' : 'ASD',
			'adres_ilce' : 'aaa',
			'adres_il' : 'asd',
			'adres_ulke' : 'asq'
		}

		#Satirlari olusturalim
		docSI.contentLines = ""
		for item in docSI.items:
			docItem = frappe.get_doc("Item", item.item_code)
			docLineWarehouse = frappe.get_doc("Warehouse", item.warehouse)
			docUnit = frappe.get_doc("UOM", item.uom)
			str_line_xml = frappe.render_template(strLine, context={"docCurrentLine": item, "docItem":docItem, "docLineWarehouse":docLineWarehouse, "docUnit": docUnit}, is_path=False)
			docSI.contentLines = docSI.contentLines + str_line_xml

		#Ayarlari alalim
		docEISettings = frappe.get_single("EFatura Ayarlar")		
		docEISettings.kullaniciadi = docEISettings.kullaniciadi 
		docEISettings.parola = docEISettings.get_password('parola')

		#Ana dokuman dosyamizi olusturalim
		strDocXML = frappe.render_template(strBody, context={"docSI": docSI, "docSettings": docSettings, "docCustomer": docCustomer, "docEISettings": docEISettings}, is_path=False)

		if docEISettings.test_modu:
			strServerURL = docEISettings.test_efatura_adresi
			#Test modunda gonderdigimiz xml i  de saklayalim
			frappe.log_error(strDocXML, _("E-Fatura (send_einvoice) gönderilen paket"))
		else:
			strServerURL = docEISettings.efatura_adresi

		#webservisine gonderelim
		#response = requests.post('https://efatura-test.uyumsoft.com.tr/services/integration', headers=strHeaders, data=strDocXML.encode('utf-8'))
		#response = requests.post('https://efatura.uyumsoft.com.tr/services/integration', headers=strHeaders, data=strDocXML.encode('utf-8'))
		response = requests.post(strServerURL, headers=strHeaders, data=strDocXML.encode('utf-8'))
		# You can inspect the response just like you did before
		print("RESPONSE")
		#print(response.headers)
		print(response.text)
		#print(response.content)
		print(response.status_code)

		bsMain = BeautifulSoup(response.text, "lxml")#response.content.decode('utf8')
		if response.status_code == 500:
			strErrorMessage = bsMain.find_all("faultstring")[0].text
			strResult = "İşlem Başarısız! Hata Kodu:500. Detay:"
			strResult += strErrorMessage
		elif response.status_code == 200:
			objSaveResult = bsMain.find_all("saveasdraftresult")[0]#['issucceded']#.get_attribute_list('is_succeddede')
			if objSaveResult['issucceded'] == "false":
				strResult = "Fatura gönderilemedi! Detay:" + objSaveResult['message']
			else:
				strResult = "İşlem Başarılı"
		else:
			strResult = _("İşlem Başarısız! Hata Kodu:{0}. Detay:").format(response.status_code)
			strResult += response.text

	except Exception as e:
		strResult = _("Sunucudan gelen mesaj işlenirken hata oluştu! Detay:{0}").format(e)
		frappe.log_error(frappe.get_traceback(), _("E-Fatura (send_einvoice) sunucudan gelen mesaj işlenemedi."))
    
	return {'result':strResult, 'response':response.text}

@frappe.whitelist()
def login_test():
	strResult = ""

	try:
		#PRODUCTION BODY
		body = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
   <soapenv:Header><wsse:Security soapenv:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"><wsse:UsernameToken><wsse:Username>{{docEISettings.kullaniciadi}}</wsse:Username><wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{{docEISettings.parola}}</wsse:Password></wsse:UsernameToken></wsse:Security></soapenv:Header>
   <soapenv:Body>
      <tem:WhoAmI/>
   </soapenv:Body>
</soapenv:Envelope>
                """

		headers = {
            'Accept-Encoding': 'gzip,deflate',
            'Accept': 'text/xml',
            'Content-Type': 'text/xml;charset=UTF-8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'SOAPAction': 'http://tempuri.org/IIntegration/WhoAmI',
            'Connection': 'Keep-Alive'
		}

		#Ayarlari alalim
		docEISettings = frappe.get_single("EFatura Ayarlar")		
		docEISettings.kullaniciadi = docEISettings.kullaniciadi 
		docEISettings.parola = docEISettings.get_password('parola')

		if docEISettings.test_modu:
			strServerURL = docEISettings.test_efatura_adresi
		else:
			strServerURL = docEISettings.efatura_adresi

		body = frappe.render_template(body, context={"docEISettings": docEISettings}, is_path=False)

		#response = requests.post('https://efatura-test.uyumsoft.com.tr/services/integration', headers=headers, data=body)
		#response = requests.post('https://efatura.uyumsoft.com.tr/services/integration', headers=headers, data=body)
		response = requests.post(strServerURL, headers=headers, data=body)
		# You can inspect the response just like you did before
		#print("RESPONSE")
		#print(response.headers)
		#print(response.text)
		#print(response.content)
		#print(response.status_code)

		bsMain = BeautifulSoup(response.text, "lxml")#response.content.decode('utf8')
		if response.status_code == 500:
			strErrorMessage = bsMain.find_all("faultstring")[0].text
			strResult = "İşlem Başarısız! Hata Kodu:500. Detay:"
			strResult += strErrorMessage
		elif response.status_code == 200:
			strResult = "İşlem Başarılı."
			strCustomerName = bsMain.find_all("name")[1].text
			strResult += _("Firma Adı:{0}").format(strCustomerName)
		else:
			strResult = _("İşlem Başarısız! Hata Kodu:{0}. Detay:").format(response.status_code)
			strResult += response.text

	except Exception as e:
		strResult = _("Sunucudan gelen mesaj işlenirken hata oluştu! Detay:{0}").format(e)
		frappe.log_error(frappe.get_traceback(), _("E-Fatura (LoginTest) sunucudan gelen mesaj işlenemedi."))

	return {'result':strResult, 'response':response.text}

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