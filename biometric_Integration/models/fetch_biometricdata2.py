from odoo import models, fields, api
from datetime import datetime
import csv
import pytz
import logging

_logger = logging.getLogger(__name__)

class CustomDataBiometricImport(models.Model):
    _inherit = "hr.attendance"

    device_name = fields.Char(string="Devices")
    machine_name = fields.Char(string="Machine")

    def import_biometric_data(self):
        _logger.info("🚀 Starting biometric data import...")
        hr_attendance = self.env['hr.attendance']
        hr_employee = self.env['hr.employee']

        # ⚙️ File path - get from system parameters or use fallback
        file_path = self.env['ir.config_parameter'].sudo().get_param('biometric.file_path')
        if not file_path:
            file_path = "C:/Users/KishorRamesh/Downloads/BiometricData_sample.csv"
            _logger.warning("⚠️ Using fallback file path. Configure 'biometric.file_path' in System Parameters.")

        if not file_path:
            _logger.error("❌ File path not configured. Set 'biometric.file_path' in System Parameters.")
            return

        # ------------------------------------------
        # Step 1: Read and process CSV data
        # ------------------------------------------
        attendance_data = []
        unique_employees = set()
        
        try:
            with open(file_path, "r", encoding="utf-8") as csvfile:
                # 🧠 Detect delimiter automatically
                sample = csvfile.read(2048)
                csvfile.seek(0)
                dialect = csv.Sniffer().sniff(sample, delimiters="\t,;")
                csv_reader = csv.reader(csvfile, dialect)

                header = next(csv_reader, None)
                _logger.info(f"CSV Header: {header}")

                for row in csv_reader:
                    if not row or len(row) < 3:
                        continue

                    employee_code = row[0].strip()
                    event_time = row[1].strip()
                    is_checkin = row[2].strip()
                    
                    # Extract additional fields if available
                    device_name = row[7].strip() if len(row) > 7 and row[7] != 'NULL' else None
                    machine_id = row[6].strip() if len(row) > 6 and row[6] != 'NULL' else None

                    if not employee_code or not event_time or is_checkin not in ['0', '1']:
                        _logger.warning(f"⚠️ Invalid data in row: {row}")
                        continue

                    # Parse datetime
                    try:
                        dt = datetime.strptime(event_time, "%d-%m-%Y %H:%M:%S")
                    except ValueError:
                        _logger.warning(f"⚠️ Invalid datetime format for employee {employee_code}: {event_time}")
                        continue

                    # Convert IST → UTC
                    ist = pytz.timezone("Asia/Kolkata")
                    dt_utc = ist.localize(dt).astimezone(pytz.utc).replace(tzinfo=None)

                    attendance_data.append({
                        'employee_code': employee_code,
                        'datetime_utc': dt_utc,
                        'is_checkin': is_checkin,
                        'device_name': device_name,
                        'machine_id': machine_id
                    })
                    unique_employees.add(employee_code)

        except Exception as e:
            _logger.error(f"❌ Error reading file: {e}")
            return

        # Sort attendance data by employee and datetime to process chronologically
        attendance_data.sort(key=lambda x: (x['employee_code'], x['datetime_utc']))
        _logger.info(f"Found {len(attendance_data)} attendance records for {len(unique_employees)} unique employees.")

        # ------------------------------------------
        # Step 2: Create employees if they don't exist
        # ------------------------------------------
        for emp_code in unique_employees:
            existing_emp = hr_employee.search([('name', '=', emp_code)], limit=1)
            if not existing_emp:
                hr_employee.create({'name': emp_code})
                _logger.info(f"✅ Employee created with name: {emp_code}")

        # ------------------------------------------
        # Step 3: Process attendance records according to business logic
        # ------------------------------------------
        processed_count = 0
        error_count = 0

        for record in attendance_data:
            employee_code = record['employee_code']
            dt_utc = record['datetime_utc']
            is_checkin = record['is_checkin']
            device_name = record['device_name']
            machine_id = record['machine_id']

            # Find employee
            employee = hr_employee.search([('name', '=', employee_code)], limit=1)
            if not employee:
                _logger.warning(f"⚠️ Employee {employee_code} not found, skipping record.")
                error_count += 1
                continue

            _logger.info(f"Processing {employee.name} at {dt_utc} (is_checkin={is_checkin})")

            try:
                # Handle Check-in (is_checkin = '1')
                if is_checkin == '1':
                    # ALWAYS create a new attendance record for check-in
                    attendance_vals = {
                        'employee_id': employee.id,
                        'check_in': dt_utc,
                    }
                    
                    # Add device information if available
                    if device_name:
                        attendance_vals['device_name'] = device_name
                    if machine_id:
                        attendance_vals['machine_name'] = machine_id

                    # Use context to bypass Odoo's attendance validation
                    new_attendance = hr_attendance.with_context(
                        tracking_disable=True,
                        check_move_validity=False
                    ).create(attendance_vals)
                    
                    _logger.info(f"✅ Check-in created for {employee.name} at {dt_utc} (ID: {new_attendance.id})")
                    processed_count += 1

                # Handle Check-out (is_checkin = '0')
                elif is_checkin == '0':
                    # Find the most recent attendance record WITHOUT check_out for this employee
                    open_attendance = hr_attendance.search([
                        ('employee_id', '=', employee.id),
                        ('check_out', '=', False)
                    ], order='check_in desc', limit=1)

                    if open_attendance:
                        # Update the most recent open record with checkout time
                        checkout_vals = {'check_out': dt_utc}
                        
                        # Add device information if available and not already set
                        if device_name and not open_attendance.device_name:
                            checkout_vals['device_name'] = device_name
                        if machine_id and not open_attendance.machine_name:
                            checkout_vals['machine_name'] = machine_id

                        open_attendance.with_context(
                            tracking_disable=True,
                            check_move_validity=False
                        ).write(checkout_vals)
                        
                        _logger.info(f"✅ Check-out updated for {employee.name} at {dt_utc} (Record ID: {open_attendance.id})")
                        processed_count += 1
                    else:
                        _logger.warning(f"⚠️ No open attendance found for {employee.name} checkout at {dt_utc}. Skipping.")

            except Exception as e:
                _logger.error(f"❌ Error processing attendance for {employee.name}: {e}")
                error_count += 1
                continue

        # ------------------------------------------
        # Step 4: Summary
        # ------------------------------------------
        _logger.info(f"✅ Biometric data import completed!")
        _logger.info(f"📊 Summary: {processed_count} processed, {error_count} errors")
        
        # Return summary for UI display
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Import Completed',
                'message': f'Successfully processed {processed_count} records with {error_count} errors.',
                'type': 'success' if error_count == 0 else 'warning',
                'sticky': False,
            }
        }

    @api.model
    def clear_attendance_for_employee(self, employee_name):
        """
        Utility method to clear all attendance records for a specific employee
        Useful for testing or re-importing data
        """
        employee = self.env['hr.employee'].search([('name', '=', employee_name)], limit=1)
        if employee:
            attendance_records = self.env['hr.attendance'].search([('employee_id', '=', employee.id)])
            count = len(attendance_records)
            attendance_records.unlink()
            _logger.info(f"🗑️ Cleared {count} attendance records for employee {employee_name}")
            return count
        else:
            _logger.warning(f"⚠️ Employee {employee_name} not found")
            return 0

    @api.model
    def show_attendance_summary(self, employee_name=None):
        """
        Utility method to show attendance summary
        """
        domain = []
        if employee_name:
            employee = self.env['hr.employee'].search([('name', '=', employee_name)], limit=1)
            if employee:
                domain = [('employee_id', '=', employee.id)]
            else:
                return f"Employee {employee_name} not found"

        # Get all attendance records
        all_records = self.env['hr.attendance'].search(domain, order='employee_id, check_in')
        open_records = self.env['hr.attendance'].search(domain + [('check_out', '=', False)])
        
        summary = f"📊 Attendance Summary:\n"
        summary += f"   Total records: {len(all_records)}\n"
        summary += f"   Open records (no checkout): {len(open_records)}\n"
        
        if employee_name:
            summary += f"\n📋 Records for {employee_name}:\n"
            for record in all_records:
                checkout_str = record.check_out.strftime('%Y-%m-%d %H:%M:%S') if record.check_out else "OPEN"
                summary += f"   Check-in: {record.check_in.strftime('%Y-%m-%d %H:%M:%S')} | Check-out: {checkout_str}\n"
        
        _logger.info(summary)
        return summary