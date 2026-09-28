export const colors = {
  blue: '#003DA5',
  blueDark: '#002855',
  blueLight: '#E8F0FA',
  accent: '#0066CC',
  text: '#1A2B4A',
  textSoft: '#4A5F7A',
  white: '#FFFFFF',
  card: '#FFFFFF',
  border: '#D9E6F5',
  background: '#F4F8FC',
  success: '#2E7D32',
  warning: '#B8860B',
  danger: '#C62828',
  info: '#2E86AB',
  inputBg: '#F7FAFD',
  disabled: '#9BB8D3',
};

/** Cores semânticas (mesma escala não alarmista da web). */
export const riskColors: Record<string, string> = {
  INCREASED: '#B8860B',
  MODERATE: '#2E86AB',
  REDUCED: '#6B8E47',
  NORMAL: '#2E7D32',
  UNKNOWN: '#7A8CA6',
};

export const spacing = (units: number): number => units * 8;

export const radius = { sm: 8, md: 12, lg: 16 };

export const shadow = {
  shadowColor: '#004085',
  shadowOffset: { width: 0, height: 2 },
  shadowOpacity: 0.08,
  shadowRadius: 6,
  elevation: 3,
};
