// ─── Auth ────────────────────────────────────────────────────────────────────
export type UserRole = 'Admins' | 'Doctors' | 'Patients';

export interface AuthUser {
  sub:        string;
  email:      string;
  name:       string;
  role:       string;
  groups:     UserRole[];
}

export interface AuthTokens {
  accessToken:  string;
  idToken:      string;
  refreshToken: string;
  expiresIn:    number;
}

// ─── Patient ─────────────────────────────────────────────────────────────────
export type PatientStatus = 'ACTIVE' | 'DEACTIVATED';
export type BloodGroup    = 'A+' | 'A-' | 'B+' | 'B-' | 'AB+' | 'AB-' | 'O+' | 'O-';

export interface Patient {
  patient_id:  string;
  record_type: 'PROFILE';
  firstName:   string;
  lastName:    string;
  dateOfBirth: string;
  gender:      'Male' | 'Female' | 'Other';
  phone:       string;
  email:       string;
  address:     string;
  bloodGroup:  BloodGroup | '';
  allergies:   string[];
  status:      PatientStatus;
  created_at:  string;
  updated_at:  string;
}

// ─── Doctor ──────────────────────────────────────────────────────────────────
export interface Doctor {
  doctor_id:      string;
  record_type:    'PROFILE';
  name:           string;
  specialty:      string;
  email:          string;
  phone:          string;
  license_number: string;
  qualifications: string[];
  status:         'ACTIVE' | 'INACTIVE';
  created_at:     string;
}

// ─── Appointment ─────────────────────────────────────────────────────────────
export type AppointmentStatus = 'PENDING' | 'CONFIRMED' | 'CANCELLED' | 'COMPLETED' | 'NO_SHOW';
export type AppointmentType   = 'IN_PERSON' | 'TELEMEDICINE';

export interface Appointment {
  appointment_id:   string;
  appointment_date: string;
  patient_id:       string;
  doctor_id:        string;
  reason:           string;
  notes:            string;
  status:           AppointmentStatus;
  type:             AppointmentType;
  duration_minutes: number;
  created_at:       string;
  updated_at:       string;
}

// ─── Medical Record ──────────────────────────────────────────────────────────
export type RecordType = 'DIAGNOSIS' | 'LAB_RESULT' | 'PRESCRIPTION' | 'NOTE' | 'IMAGING' | 'PROCEDURE';

export interface MedicalRecord {
  patient_id:      string;
  record_id:       string;
  record_type:     RecordType;
  doctor_id:       string;
  doctor_name:     string;
  title:           string;
  content:         string;
  attachments:     string[];
  appointment_id:  string;
  is_confidential: boolean;
  created_at:      string;
  updated_at:      string;
}

// ─── Notification ────────────────────────────────────────────────────────────
export type NotificationType = 'APPOINTMENT' | 'REMINDER' | 'RESULT' | 'ALERT' | 'GENERAL';

export interface Notification {
  notification_id: string;
  created_at:      string;
  recipient_id:    string;
  title:           string;
  message:         string;
  type:            NotificationType;
  is_read:         boolean;
  read_at?:        string;
}

// ─── Admin Stats ─────────────────────────────────────────────────────────────
export interface DashboardStats {
  active_patients:    number;
  total_doctors:      number;
  appointments_today: number;
  pending_approvals:  number;
  generated_at:       string;
}

// ─── API Response wrapper ────────────────────────────────────────────────────
export interface ApiResponse<T> {
  data?:    T;
  error?:   string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items:  T[];
  count:  number;
  cursor?: string;
}
