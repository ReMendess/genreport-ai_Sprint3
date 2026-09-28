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
function resolveBaseUrl(): string {
  const fromEnv = process.env.EXPO_PUBLIC_BASE_URL;
  if (fromEnv && fromEnv.trim().length > 0) {
    return fromEnv.trim().replace(/\/+$/, '');
  }
  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8010';
  }
  return 'http://localhost:8010';
}

export const BASE_URL = resolveBaseUrl();
export const API_PREFIX = `${BASE_URL}/api/v1`;
