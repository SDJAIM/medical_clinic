/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";

export class MedicalClinicDashboard extends Component {
    static template = "medical_clinic.Dashboard";
    
    setup() {
        this.title = "Medical Clinic Dashboard";
    }
}

registry.category("actions").add("medical_clinic.dashboard", MedicalClinicDashboard);
