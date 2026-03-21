import { useState } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { DiagnosisFormData } from '@/types/clinical';
import { Save, Sparkles } from 'lucide-react';

interface DiagnosisFormProps {
  onSubmit?: (data: DiagnosisFormData) => void;
  onAnalyze?: (data: DiagnosisFormData) => void;
}

const initialFormData: DiagnosisFormData = {
  chiefComplaint: '',
  historyOfPresentIllness: '',
  pastPsychiatricHistory: '',
  familyHistory: '',
  socialHistory: '',
  mentalStatusExam: '',
  assessmentPlan: '',
  dsmDiagnosis: '',
};

const formFields = [
  { key: 'chiefComplaint', label: 'Motivo de Consulta', rows: 2 },
  { key: 'historyOfPresentIllness', label: 'Historia de la Enfermedad Actual', rows: 4 },
  { key: 'pastPsychiatricHistory', label: 'Antecedentes Psiquiátricos', rows: 3 },
  { key: 'familyHistory', label: 'Historia Familiar', rows: 2 },
  { key: 'socialHistory', label: 'Historia Social', rows: 2 },
  { key: 'mentalStatusExam', label: 'Examen del Estado Mental', rows: 4 },
  { key: 'dsmDiagnosis', label: 'Diagnóstico DSM-5', rows: 2 },
  { key: 'assessmentPlan', label: 'Plan de Tratamiento', rows: 3 },
] as const;

export function DiagnosisForm({ onSubmit, onAnalyze }: DiagnosisFormProps) {
  const [formData, setFormData] = useState<DiagnosisFormData>(initialFormData);

  const handleChange = (key: keyof DiagnosisFormData, value: string) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit?.(formData);
  };

  const handleAnalyze = () => {
    onAnalyze?.(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-foreground">Formulario Clínico</h2>
          <p className="text-sm text-muted-foreground mt-1">Complete los campos para el diagnóstico</p>
        </div>
      </div>
      
      <div className="space-y-5">
        {formFields.map(({ key, label, rows }) => (
          <div key={key} className="space-y-2">
            <Label htmlFor={key} className="text-sm font-medium text-foreground">
              {label}
            </Label>
            <Textarea
              id={key}
              rows={rows}
              value={formData[key]}
              onChange={(e) => handleChange(key, e.target.value)}
              placeholder={`Ingrese ${label.toLowerCase()}...`}
              className="resize-none border-border bg-background focus:border-primary focus:ring-primary/20"
            />
          </div>
        ))}
      </div>
      
      <div className="flex items-center gap-3 pt-4 border-t border-border">
        <Button
          type="button"
          variant="outline"
          onClick={handleAnalyze}
          className="flex-1 gap-2"
        >
          <Sparkles className="h-4 w-4" />
          Analizar con IA
        </Button>
        <Button type="submit" className="flex-1 gap-2">
          <Save className="h-4 w-4" />
          Guardar
        </Button>
      </div>
    </form>
  );
}
