from odoo import http
from odoo.http import request
import json

class DailySubmissionController(http.Controller):
    
    @http.route('/daily-submission', type='http', auth='public', website=True, csrf=False)
    def daily_submission_form(self, **kw):
        """Render the daily submission form page"""
        return request.render('daily_submission_form.daily_submission_page', {})
    
    @http.route('/daily-submission/submit', type='json', auth='public', methods=['POST'], csrf=False)
    def submit_daily_form(self, **post):
        """Handle form submission"""
        try:
            # Create the submission record
            submission = request.env['daily.submission'].sudo().create({
                # 'name': post.get('name'),
                # 'phone': post.get('phone'),
                # 'email': post.get('email'),
                # 'company': post.get('company'),
                # 'subject': post.get('subject'),
                # 'latitude': float(post.get('latitude', 0)),
                # 'longitude': float(post.get('longitude', 0)),

                'crane_name' : post.get('crane_name'),
                'x_date_time' : post.get('x_date_time'),
                'customer_name' : post.get('customer_name'),
                'customer_mobile_number' : post.get('customer_mobile_number'),
                'operator_name' : post.get('operator_name'),
                'start_time' : post.get('start_time'),
                'close_time' : post.get('close_time'),
                'lunch' : post.get('lunch'),
                'working_photo' : post.get('working_photo'),
                'payment' : post.get('payment'),
                'operator_selfie' : post.get('operator_selfie'),
                'work_nature' : post.get('work_nature'),
                'operator_beta' : post.get('operator_beta'),
                'logsheet_picture' : post.get('logsheet_picture'),
                'comments_work' : post.get('comments_work'),
                'work_assigned_by' : post.get('work_assigned_by'),
                'shift_confirmed' : post.get('shift_confirmed'),
                'fill_diesel' : post.get('fill_diesel'), 

                'operator_signature': post.get('operator_signature'),
                'customer_signature': post.get('customer_signature'),
            })
            
            return {
                'success': True,
                'message': 'Thank you! Your submission has been received.',
                'submission_id': submission.id
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    @http.route('/daily-submission/thank-you', type='http', auth='public', website=True)
    def thank_you_page(self, **kw):
        """Thank you page after submission"""
        return request.render('daily_submission_form.thank_you_page', {})