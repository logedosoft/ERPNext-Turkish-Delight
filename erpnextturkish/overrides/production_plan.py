#LOGEDOSOFT-2024
import frappe
from frappe import _, msgprint
from frappe.model.document import Document

from frappe.desk.doctype.todo.todo import ToDo
from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan

class LDProductionPlan(ProductionPlan):		
	
	def get_so_items(self):
		super().get_so_items()
		#Here ERPNext already calculated the required qty. But it didn't consider the planned production.
		#So we will deduct already planned qty. https://app.asana.com/0/1206337061845755/1206702380280645/f
		blnPPQtyCheck = frappe.db.get_single_value("TD Utils", "pp_must_check_already_planned_qty")
		if blnPPQtyCheck == True:
			for item in self.po_items:
				flPlannedQty = frappe.db.get_value("Sales Order Item", item.sales_order_item, "planned_qty")
				item.planned_qty = item.planned_qty - flPlannedQty