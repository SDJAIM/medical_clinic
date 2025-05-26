from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    patient_id = fields.Many2one('clinic.patient', string='Patient')
    treatment_id = fields.Many2one('clinic.treatment', string='Treatment')
    insurance_claim_ids = fields.One2many('clinic.insurance.claim', 'invoice_id', string='Insurance Claims')
