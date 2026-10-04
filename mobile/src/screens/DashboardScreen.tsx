import React, { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { LinearGradient } from 'expo-linear-gradient';

import Banner from '../components/Banner';
import RiskCard from '../components/RiskCard';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import { colors, radius, shadow, spacing } from '../theme';
import type { ReportResponse } from '../types';

export default function DashboardScreen() {
  const { status, statusError, refreshStatus } = useApp();
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [reprocessing, setReprocessing] = useState(false);

  const load = useCallback(async () => {
    try {
      const next = await api.report();
      setReport(next);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar o relatório');
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await Promise.all([load(), refreshStatus()]);
    setRefreshing(false);
  }, [load, refreshStatus]);

  const onReprocess = useCallback(async () => {
    setReprocessing(true);
    try {
      await api.reprocess();
      await refreshStatus();
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao reprocessar o índice');
    } finally {
      setReprocessing(false);
    }
  }, [load, refreshStatus]);

  if (loading && !report) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.blue} />
        <Text style={styles.centerText}>Carregando relatório…</Text>
      </View>
    );
  }

  if (!report) {
    return (
      <View style={styles.center}>
        <Banner tone="error" text={error ?? 'Relatório indisponível'} />
        <Pressable style={styles.retry} onPress={load}>
          <Text style={styles.retryText}>Tentar novamente</Text>
        </Pressable>
      </View>
    );
  }

  const { summary, risk_cards: cards, ancestry, has_ancestry } = report.report;
  const degraded = status !== null && status.status !== 'ok';

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.blue} />
      }
    >
      <LinearGradient
        colors={['#002855', '#003DA5', '#0066CC']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.hero}
      >
        <View style={styles.badgePill}>
          <Text style={styles.badge}>DASA · Genética Preventiva</Text>
        </View>
        <Text style={styles.heroTitle}>Visão geral</Text>
        <Text style={styles.heroText}>
          Seus principais achados em linguagem clara e foco em prevenção.
        </Text>
      </LinearGradient>

      {degraded && status ? (
        <>
          <Banner
            tone="warning"
            text={`Índice ${status.status === 'error' ? 'indisponível' : 'desatualizado'} — reindexe para continuar com segurança.`}
          />
          <Pressable style={styles.reprocess} onPress={onReprocess} disabled={reprocessing}>
            {reprocessing ? (
              <ActivityIndicator color={colors.white} />
            ) : (
              <Text style={styles.reprocessText}>Reprocessar índice do relatório</Text>
            )}
          </Pressable>
        </>
      ) : null}

      {statusError ? <Banner tone="error" text={`API offline: ${statusError}`} /> : null}

      {error ? <Banner tone="error" text={error} /> : null}

      <View style={styles.summaryRow}>
        <SummaryCard
          value={summary.increased}
          label="Riscos aumentados"
          hint="Predisposição genética elevada"
          tint="#B8860B"
        />
        <SummaryCard
          value={summary.moderate}
          label="Riscos moderados"
          hint="Acompanhamento preventivo"
          tint="#2E86AB"
        />
        <SummaryCard
          value={summary.no_relevant_change}
          label="Sem alteração relevante"
          hint="Resultado dentro do esperado"
          tint="#2E7D32"
        />
      </View>

      <Text style={styles.section}>Principais achados ({cards.length})</Text>
      {cards.map((card) => (
        <RiskCard key={`${card.condition}-${card.risk_level_id}`} card={card} />
      ))}

      {has_ancestry && ancestry.length > 0 ? (
        <View style={styles.ancestryCard}>
          <Text style={styles.section}>Ancestralidade</Text>
          <View style={styles.ancestryBar}>
            {ancestry.map((item, index) => (
              <View
                key={item.origin}
                style={{
                  flex: Math.max(item.percentage, 4),
                  backgroundColor: ['\u0023003DA5', '\u00232E86AB', '\u00236C8EBF', '\u00239BB8D3', '\u0023C5D5E8'][
                    index % 5
                  ],
                }}
              />
            ))}
          </View>
          <View style={styles.ancestryLegend}>
            {ancestry.map((item) => (
              <View key={item.origin} style={styles.legendItem}>
                <Text style={styles.legendPct}>{Math.round(item.percentage)}%</Text>
                <Text style={styles.legendOrigin}>{item.origin}</Text>
              </View>
            ))}
          </View>
        </View>
      ) : null}

      {report.disclaimers.map((item) => (
        <Text key={item} style={styles.disclaimer}>
          ⚠️ {item}
        </Text>
      ))}
    </ScrollView>
  );
}

function SummaryCard({
  value,
  label,
  hint,
  tint,
}: {
  value: number;
  label: string;
  hint: string;
  tint: string;
}) {
  return (
    <View style={[styles.summaryCard, { borderTopColor: tint }]}>
      <Text style={styles.summaryValue}>{value}</Text>
      <Text style={styles.summaryLabel}>{label}</Text>
      <Text style={styles.summaryHint}>{hint}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing(2), paddingBottom: spacing(6) },
  center: {
    flex: 1,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing(3),
  },
  centerText: { marginTop: spacing(1.5), color: colors.textSoft, fontSize: 14 },
  retry: {
    marginTop: spacing(2),
    backgroundColor: colors.blue,
    borderRadius: radius.md,
    paddingVertical: spacing(1.5),
    paddingHorizontal: spacing(3),
  },
  retryText: { color: colors.white, fontWeight: '700' },
  hero: {
    borderRadius: radius.lg,
    paddingVertical: 28,
    paddingHorizontal: 32,
    marginBottom: spacing(2),
    ...shadow,
  },
  badgePill: {
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(255,255,255,0.18)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.35)',
    borderRadius: 999,
    paddingVertical: 4,
    paddingHorizontal: 12,
    marginBottom: 12,
  },
  badge: {
    color: colors.white,
    opacity: 0.95,
    fontSize: 12,
    fontWeight: '700',
  },
  heroTitle: { color: colors.white, fontSize: 28, fontWeight: '800', letterSpacing: -0.5 },
  heroText: { color: colors.white, fontSize: 15, lineHeight: 22, marginTop: 10, opacity: 0.95 },
  reprocess: {
    backgroundColor: colors.blue,
    borderRadius: radius.md,
    paddingVertical: spacing(1.5),
    alignItems: 'center',
    marginBottom: spacing(2),
  },
  reprocessText: { color: colors.white, fontWeight: '700', fontSize: 14 },
  summaryRow: { flexDirection: 'row', gap: spacing(1.5), marginBottom: spacing(2) },
  summaryCard: {
    flex: 1,
    backgroundColor: colors.white,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderTopWidth: 4,
    paddingVertical: 20,
    paddingHorizontal: 10,
    alignItems: 'center',
    marginBottom: 16,
    ...shadow,
  },
  summaryValue: { fontSize: 34, fontWeight: '800', color: colors.blue, lineHeight: 38 },
  summaryLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1F3A5F',
    marginTop: 4,
    textAlign: 'center',
  },
  summaryHint: {
    fontSize: 10.5,
    color: '#7A8CA6',
    marginTop: 2,
    textAlign: 'center',
  },
  section: { fontSize: 19, fontWeight: '800', color: colors.blueDark, marginBottom: 16 },
  ancestryCard: {
    backgroundColor: colors.white,
    borderRadius: radius.lg,
    padding: spacing(2),
    marginBottom: spacing(2),
    ...shadow,
  },
  ancestryBar: {
    flexDirection: 'row',
    height: 28,
    borderRadius: 999,
    overflow: 'hidden',
    marginBottom: 20,
  },
  ancestryLegend: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing(2) },
  legendItem: { alignItems: 'center', minWidth: 70, paddingVertical: 4 },
  legendPct: { fontWeight: '800', color: colors.blue, fontSize: 21 },
  legendOrigin: { fontSize: 13, color: colors.textSoft, fontWeight: '500' },
  disclaimer: {
    fontSize: 14,
    lineHeight: 21,
    color: '#6B5B2E',
    backgroundColor: '#FFF8E7',
    borderWidth: 1,
    borderColor: '#F0D9A8',
    borderLeftWidth: 5,
    borderLeftColor: '#B8860B',
    borderRadius: 10,
    paddingVertical: 13,
    paddingHorizontal: 16,
    marginBottom: 12,
  },
});
