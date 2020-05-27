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

def get_service_xml(strType):
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
				<InvoiceInfo LocalDocumentId="">
					<Invoice>
						<ProfileID xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">TICARIFATURA</ProfileID>
						<ID xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"/>
						<CopyIndicator xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">false</CopyIndicator>
						<IssueDate xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.posting_date_formatted}}</IssueDate>
						<IssueTime xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docSI.posting_time_formatted}}</IssueTime>
						<InvoiceTypeCode xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">SATIS</InvoiceTypeCode>
						<Note xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">Yalnız #{{docSI.in_words}}#</Note>
						<Note xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"></Note>
						<Note xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"></Note>
						<Note xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"></Note>
						<DocumentCurrencyCode xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">TRY</DocumentCurrencyCode>
						<PricingCurrencyCode xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">TRY</PricingCurrencyCode>
						
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
					<TargetCustomer VknTckn="{{docCustomer.tax_id}}" Alias="defaultpk" Title="{{docCustomer.customer_name}}"/>
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
			<PriceAmount currencyID="TRY" xmlns="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{{docCurrentLine.price_list_rate}}</PriceAmount>
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

	return strResult

@frappe.whitelist()
def send_einvoice(strSalesInvoiceName):

	strResult = ""

	try:
		
		strHeaders = get_service_xml('einvoice-headers')
		strBody = get_service_xml('einvoice-body')
		strLine = get_service_xml('einvoice-line')

		docSI = frappe.get_doc("Sales Invoice", strSalesInvoiceName)
		docCustomer = frappe.get_doc("Customer", docSI.customer)
		docCustomerAddress = frappe.get_doc("Address", docSI.customer_address)
		docCustomer.id_scheme = "VKN" if docCustomer.customer_type == "Company" else "TCKN"

		if hasattr(docCustomer, 'tax_office'):
			docCustomer.tax_office = docCustomer.tax_office if docCustomer.tax_office is not None else ''
		elif hasattr(docCustomer, 'taxoffice'):
			docCustomer.tax_office = docCustomer.taxoffice if docCustomer.taxoffice is not None else ''
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
			docSILine.AllowanceBaseAmount = docSILine.price_list_rate * docSILine.qty#Iskonto uygulanan rakam

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
		docSI.posting_time_formatted = docSI.posting_time #"03:55:40"# formatdate(docSI.posting_time, "HH:mm")#"HH:mm:ss.SSSSSSSZ")

		#Ayarlari alalim
		docEISettings = frappe.get_single("EFatura Ayarlar")
		docEISettings.parola = docEISettings.get_password('parola')

		#Ana dokuman dosyamizi olusturalim
		strDocXML = frappe.render_template(strBody, context=
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
		response = requests.post(strServerURL, headers=strHeaders, data=strDocXML.encode('utf-8'))
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

				docSI.add_comment('Comment', text=_('E-Fatura: Belge gönderildi. (Ek Bilgiler:{0}, {1})'.format(objSaveResultInfo['number'], objSaveResultInfo['id'])))

				#Fatura durumunu alalim
				docSI.db_set('td_efatura_durumu', get_invoice_status(docSI)['result'], notify=True)

				docSI.notify_update()
		else:
			strResult = _("İşlem Başarısız! Hata Kodu:{0}. Detay:").format(response.status_code)
			strResult += response.text

	except Exception as e:
		strResult = _("Hata oluştu! Detay:{0}").format(e)
		frappe.log_error(frappe.get_traceback(), _("E-Fatura (send_einvoice) sunucudan gelen mesaj işlenemedi."))
    
	return {'result':strResult, 'response':response.text if 'response' in locals() else ''}

@frappe.whitelist()
def get_invoice_status(docSI = None, strSaleInvoiceName = None):
	strResult = ""

	if docSI is None:
		docSI = frappe.get_doc("Sales Invoice", strSaleInvoiceName)

	try:
		body = get_service_xml('query-invoice-status-body')

		headers = get_service_xml('query-invoice-status-headers')

		#Ayarlari alalim
		docEISettings = frappe.get_single("EFatura Ayarlar")		
		docEISettings.kullaniciadi = docEISettings.kullaniciadi 
		docEISettings.parola = docEISettings.get_password('parola')

		if docEISettings.test_modu:
			strServerURL = docEISettings.test_efatura_adresi
		else:
			strServerURL = docEISettings.efatura_adresi

		body = frappe.render_template(body, context={"docEISettings": docEISettings, "docSI": docSI}, is_path=False)

		response = requests.post(strServerURL, headers=headers, data=body)

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
		frappe.log_error(frappe.get_traceback(), _("E-Fatura (LoginTest) sunucudan gelen mesaj işlenemedi."))

	return {'result':strResult, 'response':response.text}

@frappe.whitelist()
def login_test():
	strResult = ""

	try:
		body = get_service_xml('login-test-body')

		headers = get_service_xml('login-test-headers')

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