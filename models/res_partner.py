from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    is_insurance_company = fields.Boolean(string='Is Insurance Company', default=False)
    patient_ids = fields.One2many('clinic.patient', 'partner_id', string='Patients')
    
    # Add count field for UI
    patient_count = fields.Integer(compute='_compute_patient_count', string='Patient Count')
    
    def _compute_patient_count(self):
        for partner in self:
            partner.patient_count = len(partner.patient_ids)
    
    def action_view_patients(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Patients',
            'res_model': 'clinic.patient',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }
