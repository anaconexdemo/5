from odoo import models
from odoo.api import returns
from odoo.tools.safe_eval import datetime


class RepairXlsx(models.AbstractModel):
    _name = 'report.repair_module.repair_module_excel_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, repair):
        row=0
        col=0
        bold = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': 'yellow'})
        sheet = workbook.add_worksheet('Repair Order')
        sheet.write(row, col, 'Doc. Ref.', bold)
        sheet.write(row, col+1, 'Customer Name', bold)
        sheet.write(row, col+2, 'Product', bold)
        sheet.write(row, col+3, 'Category', bold)
        sheet.write(row, col+4, 'Brand', bold)
        sheet.write(row, col+5, 'User', bold)
        sheet.write(row, col+6, "Estimated \n Date Time", bold)
        sheet.write(row, col+7, 'Fault', bold)
        sheet.write(row, col+8, 'Qty', bold)
        sheet.write(row, col+9, 'SO.No.', bold)
        for obj in repair:
            formate_1 = ''
            today = datetime.date.today()
            date = obj.date
            if obj.state == 'returned':
                formate_1 = workbook.add_format({'align': 'center', 'color': 'green'})

            elif date >= today:
                formate_1 = workbook.add_format({'align': 'center', 'color': 'red'})

            elif obj.state == 'replaced':
                formate_1 = workbook.add_format({'align': 'center', 'color': 'blue'})

            else:
                formate_1 = workbook.add_format({'align': 'center', 'color': 'black'})
            for line in obj.repair_line_ids:
                row += 1
                sheet.write(row, col, obj.name, formate_1)
                sheet.write(row, col+1, obj.partner_id.name, formate_1)
                sheet.write(row, col+2, line.product_id.name, formate_1)
                sheet.write(row, col+3, obj.categ_id.name, formate_1)
                sheet.write(row, col+4, obj.brand_id.name, formate_1)
                sheet.write(row, col+5, obj.user_id.name, formate_1)
                sheet.write(row, col+6, str(obj.date), formate_1)
                sheet.write(row, col+7, obj.description, formate_1)
                sheet.write(row, col+8, line.uom_qty, formate_1)
                sheet.write(row, col+9, line.order_id.name, formate_1)


