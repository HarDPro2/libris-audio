import { useState } from 'react';
import { DiagnosisForm } from '@/components/diagnosis/DiagnosisForm';
import { AIInsightsPanel } from '@/components/diagnosis/AIInsightsPanel';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { mockPatients } from '@/data/mockData';
import { DiagnosisFormData } from '@/types/clinical';

export default function Diagnosis() {
  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [isSearching, setIsSearching] = useState(false);

  const handleFormSubmit = (data: DiagnosisFormData) => {
    console.log('Form submitted:', data);
    // Ready for API connection
  };

  const handleAnalyze = (data: DiagnosisFormData) => {
    console.log('Analyze with AI:', data);
    // Ready for API connection
  };

  const handleChatMessage = (message: string) => {
    console.log('Chat message:', message);
    // Ready for API connection
  };

  const handleBibliographySearch = (query: string) => {
    console.log('Bibliography search:', query);
    setIsSearching(true);
    // Simulate search - ready for API connection
    setTimeout(() => setIsSearching(false), 2000);
  };

  return (
    <div className="h-[calc(100vh-8rem)] animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Módulo de Diagnóstico</h1>
          <p className="text-muted-foreground mt-1">Evaluación clínica asistida por IA</p>
        </div>
        <Select value={selectedPatientId} onValueChange={setSelectedPatientId}>
          <SelectTrigger className="w-full sm:w-[280px]">
            <SelectValue placeholder="Seleccionar paciente..." />
          </SelectTrigger>
          <SelectContent>
            {mockPatients.filter(p => p.status === 'active').map((patient) => (
              <SelectItem key={patient.id} value={patient.id}>
                {patient.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      
      {/* Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 h-[calc(100%-5rem)]">
        {/* Form Panel */}
        <div className="lg:col-span-3 overflow-auto">
          <div className="stat-card h-full overflow-auto">
            <DiagnosisForm 
              onSubmit={handleFormSubmit}
              onAnalyze={handleAnalyze}
            />
          </div>
        </div>
        
        {/* AI Insights Panel */}
        <div className="lg:col-span-2 h-full">
          <AIInsightsPanel 
            isSearching={isSearching}
            onSendMessage={handleChatMessage}
            onSearch={handleBibliographySearch}
          />
        </div>
      </div>
    </div>
  );
}
