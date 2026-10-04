import Constants from 'expo-constants';
import { Platform } from 'react-native';

/**
 * Endereço da API AIReport (Sprint 4 — Etapa 7).
 *
 * Sobrescreva com a variável de ambiente EXPO_PUBLIC_BASE_URL:
 *   EXPO_PUBLIC_BASE_URL=http://192.168.0.10:8010 npx expo start
 *
 * Padrões:
 *   - Emulador Android: 10.0.2.2 (host machine)
 *   - iOS/Expo Web: localhost
 *   - Expo Go no celular: use o IP da LAN da sua máquina
 */
const API_PORT = 8010;

/** 1) Endereço forçado por variável de ambiente (tem prioridade). */
function envBaseUrl(): string | null {
  const value = process.env.EXPO_PUBLIC_BASE_URL;
  if (value === undefined) {
    return null;
  }
  const trimmed = value.trim().replace(/\/+$/, '');
  return trimmed.length > 0 ? trimmed : null;
}

/**
 * 2) Host da máquina que roda o Metro (ex.: "192.168.0.10:8081").
 * No Expo Go (celular físico) isso resolve o IP do PC automaticamente.
 */
function hostFromExpo(): string | null {
  const hostUri =
    Constants.expoConfig?.hostUri ?? Constants.expoGoConfig?.debuggerHost ?? null;
  if (!hostUri) {
    return null;
  }
  const host = hostUri.split('?')[0].split('/')[0].split(':')[0];
  if (!host || host === 'localhost' || host === '127.0.0.1') {
    return null;
  }
  return `http://${host}:${API_PORT}`;
}

function resolveBaseUrl(): string {
  const fallback =
    Platform.OS === 'android'
      ? `http://10.0.2.2:${API_PORT}`
      : `http://localhost:${API_PORT}`;
  return envBaseUrl() ?? hostFromExpo() ?? fallback;
}

export const BASE_URL = resolveBaseUrl();
export const API_PREFIX = `${BASE_URL}/api/v1`;
