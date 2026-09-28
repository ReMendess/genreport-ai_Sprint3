import React, { useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import Banner from '../components/Banner';
import { useApp } from '../context/AppContext';
import { colors, radius, shadow, spacing } from '../theme';

export default function ConsentScreen() {
  const { acceptConsent, denyConsent, policyVersion, statusError } = useApp();
  const [busy, setBusy] = useState<'accept' | 'deny' | null>(null);
  const [denied, setDenied] = useState(false);

  const onAccept = async () => {
    setBusy('accept');
    await acceptConsent();
    setBusy(null);
  };

  const onDeny = async () => {
    setBusy('deny');
    await denyConsent();
    setDenied(true);
    setBusy(null);
  };

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled"
    >
      <View style={styles.hero}>
        <Text style={styles.badge}>DASA · Genética Preventiva</Text>
        <Text style={styles.heroTitle}>AIReport Gen-Experience</Text>
        <Text style={styles.heroText}>
          Converse com o seu relatório genético em linguagem simples, com foco em prevenção.
        </Text>
      </View>

      {statusError ? (
        <Banner tone="warning" text={`API indisponível (${statusError}). Você pode aceitar agora e sincronizar depois.`} />
      ) : null}

      {denied ? (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Uso recusado</Text>
          <Text style={styles.cardText}>
            Nenhum dado será tratado pelo assistente. Você pode mudar de ideia quando quiser.
          </Text>
          <Pressable style={styles.primaryButton} onPress={onAccept} disabled={busy !== null}>
            {busy === 'accept' ? (
              <ActivityIndicator color={colors.white} />
            ) : (
              <Text style={styles.primaryButtonText}>Aceitar agora</Text>
            )}
          </Pressable>
        </View>
      ) : (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Consentimento (LGPD)</Text>
          <Text style={styles.cardText}>
            Seus dados genéticos são <Text style={styles.bold}>sensíveis</Text>. Antes de usar:
          </Text>

          <View style={styles.bullet}>
            <Text style={styles.bulletText}>
              • Finalidade: explicar <Text style={styles.bold}>apenas</Text> o seu relatório, sem
              diagnóstico ou prescrição.
            </Text>
          </View>
          <View style={styles.bullet}>
            <Text style={styles.bulletText}>
              • Armazenamento: processamento local da API; logs sem conteúdo das conversas.
            </Text>
          </View>
          <View style={styles.bullet}>
            <Text style={styles.bulletText}>
              • Revogação: a qualquer momento pelo app (art. 8º, LGPD).
            </Text>
          </View>
          <View style={styles.bullet}>
            <Text style={styles.bulletText}>
              • Este assistente <Text style={styles.bold}>não substitui</Text> consulta médica.
            </Text>
          </View>

          {policyVersion ? (
            <Text style={styles.policy}>Política vigente: v{policyVersion}</Text>
          ) : null}

          <Pressable style={styles.primaryButton} onPress={onAccept} disabled={busy !== null}>
            {busy === 'accept' ? (
              <ActivityIndicator color={colors.white} />
            ) : (
              <Text style={styles.primaryButtonText}>Aceitar e continuar</Text>
            )}
          </Pressable>

          <Pressable style={styles.ghostButton} onPress={onDeny} disabled={busy !== null}>
            {busy === 'deny' ? (
              <ActivityIndicator color={colors.blue} />
            ) : (
              <Text style={styles.ghostButtonText}>Recusar uso dos dados</Text>
            )}
          </Pressable>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing(2), paddingBottom: spacing(6) },
  hero: {
    backgroundColor: colors.blue,
    borderRadius: radius.lg,
    padding: spacing(3),
    marginBottom: spacing(2),
    ...shadow,
  },
  badge: {
    color: colors.white,
    opacity: 0.9,
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: spacing(1),
  },
  heroTitle: { color: colors.white, fontSize: 24, fontWeight: '800' },
  heroText: { color: colors.white, fontSize: 14, lineHeight: 20, marginTop: spacing(1), opacity: 0.95 },
  card: {
    backgroundColor: colors.white,
    borderRadius: radius.lg,
    padding: spacing(3),
    ...shadow,
  },
  cardTitle: { fontSize: 18, fontWeight: '800', color: colors.blueDark, marginBottom: spacing(1) },
  cardText: { fontSize: 14, lineHeight: 21, color: colors.text, marginBottom: spacing(1) },
  bold: { fontWeight: '700' },
  bullet: { marginBottom: spacing(0.75) },
  bulletText: { fontSize: 13.5, lineHeight: 20, color: colors.text },
  policy: { fontSize: 12, color: colors.textSoft, marginTop: spacing(1.5) },
  primaryButton: {
    backgroundColor: colors.blue,
    borderRadius: radius.md,
    paddingVertical: spacing(1.75),
    alignItems: 'center',
    marginTop: spacing(2),
  },
  primaryButtonText: { color: colors.white, fontSize: 15, fontWeight: '700' },
  ghostButton: {
    borderRadius: radius.md,
    borderWidth: 1.5,
    borderColor: colors.blue,
    paddingVertical: spacing(1.5),
    alignItems: 'center',
    marginTop: spacing(1.5),
  },
  ghostButtonText: { color: colors.blue, fontSize: 14, fontWeight: '700' },
});
