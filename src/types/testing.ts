export interface PsychTest {
  id: string;
  name: string;
  shortName: string;
  description: string;
  category: 'cognitive' | 'personality' | 'mood' | 'anxiety' | 'trauma';
  estimatedTime: number; // minutes
  questionCount: number;
  validity: 'high' | 'moderate' | 'experimental';
  domains: string[];
}

export interface TestQuestion {
  id: string;
  testId: string;
  order: number;
  text: string;
  type: 'likert' | 'multiple-choice' | 'yes-no';
  options: TestOption[];
  domain?: string;
}

export interface TestOption {
  value: number;
  label: string;
  description?: string;
}

export interface TestResponse {
  questionId: string;
  value: number;
  timestamp: string;
}

export interface TestSession {
  id: string;
  testId: string;
  patientId: string;
  startedAt: string;
  completedAt?: string;
  responses: TestResponse[];
  status: 'in-progress' | 'completed' | 'abandoned';
}

export interface TestResult {
  sessionId: string;
  testId: string;
  patientId: string;
  completedAt: string;
  totalScore: number;
  maxScore: number;
  percentile?: number;
  severity?: 'minimal' | 'mild' | 'moderate' | 'severe';
  domainScores: DomainScore[];
  differentialDiagnosis?: DifferentialDiagnosis[];
  dsmCriteria: DSMCriteria[];
  clinicalNotes: string[];
}

export interface DomainScore {
  domain: string;
  score: number;
  maxScore: number;
  percentile: number;
  interpretation: string;
}

export interface DifferentialDiagnosis {
  primaryDiagnosis: string;
  alternativeDiagnosis: string;
  overlapPercentage: number;
  distinguishingFactors: string[];
  recommendation: string;
}

export interface DSMCriteria {
  code: string;
  name: string;
  criteriaMetCount: number;
  totalCriteria: number;
  criteriaDetails: CriteriaDetail[];
}

export interface CriteriaDetail {
  criterion: string;
  met: boolean;
  evidence?: string;
}

export interface CopilotMessage {
  id: string;
  role: 'user' | 'assistant';
  type: 'reasoning' | 'evidence' | 'question';
  content: string;
  timestamp: string;
  sources?: SourceReference[];
}

export interface SourceReference {
  id: string;
  title: string;
  authors: string[];
  year: number;
  journal?: string;
  type: 'journal' | 'textbook' | 'guideline';
  impactFactor?: number;
  quartile?: 'Q1' | 'Q2' | 'Q3' | 'Q4';
  doi?: string;
}

export interface QuickSuggestion {
  id: string;
  label: string;
  prompt: string;
  icon?: string;
}
