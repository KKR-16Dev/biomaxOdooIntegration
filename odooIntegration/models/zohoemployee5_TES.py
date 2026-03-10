from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
import pymssql
import json
import os
import logging
import pytz
from datetime import timedelta
from pytz import timezone

_logger = logging.getLogger(__name__)

class CustomDataBiometricImport(models.Model):
    _inherit = "hr.employee"

    # zoho_employee_id = fields.Integer(string="Zoho ID")
    zoho_employee_id = fields.Char(string="Zoho ID")

    employee_dept = fields.Selection(string='Employee Dept', selection=[('dats', 'DATS'), ('tes', 'TES'), ('itdept', 'IT_Dept')], 
                                     default='dats', help='Helps in allocating the right shift during Integration')


class FetchBiomaxDataforOdoo(models.Model):
    _inherit = 'hr.attendance'

    z_device_in = fields.Char(string="Device_In")
    z_device_out = fields.Char(string="Device_Out")
    check_in = fields.Datetime(string="Check In", default=fields.Datetime.now, required=False, tracking=True)
    z_worked_hours = fields.Float( string='Exact Worked Hours', compute='_compute_z_worked_hours', store=True, readonly=True )

    employee_dept = fields.Selection(string='Employee Dept', readonly=True,
                                     selection=[('dats', 'DATS'), ('tes', 'TES'), ('itdept', 'IT_Dept')], 
                                     default='dats', help='Helps in allocating the right shift during Integration',
                                     related='employee_id.employee_dept',)
                                     

    tes_night_shift_day = fields.Date(
        string='TES Night Shift Day',
        compute='_compute_tes_night_shift_day',
        store=True
    )


    @api.depends('check_in')
    def _compute_tes_night_shift_day(self):
        for rec in self:
            if rec.check_in:
                user_tz = pytz.timezone(self.env.user.tz or 'Asia/Kolkata')
                check_in_utc = pytz.utc.localize(rec.check_in)
                check_in_local = check_in_utc.astimezone(user_tz)
                hour = check_in_local.hour
                if hour < 4:
                    rec.tes_night_shift_day = (check_in_local - timedelta(days=1)).date()
                elif hour >= 16:
                    rec.tes_night_shift_day = check_in_local.date()
                else:
                    rec.tes_night_shift_day = False
            else:
                rec.tes_night_shift_day = False
    

    @api.depends('check_in', 'check_out')
    def _compute_z_worked_hours(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                delta = rec.check_out - rec.check_in
                raw_hours = delta.total_seconds() / 3600.0
                rec.z_worked_hours = round(raw_hours, 2)
            else:
                rec.z_worked_hours = 0.0


    
    def biomaxOdooIntegrationMains(self):
        ReturnValueA = self.attempt_db_connection()
        UpReturnValueA = self.add_odoo_employee_ids(ReturnValueA)  # Add this line
        # self.save_output_to_file(UpReturnValueA)
        self.getandprocess_biomax_data(UpReturnValueA)


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
        # sql_query = "SELECT * FROM dbo.parallel_clone2 WHERE employeeID IN (1059) AND DeviceName IN ('Kavi Workstation', 'Korkai In Door', 'Korkai Out Door', 'Vanji Out Door', 'Vanji In Door', 'Thanjai In Door', 'Thanjai Out Door', 'Extended Team In', 'Extended Team Out' ) AND eventTime >= '2025-12-01 00:00:00' AND eventTime <  '2026-02-01 00:00:00' ORDER BY eventTime;"
        # sql_query = "SELECT * FROM dbo.parallel_clone2 WHERE employeeID IN (1027) AND DeviceName IN ( 'DATS In', 'DATS Out', 'Kavi Workstation', 'Kavi In', 'Facility In', 'Facility Out', 'TES Server Room', 'Korkai In Door','Korkai Out Door', 'Vanji Out Door','Vanji In Door', 'Thanjai In Door','Thanjai Out Door', 'Extended Team In','Extended Team Out' ) AND eventTime >= '2025-12-01 00:00:00' AND eventTime <  '2026-02-01 00:00:00' ORDER BY eventTime;"
        sql_query = "SELECT * FROM dbo.parallel_clone2 WHERE employeeID IN (1035) AND DeviceName IN ('Kavi Workstation', 'Kavi In', 'Facility In', 'Facility Out', 'TES Server Room', 'Korkai In Door','Korkai Out Door', 'Vanji Out Door','Vanji In Door', 'Thanjai In Door','Thanjai Out Door', 'Extended Team In','Extended Team Out' ) AND eventTime >= '2025-12-01 00:00:00' AND eventTime <  '2026-02-01 00:00:00' ORDER BY eventTime;"


        try:
            # --- 1. ESTABLISH CONNECTION ---
            connection = pymssql.connect(
                server='192.168.1.74', 
                port=1433,
                user='testteam',
                password='Kavi@123',
                database='DestDB2',
                timeout=20,
                login_timeout=20
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
            # print(success_result)
            # Call the function
            # self.save_output_to_file(success_result)
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
    
    
    @staticmethod
    def save_output_to_file(success_result, filename="Upoutput2.json"):
        from datetime import datetime
        
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.strftime('%Y-%m-%d %H:%M:%S')
                return super().default(obj)
        
        # Convert Python object to JSON text with custom encoder
        data_str = json.dumps(success_result, indent=4, cls=DateTimeEncoder)

        # Get full path on your local system
        file_path = os.path.join(os.getcwd(), filename)

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(data_str)

        print(f"File saved successfully at: {file_path}")


    def add_odoo_employee_ids(self, success_result):
        print("\n"*5,"Entered The Updation Block: ","\n"*5)
        """
        Adds 'odoo_emp_id' key to each record in success_result['data']
        by matching JSON's 'employeeID' with Odoo's 'zoho_employee_id' field.
        """
        if not success_result.get('success') or not success_result.get('data'):
            _logger.warning("No data to process for adding Odoo employee IDs")
            return success_result
        
        biomax_records = success_result['data']
        _logger.info("Starting to add Odoo employee IDs to %d records.", len(biomax_records))
        
        # Fetch all employees with zoho_employee_id
        employee_model = self.env['hr.employee']
        employees = employee_model.search([('zoho_employee_id', '!=', False)])
        
        # Create a mapping: zoho_employee_id (as string) -> Odoo employee ID (integer)
        employee_id_map = {
            str(emp.zoho_employee_id): emp.id 
            for emp in employees
        }
        
        _logger.info("Created employee ID map with %d entries.", len(employee_id_map))
        
        # Process each record and add odoo_emp_id
        matched_count = 0
        unmatched_count = 0
        
        for record in biomax_records:
            employee_id_raw = record.get('employeeID')
            
            if not employee_id_raw:
                _logger.warning("Record missing 'employeeID' field: %s", record)
                record['odoo_emp_id'] = None
                unmatched_count += 1
                continue
            
            # Convert to string and strip whitespace for matching
            employee_id_str = str(employee_id_raw).strip()
            
            # Look up in the map
            if employee_id_str in employee_id_map:
                odoo_emp_id = employee_id_map[employee_id_str]
                record['odoo_emp_id'] = odoo_emp_id
                matched_count += 1
                _logger.debug("Matched employeeID '%s' to Odoo employee ID %d", employee_id_str, odoo_emp_id)
            else:
                record['odoo_emp_id'] = None
                unmatched_count += 1
                _logger.warning("No Odoo employee found for employeeID '%s'", employee_id_str)
        
        _logger.info("Finished adding Odoo employee IDs. Matched: %d, Unmatched: %d", matched_count, unmatched_count)
        return success_result


    def getandprocess_biomax_data(self, success_result):
        """
        Processes Biomax data and creates/updates attendance records in Odoo
        """
        if not success_result.get('success') or not success_result.get('data'):
            _logger.warning("No data received or connection failed: %s", success_result.get('message', 'Unknown error'))
            return False

        biomax_records = success_result['data']
        _logger.info("Starting processing of %d Biomax records.", len(biomax_records))
        
        # CRITICAL FIX: Sort records by eventTime in chronological order
        # This ensures check-ins and check-outs are processed in the correct sequence
        try:
            biomax_records_sorted = sorted(
                biomax_records, 
                key=lambda x: x.get('eventTime') if isinstance(x.get('eventTime'), datetime) 
                else datetime.strptime(x.get('eventTime'), '%Y-%m-%d %H:%M:%S')
            )
            _logger.info("✓ Records sorted chronologically by eventTime")
        except Exception as e:
            _logger.error("Failed to sort records: %s. Processing in original order.", str(e))
            biomax_records_sorted = biomax_records
        
        # Use the local timezone of the MSSQL server
        LOCAL_TZ = timezone('Asia/Kolkata')
        
        processed_count = 0
        skipped_count = 0
        checkin_count = 0
        checkout_count = 0
        
        for record in biomax_records_sorted:  # Use sorted records
            # Get odoo_emp_id from the record
            odoo_emp_id = record.get('odoo_emp_id')
            
            # Skip if odoo_emp_id is null/None
            if odoo_emp_id is None:
                _logger.warning("Skipping record: odoo_emp_id is null for employeeID '%s'", record.get('employeeID'))
                skipped_count += 1
                continue
            
            # Get other required fields
            employee_id_str = str(record.get('employeeID', '')).strip()
            event_time_raw = record.get('eventTime')
            is_checkin_str = str(record.get('isCheckin', '')).strip()
            device_name = record.get('DeviceName', '')  # Extract DeviceName from JSON
            
            # Validate eventTime
            if not event_time_raw:
                _logger.warning("Skipping record: Missing 'eventTime' for Employee ID %s (Odoo ID: %s)", 
                            employee_id_str, odoo_emp_id)
                skipped_count += 1
                continue
            
            try:
                # Handle both string and datetime object
                if isinstance(event_time_raw, datetime):
                    event_time_dt = event_time_raw
                elif isinstance(event_time_raw, str):
                    event_time_dt = datetime.strptime(event_time_raw, '%Y-%m-%d %H:%M:%S')
                else:
                    _logger.error("Unexpected eventTime type '%s' for employee ID %s (Odoo ID: %s)", 
                                type(event_time_raw).__name__, employee_id_str, odoo_emp_id)
                    skipped_count += 1
                    continue
                
                # Localize the naive datetime object (add timezone info)
                local_dt = LOCAL_TZ.localize(event_time_dt)
                
                # Convert to UTC (Required for Odoo database storage)
                utc_dt = local_dt.astimezone(timezone('UTC'))
                
                # Format the UTC datetime object back into a string for Odoo's fields
                utc_time_str = utc_dt.strftime('%Y-%m-%d %H:%M:%S')
                
            except Exception as e:
                _logger.error("Failed to process eventTime '%s' for employee ID %s (Odoo ID: %s). Error: %s", 
                            event_time_raw, employee_id_str, odoo_emp_id, str(e))
                skipped_count += 1
                continue
            
            # Process based on isCheckin value
            if is_checkin_str == '1':
                # CHECK-IN: Create new attendance record
                try:
                    self.env['hr.attendance'].create({
                        'employee_id': odoo_emp_id,
                        'check_in': utc_time_str,
                        'z_device_in': device_name,
                    })
                    _logger.info("✓ Created CHECK-IN for Employee ID %s (Odoo ID: %s) at %s UTC from device '%s'", 
                            employee_id_str, odoo_emp_id, utc_time_str, device_name)
                    checkin_count += 1
                    processed_count += 1
                    
                except Exception as e:
                    _logger.error("Failed to create CHECK-IN for Employee ID %s (Odoo ID: %s). Error: %s", 
                                employee_id_str, odoo_emp_id, str(e))
                    skipped_count += 1
                    
            elif is_checkin_str == '0':
                # CHECK-OUT: Update latest open attendance record
                try:
                    from datetime import timedelta
                    
                    # Calculate the maximum allowed check-in time (24 hours before check-out)
                    utc_dt_obj = datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S')
                    max_checkin_time = (utc_dt_obj - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Find the latest open attendance record for this employee
                    latest_attendance = self.env['hr.attendance'].search([
                        ('employee_id', '=', odoo_emp_id),
                        ('check_out', '=', False),
                        ('check_in', '<=', utc_time_str),  # Check-in must be before check-out
                        ('check_in', '>=', max_checkin_time)  # Check-in must be within last 24 hours
                    ], limit=1, order='check_in DESC')
                    
                    if latest_attendance:
                        latest_attendance.write({
                            'check_out': utc_time_str,
                            'z_device_out': device_name,
                        })
                        _logger.info("✓ Updated CHECK-OUT for Employee ID %s (Odoo ID: %s) - Check-in: %s → Check-out: %s UTC from device '%s'", 
                                employee_id_str, odoo_emp_id, latest_attendance.check_in, utc_time_str, device_name)
                        checkout_count += 1
                        processed_count += 1
                    else:
                        _logger.warning("Could not find an open CHECK-IN record within 24 hours for Employee ID %s (Odoo ID: %s) to process CHECK-OUT at %s", 
                                    employee_id_str, odoo_emp_id, utc_time_str)
                        skipped_count += 1
                        
                except Exception as e:
                    _logger.error("Failed to update CHECK-OUT for Employee ID %s (Odoo ID: %s). Error: %s", 
                                employee_id_str, odoo_emp_id, str(e))
                    skipped_count += 1
            else:
                _logger.warning("Skipping record: Invalid 'isCheckin' value '%s' for Employee ID %s (Odoo ID: %s)", 
                            is_checkin_str, employee_id_str, odoo_emp_id)
                skipped_count += 1
        
        _logger.info("=" * 80)
        _logger.info("Processing Summary:")
        _logger.info("  Total Records: %d", len(biomax_records))
        _logger.info("  Processed Successfully: %d", processed_count)
        _logger.info("    - Check-ins Created: %d", checkin_count)
        _logger.info("    - Check-outs Updated: %d", checkout_count)
        _logger.info("  Skipped: %d", skipped_count)
        _logger.info("From ZohoEmployees4_DATS code")
        _logger.info("=" * 80)
        
        return True