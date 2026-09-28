import { StatusBar } from 'expo-status-bar';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import React from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { AppProvider, useApp } from './src/context/AppContext';
import ChatScreen from './src/screens/ChatScreen';
import ConsentScreen from './src/screens/ConsentScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import StatusScreen from './src/screens/StatusScreen';
import { colors, spacing } from './src/theme';

const Tab = createBottomTabNavigator();

const navTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: colors.blue,
    background: colors.background,
    card: colors.white,
    text: colors.text,
    border: colors.border,
  },
};

function tabIcon(icon: string) {
  return ({ color, size }: { color: string; size: number }) => (
    <Text style={{ fontSize: size - 4, color }}>{icon}</Text>
  );
}

function Root() {
  const { booting, consent } = useApp();

  if (booting || consent === 'checking') {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.blue} />
        <Text style={styles.centerText}>Verificando API e consentimento…</Text>
      </View>
    );
  }

  if (consent !== 'granted') {
    return <ConsentScreen />;
  }

  return (
    <NavigationContainer theme={navTheme}>
      <Tab.Navigator
        screenOptions={{
          headerShown: false,
          tabBarActiveTintColor: colors.blue,
          tabBarInactiveTintColor: colors.disabled,
          tabBarStyle: { borderTopColor: colors.border },
        }}
      >
        <Tab.Screen
          name="Painel"
          component={DashboardScreen}
          options={{ tabBarIcon: tabIcon('\uD83E\uDDEC') }}
        />
        <Tab.Screen
          name="Chat"
          component={ChatScreen}
          options={{ tabBarIcon: tabIcon('\uD83D\uDCAC') }}
        />
        <Tab.Screen
          name="Status"
          component={StatusScreen}
          options={{ tabBarIcon: tabIcon('\uD83D\uDEE1\uFE0F') }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
}

export default function App() {
  return (
    <AppProvider>
      <StatusBar style="light" backgroundColor={colors.blue} />
      <Root />
    </AppProvider>
  );
}

const styles = StyleSheet.create({
  center: {
    flex: 1,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing(3),
  },
  centerText: { marginTop: spacing(1.5), color: colors.textSoft, fontSize: 14 },
});
