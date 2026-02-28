from odoo import models, fields, api
import pytz
import logging

_logger = logging.getLogger(__name__)

TIMEZONE = 'Asia/Kolkata'
SHIFT_START = 18  # 6 PM IST
SHIFT_END = 3     # 3 AM IST


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    is_night_shift = fields.Boolean(
        string='Night Shift',
        compute='_compute_is_night_shift',
        store=True,
        index=True,
    )

    @api.depends('check_in')
    def _compute_is_night_shift(self):
        tz = pytz.timezone(TIMEZONE)
        for rec in self:
            if not rec.check_in:
                rec.is_night_shift = False
                continue
            try:
                local = rec.check_in.replace(tzinfo=pytz.utc).astimezone(tz)
                h = local.hour
                # 18-23 = evening start, 0-3 = early morning tail
                rec.is_night_shift = (h >= SHIFT_START) or (h <= SHIFT_END)
            except Exception as e:
                _logger.warning("Night shift compute error %s: %s", rec.id, e)
                rec.is_night_shift = False
