import { createContext, useContext, useState, useCallback } from 'react';

const ScanContext = createContext(null);

export function ScanProvider({ children }) {
  const [lastScan, setLastScan] = useState(null);

  const recordScan = useCallback((scanData, fileName) => {
    setLastScan({
      data: scanData,
      fileName,
      timestamp: new Date().toISOString(),
    });
  }, []);

  const clearLastScan = useCallback(() => setLastScan(null), []);

  return (
    <ScanContext.Provider value={{ lastScan, recordScan, clearLastScan }}>
      {children}
    </ScanContext.Provider>
  );
}

export function useLastScan() {
  const ctx = useContext(ScanContext);
  if (!ctx) throw new Error('useLastScan must be used inside ScanProvider');
  return ctx;
}
