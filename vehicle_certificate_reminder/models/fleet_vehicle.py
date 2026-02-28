from odoo import models, fields, api
from datetime import timedelta

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'
    
    # FC Certificate
    fc_certificate = fields.Binary(string='FC Certificate', attachment=True)
    fc_certificate_name = fields.Char(string='FC Certificate Filename')
    fc_expiry_date = fields.Date(string='FC Expiry Date')
    fc_reminder_sent = fields.Boolean(string='FC Reminder Sent', default=False)
    
    # Insurance Certificate
    insurance_certificate = fields.Binary(string='Insurance Certificate', attachment=True)
    insurance_certificate_name = fields.Char(string='Insurance Certificate Filename')
    insurance_expiry_date = fields.Date(string='Insurance Expiry Date')
    insurance_reminder_sent = fields.Boolean(string='Insurance Reminder Sent', default=False)
    
    # Battery Certificate
    battery_certificate = fields.Binary(string='Battery Certificate', attachment=True)
    battery_certificate_name = fields.Char(string='Battery Certificate Filename')
    battery_expiry_date = fields.Date(string='Battery Expiry Date')
    battery_reminder_sent = fields.Boolean(string='Battery Reminder Sent', default=False)
    
    @api.onchange('fc_expiry_date')
    def _onchange_fc_expiry_date(self):
        """Reset reminder flag when date changes"""
        if self.fc_expiry_date:
            self.fc_reminder_sent = False
    
    @api.onchange('insurance_expiry_date')
    def _onchange_insurance_expiry_date(self):
        if self.insurance_expiry_date:
            self.insurance_reminder_sent = False
    
    @api.onchange('battery_expiry_date')
    def _onchange_battery_expiry_date(self):
        if self.battery_expiry_date:
            self.battery_reminder_sent = False


    def _check_certificate_expiry(self):
        """
        Scheduled action to check certificate expiry dates
        and create activities/notifications 3 days before expiry
        """
        today = fields.Date.today()
        reminder_date = today + timedelta(days=3)
        
        vehicles = self.search([
            '|', '|',
            ('fc_expiry_date', '=', reminder_date),
            ('insurance_expiry_date', '=', reminder_date),
            ('battery_expiry_date', '=', reminder_date)
        ])
        
        for vehicle in vehicles:
            # Check FC Certificate
            if vehicle.fc_expiry_date == reminder_date and not vehicle.fc_reminder_sent:
                self._create_expiry_activity(
                    vehicle, 
                    'FC Certificate', 
                    vehicle.fc_expiry_date
                )
                vehicle.fc_reminder_sent = True
            
            # Check Insurance Certificate
            if vehicle.insurance_expiry_date == reminder_date and not vehicle.insurance_reminder_sent:
                self._create_expiry_activity(
                    vehicle, 
                    'Insurance Certificate', 
                    vehicle.insurance_expiry_date
                )
                vehicle.insurance_reminder_sent = True
            
            # Check Battery Certificate
            if vehicle.battery_expiry_date == reminder_date and not vehicle.battery_reminder_sent:
                self._create_expiry_activity(
                    vehicle, 
                    'Battery Certificate', 
                    vehicle.battery_expiry_date
                )
                vehicle.battery_reminder_sent = True
    
    def _create_expiry_activity(self, vehicle, certificate_type, expiry_date):
        """Create an activity for certificate expiry reminder"""
        activity_type = self.env.ref('mail.mail_activity_data_todo')
        
        # Get the vehicle manager or fleet manager
        user_id = vehicle.driver_id.user_id.id if vehicle.driver_id and vehicle.driver_id.user_id else self.env.user.id
        
        self.env['mail.activity'].create({
            'activity_type_id': activity_type.id,
            'summary': f'{certificate_type} Expiring Soon',
            'note': f'The {certificate_type} for vehicle {vehicle.name} (License Plate: {vehicle.license_plate}) will expire on {expiry_date}. Please renew it urgently.',
            'res_id': vehicle.id,
            'res_model_id': self.env['ir.model']._get('fleet.vehicle').id,
            'user_id': user_id,
            'date_deadline': expiry_date,
        })
        
        # Also send a notification
        vehicle.message_post(
            body=f'⚠️ Reminder: {certificate_type} will expire in 3 days (on {expiry_date}). Please take necessary action.',
            subject=f'{certificate_type} Expiry Reminder',
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )