import { createContext, useContext, useState, ReactNode } from 'react';
import { CopilotButton } from './CopilotButton';
import { CopilotPanel } from './CopilotPanel';

interface CopilotContextType {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
  patientName: string;
  setPatientName: (name: string) => void;
}

const CopilotContext = createContext<CopilotContextType | undefined>(undefined);

export function useCopilot() {
  const context = useContext(CopilotContext);
  if (!context) {
    throw new Error('useCopilot must be used within a CopilotProvider');
  }
  return context;
}

interface CopilotProviderProps {
  children: ReactNode;
}

export function CopilotProvider({ children }: CopilotProviderProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [patientName, setPatientName] = useState('María García López');

  const open = () => setIsOpen(true);
  const close = () => setIsOpen(false);
  const toggle = () => setIsOpen((prev) => !prev);

  return (
    <CopilotContext.Provider value={{ isOpen, open, close, toggle, patientName, setPatientName }}>
      {children}
      <CopilotButton onClick={toggle} isOpen={isOpen} />
      <CopilotPanel isOpen={isOpen} onClose={close} patientName={patientName} />
    </CopilotContext.Provider>
  );
}
