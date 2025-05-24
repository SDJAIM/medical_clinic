from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ClinicTreatment(models.Model):
    _name = 'clinic.treatment'
    _description = 'Medical Treatment Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'treatment_code'
    _order = 'date desc'
    
    treatment_code = fields.Char(string='Treatment #', required=True, copy=False,
                                default='New', readonly=True)
    patient_id = fields.Many2one('clinic.patient', string='Patient', required=True,
                                ondelete='restrict')
    doctor_id = fields.Many2one('hr.employee', string='Doctor', required=True,
                               domain=[('is_medical_professional', '=', True)])
    appointment_id = fields.Many2one('clinic.appointment', string='Appointment')
    date = fields.Datetime(string='Date', required=True, default=fields.Datetime.now)
    
    # Chief Complaint & History
    chief_complaint = fields.Text(string='Chief Complaint', required=True)
    history_present_illness = fields.Text(string='History of Present Illness')
    
    # Vital Signs
    blood_pressure_systolic = fields.Integer(string='Systolic BP')
    blood_pressure_diastolic = fields.Integer(string='Diastolic BP')
    pulse_rate = fields.Integer(string='Pulse Rate')
    temperature = fields.Float(string='Temperature (°C)')
    respiratory_rate = fields.Integer(string='Respiratory Rate')
    weight = fields.Float(string='Weight (kg)')
    height = fields.Float(string='Height (cm)')
    bmi = fields.Float(string='BMI', compute='_compute_bmi', store=True)
    
    # Examination
    physical_examination = fields.Text(string='Physical Examination')
    
    # Diagnosis
    diagnosis_ids = fields.One2many('clinic.diagnosis', 'treatment_id', string='Diagnosis')
    diagnosis_notes = fields.Text(string='Diagnosis Notes')
    
    # Treatment Plan
    treatment_plan = fields.Text(string='Treatment Plan')
    prescription_ids = fields.One2many('clinic.prescription', 'treatment_id', string='Prescriptions')
    
    # Lab Tests & Procedures
    lab_test_ids = fields.One2many('clinic.lab.test', 'treatment_id', string='Lab Tests')
    procedure_ids = fields.Many2many('clinic.service', string='Procedures Performed',
                                    domain=[('is_procedure', '=', True)])
    
    # Follow-up
    follow_up_date = fields.Date(string='Follow-up Date')
    follow_up_notes = fields.Text(string='Follow-up Instructions')
    
    # Attachments
    attachment_ids = fields.One2many('ir.attachment', 'res_id',
                                   domain=[('res_model', '=', 'clinic.treatment')],
                                   string='Medical Documents')
    
    # Billing
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    insurance_claim_id = fields.Many2one('clinic.insurance.claim', string='Insurance Claim')
    
    # Status
    state = fields.Selection([
        ('draft', 'In Progress'),
        ('done', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True)
    
    # Multi-company
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                default=lambda self: self.env.company)
    
    # Type
    treatment_type = fields.Selection([
        ('consultation', 'Consultation'),
        ('emergency', 'Emergency'),
        ('procedure', 'Procedure'),
        ('dental', 'Dental'),
        ('follow_up', 'Follow-up')
    ], string='Type', default='consultation')
    
    @api.depends('weight', 'height')
    def _compute_bmi(self):
        for rec in self:
            if rec.weight and rec.height:
                height_m = rec.height / 100
                rec.bmi = round(rec.weight / (height_m * height_m), 2)
            else:
                rec.bmi = 0
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('treatment_code', 'New') == 'New':
                vals['treatment_code'] = self.env['ir.sequence'].next_by_code('clinic.treatment') or 'New'
        return super().create(vals_list)
    
    def action_complete(self):
        self.ensure_one()
        if not self.diagnosis_ids:
            raise UserError(_('Please add at least one diagnosis before completing the treatment.'))
        self.state = 'done'
        
        # Create invoice if procedures or services were performed
        if self.procedure_ids and not self.invoice_id:
            self._create_invoice()
    
    def action_print_prescription(self):
        self.ensure_one()
        return self.env.ref('medical_clinic.action_report_prescription').report_action(self)
    
    def _create_invoice(self):
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.patient_id.partner_id.id,
            'patient_id': self.patient_id.id,
            'treatment_id': self.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [],
        }
        
        for service in self.procedure_ids:
            invoice_vals['invoice_line_ids'].append((0, 0, {
                'product_id': service.product_id.id,
                'name': service.name,
                'quantity': 1,
                'price_unit': service.price,
            }))
        
        invoice = self.env['account.move'].create(invoice_vals)
        self.invoice_id = invoice
        
        # Create insurance claim if patient has insurance
        if self.patient_id.primary_insurance_id:
            self._create_insurance_claim(invoice)
    
    def _create_insurance_claim(self, invoice):
        claim_vals = {
            'patient_id': self.patient_id.id,
            'insurance_id': self.patient_id.primary_insurance_id.id,
            'treatment_id': self.id,
            'invoice_id': invoice.id,
            'claim_date': fields.Date.today(),
            'amount_claimed': invoice.amount_total,
        }
        claim = self.env['clinic.insurance.claim'].create(claim_vals)
        self.insurance_claim_id = claim


class ClinicDiagnosis(models.Model):
    _name = 'clinic.diagnosis'
    _description = 'Diagnosis Line'
    
    treatment_id = fields.Many2one('clinic.treatment', string='Treatment', required=True, ondelete='cascade')
    diagnosis = fields.Char(string='Diagnosis', required=True)
    icd_code = fields.Char(string='ICD Code')
    notes = fields.Text(string='Notes')


class ClinicPrescription(models.Model):
    _name = 'clinic.prescription'
    _description = 'Prescription Line'
    
    treatment_id = fields.Many2one('clinic.treatment', string='Treatment', required=True, ondelete='cascade')
    medicine_id = fields.Many2one('product.product', string='Medicine', required=True,
                                 domain=[('is_medicine', '=', True)])
    dosage = fields.Char(string='Dosage', required=True)
    frequency = fields.Selection([
        ('od', 'Once Daily'),
        ('bd', 'Twice Daily'),
        ('tds', 'Three Times Daily'),
        ('qds', 'Four Times Daily'),
        ('sos', 'As Needed'),
        ('stat', 'Immediately'),
    ], string='Frequency', required=True)
    duration = fields.Integer(string='Duration (days)', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    instructions = fields.Text(string='Instructions')
    
    @api.onchange('medicine_id', 'duration', 'frequency')
    def _onchange_calculate_quantity(self):
        if self.medicine_id and self.duration and self.frequency:
            freq_map = {'od': 1, 'bd': 2, 'tds': 3, 'qds': 4, 'sos': 1, 'stat': 1}
            daily_qty = freq_map.get(self.frequency, 1)
            self.quantity = daily_qty * self.duration


class ClinicLabTest(models.Model):
    _name = 'clinic.lab.test'
    _description = 'Lab Test Request'
    
    treatment_id = fields.Many2one('clinic.treatment', string='Treatment', required=True, ondelete='cascade')
    test_type = fields.Selection([
        ('blood', 'Blood Test'),
        ('urine', 'Urine Test'),
        ('xray', 'X-Ray'),
        ('mri', 'MRI'),
        ('ct', 'CT Scan'),
        ('ultrasound', 'Ultrasound'),
        ('other', 'Other')
    ], string='Test Type', required=True)
    test_name = fields.Char(string='Test Name', required=True)
    notes = fields.Text(string='Notes')
    result = fields.Text(string='Result')
    attachment_ids = fields.Many2many('ir.attachment', string='Lab Reports')
    state = fields.Selection([
        ('requested', 'Requested'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed')
    ], default='requested')