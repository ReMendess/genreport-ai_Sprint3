import AsyncStorage from '@react-native-async-storage/async-storage';
import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';

import { api } from '../services/api';
import type { StatusResponse } from '../types';

const STORAGE_KEY = '@aireport/consent_v1';

export type ConsentState = 'checking' | 'pending' | 'granted' | 'denied';

interface AppContextValue {
  booting: boolean;
  consent: ConsentState;
  status: StatusResponse | null;
  statusError: string | null;
  apiOnline: boolean | null;
  policyVersion: string | null;
  refreshStatus: () => Promise<void>;
  acceptConsent: () => Promise<void>;
  denyConsent: () => Promise<void>;
}

const AppContext = createContext<AppContextValue | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [booting, setBooting] = useState(true);
  const [consent, setConsent] = useState<ConsentState>('checking');
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [policyVersion, setPolicyVersion] = useState<string | null>(null);

  const refreshStatus = useCallback(async () => {
    try {
      const next = await api.status();
      setStatus(next);
      setStatusError(null);
      setApiOnline(true);
    } catch (error) {
      setStatus(null);
      setStatusError(error instanceof Error ? error.message : 'Erro desconhecido');
      setApiOnline(false);
    }
  }, []);

  const acceptConsent = useCallback(async () => {
    setConsent('granted');
    try {
      const remote = await api.setConsent(true);
      setPolicyVersion(remote.policy_version);
    } catch {
      // Offline: decisão local prevalece; sincroniza quando houver rede.
    }
    try {
      await AsyncStorage.setItem(STORAGE_KEY, 'granted');
    } catch {
      // melhor esforço
    }
  }, []);

  const denyConsent = useCallback(async () => {
    setConsent('denied');
    try {
      await api.setConsent(false);
    } catch {
      // offline ok
    }
    try {
      await AsyncStorage.setItem(STORAGE_KEY, 'denied');
    } catch {
      // melhor esforço
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      let local: string | null = null;
      try {
        local = await AsyncStorage.getItem(STORAGE_KEY);
      } catch {
        local = null;
      }

      try {
        const remote = await api.getConsent();
        if (!cancelled) {
          setPolicyVersion(remote.current_policy_version);
          if (remote.granted) {
            setConsent('granted');
          } else if (local === 'granted') {
            // local sim, API não: ressincroniza
            api.setConsent(true).catch(() => undefined);
            setConsent('granted');
          } else {
            setConsent(local === 'denied' ? 'denied' : 'pending');
          }
        }
      } catch {
        if (!cancelled) {
          setConsent(local === 'granted' ? 'granted' : local === 'denied' ? 'denied' : 'pending');
        }
      }

      if (!cancelled) {
        setBooting(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!booting) {
      refreshStatus();
    }
  }, [booting, refreshStatus]);

  const value = useMemo<AppContextValue>(
    () => ({
      booting,
      consent,
      status,
      statusError,
      apiOnline,
      policyVersion,
      refreshStatus,
      acceptConsent,
      denyConsent,
    }),
    [booting, consent, status, statusError, apiOnline, policyVersion, refreshStatus, acceptConsent, denyConsent],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppContextValue {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp deve ser usado dentro de AppProvider');
  }
  return context;
}
