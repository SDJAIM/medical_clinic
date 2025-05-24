from odoo import models, fields, api

class InsuranceClaimRejectWizard(models.TransientModel):
    _name = 'clinic.insurance.claim.reject.wizard'
    _description = 'Reject Insurance Claim Wizard'
    
    claim_id = fields.Many2one('clinic.insurance.claim', string='Claim', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason', required=True)
    
    def action_reject(self):
        self.ensure_one()
        self.claim_id.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason
        })
        self.claim_id.message_post(
            body=f"Claim rejected. Reason: {self.rejection_reason}"
        )
        return {'type': 'ir.actions.act_window_close'}