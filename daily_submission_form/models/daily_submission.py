from odoo import models, fields, api
from odoo.exceptions import ValidationError

class DailySubmission(models.Model):
    _name = 'daily.submission'
    _description = 'Daily Submission Form'
    _order = 'create_date desc'
    
    name = fields.Char(string='Your Name', required=True)
    # phone = fields.Char(string='Phone Number')
    # email = fields.Char(string='Your Email', required=True)
    # company = fields.Char(string='Your Company')
    # subject = fields.Char(string='Subject', required=True)
    # latitude = fields.Float(string='Latitude', digits=(10, 7))
    # longitude = fields.Float(string='Longitude', digits=(10, 7))
    # location_string = fields.Char(string='Location', compute='_compute_location_string', store=True)
    submission_date = fields.Datetime(string='Submission Date', default=fields.Datetime.now)
    operator_signature = fields.Binary(string="Operator Signature", help="Signature of the Operator")
    customer_signature = fields.Binary(string="Customer Signature", help="Signature of the Customer")



    crane_name = fields.Char(string='Boom Lift/Crane Name')
    x_date_time = fields.Datetime(string='Date Time')
    customer_name = fields.Char(string='Customer Name')
    customer_mobile_number = fields.Integer(string='Mobile Number')
    operator_name = fields.Char(string='Operator Name')
    start_time = fields.Datetime(string="Starting Time", help="Start Time in HH:MM:SS")
    close_time = fields.Datetime(string="Closing Time", help="Closing Time in HH:MM:SS")
    lunch = fields.Char(string='Lunch')
    working_photo = fields.Binary( string="Working Photo" )
    payment = fields.Selection([('received','Received'),
                                ('not received','Not Received'),],
                                string="Payment")
    operator_selfie = fields.Binary( string="Operator Selfie" )
    work_nature = fields.Char(string='Work Nature')
    operator_beta = fields.Selection([('yes','Yes'), ('no','No'),], string="Operator Beta")
    logsheet_picture = fields.Binary( string="Logsheet Picture" )
    comments_work = fields.Binary( string="Comments Of Work" )
    work_assigned_by = fields.Selection([('kannan', 'Kannan'),
                                        ('archana', 'Archana'), 
                                        ('rajesh agarwal','Rajesh Agarwal'),
                                        ('ajith','Ajith'),
                                        ('sanjay','Sanjay'),
                                        ('avinash','Avinash'),], string="Work Assigned By" )
    shift_confirmed = fields.Boolean(string="Confirm Shift")
    fill_diesel = fields.Boolean( string="Fill Diesel")




    # @api.depends('latitude', 'longitude')
    # def _compute_location_string(self):
    #     for record in self:
    #         if record.latitude and record.longitude:
    #             record.location_string = f"Lat: {record.latitude:.6f}, Lng: {record.longitude:.6f}"
    #         else:
    #             record.location_string = "Location not captured"
    
    @api.constrains('email')
    def _check_email(self):
        for record in self:
            if record.email and '@' not in record.email:
                raise ValidationError("Please enter a valid email address.")