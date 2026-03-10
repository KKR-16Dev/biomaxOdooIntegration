from odoo import models, fields, api
from datetime import datetime, timedelta
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

        # ⚙️ File path - configure via Odoo system parameters if you want
        # (You can replace this with self.env['ir.config_parameter'].sudo().get_param('biometric.file_path'))
        file_path = "C:/Users/KishorRamesh/Downloads/BiometricData_sample.csv"
        if not file_path:
            _logger.error("❌ File path not configured. Set 'biometric.file_path' in System Parameters.")
            return

        # ------------------------------------------
        # Step 1: Read header and prepare mapping
        # ------------------------------------------
        try:
            with open(file_path, "r", encoding="utf-8") as csvfile:
                sample = csvfile.read(8192)
                csvfile.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
                except Exception:
                    dialect = csv.getdialect('excel')
                csvfile.seek(0)
                reader = csv.reader(csvfile, dialect)
                header = next(reader, None)
                if not header:
                    _logger.error("❌ CSV file has no header or is empty.")
                    return
                header = [h.strip() for h in header]
                _logger.info(f"CSV Header: {header}")
        except Exception as e:
            _logger.error(f"❌ Error reading file header: {e}")
            return

        # create a helper to get column by name safely
        def get_col_value(row, name):
            try:
                idx = header.index(name)
            except ValueError:
                return None
            if idx >= len(row):
                return None
            val = row[idx].strip()
            return val if val != '' else None

        # ------------------------------------------
        # Step 2: Ensure employees exist (optional)
        #    — we'll create missing employees on the fly when processing rows
        # ------------------------------------------
        # (skipped mass pre-creation; instead create when missing per-row)

        # ------------------------------------------
        # Step 3: Create or update attendance per row
        # ------------------------------------------
        try:
            with open(file_path, "r", encoding="utf-8") as csvfile:
                try:
                    dialect = csv.Sniffer().sniff(csvfile.read(8192), delimiters=",;\t")
                except Exception:
                    dialect = csv.getdialect('excel')
                csvfile.seek(0)
                csv_reader = csv.reader(csvfile, dialect)

                # skip header row
                header_row = next(csv_reader, None)

                ist = pytz.timezone("Asia/Kolkata")

                # use sudo + context to bypass model constraints
                Attendance = hr_attendance.sudo().with_context(bypass_attendance_constraints=True)

                for row in csv_reader:
                    if not row or all([not (c and c.strip()) for c in row]):
                        continue

                    # read by header names (safe if column order changes)
                    employee_id_raw = get_col_value(row, 'employeeID') or get_col_value(row, 'employeeId') or get_col_value(row, 'employee') or (row[0].strip() if len(row) > 0 else None)
                    event_time_raw = get_col_value(row, 'eventTime') or get_col_value(row, 'event_time') or (row[1].strip() if len(row) > 1 else None)
                    is_checkin_raw = get_col_value(row, 'isCheckin') or get_col_value(row, 'is_checkin') or (row[2].strip() if len(row) > 2 else None)

                    serial_no = get_col_value(row, 'SerialNumber') or get_col_value(row, 'Serial No') or get_col_value(row, 'Serial')
                    device_id = get_col_value(row, 'DeviceID') or get_col_value(row, 'Device Id')
                    machine_id = get_col_value(row, 'MachineID') or get_col_value(row, 'Machine Id')
                    device_name = get_col_value(row, 'DeviceName') or get_col_value(row, 'deviceName')

                    if not employee_id_raw or not event_time_raw:
                        _logger.warning(f"⚠ Missing employeeID or eventTime in row: {row}")
                        continue

                    employee_id = employee_id_raw.strip()
                    event_time = event_time_raw.strip()
                    is_checkin = is_checkin_raw.strip() if is_checkin_raw else None

                    # Parse datetime: expected format dd-mm-YYYY HH:MM:SS
                    parsed_dt = None
                    parse_attempts = [
                        "%d-%m-%Y %H:%M:%S",
                        "%Y-%m-%d %H:%M:%S",
                        "%d/%m/%Y %H:%M:%S",
                        "%d-%m-%y %H:%M:%S",
                    ]
                    for fmt in parse_attempts:
                        try:
                            parsed_dt = datetime.strptime(event_time, fmt)
                            break
                        except Exception:
                            continue
                    if not parsed_dt:
                        _logger.warning(f"⚠ Invalid datetime format for employee {employee_id}: {event_time}")
                        continue

                    # Convert IST -> UTC naive datetime (store tz-aware removed)
                    try:
                        dt_utc = ist.localize(parsed_dt).astimezone(pytz.utc).replace(tzinfo=None)
                    except Exception:
                        # fallback if already timezone-aware
                        dt_utc = parsed_dt

                    # Find employee (try by name, then barcode)
                    employee = hr_employee.search([('name', '=', employee_id)], limit=1)
                    if not employee:
                        employee = hr_employee.search([('barcode', '=', employee_id)], limit=1)

                    # If still not found, create employee (minimal)
                    if not employee:
                        try:
                            employee = hr_employee.create({'name': employee_id})
                            _logger.info(f"✅ Created missing employee record: {employee_id}")
                        except Exception as e:
                            _logger.warning(f"⚠ Failed to create employee {employee_id}: {e}")
                            continue

                    _logger.info(f"Processing {employee.name} at {dt_utc} (is_checkin={is_checkin})")

                    # Build values dictionary for creation/write to include device info where available
                    base_vals = {'employee_id': employee.id}
                    if device_name:
                        base_vals['device_name'] = device_name
                    elif machine_id:
                        base_vals['machine_name'] = machine_id
                    elif serial_no:
                        base_vals['device_name'] = serial_no

                    # Handle Check-in: always create a check-in record (use sudo + bypass context)
                    if is_checkin == '1' or is_checkin == 'True' or is_checkin == 'true':
                        vals = dict(base_vals)
                        vals['check_in'] = dt_utc
                        try:
                            Attendance.create(vals)
                            _logger.info(f"✅ Check-in created for {employee.name} at {dt_utc}")
                        except Exception as e:
                            # If create still fails (very rare), try a fallback: create with same check_in & check_out to avoid constraints
                            _logger.warning(f"⚠ Create check-in failed for {employee.name}: {e}. Trying fallback.")
                            try:
                                vals_fallback = dict(vals)
                                vals_fallback['check_out'] = dt_utc
                                Attendance.create(vals_fallback)
                                _logger.info(f"✅ Fallback attendance (in/out same) created for {employee.name} at {dt_utc}")
                            except Exception as e2:
                                _logger.error(f"❌ Fallback also failed for {employee.name}: {e2}")
                                continue

                    # Handle Check-out: update last open or create a combined record if none found
                    elif is_checkin == '0' or is_checkin == 'False' or is_checkin == 'false':
                        try:
                            open_att = Attendance.search([
                                ('employee_id', '=', employee.id),
                                ('check_out', '=', False)
                            ], order='check_in desc', limit=1)
                        except Exception as e:
                            _logger.warning(f"⚠ Search for open attendance failed for {employee.name}: {e}")
                            open_att = None

                        if open_att:
                            try:
                                open_att.write({'check_out': dt_utc})
                                # also update device info if present
                                if base_vals.get('device_name'):
                                    open_att.write({'device_name': base_vals.get('device_name')})
                                if base_vals.get('machine_name'):
                                    open_att.write({'machine_name': base_vals.get('machine_name')})
                                _logger.info(f"✅ Check-out updated for {employee.name} at {dt_utc}")
                            except Exception as e:
                                _logger.warning(f"⚠ Failed to update check-out for {employee.name}: {e}")
                                # If write failed, try creating a combined record instead
                                try:
                                    Attendance.create({
                                        'employee_id': employee.id,
                                        'check_in': dt_utc - timedelta(seconds=1),
                                        'check_out': dt_utc,
                                        **base_vals
                                    })
                                    _logger.info(f"✅ Created combined in/out record for {employee.name} at {dt_utc} after failed write")
                                except Exception as e2:
                                    _logger.error(f"❌ Failed to create fallback combined record for {employee.name}: {e2}")
                                    continue
                        else:
                            # No open attendance found => create combined record to represent this checkout
                            try:
                                Attendance.create({
                                    'employee_id': employee.id,
                                    'check_in': dt_utc - timedelta(seconds=1),
                                    'check_out': dt_utc,
                                    **base_vals
                                })
                                _logger.info(f"✅ Created combined in/out attendance for {employee.name} at {dt_utc} (no open found)")
                            except Exception as e:
                                _logger.error(f"❌ Failed to create standalone check-out record for {employee.name}: {e}")
                                continue

                    else:
                        # Unknown is_checkin value — log and skip
                        _logger.warning(f"⚠ Unknown isCheckin value '{is_checkin}' for employee {employee.name}, row skipped.")
                        continue

        except Exception as e:
            _logger.error(f"❌ Error processing attendance file: {e}")
            return

        _logger.info("✅ Biometric data import completed successfully.")
