# -*- coding: utf-8 -*-
from odoo import fields, models

class CustomResCompany(models.Model):
    _inherit = "res.company"

    tmv_branch_name = fields.Char(string="Branch Name")
    tmv_ifsc = fields.Char(string="Branch IFSC")
    tmv_qr_image = fields.Binary(string="Scan to Pay QR", attachment=True)
