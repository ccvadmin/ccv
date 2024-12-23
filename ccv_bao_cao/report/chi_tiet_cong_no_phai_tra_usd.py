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

class chi_tiet_cong_no_phai_tra_usd(models.AbstractModel):
    _name = "report.ccv_bao_cao.chi_tiet_cong_no_phai_tra_usd"
    _inherit = "report.report_xlsx.abstract"
    _description = "Chi Tiet Cong No Phai Tra"

    def generate_xlsx_report(self, workbook, data, objects):
        report = data
        date_start = report['date_start']
        date_end = report['date_end']
        account = report['account_id']
        partner = report['partner_id']
        data_raw = report['data']
        sheet = workbook.add_worksheet("CHI TIẾT CÔNG NỢ PHẢI TRẢ")

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

        font_size_8_number_nt = workbook.add_format(json_format(10, right=True,left=True,bottom=True,top=True))
        font_size_8_number_nt.set_align("right")
        font_size_8_number_nt.set_num_format("#,##0.00")

        format_company_title = workbook.add_format(json_format(13))
        format_company_title.set_align("left")

        # Đầu đề
        sheet.merge_range("A4:S4","CHI TIẾT CÔNG NỢ PHẢI TRẢ",format1)
        sheet.set_row(4, 35)
        sheet.set_row(5, 20)
        sheet.merge_range("A5:S5","Tài khoản: %s; Loại tiền: USD; Nhà cung cấp: %s; Từ ngày %s đến ngày %s" % (account, partner, date_start,date_end),format21)
        sheet.merge_range("C2:S2","Công ty TNHH Con Cò Vàng - Mã số thuế: 0305995751", format_company_title)
        sheet.insert_image('A1', get_module_resource('ccv_bao_cao', r'static/src/img', 'logo.png'), {'x_offset': 0, 'y_offset': 0,"x_scale": 0.22, "y_scale": 0.22})

        # Bảng
        w_row_header = 6
        header_arr = [
            {'name':"STT", "column": "A"},
            {'name':"Ngày chứng từ", "column": "B"},
            {'name':"Số chứng từ", "column": "C"},
            {'name':"Ngày hóa đơn", "column": "D"},
            {'name':"Số hóa đơn", "column": "E"},
            {'name':"Số lượng", "column": "F"},
            {'name':"Đơn giá", "column": "G"},
            {'name':"Diễn giải", "column": "H"},
            {'name':"Tài khoản công nợ", "column": "I"},
            {'name':"Tài khoản đối ứng", "column": "J"},
        ]
        i = 0
        for header_item in header_arr:
            sheet.merge_range(f"{header_item['column']}{w_row_header}:{header_item['column']}{w_row_header+1}", header_item['name'], format_header)
            i += 1
        header_arr = [
            {"name": "Phát sinh Nợ", "from":"K", "to":"L", "items": [{"name" : "Số tiền"},{"name" : "Quy đổi"},]},
            {"name": "Phát sinh Có", "from":"M", "to":"N", "items": [{"name" : "Số tiền"},{"name" : "Quy đổi"},]},
            {"name": "Dư Nợ cuối kỳ", "from":"O", "to":"P", "items": [{"name" : "Số tiền"},{"name" : "Quy đổi"},]},
            {"name": "Dư Có cuối kỳ", "from":"Q", "to":"R", "items": [{"name" : "Số tiền"},{"name" : "Quy đổi"},]},
        ]
        for header_item in header_arr:
            sheet.merge_range(f"{header_item['from']}{w_row_header}:{header_item['to']}{w_row_header}", header_item['name'], format_header)
            sheet.write(w_row_header, i, header_item['items'][0]['name'], format_header)
            sheet.write(w_row_header, i + 1, header_item['items'][1]['name'], format_header)
            i += 2
        
        sheet.merge_range(f"S{w_row_header}:S{w_row_header+1}", "ĐVT", format_header)

        prod_row = 7
        sum = data_raw["sum"]
        columns = [
            {"size": 5, "name": "no" ,                   "is_num": False},
            {"size": 15, "name": "date",                 "is_num": False},
            {"size": 12, "name": "move_id",              "is_num": False},
            {"size": 15, "name": "invoice_date",         "is_num": False},
            {"size": 15, "name": "reference",            "is_num": False},
            {"size": 10, "name": "product_uom_quantity", "is_num": False, "none": 'account_id'},
            {"size": 10, "name": "price_unit",           "is_num": False, "none": 'account_id'},
            {"size": 15, "name": "note",                 "is_num": False},
            {"size": 10, "name": "account_id",           "is_num": False},
            {"size": 10, "name": "account_dest_id",      "is_num": False},
            {"size": 10, "name": "ps_debit_usd",         "is_num": True, "currency":"usd"},
            {"size": 10, "name": "ps_debit_vnd",         "is_num": True, "currency":"vnd"},
            {"size": 10, "name": "ps_credit_usd",        "is_num": True, "currency":"usd"},
            {"size": 10, "name": "ps_credit_vnd",        "is_num": True, "currency":"vnd"},
            {"size": 10, "name": "end_debit_usd",        "is_num": True, "currency":"usd"},
            {"size": 10, "name": "end_debit_vnd",        "is_num": True, "currency":"vnd"},
            {"size": 10, "name": "end_credit_usd",       "is_num": True, "currency":"usd"},
            {"size": 10, "name": "end_credit_vnd",       "is_num": True, "currency":"vnd"},
            {"size": 5, "name": "uom_id",               "is_num": False},
        ]

        sum_end_debit_usd = ""
        sum_end_debit_vnd = ""
        sum_end_credit_usd = ""
        sum_end_credit_vnd = ""

        for each in data_raw["lines"]:
            prod_col = 0
            for column in columns:
                current_font = font_size_8
                if column["is_num"]:
                    if column["currency"] == "vnd":
                        current_font = font_size_8_number
                    else:
                        current_font = font_size_8_number_nt
                sheet.set_column(prod_col, prod_col, column["size"])
                val = each[column["name"]]
                if column.get("none", False) and each[column.get("none")] == "":
                    val = ""
                if column["name"] == "end_debit_usd":
                    sum_end_debit_usd = val
                if column["name"] == "end_debit_vnd":
                    sum_end_debit_vnd = val
                if column["name"] == "end_credit_usd":
                    sum_end_credit_usd = val
                if column["name"] == "end_credit_vnd":
                    sum_end_credit_vnd = val
                sheet.write(prod_row, prod_col, val, current_font)
                prod_col += 1
            prod_row += 1
        # Tổng cộng
        # Format cho số
        total_font_size_usd = workbook.add_format(json_format(10, right=True, left=True, bottom=True, top=True, bold=True))
        total_font_size_usd.set_align("right")
        total_font_size_usd.set_num_format("#,##0.00")

        total_font_size_vnd = workbook.add_format(json_format(10, right=True, left=True, bottom=True, top=True, bold=True))
        total_font_size_vnd.set_align("right")
        total_font_size_vnd.set_num_format("#,##0")

        total_font_size_text = workbook.add_format(json_format(10, right=True, left=True, bottom=True, top=True, bold=True))
        total_font_size_text.set_text_wrap()
        total_font_size_text.set_align("left")

        prod_row += 1
        prod_col = 0
        sheet.merge_range(f"A{prod_row}:J{prod_row}", "Tổng cộng", total_font_size_text)

        prod_row -= 1
        prod_col += 10
        total_arr = [
            {"name": "sum_ps_debit_usd", "font": "usd"},
            {"name": "sum_ps_debit_vnd", "font": "vnd"},
            {"name": "sum_ps_credit_usd", "font": "usd"},
            {"name": "sum_ps_credit_vnd", "font": "vnd"},
            # {"name": "sum_end_debit_usd", "font": "usd"},
            # {"name": "sum_end_debit_vnd", "font": "vnd"},
            # {"name": "sum_end_credit_usd", "font": "usd"},
            # {"name": "sum_end_credit_vnd", "font": "vnd"},
        ]
        for total_item in total_arr:
            current_font = total_font_size_usd
            if total_item["font"] == "vnd":
                current_font = total_font_size_vnd
            sheet.write(prod_row, prod_col, sum[total_item["name"]], current_font)
            prod_col += 1
        sheet.write(prod_row, prod_col, sum_end_debit_usd, total_font_size_usd)
        prod_col += 1
        sheet.write(prod_row, prod_col, sum_end_debit_vnd, total_font_size_vnd)
        prod_col += 1
        sheet.write(prod_row, prod_col, sum_end_credit_usd, total_font_size_usd)
        prod_col += 1
        sheet.write(prod_row, prod_col, sum_end_credit_vnd, total_font_size_vnd)
        prod_col += 1
        sheet.write(prod_row, prod_col, "", total_font_size_vnd)
        prod_col += 1
        prod_row +=1
        # Footer
        # Format cho số
        footer_font_size_title = workbook.add_format(json_format(12, bold=True))
        footer_font_size_title.set_align("center")
        footer_font_size_title.set_text_wrap()

        footer_font_size_sign = workbook.add_format(json_format(11, italic=True))
        footer_font_size_sign.set_align("center")
        footer_font_size_sign.set_text_wrap()

        prod_row = prod_row + 2
        sheet.merge_range(f"L{prod_row}:S{prod_row}","Ngày ..... tháng ..... năm .........",footer_font_size_sign)

        prod_row +=1
        sheet.merge_range(f"A{prod_row}:E{prod_row}","Người Lập Biểu",footer_font_size_title)
        sheet.merge_range(f"F{prod_row}:K{prod_row}","Kế Toán Trưởng",footer_font_size_title)
        sheet.merge_range(f"L{prod_row}:S{prod_row}","Thủ trưởng đơn vị",footer_font_size_title)

        prod_row +=1
        sheet.merge_range(f"A{prod_row}:E{prod_row}","(Ký, họ tên)",footer_font_size_sign)
        sheet.merge_range(f"F{prod_row}:K{prod_row}","(Ký, họ tên)",footer_font_size_sign)
        sheet.merge_range(f"L{prod_row}:S{prod_row}","(Ký, họ tên, đóng dấu)",footer_font_size_sign)

        prod_row = prod_row + 5
        sheet.merge_range(f"A{prod_row}:E{prod_row}","Nguyễn Thùy Linh", footer_font_size_title)
        sheet.merge_range(f"F{prod_row}:K{prod_row}","Trương Quốc Tuấn", footer_font_size_title)
        sheet.merge_range(f"L{prod_row}:S{prod_row}","Hoàng Mai Đãn",  footer_font_size_title)
