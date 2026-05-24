import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import type { SelectionItem, UserContextModel } from '../types/api';

type SetSelections = (selections: SelectionItem[] | ((prev: SelectionItem[]) => SelectionItem[])) => void;

interface DiagnosisContextValue {
  selections: SelectionItem[];
  setSelections: SetSelections;
  addSelection: (sel: SelectionItem) => void;
  removeSelection: (sel: SelectionItem) => void;
  clearSelections: () => void;
  userContext: UserContextModel;
  setUserContext: (context: UserContextModel) => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
  drawerOpen: boolean;
  setDrawerOpen: (open: boolean) => void;
}

const DiagnosisContext = createContext<DiagnosisContextValue | null>(null);

export function DiagnosisProvider({ children }: { children: ReactNode }) {
  const [selections, setSelections] = useState<SelectionItem[]>([]);
  const [userContext, setUserContext] = useState<UserContextModel>({ phenomenon: '', stack: '', params: '' });
  const [loading, setLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const addSelection = useCallback((sel: SelectionItem) => {
    setSelections(prev => {
      const exists = prev.some(s =>
        s.type === sel.type &&
        s.id === sel.id &&
        s.group_key === sel.group_key
      );
      if (exists) return prev;
      return [...prev, sel];
    });
  }, []);

  const removeSelection = useCallback((sel: SelectionItem) => {
    setSelections(prev => prev.filter(s =>
      !(s.type === sel.type && s.id === sel.id && s.group_key === sel.group_key)
    ));
  }, []);

  const clearSelections = useCallback(() => {
    setSelections([]);
    setUserContext({ phenomenon: '', stack: '', params: '' });
  }, []);

  return (
    <DiagnosisContext.Provider value={{
      selections,
      setSelections,
      addSelection,
      removeSelection,
      clearSelections,
      userContext,
      setUserContext,
      loading,
      setLoading,
      drawerOpen,
      setDrawerOpen,
    }}>
      {children}
    </DiagnosisContext.Provider>
  );
}

export function useDiagnosis() {
  const context = useContext(DiagnosisContext);
  if (!context) {
    throw new Error('useDiagnosis must be used within DiagnosisProvider');
  }
  return context;
}
