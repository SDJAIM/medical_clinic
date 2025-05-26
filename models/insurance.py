from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ClinicInsurance(models.Model):
    _name = 'clinic.insurance'
    _description = 'Patient Insurance'
    _rec_name = 'display_name'
    
    patient_id = fields.Many2one('clinic.patient', string='Patient', required=True, ondelete='cascade')
    insurance_company_id = fields.Many2one('res.partner', string='Insurance Company',
                                         domain=[('is_insurance_company', '=', True)], required=True)
    policy_number = fields.Char(string='Policy Number', required=True)
    group_number = fields.Char(string='Group Number')
    
    # Coverage Details
    plan_name = fields.Char(string='Plan Name')
    plan_type = fields.Selection([
        ('hmo', 'HMO'),
        ('ppo', 'PPO'),
        ('pos', 'POS'),
        ('epo', 'EPO'),
        ('private', 'Private'),
        ('government', 'Government')
    ], string='Plan Type')
    
    # Validity
    start_date = fields.Date(string='Coverage Start Date', required=True)
    end_date = fields.Date(string='Coverage End Date')
    is_active = fields.Boolean(string='Active', compute='_compute_is_active', store=True)
    
    # Coverage Amounts
    coverage_percentage = fields.Float(string='Coverage %', default=80.0)
    deductible = fields.Float(string='Annual Deductible')
    deductible_met = fields.Float(string='Deductible Met')
    max_coverage = fields.Float(string='Maximum Annual Coverage')
    copay_amount = fields.Float(string='Co-pay Amount')
    
    # Primary Insurance
    is_primary = fields.Boolean(string='Primary Insurance', default=True)
    
    # Claims
    claim_ids = fields.One2many('clinic.insurance.claim', 'insurance_id', string='Claims')
    total_claimed = fields.Float(string='Total Claimed', compute='_compute_claim_totals')
    total_approved = fields.Float(string='Total Approved', compute='_compute_claim_totals')
    remaining_coverage = fields.Float(string='Remaining Coverage', compute='_compute_claim_totals')
    
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                default=lambda self: self.env.company)
    
    @api.depends('insurance_company_id', 'policy_number')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.insurance_company_id.name} - {rec.policy_number}"
    
    @api.depends('start_date', 'end_date')
    def _compute_is_active(self):
        today = fields.Date.today()
        for rec in self:
            if rec.start_date and rec.start_date <= today:
                if rec.end_date:
                    rec.is_active = rec.end_date >= today
                else:
                    rec.is_active = True
            else:
                rec.is_active = False
    
    @api.depends('claim_ids.amount_claimed', 'claim_ids.amount_approved', 'claim_ids.state')
    def _compute_claim_totals(self):
        for rec in self:
            approved_claims = rec.claim_ids.filtered(lambda c: c.state == 'approved')
            rec.total_claimed = sum(rec.claim_ids.mapped('amount_claimed'))
            rec.total_approved = sum(approved_claims.mapped('amount_approved'))
            rec.remaining_coverage = rec.max_coverage - rec.total_approved if rec.max_coverage else 0
    
    @api.constrains('is_primary')
    def _check_primary_insurance(self):
        for rec in self:
            if rec.is_primary:
                other_primary = self.search([
                    ('patient_id', '=', rec.patient_id.id),
                    ('is_primary', '=', True),
                    ('id', '!=', rec.id)
                ])
                if other_primary:
                    other_primary.is_primary = False


class ClinicInsuranceClaim(models.Model):
    _name = 'clinic.insurance.claim'
    _description = 'Insurance Claim'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'claim_number'
    _order = 'claim_date desc'
    
    claim_number = fields.Char(string='Claim Number', required=True, copy=False,
                              default='New', readonly=True)
    patient_id = fields.Many2one('clinic.patient', string='Patient', required=True)
    insurance_id = fields.Many2one('clinic.insurance', string='Insurance', required=True,
                                  domain="[('patient_id', '=', patient_id), ('is_active', '=', True)]")
    treatment_id = fields.Many2one('clinic.treatment', string='Treatment')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    
    # Claim Details
    claim_date = fields.Date(string='Claim Date', required=True, default=fields.Date.today)
    service_date = fields.Date(string='Service Date', required=True)
    diagnosis_codes = fields.Text(string='Diagnosis Codes')
    procedure_codes = fields.Text(string='Procedure Codes')
    
    # Amounts
    amount_claimed = fields.Float(string='Amount Claimed', required=True)
    amount_approved = fields.Float(string='Amount Approved')
    amount_paid = fields.Float(string='Amount Paid')
    patient_responsibility = fields.Float(string='Patient Responsibility',
                                        compute='_compute_patient_responsibility')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('partial', 'Partially Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid')
    ], default='draft', tracking=True)
    
    # Dates
    submission_date = fields.Date(string='Submission Date')
    approval_date = fields.Date(string='Approval Date')
    payment_date = fields.Date(string='Payment Date')
    
    # Additional Information
    rejection_reason = fields.Text(string='Rejection Reason')
    notes = fields.Text(string='Notes')
    attachment_ids = fields.Many2many('ir.attachment', string='Supporting Documents')
    
    # Payment
    payment_reference = fields.Char(string='Payment Reference')
    payment_method = fields.Selection([
        ('check', 'Check'),
        ('eft', 'Electronic Transfer'),
        ('credit', 'Credit to Account')
    ], string='Payment Method')
    
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                default=lambda self: self.env.company)
    
    @api.depends('amount_claimed', 'amount_approved')
    def _compute_patient_responsibility(self):
        for rec in self:
            if rec.amount_approved:
                rec.patient_responsibility = rec.amount_claimed - rec.amount_approved
            else:
                rec.patient_responsibility = rec.amount_claimed
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('claim_number', 'New') == 'New':
                vals['claim_number'] = self.env['ir.sequence'].next_by_code('clinic.insurance.claim') or 'New'
        return super().create(vals_list)
    
    def action_submit(self):
        self.ensure_one()
        if self.state == 'draft':
            self.write({
                'state': 'submitted',
                'submission_date': fields.Date.today()
            })
            # Send claim to insurance company
            self._send_claim_to_insurance()
    
    def action_approve(self):
        self.ensure_one()
        if self.state in ['submitted', 'in_review']:
            self.write({
                'state': 'approved',
                'approval_date': fields.Date.today()
            })
    
    def action_reject(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.insurance.claim.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_claim_id': self.id}
        }
    
    def action_mark_paid(self):
        self.ensure_one()
        if self.state == 'approved':
            self.write({
                'state': 'paid',
                'payment_date': fields.Date.today(),
                'amount_paid': self.amount_approved
            })
            # Create payment in accounting
            self._create_payment_entry()
    
    def _send_claim_to_insurance(self):
        # Integration with insurance company API
        pass
    
    def _create_payment_entry(self):
        # Create journal entry for insurance payment
        pass
    
    @api.model
    def check_claim_status(self):
        """Cron job to check status of submitted claims"""
        submitted_claims = self.search([('state', '=', 'submitted')])
        for claim in submitted_claims:
            # Check status with insurance company API
            pass
