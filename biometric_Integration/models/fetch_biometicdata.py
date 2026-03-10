from odoo import models, fields, api
from datetime import datetime
import csv
from itertools import islice
import pdb 

class CustomDataBiometricImport(models.Model):
    _inherit = "hr.attendance"

    device_name = fields.Char(string="Devices")
    machine_name = fields.Char(string="Machine") 
    
    def import_biometric_data(self):
        print("\n"*5,"YESSSSSSSSSSSSSSSSSSSSSSSSSSSSS","\n"*5)
        # file_path = "C:/Users/KishorRamesh/Downloads/BiometricData2.csv.csv"
        file_path = "C:\Users\KishorRamesh\Downloads\BiometricData2.xlxs"
        unique_values = set() 

        with open(file_path, "r", encoding="utf-8") as csvfile:
            csv_reader = csv.reader(csvfile)
            header = next(csv_reader)  # skip header
            column_index = 0

            # Employee Creation CODE 
            for row in csv_reader:
                if row:  # make sure row is not empty
                    unique_values.add(row[column_index])
            unique_list = list(unique_values)

            for value in unique_list:
                self.env['hr.employee'].create({'name': value})
                print("Employee created with the name: ",value)

            # Attendance Creation CODE 
            for row in csv_reader:
                employee_id, event_time, is_checkin = row[0], row[1], row[2]
                dt = datetime.strptime(event_time, "%d-%m-%Y %H:%M:%S")

                employee = self.env['hr.employee'].search([('name', '=', employee_id)], limit=1)
                print("Employee :",employee.name)

                if not employee:
                    print(f"Employee {employee_id} not found, skipping...")
                    continue
                    
                print("DATETIME : ",dt)
                print("ISCHECKIN : ",is_checkin)
                if is_checkin == '1':
                    print("FROM CHECK-IN")
                    self.env['hr.attendance'].create({
                        'employee_id': int(employee),
                        'check_in': dt,
                    })
                    
                elif is_checkin == '0':
                    print("FROM CHECK-OUT")
                    self.env['hr.attendance'].create({
                        'employee_id': employee.id,   # must pass ID, not recordset
                        'check_out': dt,
                    })  

        
    # self.env['hr.employee'].import_biometric_data()
