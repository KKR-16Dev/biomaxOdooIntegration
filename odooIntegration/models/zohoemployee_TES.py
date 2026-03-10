from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
import pymssql
import json
import logging


class FetchBiomaxDataforOdooTES(models.Model):
    _inherit = 'hr.attendance'


    @api.model
    def attempt_db_connection(self):
        print("\n"*5, "Entered Integration and Query Logic", "\n"*5)
        
        # Define the final structure for success
        success_result = {
            'success': True,
            'message': 'Successfully connected and retrieved data.',
            'data': []
        }
        
        # Define the SQL Query
        sql_query = "SELECT * FROM [BiometricDB_Test].[dbo].[parallel_clone] where employeeID in (1027, 1115, 1126, 1014, 1276) and DeviceName IN ('Korkai Out Door','Korkai In Door','Thanjai In Door','Thanjai Out Door','Vanji In Door','Vanji Out Door','Kaayal In Door','Kaayal Out Door') ORDER BY eventTime;"
        
        try:
            # --- 1. ESTABLISH CONNECTION ---
            connection = pymssql.connect(
                server='192.168.1.74', 
                port=1433,
                user='testteam',
                password='Kavi@123',
                database='BiometricDB_Test',
                timeout=10,
                login_timeout=10
            )
            
            # --- 2. EXECUTE QUERY AND FETCH DATA ---
            with connection: 
                # Create a cursor object
                cursor = connection.cursor(as_dict=True) # <-- Use as_dict=True for easy JSON conversion!
                
                # Execute the query
                cursor.execute(sql_query)
                
                # Fetch all rows. If as_dict=True, this returns a list of dictionaries.
                data_rows = cursor.fetchall()
                
                # Get the column names (keys)
                # If as_dict=True is used, the data_rows are already dictionaries, 
                # so the conversion step below is slightly simplified.
                
                # Store the data in the success result structure
                success_result['data'] = data_rows
                
                print("\n"*5, "Query successful and data fetched.", "\n"*5)
                
            # --- 3. RETURN SUCCESS RESULT ---
            print(f"Returning successful result with {len(success_result['data'])} records.")
            print(success_result)
            return success_result
                
        except Exception as e:
            # --- 4. HANDLE EXCEPTION ---
            failure_result = {
                'success': False,
                'message': f'Connection or Query failed: {str(e)}',
                'data': []
            }
            print("\n"*5, "Entered Exception", "\n"*5)
            print(f"Returning failure result: {failure_result}")
            return failure_result