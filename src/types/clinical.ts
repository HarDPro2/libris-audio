export interface Patient {
  id: string;
  name: string;
  age: number;
  email: string;
  phone: string;
  diagnosis?: string;
  status: 'active' | 'inactive' | 'completed';
  lastSession?: string;
  nextAppointment?: string;
  evolutionScore?: number;
}

export interface Appointment {
  id: string;
  patientId: string;
  patientName: string;
  time: string;
  type: 'initial' | 'followup' | 'assessment';
  status: 'scheduled' | 'completed' | 'cancelled';
  notes?: string;
}

export interface ClinicalEvolution {
  date: string;
  score: number;
  notes?: string;
}

export interface ScientificFeed {
  id: string;
  title: string;
  source: string;
  category: string;
  publishedAt: string;
  summary: string;
  url: string;
  isNew?: boolean;
}

export interface AIInsight {
  id: string;
  type: 'suggestion' | 'reference' | 'alert';
  content: string;
  source?: string;
  confidence?: number;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  references?: string[];
}

export interface DiagnosisFormData {
  chiefComplaint: string;
  historyOfPresentIllness: string;
  pastPsychiatricHistory: string;
  familyHistory: string;
  socialHistory: string;
  mentalStatusExam: string;
  assessmentPlan: string;
  dsmDiagnosis: string;
}
