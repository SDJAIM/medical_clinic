from odoo import models, fields, api

class ClinicService(models.Model):
    _name = 'clinic.service'
    _description = 'Medical Service'
    _rec_name = 'name'
    
    name = fields.Char(string='Service Name', required=True)
    code = fields.Char(string='Service Code', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    
    # Department
    department = fields.Selection([
        ('general', 'General Medicine'),
        ('dental', 'Dental'),
        ('cardiology', 'Cardiology'),
        ('orthopedics', 'Orthopedics'),
        ('pediatrics', 'Pediatrics'),
        ('gynecology', 'Gynecology'),
        ('dermatology', 'Dermatology'),
        ('laboratory', 'Laboratory'),
        ('radiology', 'Radiology'),
        ('other', 'Other')
    ], string='Department', required=True)
    
    # Service Details
    description = fields.Text(string='Description')
    is_procedure = fields.Boolean(string='Is Procedure', default=False)
    duration = fields.Float(string='Duration (hours)', default=0.5)
    
    # Pricing
    price = fields.Float(string='Price', required=True)
    insurance_coverage = fields.Boolean(string='Insurance Coverage', default=True)
    
    # Requirements
    requires_appointment = fields.Boolean(string='Requires Appointment', default=True)
    preparation_instructions = fields.Text(string='Preparation Instructions')
    
    # Consumables
    consumable_ids = fields.Many2many('product.product', 'service_consumable_rel',
                                     string='Consumables', 
                                     domain=[('type', '=', 'product')])
    
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                default=lambda self: self.env.company)
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.price = self.product_id.list_price