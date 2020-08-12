SELECT 
	`TMP_GL_ENTRY`.`BELGE_TARIHI` AS `BELGE_TARIHI`,
    `TMP_GL_ENTRY`.`BELGE_SAATI` AS `BELGE_SAATI`,
    `TMP_GL_ENTRY`.`TIP` AS `TIP`,
    `TMP_GL_ENTRY`.`LD_REMARK` AS `ACIKLAMA`,
    `TMP_GL_ENTRY`.`debit` AS `BORC`,
    `TMP_GL_ENTRY`.`credit` AS `ALACAK`,
    `TMP_GL_ENTRY`.`CARI_KODU` AS `CARI_KODU`,
    `TMP_GL_ENTRY`.`CARI_ADI` AS `CARI_ADI`,
    `TMP_GL_ENTRY`.`COMPANY` AS `SIRKET`
FROM 
(
	SELECT 
		coalesce(`CUSTOMER`.`name`, `SUPPLIER`.`name`) AS `CARI_KODU`,
		coalesce(`CUSTOMER`.`customer_name`, `SUPPLIER`.`supplier_name`) AS `CARI_ADI`,
		'Muhasebe Fişi' AS `TIP`,
		`JOURNAL_ENTRY`.`posting_date` AS `BELGE_TARIHI`,
		date_format(`JOURNAL_ENTRY`.`modified`, '%H:%i:%s') AS `BELGE_SAATI`,
		`GL_ENTRY`.`debit` AS `debit`,
		`GL_ENTRY`.`credit` AS `credit`,
		`JOURNAL_ENTRY`.`title` AS `LD_REMARK`,
		`GL_ENTRY`.`company` AS `COMPANY`
	FROM 
	(
		(
			(
				`tabGL Entry` `GL_ENTRY`
				JOIN `tabJournal Entry` `JOURNAL_ENTRY`
					ON (`GL_ENTRY`.`voucher_no` = `JOURNAL_ENTRY`.`name`)
			)
			LEFT JOIN `tabSupplier` `SUPPLIER`
				ON (`GL_ENTRY`.`party` = `SUPPLIER`.`name`
					AND `GL_ENTRY`.`party_type` = 'Supplier')
		)
		LEFT JOIN `tabCustomer` `CUSTOMER`
			ON (`GL_ENTRY`.`party` = `CUSTOMER`.`name`
				AND `GL_ENTRY`.`party_type` = 'Customer')
	)
	WHERE
		`GL_ENTRY`.`voucher_type` = 'Journal Entry'
			AND `JOURNAL_ENTRY`.`docstatus` = 1
			AND `GL_ENTRY`.`docstatus` = 1
		 
	UNION ALL

	SELECT 
		`CUSTOMER`.`name` AS `CARI_KODU`,
		`CUSTOMER`.`customer_name` AS `CARI_ADI`,
		'Satış Faturası' AS `TIP`,
		`SALES_INVOICE`.`posting_date` AS `BELGE_TARIHI`,
		date_format(`SALES_INVOICE`.`posting_time`, '%H:%i:%s') AS `BELGE_SAATI`,
		`GL_ENTRY`.`debit` AS `debit`,
		`GL_ENTRY`.`credit` AS `credit`,
		group_concat(
			DISTINCT `SALES_INVOICE_ITEM`.`item_name` 
			ORDER BY `SALES_INVOICE_ITEM`.`idx` ASC 
			SEPARATOR ','
		) AS `LD_REMARK`,
		`GL_ENTRY`.`company` AS `COMPANY`
	FROM 
	(
		(
			(
				`tabGL Entry` `GL_ENTRY`
				JOIN `tabCustomer` `CUSTOMER`
					ON (`GL_ENTRY`.`party` = `CUSTOMER`.`name`)
			)
			JOIN `tabSales Invoice` `SALES_INVOICE`
				ON (`GL_ENTRY`.`voucher_no` = `SALES_INVOICE`.`name`)
		)
		JOIN `tabSales Invoice Item` `SALES_INVOICE_ITEM`
			ON (`SALES_INVOICE_ITEM`.`parent` = `SALES_INVOICE`.`name`)
	)
	WHERE     
		`GL_ENTRY`.`voucher_type` = 'Sales Invoice'
			AND `SALES_INVOICE`.`docstatus` = 1
			AND `GL_ENTRY`.`docstatus` = 1
		 
	UNION ALL
		 
	SELECT 
		`SUPPLIER`.`name` AS `CARI_KODU`,
		`SUPPLIER`.`supplier_name` AS `CARI_ADI`,
		'Alım Faturası' AS `TIP`,
		`PURCHASE_INVOICE`.`posting_date` AS `BELGE_TARIHI`,
		date_format(`PURCHASE_INVOICE`.`posting_time`, '%H:%i:%s') AS `BELGE_SAATI`,
		`GL_ENTRY`.`debit` AS `debit`,
		`GL_ENTRY`.`credit` AS `credit`,
		'' COLLATE utf8mb4_unicode_ci AS `LD_REMARK`,
		`GL_ENTRY`.`company` AS `COMPANY`
		   
	FROM 
	(
		(
			`tabGL Entry` `GL_ENTRY`
			JOIN `tabSupplier` `SUPPLIER`
				ON (`GL_ENTRY`.`party` = `SUPPLIER`.`name`)
		)
		JOIN `tabPurchase Invoice` `PURCHASE_INVOICE`
			ON (`GL_ENTRY`.`voucher_no` = `PURCHASE_INVOICE`.`name`)
	)
	WHERE
		`GL_ENTRY`.`voucher_type` = 'Purchase Invoice'
			AND `PURCHASE_INVOICE`.`docstatus` = 1
			AND `GL_ENTRY`.`docstatus` = 1
		 
	UNION ALL

	SELECT 
		coalesce(`CUSTOMER`.`name`, `SUPPLIER`.`name`) AS `CARI_KODU`,
		coalesce(`CUSTOMER`.`customer_name`, `SUPPLIER`.`supplier_name`) AS `CARI_ADI`,
		concat(
			'', 
			CASE `PAYMENT_ENTRY`.`payment_type`
				WHEN 'Pay' THEN 'Ödeme'
				WHEN 'Receive' THEN 'Tahsilat'
				ELSE 'BELİRSİZ'
			END,
			' (',
			ifnull(`PAYMENT_ENTRY`.`mode_of_payment`, ''),
			')'
		) AS `TIP`,
		`PAYMENT_ENTRY`.`posting_date` AS `BELGE_TARIHI`,
		date_format(`PAYMENT_ENTRY`.`modified`, '%H:%i:%s') AS `BELGE_SAATI`,
		sum(`GL_ENTRY`.`debit`) AS `debit`,
		sum(`GL_ENTRY`.`credit`) AS `credit`,
		CASE `PAYMENT_ENTRY`.`mode_of_payment`
			WHEN 'Çek' THEN concat('Vade:', date_format(`PAYMENT_ENTRY`.`reference_date`, '%d.%m.%Y'),'. ')
			ELSE ''
		END AS `LD_REMARK`,
		`GL_ENTRY`.`company` AS `COMPANY`
	FROM 
	(
		(
			(
				`tabGL Entry` `GL_ENTRY`
				JOIN `tabPayment Entry` `PAYMENT_ENTRY`
					 ON (`GL_ENTRY`.`voucher_no` = `PAYMENT_ENTRY`.`name`)
			)
			LEFT JOIN `tabSupplier` `SUPPLIER`
				ON (`GL_ENTRY`.`party` = `SUPPLIER`.`name`
				AND `GL_ENTRY`.`party_type` = 'Supplier')
		)
		LEFT JOIN `tabCustomer` `CUSTOMER`
			ON (`GL_ENTRY`.`party` = `CUSTOMER`.`name`
			AND `GL_ENTRY`.`party_type` = 'Customer')
	)
	WHERE
		`GL_ENTRY`.`voucher_type` = 'Payment Entry'
			AND `GL_ENTRY`.`party` IS NOT NULL
			AND `PAYMENT_ENTRY`.`docstatus` = 1
			AND `GL_ENTRY`.`docstatus` = 1
	GROUP BY 
		coalesce(`CUSTOMER`.`name`, `SUPPLIER`.`name`),
		coalesce(`CUSTOMER`.`customer_name`, `SUPPLIER`.`supplier_name`),
		coalesce(`CUSTOMER`.`tax_id`, `SUPPLIER`.`tax_id`),
		`PAYMENT_ENTRY`.`reference_date`,
		`PAYMENT_ENTRY`.`reference_no`,
		`PAYMENT_ENTRY`.`posting_date`,
		`GL_ENTRY`.`posting_date`,
		`GL_ENTRY`.`account`,
		`GL_ENTRY`.`voucher_no`,
		`GL_ENTRY`.`fiscal_year`,
		`GL_ENTRY`.`voucher_type`,
		`GL_ENTRY`.`party`,
		`GL_ENTRY`.`party_type`
) `TMP_GL_ENTRY`
ORDER BY 
	`TMP_GL_ENTRY`.`BELGE_TARIHI`, 
	`TMP_GL_ENTRY`.`BELGE_SAATI`
