from odoo import models, api

from ..libary_report import LibaryReport

libary_report = LibaryReport()

class GiayBaoCoReport(models.AbstractModel):
    _name = 'report.ccv_bao_cao.giay_bao_co_report'
    _description = 'Giấy Báo Có Report'
    _inherit = "report.report_xlsx.abstract"

    def generate_prepare_value(self, docids):
        docs = self.env['account.payment'].browse(docids)
        data = {}

        for doc in docs:
            partner_id = doc.partner_id
            partner_bank_id = doc.partner_bank_id
            line_ids = doc.move_id.line_ids
            currency_id = doc.currency_id
            currency_vn_id = currency_id
            amount = doc.amount
            currency_name = currency_vn_id.name
            currency_rate = 0
            if currency_id.name != 'VND':
                amount *= currency_id.inverse_rate
                currency_vn_id = self.env.company.currency_id
                currency_name = currency_vn_id.name
                currency_rate = currency_id.inverse_rate
            doc_data = {
                'name': doc.name,
                'date': doc.date,
                'partner_name': partner_id.name,
                'partner_address': partner_id.street or '',
                'ref': doc.ref or '',
                'acc_number': partner_bank_id.acc_number if partner_bank_id else '',
                'bank_name': partner_bank_id.bank_id.name if partner_bank_id else '',

                'amount_nt': currency_id.format(doc.amount),
                'currency_nt_name': currency_id.name,
                'amount_label': libary_report.number_to_words_vn(int(doc.amount), currency_id.currency_unit_label),

                'amount': currency_vn_id.format(amount),
                'currency_name': currency_name,
                'currency_rate': currency_rate,

                'account_credit_code': line_ids.filtered(lambda l:l.debit == 0)[0].account_id.code,
                'account_debit_code': line_ids.filtered(lambda l:l.credit == 0)[0].account_id.code,
            }

            data[doc.id] = doc_data
        
        return docs, data

    @api.model
    def generate_xlsx_report(self, workbook, data, objects):
        worksheet = workbook.add_worksheet('Giấy Báo Có')
        bold = workbook.add_format({'bold': True})
        center = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
        left = workbook.add_format({'align': 'left', 'valign': 'vcenter'})
        
        for doc in objects:
            worksheet.write(0, 0, 'Giấy Báo Có', bold)
            worksheet.write(1, 0, 'Số:', bold)
            worksheet.write(1, 1, doc.name or '', left)
            worksheet.write(2, 0, 'Ngày:', bold)
            worksheet.write(2, 1, doc.date or '', left)
            worksheet.write(3, 0, 'Nguời nộp tiền:', bold)
            worksheet.write(3, 1, doc.partner_id.name or '', left)
            worksheet.write(4, 0, 'Địa chỉ:', bold)
            worksheet.write(4, 1, doc.partner_id.contact_address_complete or '', left)
            worksheet.write(5, 0, 'Lý do:', bold)
            worksheet.write(5, 1, doc.ref or '', left)
            worksheet.write(6, 0, 'Số tài khoản đơn vị thụ hưởng:', bold)
            worksheet.write(6, 1, doc.partner_bank_id.acc_number or '', left)
            worksheet.write(7, 0, 'Tại ngân hàng:', bold)
            worksheet.write(7, 1, doc.partner_bank_id.bank_id.name or '', left)
            worksheet.write(8, 0, 'Số tiền:', bold)
            worksheet.write(8, 1, doc.amount_total_signed or 0.0, left)
            worksheet.write(9, 0, 'Loại tiền:', bold)
            worksheet.write(9, 1, doc.currency_id.name or '', left)

            row = 11
            worksheet.write(row, 0, 'Diễn giải', bold)
            worksheet.write(row, 1, 'Số tiền nguyên tệ', bold)
            worksheet.write(row, 2, 'Số tiền (VND)', bold)
            worksheet.write(row, 3, 'Ghi nợ', bold)
            worksheet.write(row, 4, 'Ghi có', bold)

            for line in doc.line_ids:
                row += 1
                worksheet.write(row, 0, line.name or '', left)
                worksheet.write(row, 1, line.debit or 0.0, left)
                worksheet.write(row, 2, line.credit or 0.0, left)
                worksheet.write(row, 3, line.account_id.code or '', left)
                worksheet.write(row, 4, line.partner_id.name or '', left)
        
        return

    @api.model
    def _get_report_values(self, docids, data=None):
        docs, data = self.generate_prepare_value(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'account.payment',
            'docs': docs,
            'data': data,
        }
