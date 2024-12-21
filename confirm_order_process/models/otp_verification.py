import logging

from odoo import fields, models, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError

from ..const import generate_otp

_logger = logging.getLogger(__name__)


class OtpVerification(models.Model):
    _name = "otp.verification"
    _description = "Otp Verification"

    otp = fields.Text(string="OTP", required=True, readonly=True)
    state = fields.Selection(
        [
            ("unverified", "Chưa xác nhận"),
            ("verified", "Đã xác nhận"),
            ("expired", "Hết hạn"),
            ("rejected", "Từ chối"),
        ],
        string="Trạng thái",
        default="unverified",
        readonly=True,
    )
    phone = fields.Char(string="Điện thoại", readonly=True)
    email = fields.Char(readonly=True)
    sale_order_id = fields.Many2one("sale.order", string="Đơn bán hàng", readonly=True)
    date_end = fields.Datetime(string="Ngày hết hạn", default=datetime.now() + timedelta(minutes=10), readonly=True)

    @api.constrains("otp")
    def unit_opt_contrains(self):
        for record in self:
            if record.otp:
                if len(record.otp) != 6:
                    raise ValidationError("OTP phải có đúng 6 ký tự.")
                if not record.otp.isdigit():
                    raise ValidationError("OTP chỉ có thể là các chữ số.")

                existing_otp = self.search(
                    [
                        ("id", "!=", record.id),
                        ("otp", "=", record.otp),
                        ("sale_order_id", "=", record.sale_order_id.id),
                    ]
                )
                if existing_otp:
                    if existing_otp.state == "unverified":
                        raise ValidationError(
                            "OTP này đã tồn tại cho đơn hàng này và chưa được xác nhận."
                        )
                    if existing_otp.state == "expired":
                        raise ValidationError(
                            "OTP này đã hết hạn cho đơn hàng này và không thể sử dụng lại."
                        )
                    raise ValidationError("OTP không thể trùng trong một đơn hàng.")

    @api.model
    def create(self, values):
        if "otp" not in values or not values["otp"]:
            otp = generate_otp()
            if "sale_order_id" in values:
                existing_otp = self.search(
                    [("sale_order_id", "=", values["sale_order_id"])]
                )
                while otp in existing_otp.mapped("otp"):
                    otp = generate_otp()
            values["otp"] = otp
        return super(OtpVerification, self).create(values)

    @api.model
    def _cron_delete_verified_otp(self):
        otp = self.search([("state", "=", "verified")])
        otp.unlink()

    @api.model
    def update_expired_otps(self):
        otp_records = self.search([("state", "=", "unverified"), ("date_end", "<", fields.Datetime.now())])
        otp_records.write({"state": "expired"})

    @api.model
    def get_state_otp(self):
        msg = ""
        if self.date_end <= datetime.now() or self.state == "expired":
            self.state = "expired"
            msg = "OTP đã hết hạn!"
        elif self.state in ["rejected"]:
            msg = "OTP đã bị từ chối!"
        elif self.state in ["verified"]:
            msg = "OTP đã xác nhận!"
        if self.state not in ["verified", "rejected", "expired"]:
            return False, msg
        return True, msg

    def action_send_sms(self):
        for record in self:
            try:
                sms_env = self.env['sms.sms'].sudo()
                sever_env = self.env['sms.vi.hat.configuration'].sudo()
                sms_sever = sever_env.search([('esms_type','=',7)], limit=1)
                message_body = 'CCV: Mã OTP của bạn: %s. Mã sẽ hết hạn trong 10 phút. Vui lòng chia sẽ mã này.' % record.otp
                val = {'body' : message_body}
                if sms_sever:
                    val.update({'configuration_id' : sms_sever.id})
                else:
                    _logger.error('SMS Server OTP chưa được cấu hình!!!')
                val.update({'number' : record.phone if record.phone else ""})
                sms_sms = sms_env.create(val)
                sms_sms.send()
            except Exception as e:
                _logger.error('Error during send SMS: %s', e)
                continue

    def action_send_email(self):
        subject = "OTP"
        body = """
            Đây là OTP của bạn: <strong>%s</strong>
        """ % self.otp
        to_email = self.email
        from_email = self.email

        mail_values = {
            "subject": subject,
            "body_html": body,
            "email_from": from_email,
            "email_to": to_email,
        }

        try:
            mail = self.env["mail.mail"].sudo().create(mail_values)
            mail.send()
            return True
        except Exception as e:
            _logger.error(f"Error sending email: {str(e)}")
            return False
