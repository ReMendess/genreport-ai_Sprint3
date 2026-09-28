import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { RiskCard as RiskCardModel } from '../types';
import { colors, radius, shadow, spacing } from '../theme';

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

      <Text style={styles.short}>{card.risk_short_description}</Text>

      {expanded ? (
        <View style={styles.detail}>
          <Text style={styles.detailLabel}>Descrição do relatório</Text>
          <Text style={styles.detailText}>{card.description || 'Sem descrição detalhada.'}</Text>

          {card.ai_summary ? (
            <>
              <Text style={styles.detailLabel}>Resumo automático</Text>
              <Text style={styles.detailText}>{card.ai_summary}</Text>
            </>
          ) : null}

          {card.recommendations.length > 0 ? (
            <>
              <Text style={styles.detailLabel}>Recomendações do relatório</Text>
              {card.recommendations.map((item) => (
                <Text key={item} style={styles.recommendation}>
                  • {item}
                </Text>
              ))}
            </>
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
    borderLeftWidth: 5,
    borderRadius: radius.md,
    padding: spacing(2),
    marginBottom: spacing(1.5),
    ...shadow,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing(0.5),
  },
  titleBlock: {
    flex: 1,
    paddingRight: spacing(1),
  },
  category: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.textSoft,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.blueDark,
    marginTop: 2,
  },
  badge: {
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: spacing(1),
    paddingVertical: spacing(0.4),
    maxWidth: '48%',
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '700',
  },
  short: {
    color: colors.textSoft,
    fontSize: 13,
    lineHeight: 19,
  },
  detail: {
    marginTop: spacing(1),
    paddingTop: spacing(1),
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
  },
  detailLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.blue,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: spacing(1),
    marginBottom: 4,
  },
  detailText: {
    fontSize: 13,
    lineHeight: 19,
    color: colors.text,
  },
  recommendation: {
    fontSize: 13,
    lineHeight: 20,
    color: colors.text,
  },
  toggle: {
    marginTop: spacing(1),
    color: colors.accent,
    fontSize: 12,
    fontWeight: '600',
  },
});
