from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    is_medical_professional = fields.Boolean(string='Medical Professional', default=False)
    medical_specialization = fields.Selection([
        ('general', 'General Practitioner'),
        ('dentist', 'Dentist'),
        ('cardiologist', 'Cardiologist'),
        ('orthopedist', 'Orthopedist'),
        ('pediatrician', 'Pediatrician'),
        ('gynecologist', 'Gynecologist'),
        ('dermatologist', 'Dermatologist'),
        ('surgeon', 'Surgeon'),
        ('anesthesiologist', 'Anesthesiologist'),
        ('radiologist', 'Radiologist'),
        ('other', 'Other')
    ], string='Specialization')
    
    license_number = fields.Char(string='Medical License Number')
    license_expiry = fields.Date(string='License Expiry Date')