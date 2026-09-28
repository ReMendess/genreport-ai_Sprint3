import React, { useCallback, useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import Banner from '../components/Banner';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import { colors, radius, shadow, spacing } from '../theme';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  sources?: string[];
  refused?: boolean;
  refusalReason?: string | null;
  groundedness?: number | null;
  showSources?: boolean;
}

const REFUSAL_LABEL: Record<string, string> = {
  no_context: 'Fora do escopo do relatório',
  prompt_injection: 'Bloqueado pelo guardrail de segurança',
  not_grounded: 'Sem fundamentação no trecho consultado',
  output_policy: 'Bloqueado pela política de conteúdo',
  empty: 'Pergunta vazia',
  too_long: 'Pergunta muito longa',
};

let nextId = 1;

export default function ChatScreen() {
  const { status, apiOnline } = useApp();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const listRef = useRef<FlatList<Message>>(null);

  const send = useCallback(async () => {
    const question = input.trim();
    if (question.length === 0 || sending) {
      return;
    }

    setInput('');
    setError(null);
    setSending(true);

    const userMessage: Message = { id: `u${nextId++}`, role: 'user', text: question };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const result = await api.chat(question);
      const assistant: Message = {
        id: `a${nextId++}`,
        role: 'assistant',
        text: result.answer,
        sources: result.sources,
        refused: result.refused,
        refusalReason: result.refusal_reason,
        groundedness: result.groundedness,
        showSources: false,
      };
      setMessages((prev) => [...prev, assistant]);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao enviar a pergunta');
      setMessages((prev) => [...prev, userMessage]);
    } finally {
      setSending(false);
      setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 80);
    }
  }, [input, sending]);

  const clear = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  const toggleSources = useCallback((id: string) => {
    setMessages((prev) =>
      prev.map((message) =>
        message.id === id ? { ...message, showSources: !message.showSources } : message,
      ),
    );
  }, []);

  const renderItem = ({ item }: { item: Message }) => {
    const isUser = item.role === 'user';
    return (
      <View style={[styles.bubble, isUser ? styles.userBubble : styles.botBubble]}>
        {!isUser && item.refused ? (
          <View style={styles.refusalBadge}>
            <Text style={styles.refusalBadgeText}>
              {REFUSAL_LABEL[item.refusalReason ?? ''] ?? 'Resposta bloqueada'}
            </Text>
          </View>
        ) : null}
        <Text style={[styles.bubbleText, isUser ? styles.userText : styles.botText]}>{item.text}</Text>

        {!isUser && item.sources && item.sources.length > 0 ? (
          <Pressable onPress={() => toggleSources(item.id)} style={styles.sourcesToggle}>
            <Text style={styles.sourcesToggleText}>
              {item.showSources ? '▲ Ocultar fontes' : `▼ Fontes utilizadas (${item.sources.length})`}
            </Text>
          </Pressable>
        ) : null}

        {item.showSources && item.sources
          ? item.sources.map((source, index) => (
              <View key={`src-${index}`} style={styles.sourceCard}>
                <Text style={styles.sourceText} numberOfLines={8}>
                  {source}
                </Text>
              </View>
            ))
          : null}

        {!isUser && !item.refused && item.groundedness !== null && item.groundedness !== undefined ? (
          <Text style={styles.grounding}>Fundamentação: {Math.round(item.groundedness * 100)}%</Text>
        ) : null}
      </View>
    );
  };

  const disclaimer = status?.report.found
    ? 'Este assistente não substitui consulta médica. Sempre consulte um profissional de saúde.'
    : 'Este assistente não substitui consulta médica.';

  return (
    <KeyboardAvoidingView
      style={styles.screen}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={90}
    >
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Assistente genético</Text>
        <View style={styles.headerRight}>
          <View
            style={[
              styles.apiChip,
              apiOnline === false ? styles.apiChipOffline : styles.apiChipOnline,
            ]}
          >
            <Text style={styles.apiChipText}>
              {apiOnline === null ? '…' : apiOnline ? 'API conectada' : 'API offline'}
            </Text>
          </View>
          <Pressable onPress={clear} accessibilityRole="button">
            <Text style={styles.headerAction}>Nova conversa</Text>
          </Pressable>
        </View>
      </View>

      <FlatList
        ref={listRef}
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyTitle}>Pergunte sobre o seu relatório</Text>
            <Text style={styles.emptyText}>
              Ex.: Quais são meus principais riscos?{'\n'}O que significa predisposição aumentada?
            </Text>
          </View>
        }
      />

      {error ? (
        <View style={styles.errorBox}>
          <Banner tone="error" text={error} />
        </View>
      ) : null}

      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Faça uma pergunta sobre o relatório…"
          placeholderTextColor={colors.disabled}
          multiline
          maxLength={2000}
          editable={!sending}
          onSubmitEditing={send}
        />
        <Pressable
          style={[styles.sendButton, (sending || input.trim().length === 0) && styles.sendDisabled]}
          onPress={send}
          disabled={sending || input.trim().length === 0}
          accessibilityRole="button"
        >
          {sending ? (
            <ActivityIndicator color={colors.white} size="small" />
          ) : (
            <Text style={styles.sendText}>➤</Text>
          )}
        </Pressable>
      </View>

      <Text style={styles.disclaimer}>{disclaimer}</Text>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing(2),
    paddingVertical: spacing(1.5),
    backgroundColor: colors.white,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  headerTitle: { fontSize: 16, fontWeight: '800', color: colors.blueDark },
  headerAction: { fontSize: 13, fontWeight: '700', color: colors.accent },
  headerRight: { flexDirection: 'row', alignItems: 'center', gap: spacing(1) },
  apiChip: {
    borderRadius: 999,
    paddingHorizontal: spacing(1),
    paddingVertical: 3,
    borderWidth: 1,
  },
  apiChipOnline: { backgroundColor: '#E8F5E9', borderColor: colors.success },
  apiChipOffline: { backgroundColor: '#FDECEA', borderColor: colors.danger },
  apiChipText: { fontSize: 10.5, fontWeight: '700', color: colors.textSoft },
  list: { padding: spacing(2), flexGrow: 1 },
  empty: { alignItems: 'center', paddingTop: spacing(6), paddingHorizontal: spacing(2) },
  emptyTitle: { fontSize: 17, fontWeight: '800', color: colors.blueDark },
  emptyText: {
    marginTop: spacing(1),
    fontSize: 13.5,
    color: colors.textSoft,
    textAlign: 'center',
    lineHeight: 21,
  },
  bubble: {
    borderRadius: radius.md,
    padding: spacing(1.5),
    marginBottom: spacing(1.5),
    maxWidth: '92%',
    ...shadow,
  },
  userBubble: { alignSelf: 'flex-end', backgroundColor: colors.blue },
  botBubble: { alignSelf: 'flex-start', backgroundColor: colors.white, borderLeftWidth: 4, borderLeftColor: colors.accent },
  bubbleText: { fontSize: 14, lineHeight: 20 },
  userText: { color: colors.white },
  botText: { color: colors.text },
  refusalBadge: {
    backgroundColor: colors.blueLight,
    borderRadius: 999,
    alignSelf: 'flex-start',
    paddingHorizontal: spacing(1),
    paddingVertical: 3,
    marginBottom: spacing(0.75),
  },
  refusalBadgeText: { fontSize: 11, fontWeight: '700', color: colors.warning },
  sourcesToggle: { marginTop: spacing(1) },
  sourcesToggleText: { fontSize: 12, fontWeight: '700', color: colors.accent },
  sourceCard: {
    marginTop: spacing(1),
    backgroundColor: colors.inputBg,
    borderRadius: radius.sm,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    padding: spacing(1),
  },
  sourceText: { fontSize: 11.5, lineHeight: 17, color: colors.textSoft },
  grounding: { marginTop: spacing(0.75), fontSize: 10.5, color: colors.disabled },
  errorBox: { paddingHorizontal: spacing(2) },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: spacing(2),
    paddingVertical: spacing(1),
    backgroundColor: colors.white,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
  },
  input: {
    flex: 1,
    minHeight: 44,
    maxHeight: 120,
    backgroundColor: colors.inputBg,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing(1.5),
    paddingVertical: spacing(1),
    fontSize: 14,
    color: colors.text,
  },
  sendButton: {
    marginLeft: spacing(1),
    width: 46,
    height: 46,
    borderRadius: 23,
    backgroundColor: colors.blue,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendDisabled: { backgroundColor: colors.disabled },
  sendText: { color: colors.white, fontSize: 18, fontWeight: '700' },
  disclaimer: {
    fontSize: 10.5,
    color: colors.textSoft,
    textAlign: 'center',
    paddingHorizontal: spacing(2),
    paddingVertical: spacing(1),
    backgroundColor: colors.background,
  },
});
