from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
import pymssql
import json
import logging

class CustomDataBiometricImport(models.Model):
    _inherit = "hr.employee"

    zoho_employee_id = fields.Integer(string="Zoho ID")


class FetchBiomaxDataforOdoo(models.Model):
    _inherit = 'hr.attendance'


    @api.model
    def attempt_db_connection(self):
        print("\n"*5, "Entered Integration", "\n"*5)
        
        # Define the success result
        success_result = {
            'success': True,
            'message': 'Successfully connected to Biomax Cloud database'
        }
        
        try:
            connection = pymssql.connect(
                server='192.168.1.74', 
                port=1433,
                user='testteam',
                password='Kavi@123',
                database='BiometricDB_Test',
                timeout=10,
                login_timeout=10
            )
            
            # Connection is successful here
            with connection: 
                # The 'with' block ensures connection is closed.
                # We don't need 'pass' or other code here just to test connection.
                print("\n"*5, "Connection successful, closing connection...", "\n"*5) 
                
            # 🔑 MOVED: The return statement is OUTSIDE the 'with' block, 
            # but STILL inside the 'try' block.
            print(f"Returning successful result: {success_result}")
            return success_result
                
        except Exception as e:
            # Define the failure result
            failure_result = {
                'success': False,
                'message': f'Connection failed: {str(e)}'
            }
            print("\n"*5, "Entered Exception", "\n"*5)
            print(f"Returning failure result: {failure_result}")
            return failure_result
        
        
        # def get_biomaxcloud_data(self):
        #     data = 0
        #     return data 
