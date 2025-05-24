from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    is_insurance_company = fields.Boolean(string='Is Insurance Company', default=False)
    patient_ids = fields.One2many('clinic.patient', 'partner_id', string='Patients')


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    is_medicine = fields.Boolean(string='Is Medicine', default=False)
    active_ingredient = fields.Char(string='Active Ingredient')
    medicine_category = fields.Selection([
        ('antibiotic', 'Antibiotic'),
        ('analgesic', 'Analgesic'),
        ('antiviral', 'Antiviral'),
        ('vitamin', 'Vitamin'),
        ('other', 'Other')
    ], string='Medicine Category')