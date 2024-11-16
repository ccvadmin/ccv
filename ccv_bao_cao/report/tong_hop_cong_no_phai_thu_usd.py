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


class tong_hop_cong_no_phai_thu_usd(models.AbstractModel):
    _name = "report.ccv_bao_cao_usd.tong_hop_cong_no_phai_thu_usd"
    _inherit = "report.report_xlsx.abstract"
    _description = "Tong Hop Cong No Phai Thu"

    def generate_xlsx_report(self, workbook, data, objects):
        report = data
        date_start = report["date_start"]
        date_end = report["date_end"]
        account_id = report["account_id"]
        data_raw = report["data"]
        sheet = workbook.add_worksheet("TỔNG HỢP CÔNG NỢ PHẢI THU")

        workbook.set_properties({"title": "Báo cáo CCV", "author": self.env.user.display_name})
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
        title = "TỔNG HỢP CÔNG NỢ PHẢI THU"
        sheet.merge_range("A4:R4", title, format1)
        sheet.set_row(4, 35)
        sheet.set_row(5, 20)
        account_account = self.env["account.account"].browse(account_id)
        account = ""
        currency = ""
        if account_account:
            account = account_account.code
            currency = (account_account.currency_id.display_name if account_account.currency_id else "Chưa xác định")
        sub_title = "Tài khoản: %s; Loại tiền: USD; Từ ngày %s đến ngày %s" % (account,date_start,date_end,)
        sheet.merge_range("A5:R5", sub_title, format21)
        sub_title = "Công ty TNHH Con Cò Vàng - Mã số thuế: 0305995751"
        sheet.merge_range("C2:R2", sub_title, format_company_title)
        image_path = get_module_resource("ccv_bao_cao", r"static/src/img", "logo.png")
        image_format = {"x_offset": 0, "y_offset": 0, "x_scale": 0.22, "y_scale": 0.22}
        sheet.insert_image("A1", image_path, image_format)
        # Bảng
        w_row_header = 6
        header_arr = [
            {'name':"STT", "column": "A"},
            {'name':"Mã khách hàng", "column": "B"},
            {'name':"Tên khách hàng", "column": "C"},
            {'name':"Địa chỉ", "column": "D"},
            {'name':"Mã số thuế", "column": "E"},
            {'name':"Tài khoản công nợ", "column": "F"},
        ]
        i = 0
        for header_item in header_arr:
            sheet.merge_range(f"{header_item['column']}{w_row_header}:{header_item['column']}{w_row_header+1}", header_item['name'], format_header)
            i += 1
        header_arr = [
            {"name": "Dư Nợ đầu kỳ", "from":"G", "to":"H", "items": [{"name" : "Số tiền"},{"name" : "Quy đổi"},]},
            {"name": "Dư Có đầu kỳ", "from":"I", "to":"J", "items": [{"name" : "Số tiền"},{"name" : "Quy đổi"},]},
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

        prod_row = 7
        sum = data_raw["sum"]

        columns = [
            {"size": 5, "name": "no", "is_num": False},
            {"size": 12, "name": "customer_code", "is_num": False},
            {"size": 25, "name": "customer_name", "is_num": False},
            {"size": 25, "name": "address", "is_num": False},
            {"size": 15, "name": "vat", "is_num": False},
            {"size": 10, "name": "account_id", "is_num": False},
            {"size": 10, "name": "start_debit_usd", "is_num": True, "currency": "usd"},
            {"size": 10, "name": "start_debit_vnd", "is_num": True, "currency": "vnd"},
            {"size": 10, "name": "start_credit_usd", "is_num": True, "currency": "usd"},
            {"size": 10, "name": "start_credit_vnd", "is_num": True, "currency": "vnd"},
            {"size": 10, "name": "ps_debit_usd", "is_num": True, "currency": "usd"},
            {"size": 10, "name": "ps_debit_vnd", "is_num": True, "currency": "vnd"},
            {"size": 10, "name": "ps_credit_usd", "is_num": True, "currency": "usd"},
            {"size": 10, "name": "ps_credit_vnd", "is_num": True, "currency": "vnd"},
            {"size": 10, "name": "end_debit_usd", "is_num": True, "currency": "usd"},
            {"size": 10, "name": "end_debit_vnd", "is_num": True, "currency": "vnd"},
            {"size": 10, "name": "end_credit_usd", "is_num": True, "currency": "usd"},
            {"size": 10, "name": "end_credit_vnd", "is_num": True, "currency": "vnd"},
        ]

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
                sheet.write(prod_row, prod_col, each[column["name"]], current_font)
                prod_col += 1

            prod_row +=1
        
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
        sheet.merge_range(f"A{prod_row}:F{prod_row}", "Tổng cộng", total_font_size_text)

        prod_row -= 1
        prod_col += 6
        total_arr = [
            {"name": "sum_start_debit_usd", "font": "usd"},
            {"name": "sum_start_debit_vnd", "font": "vnd"},
            {"name": "sum_start_credit_usd", "font": "us"},
            {"name": "sum_start_credit_vnd", "font": "vn"},
            {"name": "sum_ps_debit_usd", "font": "usd"},
            {"name": "sum_ps_debit_vnd", "font": "vnd"},
            {"name": "sum_ps_credit_usd", "font": "usd"},
            {"name": "sum_ps_credit_vnd", "font": "vnd"},
            {"name": "sum_end_debit_usd", "font": "usd"},
            {"name": "sum_end_debit_vnd", "font": "vnd"},
            {"name": "sum_end_credit_usd", "font": "usd"},
            {"name": "sum_end_credit_vnd", "font": "vnd"},
        ]
        for total_item in total_arr:
            current_font = total_font_size_usd
            if total_item["font"] == "vnd":
                current_font = total_font_size_vnd
            sheet.write(prod_row, prod_col, sum[total_item["name"]], current_font)
            prod_col += 1

        prod_row +=1

        # Footer
        # Format cho số
        footer_font_size_title = workbook.add_format(json_format(12, bold=True))
        footer_font_size_title.set_align("center")
        footer_font_size_title.set_text_wrap()

        footer_font_size_sign = workbook.add_format(json_format(11, bold=True))
        footer_font_size_sign.set_align("center")
        footer_font_size_sign.set_text_wrap()

        prod_row = prod_row + 2
        sheet.merge_range(f"K{prod_row}:R{prod_row}","Ngày ..... tháng ..... năm .........",footer_font_size_sign,)

        prod_row += 1
        sheet.merge_range(f"A{prod_row}:E{prod_row}", "Người Lập Biểu", footer_font_size_title)
        sheet.merge_range(f"F{prod_row}:J{prod_row}", "Kế Toán Trưởng", footer_font_size_title)
        sheet.merge_range(f"K{prod_row}:R{prod_row}", "Thủ trưởng đơn vị", footer_font_size_title)

        prod_row += 1
        sheet.merge_range(f"A{prod_row}:E{prod_row}", "(Ký, họ tên)", footer_font_size_sign)
        sheet.merge_range(f"F{prod_row}:J{prod_row}", "(Ký, họ tên)", footer_font_size_sign)
        sheet.merge_range(f"K{prod_row}:R{prod_row}", "(Ký, họ tên, đóng dấu)", footer_font_size_sign)

        prod_row = prod_row + 5
        sheet.merge_range(f"A{prod_row}:E{prod_row}", "Nguyễn Thu Ngân", footer_font_size_title)
        sheet.merge_range(f"F{prod_row}:J{prod_row}", "Trương Quốc Tuấn", footer_font_size_title)
        sheet.merge_range(f"K{prod_row}:R{prod_row}", "Hoàng Mai Đãn", footer_font_size_title)
