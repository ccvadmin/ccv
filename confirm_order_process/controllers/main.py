# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Odoo lib
from odoo import http, _, fields
from odoo.http import request
import time

# Python lib
from ..lib.const import get_date, get_timestamp, encode_token, decode_token
import logging

from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class MainController(http.Controller):
    @http.route(
        "/public/order/confirm-order",
        type="http",
        auth="public",
        website=True,
    )
    def order_confirmation_page(self, **kwargs):
        try:
            token = kwargs.get("token")
            if not token:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Đường dẫn không hợp lệ",
                        "message": "Đường dẫn không hợp lệ",
                    },
                )
            secret_key_public_user = (
                request.env["ir.config_parameter"]
                .sudo()
                .get_param("confirm_order_process.serect_key_public_user", False)
            )
            decoded_data = decode_token(token, secret_key_public_user)
            if not decoded_data:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Không thể xác thực người dùng",
                        "message": "Không thể xác thực người dùng",
                    },
                )

            time_from_token, public_key, order_id = decoded_data.split(" | ")
            time_from_token = float(time_from_token)

            current_date = datetime.now().date()
            token_date = datetime.fromtimestamp(time_from_token).date()

            if current_date != token_date:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Đường dẫn đã hết hạn",
                        "message": "Đường dẫn xác nhận đơn hàng đã hết hạn.",
                    },
                )

            order = request.env["sale.order"].sudo().browse(int(order_id))
            if not order:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Đơn Hàng Thất Bại",
                        "message": "Đơn hàng không được tìm thấy!",
                    },
                )
            if order.state not in ["draft", "sent"]:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Đơn Hàng Không Thể Xác Nhận Lúc Này",
                        "message": "Đơn Hàng Không Thể Xác Nhận Lúc Này",
                    },
                )
            otp_model = request.env['otp.verification'].sudo().search([('sale_order_id.id','=', order.id)])
            if not otp_model:
                otp_model = request.env['otp.verification'].sudo().create({
                    'sale_order_id': order.id,
                    'phone': order.partner_id.phone,
                })
                otp_model.action_send_email()

            order_data = {
                "currency": request.env.user.company_id.currency_id.currency_unit_label,
                "logo": request.env["res.company"].search([], limit=1).logo,
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
            return request.render(
                "confirm_order_process.order_confirmation_notify_template",
                {
                    "title": "Đường dẫn không hợp lệ",
                    "message": "Đường dẫn không hợp lệ",
                },
            )

    @http.route(
        "/public/order/confirm-order",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
    )
    def order_confirmation(self, **kwargs):
        user_ip = request.httprequest.remote_addr
        if user_ip:
            if self._check_ip_request_limit(user_ip):
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Đơn Hàng Thất Bại",
                        "message": "Bạn đã vượt quá số lần yêu cầu trong vòng 2 giờ. Vui lòng thử lại sau.",
                    },
                )
            self._log_user_ip(user_ip)
        try:
            token = kwargs.get("token")
            otp = kwargs.get("otp")

            if not token:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Đơn Hàng Thất Bại",
                        "message": "Đường dẫn không hợp lệ",
                    },
                )

            if not otp:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Đơn Hàng Thất Bại",
                        "message": "OTP không được cung cấp",
                    },
                )
            if len(otp) != 6:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Đơn Hàng Thất Bại",
                        "message": "OTP không được cung cấp",
                    }
                )
            if not otp.isdigit():
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Đơn Hàng Thất Bại",
                        "message": "OTP không được cung cấp",
                    }
                )
            secret_key_public_user = (
                request.env["ir.config_parameter"]
                .sudo()
                .get_param("confirm_order_process.serect_key_public_user", False)
            )
            decoded_data = decode_token(token, secret_key_public_user)
            if not decoded_data:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Đơn Hàng Thất Bại",
                        "message": "Không thể xác thực người dùng",
                    },
                )

            time_from_token, public_key, order_id = decoded_data.split(" | ")
            time_from_token = float(time_from_token)

            current_date = datetime.now().date()
            token_date = datetime.fromtimestamp(time_from_token).date()

            if current_date != token_date:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Đơn Hàng Thất Bại",
                        "message": "Đường dẫn xác nhận đơn hàng đã hết hạn.",
                    },
                )

            order = request.env["sale.order"].sudo().browse(int(order_id))
            if not order:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Đơn Hàng Thất Bại",
                        "message": "Đơn hàng không được tìm thấy!",
                    },
                )
            # Check OTP
            opt_id = request.env["otp.verification"].sudo().search([
                ('sale_order_id.id', '=', int(order_id)),
                ('otp', '=', otp),
            ])
            if not opt_id:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Đơn Hàng Thất Bại",
                        "message": "OTP không đúng!",
                    },
                )
            otp_state, otp_msg = opt_id.get_state_otp()
            if not otp_state:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Đơn Hàng Thất Bại",
                        "message": otp_msg,
                    },
                )

            if order.state not in ['draft', 'sent']:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Giao Hàng Thất Bại",
                        "message": "Đơn hàng ở trạng thái không thể xác nhận!",
                    },
                )

            order.public_confirm(opt_id)
            order.send_message_w_trigger()

            return request.render(
                "confirm_order_process.order_confirmation_notify_template",
                {
                    "title": "Xác Nhận Đơn Hàng Thành Công",
                    "message": f"Đơn hàng {order.name} của bạn đã được xác nhận thành công!",
                },
            )

        except Exception as e:
            _logger.error(f"Error while confirming order: {e}")
            return request.render(
                "confirm_order_process.order_confirmation_notify_template",
                {
                    "title": "Xác Nhận Đơn Hàng Thất Bại",
                    "message": "Có lỗi xảy ra trong quá trình xác nhận đơn hàng.",
                },
            )
        
    @http.route(
        "/public/order/confirm-delivery",
        type="http",
        auth="public",
        website=True,
    )
    def order_delivery_page(self, **kwargs):
        try:
            token = kwargs.get("token")
            if not token:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Đường dẫn không hợp lệ",
                        "message": "Đường dẫn không hợp lệ",
                    },
                )

            secret_key_public_user = (
                request.env["ir.config_parameter"]
                .sudo()
                .get_param("confirm_order_process.serect_key_public_user", False)
            )

            decoded_data = decode_token(token, secret_key_public_user)
            if not decoded_data:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Không thể xác thực người dùng",
                        "message": "Không thể xác thực người dùng",
                    },
                )

            time_from_token, public_key, order_id = decoded_data.split(" | ")
            time_from_token = float(time_from_token)

            current_date = datetime.now().date()
            token_date = datetime.fromtimestamp(time_from_token).date()

            if current_date != token_date:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Đường dẫn đã hết hạn",
                        "message": "Đường dẫn xác nhận giao hàng đã hết hạn.",
                    },
                )

            order = request.env["sale.order"].sudo().browse(int(order_id))
            if not order:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Đơn Hàng Thất Bại",
                        "message": "Đơn hàng không được tìm thấy!",
                    },
                )

            if order.state != "sale":
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Đơn Hàng Không Thể Giao Lúc Này",
                        "message": "Đơn hàng không ở trạng thái có thể giao!",
                    },
                )
            
            otp_model = request.env['otp.verification'].sudo().search([('sale_order_id.id','=', order.id)])
            if not otp_model:
                otp_model = request.env['otp.verification'].sudo().create({
                    'sale_order_id': order.id,
                    'phone': order.partner_id.phone,
                })
                otp_model.action_send_email()

            # Dữ liệu trả về cho template
            order_data = {
                "currency": request.env.user.company_id.currency_id.currency_unit_label,
                "logo": request.env["res.company"].search([], limit=1).logo,
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
                'images': order.attachment_ids,
                "status": order.state == "sale",
                "token": token,
            }

            # TODO: Gửi OTP nếu cần thiết

            return request.render(
                "confirm_order_process.order_delivery_template", order_data
            )

        except Exception as e:
            _logger.error(f"Error during order delivery confirmation: {e}")
            return request.render(
                "confirm_order_process.order_confirmation_notify_template",
                {
                    "title": "Đường dẫn không hợp lệ",
                    "message": "Đường dẫn không hợp lệ",
                },
            )

    @http.route(
        "/public/order/confirm-delivery",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
    )
    def order_delivery(self, **kwargs):
        user_ip = request.httprequest.remote_addr
        if user_ip:
            if self._check_ip_request_limit(user_ip):
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Giao Hàng Thất Bại",
                        "message": "Bạn đã vượt quá số lần yêu cầu trong vòng 2 giờ. Vui lòng thử lại sau.",
                    },
                )
            self._log_user_ip(user_ip)
        try:
            token = kwargs.get("token")
            otp = kwargs.get("otp")

            if not token:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Giao Hàng Thất Bại",
                        "message": "Đường dẫn không hợp lệ",
                    },
                )

            if not otp:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Giao Hàng Thất Bại",
                        "message": "OTP không được cung cấp",
                    },
                )
            secret_key_public_user = (
                request.env["ir.config_parameter"]
                .sudo()
                .get_param("confirm_order_process.serect_key_public_user", False)
            )
            decoded_data = decode_token(token, secret_key_public_user)
            if not decoded_data:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Giao Hàng Thất Bại",
                        "message": "Không thể xác thực người dùng",
                    },
                )

            time_from_token, public_key, order_id = decoded_data.split(" | ")
            time_from_token = float(time_from_token)

            current_date = datetime.now().date()
            token_date = datetime.fromtimestamp(time_from_token).date()

            if current_date != token_date:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Giao Hàng Thất Bại",
                        "message": "Đường dẫn xác nhận giao hàng đã hết hạn.",
                    },
                )

            order = request.env["sale.order"].sudo().browse(int(order_id))
            if not order:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Giao Hàng Thất Bại",
                        "message": "Đơn hàng không được tìm thấy!",
                    },
                )

            # Check OTP
            opt_id = request.env["otp.verification"].sudo().search([
                ('sale_order_id.id', '=', int(order_id)),
                ('otp', '=', otp),
            ])
            if not opt_id:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Đơn Hàng Thất Bại",
                        "message": "OTP không đúng!",
                    },
                )
            otp_state, otp_msg = opt_id.get_state_otp()
            if not otp_state:
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Đơn Hàng Thất Bại",
                        "message": otp_msg,
                    },
                )

            if not (order.state_delivery not in ['done','confirm'] \
                and order.state == 'sale' and order.state_mrp == 'done'):
                return request.render(
                    "confirm_order_process.order_confirmation_notify_template",
                    {
                        "title": "Xác Nhận Giao Hàng Thất Bại",
                        "message": "Đơn hàng không ở trạng thái có thể xác nhận!",
                    },
                )

            order.public_confirm()
            order.send_message_w_trigger('delivery')

            return request.render(
                "confirm_order_process.order_confirmation_notify_template",
                {
                    "title": "Xác Nhận Giao Hàng Thành Công",
                    "message": f"Đơn hàng {order.name} của bạn đã được xác nhận giao thành công!",
                },
            )

        except Exception as e:
            _logger.error(f"Error while confirming order: {e}")
            return request.render(
                "confirm_order_process.order_confirmation_notify_template",
                {
                    "title": "Xác Nhận Giao Hàng Thất Bại",
                    "message": "Có lỗi xảy ra trong quá trình xác nhận giao hàng.",
                },
            )

    def _log_user_ip(self, user_ip):
        ip_history_model = request.env['user.ip.history'].sudo()
        ip_history_model.create({
            'user_ip': user_ip,
            'timestamp': fields.Datetime.now(),
        })

    def _check_ip_request_limit(self, user_ip):
        two_hours_ago = fields.Datetime.now() - timedelta(hours=2)
        ip_history_model = request.env['user.ip.history']
        recent_requests = ip_history_model.search_count([
            ('user_ip', '=', user_ip),
            ('timestamp', '>=', two_hours_ago)
        ])
        return recent_requests == 5

