import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { RiskCard as RiskCardModel } from '../types';
import { colors, radius, shadow, spacing } from '../theme';

/**
 * Card de risco — ESPELHA o CSS da web (app/ui.py: .dasa-risk-card):
 *   padding 1.25rem 1.5rem (20/24) · radius 12 · borda esquerda 5px colorida
 *   categoria 0.72rem (11.5) · título 1.1rem (17.5) · badge 0.78rem (12.5)
 *   descrição 0.9rem (14.5)/lh 1.55 · resumo IA e recomendações em bloco azul
 */
export default function RiskCard({ card }: { card: RiskCardModel }) {
  const [expanded, setExpanded] = useState(false);
  const accent = card.risk_color || colors.warning;
  const badgeBg = card.risk_badge_color || colors.blueLight;

  return (
    <Pressable
      accessibilityRole="button"
      onPress={() => setExpanded((value) => !value)}
      style={[styles.card, { borderLeftColor: accent }]}
    >
      <View style={styles.header}>
        <View style={styles.titleBlock}>
          <Text style={styles.category}>{card.category}</Text>
          <Text style={styles.title}>{card.condition}</Text>
        </View>
        <View style={[styles.badge, { backgroundColor: badgeBg, borderColor: `${accent}55` }]}>
          <Text style={[styles.badgeText, { color: accent }]}>
            {card.risk_icon} {card.risk_display}
          </Text>
        </View>
      </View>

      {card.ai_summary ? (
        <View style={styles.aiSummary}>
          <Text style={styles.aiSummaryText}>
            <Text style={styles.aiSummaryLabel}>Resumo: </Text>
            {card.ai_summary}
          </Text>
        </View>
      ) : null}

      <Text style={styles.short}>{card.risk_short_description}</Text>

      {expanded ? (
        <View style={styles.detail}>
          <Text style={styles.detailLabel}>Descrição do relatório</Text>
          <Text style={styles.detailText}>{card.description || 'Sem descrição detalhada.'}</Text>

          {card.recommendations.length > 0 ? (
            <View style={styles.recommendations}>
              <Text style={styles.recommendationsTitle}>Recomendações de prevenção</Text>
              {card.recommendations.map((item) => (
                <Text key={item} style={styles.recommendationItem}>
                  •  {item}
                </Text>
              ))}
            </View>
          ) : null}

          <Text style={styles.toggle}>▲ Fechar</Text>
        </View>
      ) : (
        <Text style={styles.toggle}>▼ Ver mais sobre {card.condition}</Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    borderLeftWidth: 5,
    borderRadius: radius.md,
    paddingVertical: 20,
    paddingHorizontal: 24,
    marginBottom: 20,
    ...shadow,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 6,
  },
  titleBlock: {
    flex: 1,
    paddingRight: spacing(1),
    minWidth: 0,
  },
  category: {
    fontSize: 11.5,
    fontWeight: '700',
    color: colors.accent,
    textTransform: 'uppercase',
    letterSpacing: 0.7,
    marginBottom: 1,
  },
  title: {
    fontSize: 17.5,
    fontWeight: '700',
    color: colors.blueDark,
    lineHeight: 23,
  },
  badge: {
    borderRadius: 999,
    borderWidth: 1,
    paddingVertical: 6,
    paddingHorizontal: 14,
    maxWidth: '50%',
  },
  badgeText: {
    fontSize: 12.5,
    fontWeight: '700',
  },
  aiSummary: {
    backgroundColor: colors.blueLight,
    borderWidth: 1,
    borderColor: '#C5D8F0',
    borderRadius: radius.sm,
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  aiSummaryText: {
    fontSize: 14.5,
    lineHeight: 22,
    color: '#1F3A5F',
  },
  aiSummaryLabel: {
    fontWeight: '700',
    color: colors.blueDark,
  },
  short: {
    color: colors.textSoft,
    fontSize: 14.5,
    lineHeight: 22.5,
    marginBottom: 12,
  },
  detail: {
    marginTop: spacing(0.5),
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
  },
  detailLabel: {
    fontSize: 11.5,
    fontWeight: '700',
    color: colors.accent,
    textTransform: 'uppercase',
    letterSpacing: 0.7,
    marginBottom: 4,
  },
  detailText: {
    fontSize: 14.5,
    lineHeight: 22,
    color: colors.text,
  },
  recommendations: {
    backgroundColor: colors.blueLight,
    borderRadius: radius.sm,
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginTop: 12,
  },
  recommendationsTitle: {
    fontSize: 13.5,
    fontWeight: '700',
    color: '#1F3A5F',
    marginBottom: 4,
  },
  recommendationItem: {
    fontSize: 13.5,
    lineHeight: 20,
    color: '#1F3A5F',
  },
  toggle: {
    marginTop: 12,
    color: colors.accent,
    fontSize: 12.5,
    fontWeight: '600',
  },
});
