# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Odoo lib
from odoo import http, _, fields
from odoo.http import request

# Python lib
import urllib.parse
import logging
from werkzeug.utils import secure_filename
import time
import base64
from datetime import datetime, timedelta
from ..lib.const import get_date, get_timestamp, encode_token, decode_token
from werkzeug.wrappers import Request, Response
import json

_logger = logging.getLogger(__name__)


class MainController(http.Controller):
    @http.route("/public/order/confirm-order",type="http",auth="public",website=True,)
    def order_confirmation_page(self, **kwargs):
        try:
            token = kwargs.get("token")
            if not token:
                return self.msg("Đường dẫn không hợp lệ", "Đường dẫn không hợp lệ")
            secret_key_public_user = (
                request.env["ir.config_parameter"]
                .sudo()
                .get_param("confirm_order_process.serect_key_public_user", False)
            )
            decoded_data = decode_token(token, secret_key_public_user)
            if not decoded_data:
                return self.msg("Không thể xác thực người dùng", "Không thể xác thực người dùng")

            time_from_token, public_key, order_id = decoded_data.split(" | ")
            time_from_token = float(time_from_token)

            current_date = datetime.now().date()
            token_date = datetime.fromtimestamp(time_from_token).date()

            if current_date != token_date:
                order = request.env["sale.order"].sudo().browse(int(order_id))
                order.order_link_ids.filtered(
                    lambda l: l.type == "order" and l.state == "draft"
                ).write({"state": "expired"})
                return self.msg("Đường dẫn đã hết hạn", "Đường dẫn xác nhận đơn hàng đã hết hạn")

            order = request.env["sale.order"].sudo().browse(int(order_id))
            if not order:
                return self.msg("Xác Nhận Đơn Hàng Thất Bại", "Đơn hàng không được tìm thấy!")
            if order.state not in ["draft", "sent"]:
                return self.msg("Xác Nhận Đơn Hàng Thất Bại", "Đơn Hàng Không Thể Xác Nhận Lúc Này!")
            otp_model = (
                request.env["otp.verification"]
                .sudo()
                .search(
                    [("sale_order_id.id", "=", order.id), ("state", "=", "unverified")]
                )
            )
            if not otp_model:
                otp_model = (
                    request.env["otp.verification"]
                    .sudo()
                    .create(
                        {
                            "sale_order_id": order.id,
                            "phone": getattr(order.partner_id, "phone", ""),
                            "email": getattr(order.partner_id, "email", ""),
                        }
                    )
                )
                otp_model.action_send_email()

            order_data = {
                "title": "Xác nhận đơn hàng - %s - %s"
                % (order_id, order.partner_id.name),
                "currency": request.env.user.company_id.currency_id.currency_unit_label,
                "logo": request.env["res.company"].sudo().search([], limit=1).logo,
                "order_id": order.name,
                "customer_name": order.partner_id.name,
                "address": order.partner_id.contact_address,
                "phone": order.partner_id.phone,
                "total_amount": "{:,}".format(order.amount_total),
                "products": [
                    {
                        "name": line.product_id.display_name,
                        "quantity": line.product_uom_qty,
                        "product_uom": line.product_uom.display_name,
                        "price_unit": "{:,}".format(line.price_unit),
                        "price_subtotal": "{:,}".format(line.price_subtotal),
                    }
                    for line in order.order_line
                ],
                "status": order.state in ["draft", "sent"],
                "token": token,
            }

            return request.render(
                "confirm_order_process.order_confirmation_template", order_data
            )
        except Exception as e:
            _logger.error(f"Error during order confirmation: {e}")
            return self.msg("Xác Nhận Đơn Hàng Thất Bại", "Đường dẫn không hợp lệ!")

    @http.route("/public/order/confirm-order",type="http",auth="public",website=True,methods=["POST"],)
    def order_confirmation(self, **kwargs):
        user_ip = request.httprequest.remote_addr
        if user_ip:
            if self._check_ip_request_limit(user_ip):
                return self.msg("Xác Nhận Đơn Hàng Thất Bại", "Bạn đã vượt quá số lần yêu cầu trong vòng 1 giờ. Vui lòng thử lại sau.")
            self._log_user_ip(user_ip)
        try:
            token = kwargs.get("token")
            otp = kwargs.get("otp")

            if not token:
                return self.msg("Xác Nhận Đơn Hàng Thất Bại", "Đường dẫn không hợp lệ!")

            if not otp:
                return self.msg("Xác Nhận Đơn Hàng Thất Bại", "OTP không được cung cấp!")
            if len(otp) != 6:
                return self.msg("Xác Nhận Đơn Hàng Thất Bại", "OTP không đúng!")
            if not otp.isdigit():
                return self.msg("Xác Nhận Đơn Hàng Thất Bại", "OTP không đúng!")
            secret_key_public_user = (
                request.env["ir.config_parameter"]
                .sudo()
                .get_param("confirm_order_process.serect_key_public_user", False)
            )
            decoded_data = decode_token(token, secret_key_public_user)
            if not decoded_data:
                return self.msg("Không thể xác thực người dùng", "Không thể xác thực người dùng")
            time_from_token, public_key, order_id = decoded_data.split(" | ")
            time_from_token = float(time_from_token)

            current_date = datetime.now().date()
            token_date = datetime.fromtimestamp(time_from_token).date()

            if current_date != token_date:
                return self.msg("Xác Nhận Đơn Hàng Thất Bại", "Đường dẫn xác nhận đơn hàng đã hết hạn!")

            order = request.env["sale.order"].sudo().browse(int(order_id))
            if not order:
                return self.msg("Xác Nhận Đơn Hàng Thất Bại", "Đơn hàng không được tìm thấy!")
            # Check OTP
            opt_id = (
                request.env["otp.verification"]
                .sudo()
                .search(
                    [
                        ("sale_order_id.id", "=", int(order_id)),
                        ("otp", "=", otp),
                    ]
                )
            )
            if not opt_id:
                return self.msg("Xác Nhận Đơn Hàng Thất Bại", "OTP không đúng!")
            otp_state, otp_msg = opt_id.get_state_otp()
            if not otp_state:
                return self.msg("Xác Nhận Đơn Hàng Thất Bại", otp_msg)

            if order.state not in ["draft", "sent"]:
                return self.msg("Xác Nhận Đơn Hàng Thất Bại", "Có lỗi xảy ra trong quá trình xác nhận đơn hàng.")

            order.public_confirm(opt_id)
            order.send_message_w_trigger()

            return self.msg("Xác Nhận Đơn Hàng Thành Công", f"Đơn hàng {order.name} của bạn đã được xác nhận thành công!")

        except Exception as e:
            _logger.error(f"Error while confirming order: {e}")
            return self.msg("Xác Nhận Đơn Hàng Thất Bại", "Có lỗi xảy ra trong quá trình xác nhận đơn hàng.")

    @http.route("/public/order/confirm-delivery",type="http",auth="public",website=True,)
    def order_delivery_page(self, **kwargs):
        try:
            token = kwargs.get("token")
            if not token:
                return self.msg("Đường dẫn không hợp lệ", "Đường dẫn không hợp lệ")

            secret_key_public_user = (
                request.env["ir.config_parameter"]
                .sudo()
                .get_param("confirm_order_process.serect_key_public_user", False)
            )

            decoded_data = decode_token(token, secret_key_public_user)
            if not decoded_data:
                return self.msg("Không thể xác thực người dùng", "Không thể xác thực người dùng")

            time_from_token, public_key, order_id = decoded_data.split(" | ")
            time_from_token = float(time_from_token)

            current_date = datetime.now().date()
            token_date = datetime.fromtimestamp(time_from_token).date()

            if current_date != token_date:
                order = request.env["sale.order"].sudo().browse(int(order_id))
                order.order_link_ids.filtered(
                    lambda l: l.type == "delivery" and l.state == "draft"
                ).write({"state": "expired"})
                return self.msg("Đường dẫn đã hết hạn", "Đường dẫn xác nhận giao hàng đã hết hạn")

            order = request.env["sale.order"].sudo().browse(int(order_id))
            if not order:
                return self.msg("Xác Nhận Đơn Hàng Thất Bại", "Đơn hàng không được tìm thấy.")

            if not (
                order.state == "sale"
                and order.state_mrp == "done"
                and order.state_delivery == "draft"
            ):
                return self.msg("Đơn Hàng Không Thể Giao Lúc Này", "Đơn hàng không ở trạng thái có thể giao.")

            otp_model = (
                request.env["otp.verification"]
                .sudo()
                .search(
                    [("sale_order_id.id", "=", order.id), ("state", "=", "unverified")]
                )
            )
            if not otp_model:
                otp_model = (
                    request.env["otp.verification"]
                    .sudo()
                    .create(
                        {
                            "sale_order_id": order.id,
                            "phone": getattr(order.partner_id, "phone", ""),
                            "email": getattr(order.partner_id, "email", ""),
                        }
                    )
                )
                otp_model.action_send_email()

            # Dữ liệu trả về cho template
            order_data = {
                "title": "Xác nhận đơn hàng - %s - %s"
                % (order_id, order.partner_id.name),
                "currency": request.env.user.company_id.currency_id.currency_unit_label,
                "logo": request.env["res.company"].sudo().search([], limit=1).logo,
                "order_id": order.name,
                "customer_name": order.partner_id.name,
                "address": order.partner_id.contact_address,
                "phone": order.partner_id.phone,
                "total_amount": "{:,}".format(order.amount_total),
                "products": [
                    {
                        "name": line.product_id.display_name,
                        "quantity": line.product_uom_qty,
                        "product_uom": line.product_uom.display_name,
                        "price_unit": "{:,}".format(line.price_unit),
                        "price_subtotal": "{:,}".format(line.price_subtotal),
                    }
                    for line in order.order_line
                ],
                "images": [
                    self.get_attachment(attachment)
                    for attachment in order.mrp_attachment_ids
                ],
                "status": order.state == "sale",
                "token": token,
            }

            return request.render(
                "confirm_order_process.order_delivery_template", order_data
            )

        except Exception as e:
            _logger.error(f"Error during order delivery confirmation: {e}")
            return self.msg("Đường dẫn không hợp lệ", "Đường dẫn không hợp lệ.")

    @http.route("/public/order/confirm-delivery",type="http",auth="public",website=True,methods=["POST"],)
    def order_delivery(self, **kwargs):
        user_ip = request.httprequest.remote_addr
        if user_ip:
            if self._check_ip_request_limit(user_ip):
                return self.msg("Xác Nhận Giao Hàng Thất Bại", "Bạn đã vượt quá số lần yêu cầu trong vòng 1 giờ. Vui lòng thử lại sau.")
            self._log_user_ip(user_ip)
        try:
            token = kwargs.get("token")
            otp = kwargs.get("otp")

            if not token:
                return self.msg("Xác Nhận Giao Hàng Thất Bại", "Đường dẫn không hợp lệ.")

            if not otp:
                return self.msg("Xác Nhận Giao Hàng Thất Bại", "OTP không được cung cấp.")
            secret_key_public_user = (
                request.env["ir.config_parameter"]
                .sudo()
                .get_param("confirm_order_process.serect_key_public_user", False)
            )
            decoded_data = decode_token(token, secret_key_public_user)
            if not decoded_data:
                return self.msg("Không thể xác thực người dùng", "Không thể xác thực người dùng")

            time_from_token, public_key, order_id = decoded_data.split(" | ")
            time_from_token = float(time_from_token)

            current_date = datetime.now().date()
            token_date = datetime.fromtimestamp(time_from_token).date()

            if current_date != token_date:
                return self.msg("Xác Nhận Giao Hàng Thất Bại", "Đường dẫn xác nhận giao hàng đã hết hạn!")

            order = request.env["sale.order"].sudo().browse(int(order_id))
            if not order:
                return self.msg("Xác Nhận Giao Hàng Thất Bại", "Đơn hàng không được tìm thấy!")

            # Check OTP
            opt_id = (
                request.env["otp.verification"]
                .sudo()
                .search(
                    [
                        ("sale_order_id.id", "=", int(order_id)),
                        ("otp", "=", otp),
                    ]
                )
            )
            if not opt_id:
                return self.msg("Xác Nhận Giao Hàng Thất Bại", "OTP không đúng!")
            otp_state, otp_msg = opt_id.get_state_otp()
            if not otp_state:
                return self.msg("Xác Nhận Giao Hàng Thất Bại", otp_msg)
            if not (
                order.state == "sale"
                and order.state_mrp == "done"
                and order.state_delivery == "draft"
            ):
                return self.msg("Xác Nhận Giao Hàng Thất Bại", "Đơn hàng không ở trạng thái có thể xác nhận!")

            order.public_confirm(opt_id)
            order.send_message_w_trigger("delivery")

            return self.msg("Xác Nhận Giao Hàng Thành Công", f"Đơn hàng {order.name} của bạn đã được xác nhận giao thành công!")

        except Exception as e:
            _logger.error(f"Error while confirming order: {e}")
            return self.msg("Xác Nhận Giao Hàng Thất Bại", "Có lỗi xảy ra trong quá trình xác nhận giao hàng.")

    def _log_user_ip(self, user_ip):
        ip_history_model = request.env["user.ip.history"].sudo()
        ip_history_model.create(
            {
                "user_ip": user_ip,
                "timestamp": fields.Datetime.now(),
            }
        )

    def _check_ip_request_limit(self, user_ip):
        two_hours_ago = fields.Datetime.now() - timedelta(hours=1)
        ip_history_model = request.env["user.ip.history"].sudo()
        recent_requests = ip_history_model.search_count(
            [("user_ip", "=", user_ip), ("timestamp", ">=", two_hours_ago)]
        )
        return recent_requests == 5

    def get_attachment(self, attachment):
        data_uri = ""
        if attachment and attachment.mimetype.startswith("image/"):
            attachment.generate_access_token()
            data_uri = "/web/image/%s?access_token=%s" % (
                attachment.id,
                attachment.access_token,
            )
        return {
            "id": attachment.id,
            "name": attachment.name,
            "url": data_uri,
        }

    @http.route("/public/upload_files_to_order",type="http",auth="public",website=True,)
    def upload_files_to_order_page(self, **kwargs):
        try:
            token = kwargs.get("token")
            if not token:
                return self.msg("Đường dẫn không hợp lệ", "Đường dẫn không hợp lệ")
            secret_key_public_user = (
                request.env["ir.config_parameter"]
                .sudo()
                .get_param("confirm_order_process.serect_key_public_user", False)
            )
            decoded_data = decode_token(token, secret_key_public_user)
            if not decoded_data:
                return self.msg("Không thể xác thực người dùng", "Không thể xác thực người dùng")
            time_from_token, public_key, order_id = decoded_data.split(" | ")
            time_from_token = float(time_from_token)

            current_date = datetime.now().date()
            token_date = datetime.fromtimestamp(time_from_token).date()

            if current_date != token_date:
                order = request.env["sale.order"].sudo().browse(int(order_id))
                order.order_link_ids.filtered(
                    lambda l: l.type == "image" and l.state == "draft"
                ).write({"state": "expired"})
                return self.msg("Đường dẫn đã hết hạn", "Đường dẫn xác nhận đơn hàng đã hết hạn")

            order = request.env["sale.order"].sudo().browse(int(order_id))
            order_data = {
                "title": "Đơn hàng - %s" % order.name,
                "order": order,
                "urlpost": "/public/upload_files_to_order?token=%s"
                % (urllib.parse.quote(token)),
            }

            return request.render("confirm_order_process.file_upload_form", order_data)
        except Exception as e:
            _logger.error(f"Error during order confirmation: {e}")
            return self.msg("Đường dẫn không hợp lệ", "Đường dẫn không hợp lệ.")


    @http.route("/public/upload_files_to_order",type="http",auth="public",website=True,methods=["POST"],)
    def upload_files_to_order(self, **kwargs):
        try:
            token = kwargs.get("token")
            if not token:
                return self.msg("Đường dẫn không hợp lệ", "Đường dẫn không hợp lệ")
            secret_key_public_user = (
                request.env["ir.config_parameter"]
                .sudo()
                .get_param("confirm_order_process.serect_key_public_user", False)
            )
            decoded_data = decode_token(token, secret_key_public_user)
            if not decoded_data:
                return self.msg("Không thể xác thực người dùng", "Không thể xác thực người dùng")

            time_from_token, public_key, order_id = decoded_data.split(" | ")
            time_from_token = float(time_from_token)

            current_date = datetime.now().date()
            token_date = datetime.fromtimestamp(time_from_token).date()

            if current_date != token_date:
                order = request.env["sale.order"].sudo().browse(int(order_id))
                order.order_link_ids.filtered(
                    lambda l: l.type == "image" and l.state == "draft"
                ).write({"state": "expired"})
                return self.msg("Đường dẫn đã hết hạn", "Đường dẫn xác nhận đơn hàng đã hết hạn")

            order = request.env["sale.order"].sudo().browse(int(order_id))

            if not order:
                return self.msg("Thêm ảnh thất bại", "Đơn hàng không được tìm thấy!")


            uploaded_files = request.httprequest.files.getlist("files")

            if uploaded_files:
                if len(uploaded_files) > 5:
                    return self.msg("Thêm ảnh thất bại", "Số lượng ảnh vượt quá cho phép!")
                is_mrp_images = (
                    order.state_mrp == "done"
                    and order.state == "sale"
                    and order.state_delivery == "draft"
                )
                is_sale_images = (
                    order.state_mrp == "done"
                    and order.state == "sale"
                    and order.state_delivery == "confirm"
                )
                for i, uploaded_file in enumerate(uploaded_files):
                    filename = secure_filename(uploaded_file.filename)
                    file_data = uploaded_file.read()
                    image_name = kwargs.get(filename, "")
                    encoded_file_data = base64.b64encode(file_data).decode("utf-8")
                    attachment = (
                        request.env["ir.attachment"]
                        .sudo()
                        .create(
                            {
                                "name": image_name.strip()
                                if image_name
                                else filename[:-4],
                                "type": "binary",
                                "datas": encoded_file_data,
                                # 'datas_fname': filename,
                                "res_model": "sale.order",
                                "res_id": order.id,
                            }
                        )
                    )
                    if is_sale_images:
                        order.write({"sale_attachment_ids": [(4, attachment.id)]})
                    else:
                        order.write({"mrp_attachment_ids": [(4, attachment.id)]})
                order.order_link_ids.filtered(
                    lambda l: l.type == "image" and l.state == "draft"
                ).write({"state": "consume"})
                if not is_sale_images:
                    return request.render(
                        "confirm_order_process.file_upload_result",
                        {
                            "message": "Tải ảnh lên thành công và đã gắn vào đơn hàng!",
                            "order": order,
                            "attachments": [
                                self.get_attachment(attachment)
                                for attachment in order.sale_attachment_ids
                            ],
                        },
                    )
                else:
                    return request.render(
                        "confirm_order_process.file_upload_result",
                        {
                            "message": "Tải ảnh lên thành công và đã gắn vào đơn hàng!",
                            "order": order,
                            "attachments": [
                                self.get_attachment(attachment)
                                for attachment in order.mrp_attachment_ids
                            ],
                        },
                    )

            return request.render(
                "confirm_order_process.file_upload_form",
                {"message": "Không có tệp hoặc tên ảnh không hợp lệ!"},
            )
        except Exception as e:
            _logger.error(f"Error: {e}")
            return self.msg("Đường dẫn không hợp lệ", "Đường dẫn không hợp lệ.")

    @http.route("/public/order/get-location", auth="public", type="http", methods=["GET"])
    def get_location(self, **kwag):
        headers = {"Content-Type": "application/json"}
        body = {}
        try:
            k_id = kwag.get("id", False)
            k_model = kwag.get("model", False)
            k_role = kwag.get("role", False)
            token = kwag.get("token", False)
            secret_key_public_user = (
                request.env["ir.config_parameter"]
                .sudo()
                .get_param("confirm_order_process.image_key_public_user", False)
            )
            decoded_data = decode_token(token, secret_key_public_user)

            if not decoded_data:
                body = {
                    "status": 3,
                    "message": "Đường dẫn không hợp lệ.",
                    "state": "invalid",
                }
            else:
                time_from_token, public_key, role, model, id = decoded_data.split(" | ")
                time_from_token = float(time_from_token)

                if not token:
                    body = {
                        "status": 3,
                        "message": "Đường dẫn không hợp lệ.",
                        "state": "invalid",
                    }
                elif k_role != role or k_model != model or k_id != id:
                    body = {
                        "status": 3,
                        "message": "Đường dẫn không hợp lệ.",
                        "state": "invalid",
                    }
                elif id:
                    model = "sales.order"
                    if role == "driver":
                        model = "sales.order.location"
                        cur_location = (
                            request.env["sales.order.location"].sudo().browse(int(id))
                        )
                        if cur_location:
                            order = cur_location.order_id
                            if order:
                                if order.state == "done":
                                    body = {
                                        "status": 2,
                                        "message": "Trạng thái đơn hàng: Đã Hoàn thành.",
                                        "state": order.state,
                                    }
                                else:
                                    location = order.order_link_ids.mapped(
                                        "location_id"
                                    ).filtered(lambda l: l.id == id)
                                    if location or role == "driver":
                                        src_location = (
                                            request.env["tracking.order.config"]
                                            .sudo()
                                            .search([], limit=1)
                                            .src_location
                                        )
                                        dest_location = order.partner_id

                                        body = {
                                            "locations": {
                                                "current": {
                                                    "lat": location.latitude,
                                                    "lng": location.longitude,
                                                },
                                                "src": {
                                                    "lat": src_location.partner_latitude,
                                                    "lng": src_location.partner_longitude,
                                                },
                                                "dest": {
                                                    "lat": dest_location.partner_latitude,
                                                    "lng": dest_location.partner_longitude,
                                                },
                                            },
                                            "status": 0,
                                            "message": "Thành công!!!",
                                            "state": order.state,
                                        }
                                    else:
                                        body = {
                                            "status": 1,
                                            "message": "Không tìm thấy toạ độ.",
                                            "state": order.state,
                                        }
                            else:
                                body = {
                                    "status": 1,
                                    "message": "Không tìm thấy đơn hàng.",
                                    "state": "not_found",
                                }
                        else:
                            body = {
                                "status": 1,
                                "message": "Không tìm thấy đơn hàng.",
                                "state": "not_found",
                            }
                    else:
                        order = (
                            request.env['sale.order'].sudo().browse(int(id))
                        )
                        if order:
                            if order.state == "done":
                                body = {
                                    "status": 2,
                                    "message": "Trạng thái đơn hàng: Đã Hoàn thành.",
                                    "state": order.state,
                                }
                            else:
                                locations = order.order_link_ids.mapped("location_id")
                                if locations:
                                    src_location = (
                                        request.env["tracking.order.config"]
                                        .sudo()
                                        .search([], limit=1)
                                        .src_location
                                    )
                                    dest_location = order.partner_id

                                    body = {
                                        "locations": {
                                            "current": [{
                                                "num": location.vehicle_number,
                                                "lat": location.latitude,
                                                "lng": location.longitude,
                                            } for location in locations],
                                            "src": {
                                                "lat": src_location.partner_latitude,
                                                "lng": src_location.partner_longitude,
                                            },
                                            "dest": {
                                                "lat": dest_location.partner_latitude,
                                                "lng": dest_location.partner_longitude,
                                            },
                                        },
                                        "status": 0,
                                        "message": "Thành công!!!",
                                        "state": order.state,
                                    }
                                else:
                                    body = {
                                        "status": 1,
                                        "message": "Không tìm thấy toạ độ.",
                                        "state": order.state,
                                    }
                        else:
                            body = {
                                "status": 1,
                                "message": "Không tìm thấy đơn hàng.",
                                "state": "not_found",
                            }
                else:
                    body = {
                        "status": 1,
                        "message": "Không tìm thấy đơn hàng.",
                        "state": "not_found",
                    }

        except Exception as e:
            body = {
                "status": 3,
                "message": "Có lỗi xảy ra khi lấy vị trí.",
                "state": "error",
            }

        return Response(json.dumps(body), headers=headers)

    @http.route("/public/order/set-location", auth="public", type="http", methods=["GET"])
    def set_location(self, **kwag):
        headers = {"Content-Type": "application/json"}
        body = {}
        try:
            k_id = kwag.get("id", False)
            k_model = kwag.get("model", False)
            k_role = kwag.get("role", False)
            token = kwag.get("token", False)
            latitude = kwag.get("lat", False)
            longitude = kwag.get("lng", False)

            secret_key_public_user = (
                request.env["ir.config_parameter"]
                .sudo()
                .get_param("confirm_order_process.image_key_public_user", False)
            )
            decoded_data = decode_token(token, secret_key_public_user)

            if not decoded_data:
                body = {
                    "status": 3,
                    "message": "Đường dẫn không hợp lệ.",
                    "state": "invalid",
                }
            else:
                time_from_token, public_key, role, model, id = decoded_data.split(" | ")
                time_from_token = float(str(time_from_token))

                if not token:
                    body = {
                        "status": 3,
                        "message": "Đường dẫn không hợp lệ.",
                        "state": "invalid",
                    }
                elif k_role != role or k_model != model or k_id != id:
                    body = {
                        "status": 3,
                        "message": "Đường dẫn không hợp lệ.",
                        "state": "invalid",
                    }
                elif role != "driver":
                    body = {
                        "status": 3,
                        "message": "Bạn không có quyền thực hiện.",
                        "state": "invalid",
                    }
                elif id:
                    cur_location = (
                        request.env["sales.order.location"].sudo().browse(int(id))
                    )
                    if cur_location:
                        order = cur_location.order_id
                        if order:
                            if order.state == "done":
                                body = {
                                    "status": 2,
                                    "message": "Trạng thái đơn hàng: Đã Hoàn thành.",
                                    "state": order.state,
                                }
                            else:
                                if latitude == 0 or longitude == 0:
                                    body = {
                                        "status": 2,
                                        "message": "Tọa độ không hợp lệ.",
                                        "state": "not_found",
                                    }
                                now = datetime.now()
                                if cur_location.line_ids.filtered(lambda l: l.date.date() == now.date() and abs((l.date - now).total_seconds()) < 10):
                                    body = {
                                        "status": 2,
                                        "message": "2 lần request quá lần nhau.",
                                        "state": "not_found",
                                    }
                                else:
                                    cur_location.write(
                                        {
                                            "line_ids": [(0,0,{
                                                        "latitude": latitude,
                                                        "longitude": longitude,
                                                        "date": now,
                                            })]})
                                    body = {
                                        "status": 0,
                                        "message": "Thành công!!!",
                                        "state": order.state,
                                    }
                        else:
                            body = {
                                "status": 1,
                                "message": "Không tìm thấy đơn hàng.",
                                "state": "not_found",
                            }
                    else:
                        body = {
                            "status": 1,
                            "message": "Không tìm thấy đơn hàng.",
                            "state": "not_found",
                        }
                else:
                    body = {
                        "status": 1,
                        "message": "Không tìm thấy đơn hàng.",
                        "state": "not_found",
                    }

        except Exception as e:
            _logger.info(e)
            body = {
                "status": 3,
                "message": "Có lỗi xảy ra khi lấy vị trí.",
                "state": "error",
            }

        return Response(json.dumps(body), headers=headers)

    @http.route("/public/order/track-journey", type="http", auth="public", website=True)
    def get_view(self, **kwag):
        try:
            k_id = kwag.get("id", False)
            k_model = kwag.get("model", False)
            k_role = kwag.get("role", False)
            token = kwag.get("token", False)
            config_parameter = request.env["ir.config_parameter"].sudo()
            secret_key_public_user = config_parameter.get_param(
                "confirm_order_process.image_key_public_user", False
            )
            decoded_data = decode_token(token, secret_key_public_user)
            if not decoded_data:
                return {"status": 3, "message": "Đường dẫn không hợp lệ."}
            time_from_token, public_key, role, model, id = decoded_data.split(" | ")
            time_from_token = float(time_from_token)
            if not token:
                return self.msg("Tạo map thất bại", "Đường dẫn không hợp lệ.")
            if k_role != role or k_model != model or k_id != id:
                return self.msg("Tạo map thất bại", "Đường dẫn không hợp lệ.")
            map_key = config_parameter.get_param(
                "base_geolocalize.google_map_api_key", False
            )
            if not map_key:
                return self.msg("Tạo map thất bại", "Bạn chưa cấu hình map key.")
            model = "sale.order"
            if role == "driver":
                model = "sales.order.location"
            if id:
                order = (
                    request.env[model].sudo().search([("id", "=", id)], limit=1)
                )
                if role == "driver":
                    if order and order.order_id:
                        if order.order_id.state == "done":
                            return self.msg("Tạo map thất bại", "Trạng thái đơn hàng: Hoàn thành.")
                    else:
                        return self.msg("Tạo map thất bại", "Không xác định được đơn hàng.")
                else:
                    if order:
                        if order.state == "done":
                            return self.msg("Tạo map thất bại", "Trạng thái đơn hàng: Hoàn thành.")
                    else:
                        return self.msg("Tạo map thất bại", "Không xác định được đơn hàng.")
            else:
                return self.msg("Tạo map thất bại", "Không xác định được đơn hàng.")
            return request.render(
                "confirm_order_process.map_view_template",
                {"role": role, "map_key": map_key},
            )
        except Exception as e:
            _logger.error(f"Error: {e}")
            return self.msg("Tạo map thất bại", "Có lỗi xảy ra trong quá trình tạo map.")

    def msg(self, title, message):
        return self.generate_message({"title": title, "message": message})

    def generate_message(self, data, view_name="confirm_order_process.notify_template"):
        return request.render(view_name, data)
