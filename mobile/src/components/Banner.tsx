import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { colors, radius, spacing } from '../theme';

type Tone = 'info' | 'success' | 'warning' | 'error';

const TONE_COLORS: Record<Tone, string> = {
  info: colors.info,
  success: colors.success,
  warning: colors.warning,
  error: colors.danger,
};

const TONE_LABEL: Record<Tone, string> = {
  info: 'ℹ️',
  success: '✅',
  warning: '⚠️',
  error: '⛔',
};

export default function Banner({ tone = 'info', text }: { tone?: Tone; text: string }) {
  const accent = TONE_COLORS[tone];
  return (
    <View style={[styles.container, { borderLeftColor: accent }]}>
      <Text style={styles.icon}>{TONE_LABEL[tone]}</Text>
      <Text style={styles.text}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.white,
    borderLeftWidth: 4,
    borderRadius: radius.md,
    padding: spacing(1.5),
    marginBottom: spacing(1.5),
    flexDirection: 'row',
    alignItems: 'flex-start',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
  },
  icon: {
    marginRight: spacing(1),
    fontSize: 14,
    marginTop: 2,
  },
  text: {
    flex: 1,
    color: colors.text,
    fontSize: 13,
    lineHeight: 19,
  },
});
