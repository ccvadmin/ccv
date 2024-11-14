# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api
from odoo.modules.module import get_module_resource

import logging

_logger = logging.getLogger(__name__)

def json_format(font_size, font_name="Times New Roman", align="vcenter", right=False, left=False, bottom=False, top=False, bold=False, italic=False):
    return {
        "font_name": font_name,
        "font_size": font_size,
        "align": align,
        "right": right,
        "left": left,
        "bottom": bottom,
        "top": top,
        "bold": bold,
        "italic": italic,
    }

class tong_hop_cong_no_phai_thu(models.AbstractModel):
    _name = "report.ccv_bao_cao.tong_hop_cong_no_phai_thu"
    _inherit = "report.report_xlsx.abstract"
    _description = "Tong Hop Cong No Phai Thu"

    def generate_xlsx_report(self, workbook, data, objects):
        report = data
        date_start = report['date_start']
        date_end = report['date_end']
        account_id = report['account_id']
        data_raw = report['data']
        sheet = workbook.add_worksheet("TỔNG HỢP CÔNG NỢ PHẢI THU")

        workbook.set_properties({'title': 'Báo cáo CCV', 'author': self.env.user.display_name})
        sheet.set_landscape()

        # Format cho tiêu đề
        format1 = workbook.add_format(json_format(16, bold=True))
        format1.set_align("center")

        # Format cho tiêu đề phụ
        format21 = workbook.add_format(json_format(12, bold=True, italic=True))
        format21.set_text_wrap(True)
        format21.set_align("center")

        # Format cho header
        format_header = workbook.add_format(json_format(11, bold=True, right=True,left=True,bottom=True,top=True))
        format_header.set_text_wrap(True)
        format_header.set_align("center")

        # Format cho chữ
        font_size_8 = workbook.add_format(json_format(11.5, right=True,left=True,bottom=True,top=True))
        font_size_8.set_align("center")
        font_size_8.set_text_wrap()
        # Format cho số
        font_size_8_number = workbook.add_format(json_format(10, right=True,left=True,bottom=True,top=True))
        font_size_8_number.set_align("right")
        font_size_8_number.set_num_format("#,##0")

        format_company_title = workbook.add_format(json_format(13))
        format_company_title.set_align("left")

        # Đầu đề
        sheet.merge_range("A4:J4","TỔNG HỢP CÔNG NỢ PHẢI THU",format1)
        sheet.set_row(4, 35)
        sheet.set_row(5, 20)
        account_account = self.env['account.account'].browse(account_id)
        account = ""
        currency = ""
        if account_account:
            account = account_account.code
            currency = account_account.currency_id.display_name if account_account.currency_id else "Chưa xác định"
        sheet.merge_range("A5:J5","Tài khoản: %s; Loại tiền: VND; Từ ngày %s đến ngày %s" % (account,date_start,date_end),format21)
        sheet.merge_range("C2:J2","Công ty TNHH Con Cò Vàng - Mã số thuế: 0305995751", format_company_title)
        sheet.insert_image('A1', get_module_resource('ccv_bao_cao', 'static/src/img', 'logo.png'), {'x_offset': 0, 'y_offset': 0,"x_scale": 0.22, "y_scale": 0.22})

        # Bảng
        w_row_header = 6
        header_arr = [
            {'name':"STT", "column": "A"},
            {'name':"Mã khách hàng", "column": "B"},
            {'name':"Tên khách hàng", "column": "C"},
        ]
        i = 0
        for header_item in header_arr:
            sheet.merge_range(f"{header_item['column']}{w_row_header}:{header_item['column']}{w_row_header+1}", header_item['name'], format_header)
            i += 1
        header_arr = [
            {"name": "Số dư đầu kỳ", "from":"D", "to":"E", "items": [{"name" : "Có"},{"name" : "Nợ"},]},
            {"name": "Số phát sinh", "from":"F", "to":"G", "items": [{"name" : "Có"},{"name" : "Nợ"},]},
            {"name": "Số dư cuối kỳ", "from":"H", "to":"I", "items": [{"name" : "Có"},{"name" : "Nợ"},]},
        ]
        for header_item in header_arr:
            sheet.merge_range(f"{header_item['from']}{w_row_header}:{header_item['to']}{w_row_header}", header_item['name'], format_header)
            sheet.write(w_row_header, i, header_item['items'][0]['name'], format_header)
            sheet.write(w_row_header, i + 1, header_item['items'][1]['name'], format_header)
            i += 2
        i -= 1
        sheet.merge_range(f"J{w_row_header}:J{w_row_header+1}","Mã nhóm khách hàng",format_header)

        prod_row = 7
        sum = data_raw['sum']
        columns = [
            {"size": 5, "name": "no", "is_num": False},
            {"size": 12, "name": "customer_code", "is_num": False},
            {"size": 25, "name": "customer_name", "is_num": False},
            {"size": 10, "name": "start_credit", "is_num": True},
            {"size": 10, "name": "start_debit", "is_num": True},
            {"size": 10, "name": "ps_credit", "is_num": True},
            {"size": 10, "name": "ps_debit", "is_num": True},
            {"size": 10, "name": "end_credit", "is_num": True},
            {"size": 10, "name": "end_debit", "is_num": True},
            {"size": 14, "name": "customer_group", "is_num": False},
        ]

        for each in data_raw["lines"]:
            prod_col = 0
            for column in columns:
                current_font = font_size_8
                if column["is_num"]:
                    current_font = font_size_8_number
                sheet.set_column(prod_col, prod_col, column["size"])
                sheet.write(prod_row, prod_col, each[column["name"]], current_font)
                prod_col += 1
            prod_row +=1

        # Tổng cộng
        total_font_size = workbook.add_format(json_format(10, right=True,left=True,bottom=True,top=True, bold=True))
        total_font_size.set_align("right")
        total_font_size.set_text_wrap()

        total_font_size_text = workbook.add_format(json_format(10, right=True,left=True,bottom=True,top=True, bold=True))
        total_font_size_text.set_text_wrap()
        total_font_size_text.set_align("left")

        prod_row += 1
        prod_col = 0
        sheet.merge_range(f"A{prod_row}:C{prod_row}","Tổng cộng",total_font_size_text)

        prod_row -= 1
        prod_col += 3
        total_arr = [
            "sum_start_credit",
            "sum_start_debit",
            "sum_ps_credit",
            "sum_ps_debit",
            "sum_end_credit",
            "sum_end_debit"
        ]
        for total_item in total_arr:
            sheet.write(prod_row, prod_col, sum[total_item], total_font_size)
            prod_col += 1
        
        sheet.write(prod_row, prod_col, "", total_font_size)
        prod_row +=1

        # Footer
        # Format cho số
        footer_font_size_title = workbook.add_format(
            {
                "bottom": False,
                "top": False,
                "right": False,
                "left": False,
                "font_size": 12,
                "align": "vcenter",
                "font_name": "Times New Roman",
                "bold": True,
            }
        )
        footer_font_size_title.set_align("center")
        footer_font_size_title.set_text_wrap()

        footer_font_size_sign = workbook.add_format(
            {
                "bottom": False,
                "top": False,
                "right": False,
                "left": False,
                "font_size": 11,
                "align": "vcenter",
                "font_name": "Times New Roman",
                "italic": True,
            }
        )
        footer_font_size_sign.set_align("center")
        footer_font_size_sign.set_text_wrap()

        prod_row = prod_row + 2
        sheet.merge_range(f"G{prod_row}:J{prod_row}","Ngày ..... tháng ..... năm .........",footer_font_size_sign)

        prod_row +=1
        sheet.merge_range(f"A{prod_row}:C{prod_row}","Người Lập Biểu",footer_font_size_title)
        sheet.merge_range(f"D{prod_row}:F{prod_row}","Kế Toán Trưởng",footer_font_size_title)
        sheet.merge_range(f"G{prod_row}:J{prod_row}","Thủ trưởng đơn vị",footer_font_size_title)

        prod_row +=1
        sheet.merge_range(f"A{prod_row}:C{prod_row}","(Ký, họ tên)",footer_font_size_sign)
        sheet.merge_range(f"D{prod_row}:F{prod_row}","(Ký, họ tên)",footer_font_size_sign)
        sheet.merge_range(f"G{prod_row}:J{prod_row}","(Ký, họ tên, đóng dấu)",footer_font_size_sign)

        prod_row = prod_row + 5
        sheet.merge_range(f"A{prod_row}:C{prod_row}","Nguyễn Thùy Linh", footer_font_size_title)
        sheet.merge_range(f"D{prod_row}:F{prod_row}","Trương Quốc Tuấn", footer_font_size_title)
        sheet.merge_range(f"G{prod_row}:J{prod_row}","",  footer_font_size_title)