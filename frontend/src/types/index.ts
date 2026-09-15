/**
 * CareRoute AI - Frontend Type Definitions
 */

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'patient' | 'doctor' | 'admin' | 'community_authority';
  phone?: string;
  is_active: boolean;
  health_data_sharing?: boolean;
  emergency_info_sharing?: boolean;
  community_analytics_participation?: boolean;
}

export interface PatientProfile {
  id: number;
  user_id: number;
  date_of_birth?: string;
  gender?: string;
  blood_group?: string;
  address?: string;
  village?: string;
  district?: string;
  state?: string;
  latitude?: number;
  longitude?: number;
  preferred_language?: string;
  allergies?: string;
  chronic_conditions?: string;
  user_name?: string;
  user_email?: string;
  user_phone?: string;
}

export interface EmergencyContact {
  id: number;
  name: string;
  relationship_type?: string;
  phone: string;
  is_primary: boolean;
}

export interface HealthCheckin {
  id: number;
  feeling_today?: string;
  fever: boolean;
  fever_temperature?: number;
  cough: boolean;
  breathing_difficulty: boolean;
  chest_discomfort: boolean;
  headache: boolean;
  dizziness: boolean;
  weakness: boolean;
  pain: boolean;
  pain_location?: string;
  pain_severity?: number;
  vomiting: boolean;
  diarrhea: boolean;
  medication_taken: boolean;
  new_symptoms_text?: string;
  symptoms?: string[];
  ai_risk_level?: string;
  red_flags_detected: boolean;
  created_at?: string;
}

export interface HealthAssessment {
  id: number;
  checkin_id: number;
  possible_concerns?: any[];
  urgency_level?: string;
  reasons?: string[];
  recommended_action?: string;
  warning_signs?: string[];
  doctor_assessment?: any;
  diagnosis?: string;
  doctor_notes?: string;
  care_route?: CareRouteResult;
  created_at?: string;
}

export interface CareRouteResult {
  what: string;
  how_serious: string;
  where: string;
  what_next: string;
  recommended_care_level: string;
  recommended_facilities: Facility[];
  urgency_explanation: string;
}

export interface ScreeningResult {
  assessment_id?: number;
  urgency_level: string;
  possible_concerns: Array<{concern: string; reason: string; relevance: string}>;
  reasons: string[];
  recommended_action: string;
  warning_signs: string[];
  care_route?: CareRouteResult;
  red_flags_detected: boolean;
  red_flags?: Array<{description: string; guidance: string}>;
  emergency_guidance?: string;
  emergency_alert?: boolean;
  emergency_message?: string;
  ai_service_used: string;
}

export interface Facility {
  id: number;
  name: string;
  facility_type: string;
  latitude: number;
  longitude: number;
  address?: string;
  village?: string;
  district?: string;
  services?: string[];
  emergency_available: boolean;
  opening_hours?: string;
  contact_number?: string;
  accessibility_info?: string;
  distance_km?: number;
}

export interface CarePlan {
  id: number;
  patient_id: number;
  doctor_id: number;
  title?: string;
  description?: string;
  medications?: any[];
  follow_up_date?: string;
  lab_tests?: string[];
  doctor_instructions?: string;
  lifestyle_instructions?: string;
  is_active: boolean;
  created_at?: string;
}

export interface MedicationReminder {
  id: number;
  medicine_name: string;
  dosage?: string;
  frequency?: string;
  time_of_day?: string;
  is_active: boolean;
}

export interface Appointment {
  id: number;
  patient_id: number;
  doctor_id?: number;
  appointment_date: string;
  reason?: string;
  notes?: string;
  status: string;
  is_follow_up: boolean;
}

export interface Community {
  id: number;
  name: string;
  village?: string;
  district?: string;
  latitude: number;
  longitude: number;
  population?: number;
  distance_to_nearest_facility_km?: number;
  priority_score?: number;
  priority_level?: string;
  reasons?: string[];
}

export interface EmergencyHealthCard {
  patient_name: string;
  age?: number;
  blood_group?: string;
  allergies?: string[];
  medical_conditions?: string[];
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  current_location?: string;
  share_token?: string;
}

export interface MedicalDocument {
  id: number;
  title: string;
  document_type: string;
  file_size?: number;
  doctor_name?: string;
  facility_name?: string;
  document_date?: string;
  created_at?: string;
}

export interface Prescription {
  id: number;
  diagnosis?: string;
  notes?: string;
  is_confirmed: boolean;
  items: PrescriptionItem[];
  created_at?: string;
}

export interface PrescriptionItem {
  id: number;
  medicine_name: string;
  dosage?: string;
  frequency?: string;
  duration?: string;
  instructions?: string;
  needs_verification?: boolean;
}

export interface TimelineEntry {
  type: string;
  date?: string;
  data: any;
}
