from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AppointmentRescheduleWizard(models.TransientModel):
    _name = 'clinic.appointment.reschedule.wizard'
    _description = 'Reschedule Appointment Wizard'
    
    appointment_id = fields.Many2one('clinic.appointment', string='Appointment', readonly=True)
    patient_id = fields.Many2one(related='appointment_id.patient_id', readonly=True)
    doctor_id = fields.Many2one(related='appointment_id.doctor_id', readonly=True)
    old_date = fields.Datetime(related='appointment_id.date', string='Current Date', readonly=True)
    
    new_date = fields.Datetime(string='New Date & Time', required=True)
    reason = fields.Text(string='Reason for Rescheduling')
    notify_patient = fields.Boolean(string='Notify Patient', default=True)
    
    @api.constrains('new_date')
    def _check_new_date(self):
        for wizard in self:
            if wizard.new_date <= fields.Datetime.now():
                raise ValidationError(_('Please select a future date and time.'))
    
    def action_reschedule(self):
        self.ensure_one()
        # Log the change
        self.appointment_id.message_post(
            body=f"Appointment rescheduled from {self.old_date} to {self.new_date}. Reason: {self.reason or 'Not specified'}"
        )
        
        # Update appointment
        self.appointment_id.write({
            'date': self.new_date,
            'state': 'draft' if self.appointment_id.state == 'confirmed' else self.appointment_id.state
        })
        
        # Notify patient if requested
        if self.notify_patient:
            # Send notification email/SMS
            pass
        
        return {'type': 'ir.actions.act_window_close'}


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
