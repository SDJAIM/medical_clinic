{
    'name': 'Medical Clinic Management',
    'version': '18.0.1.0.0',
    'category': 'Healthcare',
    'summary': 'Complete medical & dental clinic management with multi-company support',
    'description': """
Medical Clinic Management System
================================
Comprehensive solution for medical and dental clinics featuring:
- Patient management with medical history
- Appointment scheduling for doctors and dentists
- Treatment recording and prescriptions
- Dental charting with tooth-specific procedures
- Insurance claim workflow
- Integration with HR for staff management
- Integration with Stock for medical supplies
- Multi-company support for clinic chains
    """,
    'author': 'Medical Clinic Solutions',
    'depends': [
        'base',
        'mail',
        'calendar',
        'account',
        'hr',
        'stock',
        'web',
        'portal',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/clinic_security.xml',
        
        # Data
        'data/clinic_data.xml',
        'data/dental_data.xml',
        'data/service_data.xml',
        
        # Views
        'views/menu_views.xml',
        'views/patient_views.xml',
        'views/appointment_views.xml',
        'views/treatment_views.xml',
        'views/dental_views.xml',
        'views/insurance_views.xml',
        'views/dashboard_views.xml',
        
        # Reports
        'report/treatment_report.xml',
        'report/invoice_report.xml',
        
        # Wizards
        'wizard/appointment_wizard_views.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'medical_clinic/static/src/js/dental_chart.js',
            'medical_clinic/static/src/xml/dental_chart.xml',
            'medical_clinic/static/src/css/dental_chart.css',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}