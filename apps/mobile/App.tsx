import { StatusBar } from 'expo-status-bar';
import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import {
  ChatLine,
  OfflineError,
  ReportRequest,
  Reporter,
  TurnCore,
  createHttpReporter,
  createHttpTurnCore,
} from './src/core';
import {
  publicReadOnlyTools,
  ReadOnlyTools,
  SearchResult,
  validateCity,
  validateSearchQuery,
  WeatherResult,
} from './src/tools';

const COLORS = {
  ink: '#19251f',
  muted: '#65736b',
  green: '#175b42',
  pale: '#eef5ef',
  border: '#dfe7e1',
  paper: '#fbfcfa',
  white: '#ffffff',
  error: '#922f2b',
};

type Tab = 'Home' | 'Chat' | 'Projects';
export type Project = { id: string; name: string; description?: string };
export type ProjectsLoader = () => Promise<Project[]>;
const emptyProjectsLoader: ProjectsLoader = async () => [];
type ProjectsState =
  | { status: 'loading' }
  | { status: 'error'; message?: string }
  | { status: 'ready'; projects: Project[] };
type ReplyState = 'sending' | 'waiting' | 'success' | 'error' | 'offline';
type Message = {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  state?: ReplyState;
  reportState?: 'sending' | 'sent' | 'error';
};
type PendingTurn = {
  sessionId: string;
  requestId: string;
  history: ChatLine[];
  assistantId: string;
};

export interface AppProps {
  apiBaseUrl?: string;
  turnCore?: TurnCore;
  tools?: ReadOnlyTools;
  reporter?: Reporter;
  projectsLoader?: ProjectsLoader;
}

function makeId(prefix: string): string {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

function AppButton({
  label,
  onPress,
  disabled = false,
  secondary = false,
}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  secondary?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        secondary && styles.secondaryButton,
        disabled && styles.disabledButton,
        pressed && !disabled && styles.pressedButton,
      ]}
    >
      <Text allowFontScaling style={[styles.buttonText, secondary && styles.secondaryButtonText]}>
        {label}
      </Text>
    </Pressable>
  );
}

function HomeScreen({ onOpen }: { onOpen: (tab: Tab) => void }) {
  return (
    <ScrollView contentContainerStyle={styles.page}>
      <Text style={styles.eyebrow}>MAYA</Text>
      <Text accessibilityRole="header" style={styles.title}>A place to pick up the thread.</Text>
      <Text style={styles.body}>Start a conversation or open a project. Your next step is yours to choose.</Text>
      <View style={styles.entryCard}>
        <Text accessibilityRole="header" style={styles.cardTitle}>Chat</Text>
        <Text style={styles.body}>Send a message through the shared Maya turn service.</Text>
        <AppButton label="Go to Chat" onPress={() => onOpen('Chat')} />
      </View>
      <View style={styles.entryCard}>
        <Text accessibilityRole="header" style={styles.cardTitle}>Projects</Text>
        <Text style={styles.body}>See the projects available in this shell.</Text>
        <AppButton label="Go to Projects" onPress={() => onOpen('Projects')} secondary />
      </View>
      <Text style={styles.smallText}>No sign-in, social feed, location access, or checkout in this slice.</Text>
    </ScrollView>
  );
}

export function ProjectsScreen({ state }: { state: ProjectsState }) {
  if (state.status === 'loading') {
    return (
      <View style={styles.page}>
        <Text accessibilityRole="header" style={styles.title}>Projects</Text>
        <Text accessibilityRole="progressbar" accessibilityLabel="Loading projects" style={styles.body}>Loading projects…</Text>
      </View>
    );
  }
  if (state.status === 'error') {
    return (
      <View style={styles.page}>
        <Text accessibilityRole="header" style={styles.title}>Projects</Text>
        <View accessibilityRole="alert" style={styles.noticeError}>
          <Text style={styles.errorText}>{state.message || 'Projects could not be loaded. Try again later.'}</Text>
        </View>
      </View>
    );
  }
  return (
    <ScrollView contentContainerStyle={styles.page}>
      <Text accessibilityRole="header" style={styles.title}>Projects</Text>
      {state.projects.length === 0 ? (
        <View style={styles.entryCard}>
          <Text style={styles.cardTitle}>No projects yet</Text>
          <Text style={styles.body}>Projects will appear here when a project source is connected.</Text>
        </View>
      ) : state.projects.map((project) => (
        <View key={project.id} style={styles.entryCard}>
          <Text accessibilityRole="header" style={styles.cardTitle}>{project.name}</Text>
          {project.description ? <Text style={styles.body}>{project.description}</Text> : null}
        </View>
      ))}
    </ScrollView>
  );
}

function StatusLine({ children, error = false, alert = false }: { children: string; error?: boolean; alert?: boolean }) {
  return <Text accessibilityRole={alert ? 'alert' : undefined} accessibilityLiveRegion={alert ? 'assertive' : 'polite'} style={[styles.smallText, error && styles.errorText]}>{children}</Text>;
}

function ChatScreen({
  core,
  tools,
  reporter,
  sessionId,
}: {
  core: TurnCore;
  tools: ReadOnlyTools;
  reporter: Reporter;
  sessionId: string;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchStatus, setSearchStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [searchError, setSearchError] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [weatherCity, setWeatherCity] = useState('');
  const [weatherStatus, setWeatherStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [weatherError, setWeatherError] = useState('');
  const [weatherResult, setWeatherResult] = useState<WeatherResult | null>(null);
  const pendingTurns = useRef<Record<string, PendingTurn>>({});
  const busyRef = useRef(false);

  const updateReply = (assistantId: string, update: (message: Message) => Message) => {
    setMessages((current) => current.map((message) => message.id === assistantId ? update(message) : message));
  };

  const performTurn = async (turn: PendingTurn) => {
    if (busyRef.current) return;
    busyRef.current = true;
    setBusy(true);
    updateReply(turn.assistantId, (message) => ({ ...message, state: 'sending', text: '' }));
    try {
      await new Promise<void>((resolve) => setTimeout(resolve, 0));
      updateReply(turn.assistantId, (message) => ({ ...message, state: 'waiting' }));
      const reply = await core.complete({
        sessionId: turn.sessionId,
        requestId: turn.requestId,
        messages: turn.history,
      });
      delete pendingTurns.current[turn.assistantId];
      updateReply(turn.assistantId, (message) => ({ ...message, text: reply, state: 'success' }));
    } catch (error) {
      const offline = error instanceof OfflineError || (error as { code?: string })?.code === 'offline';
      const text = error instanceof Error ? error.message : 'That turn could not be completed.';
      updateReply(turn.assistantId, (message) => ({ ...message, text, state: offline ? 'offline' : 'error' }));
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  };

  const hasRetry = messages.some((message) => message.role === 'assistant' && (message.state === 'offline' || message.state === 'error'));

  const sendMessage = async () => {
    const text = draft.trim();
    if (!text || busyRef.current || hasRetry) return;
    const userMessage: Message = { id: makeId('user'), role: 'user', text };
    const assistantId = makeId('assistant');
    const previousHistory: ChatLine[] = messages.flatMap<ChatLine>((message) => {
      if (message.role === 'user') return [{ role: 'user' as const, content: message.text }];
      if (message.role === 'assistant' && message.state === 'success') return [{ role: 'assistant' as const, content: message.text }];
      return [];
    });
    const history = [...previousHistory, { role: 'user' as const, content: text }];
    const turn: PendingTurn = { sessionId, requestId: assistantId, history, assistantId };
    pendingTurns.current[assistantId] = turn;
    setMessages((current) => [
      ...current,
      userMessage,
      { id: assistantId, role: 'assistant', text: '', state: 'sending' },
    ]);
    setDraft('');
    await performTurn(turn);
  };

  const retryTurn = (assistantId: string) => {
    const turn = pendingTurns.current[assistantId];
    if (turn) void performTurn(turn);
  };

  const reportReply = async (message: Message) => {
    if (message.reportState === 'sending' || message.reportState === 'sent') return;
    updateReply(message.id, (current) => ({ ...current, reportState: 'sending' }));
    const report: ReportRequest = {
      reportId: `report-${message.id}`,
      sessionId,
      messageId: message.id,
      category: 'offensive_output',
      content: message.text,
    };
    try {
      await reporter.submit(report);
      updateReply(message.id, (current) => ({ ...current, reportState: 'sent' }));
    } catch {
      updateReply(message.id, (current) => ({ ...current, reportState: 'error' }));
    }
  };

  const runSearch = async () => {
    let query: string;
    try {
      query = validateSearchQuery(searchQuery);
    } catch (error) {
      setSearchError(error instanceof Error ? error.message : 'Check the search query.');
      setSearchStatus('error');
      return;
    }
    setSearchStatus('loading');
    setSearchError('');
    setSearchResults([]);
    try {
      setSearchResults(await tools.search(query));
      setSearchStatus('success');
    } catch (error) {
      setSearchError(error instanceof Error ? error.message : 'Search could not be completed.');
      setSearchStatus('error');
    }
  };

  const runWeather = async () => {
    let city: string;
    try {
      city = validateCity(weatherCity);
    } catch (error) {
      setWeatherError(error instanceof Error ? error.message : 'Check the city name.');
      setWeatherStatus('error');
      return;
    }
    setWeatherStatus('loading');
    setWeatherError('');
    setWeatherResult(null);
    try {
      setWeatherResult(await tools.weather(city));
      setWeatherStatus('success');
    } catch (error) {
      setWeatherError(error instanceof Error ? error.message : 'Weather could not be loaded.');
      setWeatherStatus('error');
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.chatPage} keyboardShouldPersistTaps="handled">
      <Text accessibilityRole="header" style={styles.title}>Chat</Text>
      <Text style={styles.smallText}>Messages use the shared Maya turn service. This session stays on this device until you leave or close the app.</Text>

      <View style={styles.messages} accessibilityLabel="Conversation messages">
        {messages.length === 0 ? <Text style={styles.body}>Start with a message when you’re ready.</Text> : null}
        {messages.map((message) => (
          <View key={message.id} style={[styles.messageCard, message.role === 'user' ? styles.userMessage : styles.assistantMessage]}>
            <Text style={styles.messageRole}>{message.role === 'user' ? 'You' : 'Maya'}</Text>
            {message.state === 'sending' ? <StatusLine>Sending…</StatusLine> : null}
            {message.state === 'waiting' ? <StatusLine>Maya is waiting for a reply…</StatusLine> : null}
            {message.text ? <Text accessibilityLabel={`${message.role === 'user' ? 'You' : 'Maya'}: ${message.text}`} style={styles.messageText}>{message.text}</Text> : null}
            {message.state === 'success' ? <StatusLine>Reply received</StatusLine> : null}
            {message.state === 'success' ? (
              <View style={styles.messageActions}>
                <AppButton
                  label={message.reportState === 'sent' ? 'Report sent' : message.reportState === 'sending' ? 'Sending report…' : message.reportState === 'error' ? 'Retry report' : 'Report reply'}
                  onPress={() => void reportReply(message)}
                  disabled={message.reportState === 'sent' || message.reportState === 'sending'}
                  secondary
                />
                {message.reportState === 'error' ? <StatusLine error alert>Report not sent. Check your connection and retry.</StatusLine> : null}
              </View>
            ) : null}
            {(message.state === 'offline' || message.state === 'error') ? (
              <View style={styles.messageActions}>
                <StatusLine error>{message.state === 'offline' ? `Offline: ${message.text}` : message.text}</StatusLine>
                <AppButton label="Retry turn" onPress={() => retryTurn(message.id)} secondary />
              </View>
            ) : null}
          </View>
        ))}
      </View>

      <View style={styles.entryCard}>
        <TextInput
          accessibilityLabel="Message Maya"
          allowFontScaling
          multiline
          maxLength={4000}
          placeholder="Write a message"
          placeholderTextColor={COLORS.muted}
          value={draft}
          onChangeText={setDraft}
          style={styles.input}
          editable={!busy && !hasRetry}
        />
        <AppButton label="Send message" onPress={() => void sendMessage()} disabled={busy || hasRetry || !draft.trim()} />
      </View>
      {hasRetry ? <StatusLine error>Retry this turn before sending another so messages stay in order.</StatusLine> : null}

      <View style={styles.toolPanel}>
        <Text accessibilityRole="header" style={styles.cardTitle}>Read-only tools</Text>
        <Text style={styles.smallText}>Only the buttons below start public lookups. Results are shown as untrusted text.</Text>
        <TextInput
          accessibilityLabel="Public web search query"
          allowFontScaling
          maxLength={200}
          placeholder="Search the public web"
          placeholderTextColor={COLORS.muted}
          value={searchQuery}
          onChangeText={setSearchQuery}
          style={styles.input}
        />
        <AppButton label="Search the web" onPress={() => void runSearch()} disabled={searchStatus === 'loading'} secondary />
        {searchStatus === 'loading' ? <StatusLine>Searching the public web…</StatusLine> : null}
        {searchStatus === 'error' ? <StatusLine error>{searchError}</StatusLine> : null}
        {searchStatus === 'success' ? (
          <View accessibilityLiveRegion="polite">
            <Text style={styles.smallText}>Search results from DuckDuckGo</Text>
            {searchResults.length === 0 ? <Text style={styles.body}>No results were returned.</Text> : searchResults.map((result, index) => (
              <View key={`${result.url}-${index}`} style={styles.sourceCard}>
                <Text style={styles.sourceTitle}>{result.title}</Text>
                <Text selectable style={styles.sourceUrl}>{result.url}</Text>
                <Text style={styles.smallText}>Source: {new URL(result.url).hostname}</Text>
              </View>
            ))}
          </View>
        ) : null}

        <TextInput
          accessibilityLabel="Weather city"
          allowFontScaling
          maxLength={80}
          placeholder="Enter a city"
          placeholderTextColor={COLORS.muted}
          value={weatherCity}
          onChangeText={setWeatherCity}
          style={styles.input}
        />
        <AppButton label="Get weather for this city" onPress={() => void runWeather()} disabled={weatherStatus === 'loading'} secondary />
        {weatherStatus === 'loading' ? <StatusLine>Getting weather for the city you entered…</StatusLine> : null}
        {weatherStatus === 'error' ? <StatusLine error>{weatherError}</StatusLine> : null}
        {weatherResult ? (
          <View accessibilityLiveRegion="polite" style={styles.sourceCard}>
            <Text style={styles.sourceTitle}>{weatherResult.city}{weatherResult.country ? `, ${weatherResult.country}` : ''}</Text>
            <Text style={styles.messageText}>{weatherResult.conditions}, {weatherResult.temperatureC}°C{weatherResult.apparentTemperatureC === undefined ? '' : ` (feels like ${weatherResult.apparentTemperatureC}°C)`}</Text>
            <Text style={styles.smallText}>Source: {weatherResult.source} · Updated: {weatherResult.updatedAt}</Text>
          </View>
        ) : null}
      </View>
    </ScrollView>
  );
}

function NavBar({ active, onSelect }: { active: Tab; onSelect: (tab: Tab) => void }) {
  return (
    <View accessibilityRole="tablist" style={styles.navBar}>
      {(['Home', 'Chat', 'Projects'] as Tab[]).map((tab) => (
        <Pressable
          key={tab}
          accessibilityRole="tab"
          accessibilityLabel={`${tab} tab`}
          accessibilityState={{ selected: active === tab }}
          onPress={() => onSelect(tab)}
          style={[styles.navItem, active === tab && styles.navItemActive]}
        >
          <Text allowFontScaling style={[styles.navText, active === tab && styles.navTextActive]}>{tab}</Text>
        </Pressable>
      ))}
    </View>
  );
}

export default function App({ apiBaseUrl, turnCore, tools, reporter, projectsLoader }: AppProps) {
  const configuredBaseUrl = apiBaseUrl ?? process.env.EXPO_PUBLIC_MAYA_API_BASE_URL ?? '';
  const core = useMemo(() => turnCore ?? createHttpTurnCore(configuredBaseUrl), [turnCore, configuredBaseUrl]);
  const readOnlyTools = tools ?? publicReadOnlyTools;
  const reportClient = useMemo(() => reporter ?? createHttpReporter(configuredBaseUrl), [reporter, configuredBaseUrl]);
  const loadProjects = projectsLoader ?? emptyProjectsLoader;
  const [activeTab, setActiveTab] = useState<Tab>('Home');
  const [projectState, setProjectState] = useState<ProjectsState>({ status: 'loading' });
  const [sessionId] = useState(() => makeId('session'));

  useEffect(() => {
    let current = true;
    Promise.resolve().then(() => loadProjects()).then((projects) => {
      if (current) setProjectState({ status: 'ready', projects });
    }).catch(() => {
      if (current) setProjectState({ status: 'error', message: 'Projects could not be loaded. Try again later.' });
    });
    return () => { current = false; };
  }, [loadProjects]);

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.safe} edges={['top', 'right', 'bottom', 'left']}>
      <StatusBar style="dark" />
      <View style={styles.header}>
        <Text style={styles.brand}>Maya</Text>
        <Text style={styles.headerCaption}>A small, private-feeling space to talk</Text>
      </View>
      <View style={styles.screenHost}>
        <View style={activeTab === 'Home' ? styles.visibleScreen : styles.hiddenScreen} accessibilityElementsHidden={activeTab !== 'Home'} importantForAccessibility={activeTab === 'Home' ? 'auto' : 'no-hide-descendants'}>
          <HomeScreen onOpen={setActiveTab} />
        </View>
        <View style={activeTab === 'Chat' ? styles.visibleScreen : styles.hiddenScreen} accessibilityElementsHidden={activeTab !== 'Chat'} importantForAccessibility={activeTab === 'Chat' ? 'auto' : 'no-hide-descendants'}>
          <ChatScreen core={core} tools={readOnlyTools} reporter={reportClient} sessionId={sessionId} />
        </View>
        <View style={activeTab === 'Projects' ? styles.visibleScreen : styles.hiddenScreen} accessibilityElementsHidden={activeTab !== 'Projects'} importantForAccessibility={activeTab === 'Projects' ? 'auto' : 'no-hide-descendants'}>
          <ProjectsScreen state={projectState} />
        </View>
      </View>
      <NavBar active={activeTab} onSelect={setActiveTab} />
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.paper },
  header: { paddingHorizontal: 20, paddingTop: 8, paddingBottom: 12, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: COLORS.border },
  brand: { color: COLORS.green, fontSize: 21, fontWeight: '700' },
  headerCaption: { color: COLORS.muted, fontSize: 13, marginTop: 2 },
  screenHost: { flex: 1 },
  visibleScreen: { flex: 1 },
  hiddenScreen: { display: 'none' },
  page: { flexGrow: 1, padding: 20, gap: 16 },
  chatPage: { padding: 16, gap: 14, paddingBottom: 30 },
  eyebrow: { color: COLORS.green, letterSpacing: 2, fontWeight: '700', fontSize: 12 },
  title: { color: COLORS.ink, fontSize: 27, lineHeight: 34, fontWeight: '700' },
  cardTitle: { color: COLORS.ink, fontSize: 18, lineHeight: 24, fontWeight: '700' },
  body: { color: COLORS.ink, fontSize: 16, lineHeight: 24 },
  smallText: { color: COLORS.muted, fontSize: 13, lineHeight: 19 },
  entryCard: { padding: 16, gap: 12, borderRadius: 16, backgroundColor: COLORS.white, borderColor: COLORS.border, borderWidth: 1 },
  toolPanel: { padding: 16, gap: 12, borderRadius: 16, backgroundColor: COLORS.pale, borderColor: COLORS.border, borderWidth: 1 },
  button: { minHeight: 48, paddingHorizontal: 16, paddingVertical: 12, borderRadius: 12, backgroundColor: COLORS.green, alignItems: 'center', justifyContent: 'center' },
  secondaryButton: { backgroundColor: COLORS.white, borderWidth: 1, borderColor: COLORS.green },
  disabledButton: { opacity: 0.52 },
  pressedButton: { opacity: 0.78 },
  buttonText: { color: COLORS.white, fontSize: 16, lineHeight: 22, fontWeight: '700', textAlign: 'center' },
  secondaryButtonText: { color: COLORS.green },
  input: { minHeight: 48, maxHeight: 112, borderWidth: 1, borderColor: COLORS.border, borderRadius: 12, backgroundColor: COLORS.white, color: COLORS.ink, paddingHorizontal: 14, paddingVertical: 12, fontSize: 16, textAlignVertical: 'top' },
  messages: { gap: 10 },
  messageCard: { maxWidth: '94%', borderRadius: 14, padding: 12, gap: 6 },
  userMessage: { alignSelf: 'flex-end', backgroundColor: '#e7f1e9' },
  assistantMessage: { alignSelf: 'flex-start', backgroundColor: COLORS.white, borderWidth: 1, borderColor: COLORS.border },
  messageRole: { color: COLORS.green, fontSize: 12, fontWeight: '700' },
  messageText: { color: COLORS.ink, fontSize: 16, lineHeight: 24 },
  messageActions: { gap: 8, marginTop: 4 },
  noticeError: { padding: 14, backgroundColor: '#fff0ee', borderRadius: 12 },
  errorText: { color: COLORS.error, fontSize: 14, lineHeight: 20 },
  sourceCard: { padding: 12, marginTop: 8, backgroundColor: COLORS.white, borderRadius: 10, borderColor: COLORS.border, borderWidth: 1, gap: 4 },
  sourceTitle: { color: COLORS.ink, fontSize: 15, lineHeight: 21, fontWeight: '700' },
  sourceUrl: { color: COLORS.green, fontSize: 13, lineHeight: 18 },
  navBar: { flexDirection: 'row', padding: 8, paddingTop: 6, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: COLORS.border, backgroundColor: COLORS.white },
  navItem: { flex: 1, minHeight: 48, alignItems: 'center', justifyContent: 'center', borderRadius: 12 },
  navItemActive: { backgroundColor: COLORS.pale },
  navText: { color: COLORS.muted, fontSize: 15, fontWeight: '600' },
  navTextActive: { color: COLORS.green, fontWeight: '700' },
});
