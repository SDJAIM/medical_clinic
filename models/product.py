from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    is_medicine = fields.Boolean(string='Is Medicine', default=False,
                                help='Check if this product is a medicine')
    
    medicine_type = fields.Selection([
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('syrup', 'Syrup'),
        ('injection', 'Injection'),
        ('ointment', 'Ointment'),
        ('drops', 'Drops'),
        ('inhaler', 'Inhaler'),
        ('other', 'Other')
    ], string='Medicine Type')
    
    active_ingredient = fields.Char(string='Active Ingredient')
    dosage_form = fields.Char(string='Dosage Form')
    manufacturer = fields.Char(string='Manufacturer')
    
class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    # Inherit is_medicine from template
    is_medicine = fields.Boolean(related='product_tmpl_id.is_medicine', 
                                readonly=True, store=True)
