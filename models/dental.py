from odoo import models, fields, api, _

class ClinicDentalChart(models.Model):
    _name = 'clinic.dental.chart'
    _description = 'Dental Chart'
    _rec_name = 'patient_id'
    
    patient_id = fields.Many2one('clinic.patient', string='Patient', required=True, ondelete='cascade')
    tooth_ids = fields.One2many('clinic.dental.tooth', 'chart_id', string='Teeth')
    last_update = fields.Datetime(string='Last Updated', compute='_compute_last_update')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                default=lambda self: self.env.company)
    
    @api.depends('tooth_ids.write_date')
    def _compute_last_update(self):
        for rec in self:
            if rec.tooth_ids:
                rec.last_update = max(rec.tooth_ids.mapped('write_date'))
            else:
                rec.last_update = False
    
    @api.model
    def create(self, vals):
        chart = super().create(vals)
        chart._create_teeth()
        return chart
    
    def _create_teeth(self):
        """Create all 32 teeth for adult or 20 for child based on patient age"""
        tooth_numbers = []
        if self.patient_id.age < 13:
            # Primary teeth (A-T)
            tooth_numbers = [
                ('A', 'Upper Right Second Molar'), ('B', 'Upper Right First Molar'),
                ('C', 'Upper Right Canine'), ('D', 'Upper Right Lateral Incisor'),
                ('E', 'Upper Right Central Incisor'), ('F', 'Upper Left Central Incisor'),
                ('G', 'Upper Left Lateral Incisor'), ('H', 'Upper Left Canine'),
                ('I', 'Upper Left First Molar'), ('J', 'Upper Left Second Molar'),
                ('K', 'Lower Left Second Molar'), ('L', 'Lower Left First Molar'),
                ('M', 'Lower Left Canine'), ('N', 'Lower Left Lateral Incisor'),
                ('O', 'Lower Left Central Incisor'), ('P', 'Lower Right Central Incisor'),
                ('Q', 'Lower Right Lateral Incisor'), ('R', 'Lower Right Canine'),
                ('S', 'Lower Right First Molar'), ('T', 'Lower Right Second Molar'),
            ]
        else:
            # Permanent teeth (1-32)
            tooth_numbers = [
                (1, 'Upper Right Third Molar'), (2, 'Upper Right Second Molar'),
                (3, 'Upper Right First Molar'), (4, 'Upper Right Second Premolar'),
                (5, 'Upper Right First Premolar'), (6, 'Upper Right Canine'),
                (7, 'Upper Right Lateral Incisor'), (8, 'Upper Right Central Incisor'),
                (9, 'Upper Left Central Incisor'), (10, 'Upper Left Lateral Incisor'),
                (11, 'Upper Left Canine'), (12, 'Upper Left First Premolar'),
                (13, 'Upper Left Second Premolar'), (14, 'Upper Left First Molar'),
                (15, 'Upper Left Second Molar'), (16, 'Upper Left Third Molar'),
                (17, 'Lower Left Third Molar'), (18, 'Lower Left Second Molar'),
                (19, 'Lower Left First Molar'), (20, 'Lower Left Second Premolar'),
                (21, 'Lower Left First Premolar'), (22, 'Lower Left Canine'),
                (23, 'Lower Left Lateral Incisor'), (24, 'Lower Left Central Incisor'),
                (25, 'Lower Right Central Incisor'), (26, 'Lower Right Lateral Incisor'),
                (27, 'Lower Right Canine'), (28, 'Lower Right First Premolar'),
                (29, 'Lower Right Second Premolar'), (30, 'Lower Right First Molar'),
                (31, 'Lower Right Second Molar'), (32, 'Lower Right Third Molar'),
            ]
        
        for number, name in tooth_numbers:
            self.env['clinic.dental.tooth'].create({
                'chart_id': self.id,
                'number': str(number),
                'name': name,
            })


class ClinicDentalTooth(models.Model):
    _name = 'clinic.dental.tooth'
    _description = 'Dental Tooth'
    _rec_name = 'display_name'
    
    chart_id = fields.Many2one('clinic.dental.chart', string='Dental Chart', required=True, ondelete='cascade')
    number = fields.Char(string='Tooth Number', required=True)
    name = fields.Char(string='Tooth Name', required=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    
    # Tooth Status
    status = fields.Selection([
        ('healthy', 'Healthy'),
        ('cavity', 'Cavity'),
        ('filled', 'Filled'),
        ('crown', 'Crown'),
        ('root_canal', 'Root Canal'),
        ('extracted', 'Extracted'),
        ('implant', 'Implant'),
        ('bridge', 'Bridge'),
    ], string='Status', default='healthy')
    
    # Surfaces
    mesial = fields.Boolean(string='Mesial')
    distal = fields.Boolean(string='Distal')
    occlusal = fields.Boolean(string='Occlusal')
    buccal = fields.Boolean(string='Buccal')
    lingual = fields.Boolean(string='Lingual')
    
    # Procedures
    procedure_ids = fields.One2many('clinic.dental.procedure', 'tooth_id', string='Procedures')
    notes = fields.Text(string='Notes')
    
    # Multi-company
    company_id = fields.Many2one('res.company', string='Company', 
                                related='chart_id.company_id', store=True, readonly=True)
    
    @api.depends('number', 'name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"#{rec.number} - {rec.name}"


class ClinicDentalProcedure(models.Model):
    _name = 'clinic.dental.procedure'
    _description = 'Dental Procedure'
    _order = 'date desc'
    
    tooth_id = fields.Many2one('clinic.dental.tooth', string='Tooth', required=True, ondelete='cascade')
    treatment_id = fields.Many2one('clinic.treatment', string='Treatment', required=True)
    date = fields.Datetime(string='Date', required=True, default=fields.Datetime.now)
    
    procedure_type = fields.Selection([
        ('filling', 'Filling'),
        ('extraction', 'Extraction'),
        ('root_canal', 'Root Canal'),
        ('crown', 'Crown'),
        ('bridge', 'Bridge'),
        ('implant', 'Implant'),
        ('cleaning', 'Cleaning'),
        ('whitening', 'Whitening'),
        ('other', 'Other')
    ], string='Procedure Type', required=True)
    
    description = fields.Text(string='Description', required=True)
    doctor_id = fields.Many2one('hr.employee', string='Dentist', required=True,
                               domain=[('is_medical_professional', '=', True)])
    notes = fields.Text(string='Notes')
    
    # Surfaces treated
    surfaces = fields.Char(string='Surfaces Treated')
    
    # Link to service for billing
    service_id = fields.Many2one('clinic.service', string='Service',
                                domain=[('department', '=', 'dental')])
    
    # Multi-company
    company_id = fields.Many2one('res.company', string='Company', 
                                related='tooth_id.company_id', store=True, readonly=True)
