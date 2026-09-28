import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import Banner from '../components/Banner';
import { useApp } from '../context/AppContext';
import { BASE_URL } from '../config';
import { api } from '../services/api';
import { colors, radius, shadow, spacing } from '../theme';
import type { MetricsResponse } from '../types';

export default function StatusScreen() {
  const { status, statusError, refreshStatus, consent, policyVersion } = useApp();
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    await refreshStatus();
    try {
      setMetrics(await api.metrics());
    } catch {
      setMetrics(null);
    }
  }, [refreshStatus]);

  useEffect(() => {
    load();
  }, [load]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  const stateTone =
    status === null ? 'error' : status.status === 'ok' ? 'success' : 'warning';
  const stateText =
    status === null
      ? `API inacessível (${statusError ?? 'erro desconhecido'})`
      : status.status === 'ok'
        ? 'Tudo operacional — índice válido e relatório carregado.'
        : `Estado ${status.status}: índice ${status.index.valid ? 'válido' : 'desatualizado'}.`;

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.blue} />
      }
    >
      <View style={styles.hero}>
        <Text style={styles.heroTitle}>Status da operação</Text>
        <Text style={styles.heroText}>Endpoints /status e /metrics (Etapa 6)</Text>
      </View>

      <Banner tone={stateTone} text={stateText} />

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Serviço</Text>
        <Row label="Serviço" value={status?.service ?? '—'} />
        <Row label="Endpoint" value={BASE_URL} />
        <Row label="Uptime" value={status ? `${Math.round(status.uptime_seconds)}s` : '—'} />
        <Row label="Iniciado" value={status?.started_at ?? '—'} />
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Relatório e índice</Text>
        <Row label="PDF" value={status?.report.found ? status.report.name ?? 'sim' : 'não encontrado'} />
        <Row
          label="Tamanho"
          value={status?.report.size_bytes ? `${status.report.size_bytes} bytes` : '—'}
        />
        <Row label="Fingerprint" value={status?.report.fingerprint ?? '—'} />
        <Row label="Índice" value={status?.index.valid ? 'válido (cache)' : 'reindex necessário'} />
        <Row
          label="Embeddings"
          value={status?.index.embedding_model ?? '—'}
        />
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Governança</Text>
        <Row label="Consentimento" value={consent === 'granted' ? 'concedido' : 'pendente'} />
        <Row label="Política" value={policyVersion ? `v${policyVersion}` : '—'} />
        <Row
          label="Retenção de logs"
          value={status ? `${status.logging.retention_days} dias` : '—'}
        />
        <Row
          label="audit.log"
          value={status ? `${status.logging.audit_log_bytes} bytes` : '—'}
        />
      </View>

      {metrics ? (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Métricas (em memória)</Text>
          <Row label="Requisições" value={String(metrics.http.requests_total)} />
          <Row label="Erros 4xx / 5xx" value={`${metrics.http.errors_client_total} / ${metrics.http.errors_server_total}`} />
          <Row label="Turnos de chat" value={String(metrics.chat.turns_total)} />
          <Row label="Recusas" value={String(metrics.chat.refusals_total)} />
          <Row
            label="Groundedness médio"
            value={metrics.chat.groundedness_avg !== null ? String(metrics.chat.groundedness_avg) : '—'}
          />
        </View>
      ) : null}

      <Pressable style={styles.refresh} onPress={load}>
        <Text style={styles.refreshText}>Atualizar status</Text>
      </Pressable>
    </ScrollView>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.row}>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text style={styles.rowValue} numberOfLines={1}>
        {value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing(2), paddingBottom: spacing(6) },
  hero: {
    backgroundColor: colors.blueDark,
    borderRadius: radius.lg,
    padding: spacing(2.5),
    marginBottom: spacing(2),
    ...shadow,
  },
  heroTitle: { color: colors.white, fontSize: 20, fontWeight: '800' },
  heroText: { color: colors.white, fontSize: 13, marginTop: spacing(0.5), opacity: 0.9 },
  card: {
    backgroundColor: colors.white,
    borderRadius: radius.lg,
    padding: spacing(2),
    marginBottom: spacing(1.5),
    ...shadow,
  },
  cardTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: colors.blue,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    marginBottom: spacing(1),
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: spacing(0.5),
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
    gap: spacing(1),
  },
  rowLabel: { fontSize: 13, color: colors.textSoft, flexShrink: 0 },
  rowValue: { fontSize: 13, color: colors.text, fontWeight: '600', flex: 1, textAlign: 'right' },
  refresh: {
    backgroundColor: colors.blue,
    borderRadius: radius.md,
    paddingVertical: spacing(1.5),
    alignItems: 'center',
    marginTop: spacing(1),
  },
  refreshText: { color: colors.white, fontWeight: '700', fontSize: 14 },
});
