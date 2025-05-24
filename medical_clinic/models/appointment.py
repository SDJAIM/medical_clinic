from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class ClinicAppointment(models.Model):
    _name = 'clinic.appointment'
    _description = 'Medical Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'appointment_code'
    _order = 'date desc'
    
    appointment_code = fields.Char(string='Appointment #', required=True, copy=False,
                                  default='New', readonly=True)
    patient_id = fields.Many2one('clinic.patient', string='Patient', required=True,
                                tracking=True, ondelete='restrict')
    doctor_id = fields.Many2one('hr.employee', string='Doctor/Dentist', required=True,
                               domain=[('is_medical_professional', '=', True)],
                               tracking=True)
    
    # Appointment Details
    date = fields.Datetime(string='Date & Time', required=True, tracking=True)
    duration = fields.Float(string='Duration (hours)', default=0.5)
    end_date = fields.Datetime(string='End Time', compute='_compute_end_date', store=True)
    appointment_type = fields.Selection([
        ('consultation', 'Consultation'),
        ('follow_up', 'Follow-up'),
        ('emergency', 'Emergency'),
        ('routine_checkup', 'Routine Checkup'),
        ('procedure', 'Procedure'),
        ('dental', 'Dental')
    ], string='Type', required=True, default='consultation')
    
    # Department/Service
    department = fields.Selection([
        ('general', 'General Medicine'),
        ('dental', 'Dental'),
        ('cardiology', 'Cardiology'),
        ('orthopedics', 'Orthopedics'),
        ('pediatrics', 'Pediatrics'),
        ('gynecology', 'Gynecology'),
        ('dermatology', 'Dermatology'),
        ('other', 'Other')
    ], string='Department', required=True, default='general')
    service_ids = fields.Many2many('clinic.service', string='Services')
    
    # Appointment Information
    chief_complaint = fields.Text(string='Chief Complaint')
    notes = fields.Text(string='Notes')
    internal_notes = fields.Text(string='Internal Notes')
    
    # Related Records
    treatment_id = fields.Many2one('clinic.treatment', string='Treatment Record')
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    
    # Status
    state = fields.Selection([
        ('draft', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('arrived', 'Arrived'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show')
    ], default='draft', tracking=True, required=True)
    
    # Reminder
    reminder_sent = fields.Boolean(string='Reminder Sent', default=False)
    reminder_date = fields.Datetime(string='Reminder Date', compute='_compute_reminder_date')
    
    # Multi-company
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                default=lambda self: self.env.company)
    
    # Calendar Integration
    calendar_event_id = fields.Many2one('calendar.event', string='Calendar Event')
    
    # Computed Fields
    patient_phone = fields.Char(related='patient_id.phone', string='Patient Phone')
    patient_email = fields.Char(related='patient_id.email', string='Patient Email')
    patient_age = fields.Integer(related='patient_id.age', string='Age')
    
    @api.depends('date', 'duration')
    def _compute_end_date(self):
        for rec in self:
            if rec.date and rec.duration:
                rec.end_date = rec.date + timedelta(hours=rec.duration)
            else:
                rec.end_date = rec.date
    
    @api.depends('date')
    def _compute_reminder_date(self):
        for rec in self:
            if rec.date:
                rec.reminder_date = rec.date - timedelta(days=1)
            else:
                rec.reminder_date = False
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('appointment_code', 'New') == 'New':
                vals['appointment_code'] = self.env['ir.sequence'].next_by_code('clinic.appointment') or 'New'
        appointments = super().create(vals_list)
        appointments._create_calendar_events()
        return appointments
    
    def write(self, vals):
        res = super().write(vals)
        if any(field in vals for field in ['date', 'duration', 'doctor_id', 'patient_id', 'state']):
            self._update_calendar_events()
        return res
    
    def _create_calendar_events(self):
        for rec in self:
            if not rec.calendar_event_id and rec.state not in ['cancelled', 'no_show']:
                event_vals = {
                    'name': f"Appointment - {rec.patient_id.full_name}",
                    'start': rec.date,
                    'stop': rec.end_date,
                    'user_id': rec.doctor_id.user_id.id if rec.doctor_id.user_id else self.env.user.id,
                    'partner_ids': [(4, rec.patient_id.partner_id.id)] if rec.patient_id.partner_id else [],
                    'description': f"Type: {rec.appointment_type}\nDepartment: {rec.department}\n{rec.chief_complaint or ''}",
                }
                event = self.env['calendar.event'].create(event_vals)
                rec.calendar_event_id = event
    
    def _update_calendar_events(self):
        for rec in self:
            if rec.calendar_event_id:
                if rec.state in ['cancelled', 'no_show']:
                    rec.calendar_event_id.unlink()
                else:
                    rec.calendar_event_id.write({
                        'start': rec.date,
                        'stop': rec.end_date,
                        'user_id': rec.doctor_id.user_id.id if rec.doctor_id.user_id else self.env.user.id,
                    })
    
    @api.constrains('date', 'doctor_id', 'duration')
    def _check_appointment_conflict(self):
        for rec in self:
            if rec.state not in ['cancelled', 'no_show']:
                domain = [
                    ('doctor_id', '=', rec.doctor_id.id),
                    ('date', '<', rec.end_date),
                    ('end_date', '>', rec.date),
                    ('state', 'not in', ['cancelled', 'no_show']),
                    ('id', '!=', rec.id),
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(_('This doctor already has an appointment scheduled at this time.'))
    
    def action_confirm(self):
        self.ensure_one()
        if self.state == 'draft':
            self.state = 'confirmed'
            # Send confirmation email/SMS here
    
    def action_mark_arrived(self):
        self.ensure_one()
        self.state = 'arrived'
    
    def action_start_consultation(self):
        self.ensure_one()
        self.state = 'in_progress'
        # Create treatment record
        if not self.treatment_id:
            treatment = self.env['clinic.treatment'].create({
                'patient_id': self.patient_id.id,
                'doctor_id': self.doctor_id.id,
                'appointment_id': self.id,
                'date': fields.Datetime.now(),
                'chief_complaint': self.chief_complaint,
            })
            self.treatment_id = treatment
        # Open treatment form
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.treatment',
            'res_id': self.treatment_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_done(self):
        self.ensure_one()
        if self.state == 'in_progress':
            self.state = 'done'
            if self.treatment_id:
                self.treatment_id.state = 'done'
    
    def action_cancel(self):
        self.state = 'cancelled'
        if self.calendar_event_id:
            self.calendar_event_id.unlink()
    
    def action_no_show(self):
        self.state = 'no_show'
    
    def action_reschedule(self):
        # Open wizard to reschedule
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.appointment.reschedule.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_appointment_id': self.id}
        }
    
    @api.model
    def send_appointment_reminders(self):
        """Cron job to send appointment reminders"""
        tomorrow = fields.Datetime.now() + timedelta(days=1)
        appointments = self.search([
            ('date', '>=', fields.Datetime.now()),
            ('date', '<=', tomorrow),
            ('state', '=', 'confirmed'),
            ('reminder_sent', '=', False)
        ])
        for appointment in appointments:
            # Send reminder email/SMS
            appointment.reminder_sent = True