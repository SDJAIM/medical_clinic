from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta

class ClinicPatient(models.Model):
    _name = 'clinic.patient'
    _description = 'Medical Clinic Patient'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'full_name'
    
    # Basic Information
    first_name = fields.Char(string='First Name', required=True, tracking=True)
    last_name = fields.Char(string='Last Name', required=True, tracking=True)
    full_name = fields.Char(string='Full Name', compute='_compute_full_name', store=True)
    patient_code = fields.Char(string='Patient Code', required=True, copy=False, 
                               default='New', readonly=True)
    image = fields.Binary(string='Photo', attachment=True)
    
    # Demographics
    date_of_birth = fields.Date(string='Date of Birth', required=True)
    age = fields.Integer(string='Age', compute='_compute_age')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Gender', required=True)
    blood_group = fields.Selection([
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-')
    ], string='Blood Group')
    
    # Contact Information
    phone = fields.Char(string='Phone', required=True)
    mobile = fields.Char(string='Mobile')
    email = fields.Char(string='Email')
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street2')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')
    zip = fields.Char(string='ZIP')
    
    # Emergency Contact
    emergency_contact = fields.Char(string='Emergency Contact Name')
    emergency_phone = fields.Char(string='Emergency Phone')
    emergency_relation = fields.Char(string='Relationship')
    
    # Medical Information
    allergies = fields.Text(string='Allergies')
    chronic_conditions = fields.Text(string='Chronic Conditions')
    current_medications = fields.Text(string='Current Medications')
    family_history = fields.Text(string='Family Medical History')
    notes = fields.Text(string='Additional Notes')
    
    # Insurance Information
    insurance_ids = fields.One2many('clinic.insurance', 'patient_id', string='Insurance Plans')
    primary_insurance_id = fields.Many2one('clinic.insurance', string='Primary Insurance',
                                          compute='_compute_primary_insurance', store=True)
    
    # Relationships
    appointment_ids = fields.One2many('clinic.appointment', 'patient_id', string='Appointments')
    treatment_ids = fields.One2many('clinic.treatment', 'patient_id', string='Treatments')
    attachment_ids = fields.One2many('ir.attachment', 'res_id', 
                                   domain=[('res_model', '=', 'clinic.patient')],
                                   string='Medical Documents')
    partner_id = fields.Many2one('res.partner', string='Related Partner', ondelete='cascade')
    
    # Statistics
    appointment_count = fields.Integer(compute='_compute_counts')
    treatment_count = fields.Integer(compute='_compute_counts')
    last_visit_date = fields.Date(compute='_compute_last_visit', store=True)
    
    # Multi-company
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                default=lambda self: self.env.company)
    
    # Status
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('deceased', 'Deceased')
    ], default='active', tracking=True)
    
    @api.depends('first_name', 'last_name')
    def _compute_full_name(self):
        for rec in self:
            rec.full_name = f"{rec.first_name or ''} {rec.last_name or ''}".strip()
    
    @api.depends('date_of_birth')
    def _compute_age(self):
        for rec in self:
            if rec.date_of_birth:
                rec.age = relativedelta(fields.Date.today(), rec.date_of_birth).years
            else:
                rec.age = 0
    
    @api.depends('appointment_ids', 'treatment_ids')
    def _compute_counts(self):
        for rec in self:
            rec.appointment_count = len(rec.appointment_ids)
            rec.treatment_count = len(rec.treatment_ids)
    
    @api.depends('appointment_ids.date')
    def _compute_last_visit(self):
        for rec in self:
            appointments = rec.appointment_ids.filtered(lambda a: a.state == 'done')
            if appointments:
                rec.last_visit_date = max(appointments.mapped('date')).date()
            else:
                rec.last_visit_date = False
    
    @api.depends('insurance_ids', 'insurance_ids.is_primary')
    def _compute_primary_insurance(self):
        for rec in self:
            primary = rec.insurance_ids.filtered('is_primary')
            rec.primary_insurance_id = primary[0] if primary else False
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('patient_code', 'New') == 'New':
                vals['patient_code'] = self.env['ir.sequence'].next_by_code('clinic.patient') or 'New'
            
            # Create corresponding partner if not specified
            if not vals.get('partner_id'):
                partner_vals = {
                    'name': f"{vals.get('first_name', '')} {vals.get('last_name', '')}".strip(),
                    'phone': vals.get('phone'),
                    'mobile': vals.get('mobile'),
                    'email': vals.get('email'),
                    'street': vals.get('street'),
                    'street2': vals.get('street2'),
                    'city': vals.get('city'),
                    'state_id': vals.get('state_id'),
                    'country_id': vals.get('country_id'),
                    'zip': vals.get('zip'),
                    'is_company': False,
                    'partner_share': True,
                    'company_id': vals.get('company_id', self.env.company.id),
                }
                partner = self.env['res.partner'].create(partner_vals)
                vals['partner_id'] = partner.id
                
        return super().create(vals_list)
    
    def write(self, vals):
        # Update partner information when patient info changes
        res = super().write(vals)
        
        if any(field in vals for field in ['first_name', 'last_name', 'phone', 'mobile', 
                                           'email', 'street', 'street2', 'city', 
                                           'state_id', 'country_id', 'zip']):
            for rec in self:
                if rec.partner_id:
                    partner_vals = {}
                    if 'first_name' in vals or 'last_name' in vals:
                        partner_vals['name'] = rec.full_name
                    for field in ['phone', 'mobile', 'email', 'street', 'street2', 
                                 'city', 'state_id', 'country_id', 'zip']:
                        if field in vals:
                            partner_vals[field] = vals[field]
                    if partner_vals:
                        rec.partner_id.write(partner_vals)
        
        return res
    
    def action_view_appointments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Appointments'),
            'res_model': 'clinic.appointment',
            'view_mode': 'calendar,tree,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id}
        }
    
    def action_view_treatments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Treatments'),
            'res_model': 'clinic.treatment',
            'view_mode': 'tree,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id}
        }
