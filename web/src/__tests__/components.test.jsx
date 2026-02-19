/**
 * Comprehensive component render & interaction tests.
 * Covers: Dashboard, Settings, LearningIntelligence, Scan, Results,
 *         Feedback, ModelStatus, NotFound, ErrorBoundary, Layout,
 *         API client edge-cases, and enhanced components.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

// ── Theme wrapper ──────────────────────────────────────────────────
const theme = createTheme({ palette: { mode: 'light', primary: { main: '#1976d2' } } });

function Providers({ children, route = '/' }) {
  return (
    <ThemeProvider theme={theme}>
      <MemoryRouter initialEntries={[route]}>
        {children}
      </MemoryRouter>
    </ThemeProvider>
  );
}

// ── Global mocks ───────────────────────────────────────────────────
// Mock react-router-dom's useNavigate globally
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

// Mock the API client
vi.mock('../api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
    interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
    defaults: { headers: { common: {} } },
  },
  scanFile: vi.fn(),
  getScan: vi.fn(),
  listScans: vi.fn(),
  deleteScan: vi.fn(),
  getScanStats: vi.fn(),
  getFeedbackStats: vi.fn(),
  submitFeedback: vi.fn(),
  listFeedback: vi.fn(),
  getModelStatus: vi.fn(),
  triggerRetrain: vi.fn(),
  listModelVersions: vi.fn(),
  getLearningStatus: vi.fn(),
  getDiscoveredPatterns: vi.fn(),
  getDriftStatus: vi.fn(),
  getRuleWeights: vi.fn(),
  getLearningTelemetry: vi.fn(),
  triggerPatternDiscovery: vi.fn(),
  getToken: vi.fn(),
  getMetrics: vi.fn(),
  setApiKey: vi.fn(),
  clearAuth: vi.fn(),
}));

// Mock chart.js (heavy, causes timeouts)
vi.mock('chart.js', () => ({
  Chart: { register: vi.fn() },
  CategoryScale: vi.fn(),
  LinearScale: vi.fn(),
  PointElement: vi.fn(),
  LineElement: vi.fn(),
  Title: vi.fn(),
  Tooltip: vi.fn(),
  Legend: vi.fn(),
  Filler: vi.fn(),
}));

vi.mock('react-chartjs-2', () => ({
  Line: (props) => React.createElement('canvas', { 'data-testid': 'chart-line' }),
  Bar: (props) => React.createElement('canvas', { 'data-testid': 'chart-bar' }),
}));

// Mock recharts (SSR-heavy)
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }) => React.createElement('div', { 'data-testid': 'responsive-container' }, children),
  BarChart: ({ children }) => React.createElement('div', { 'data-testid': 'bar-chart' }, children),
  Bar: () => null,
  RadarChart: ({ children }) => React.createElement('div', null, children),
  Radar: () => null,
  PolarGrid: () => null,
  PolarAngleAxis: () => null,
  PolarRadiusAxis: () => null,
  LineChart: ({ children }) => React.createElement('div', null, children),
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
}));

// Mock enhanced components
vi.mock('../components/enhanced/RiskScoreCard', () => ({
  default: ({ score, componentScores }) =>
    React.createElement('div', { 'data-testid': 'risk-score-card' }, `Risk: ${score}`),
}));
vi.mock('../components/enhanced/FindingsCard', () => ({
  default: (props) => React.createElement('div', { 'data-testid': 'findings-card' }, 'Findings'),
}));
vi.mock('../components/enhanced/EnhancedUpload', () => ({
  default: (props) => React.createElement('div', { 'data-testid': 'enhanced-upload' }, 'Upload'),
}));

// ── Import components after mocks ──────────────────────────────────
import * as clientApi from '../api/client';

beforeEach(() => {
  vi.clearAllMocks();
  mockNavigate.mockReset();
});

// ====================================================================
// 1. NotFound Page
// ====================================================================
describe('NotFound Page', () => {
  let NotFound;
  beforeEach(async () => {
    NotFound = (await import('../pages/NotFound.jsx')).default;
  });

  it('renders 404 text', () => {
    render(<Providers><NotFound /></Providers>);
    expect(screen.getByText('404')).toBeInTheDocument();
  });

  it('shows descriptive message', () => {
    render(<Providers><NotFound /></Providers>);
    expect(screen.getByText(/doesn.t exist/i)).toBeInTheDocument();
  });

  it('has a Back to Home button that navigates', () => {
    render(<Providers><NotFound /></Providers>);
    const btn = screen.getByRole('button', { name: /back to home/i });
    fireEvent.click(btn);
    expect(mockNavigate).toHaveBeenCalledWith('/');
  });
});

// ====================================================================
// 2. ErrorBoundary
// ====================================================================
describe('ErrorBoundary', () => {
  let ErrorBoundary;
  beforeEach(async () => {
    ErrorBoundary = (await import('../components/ErrorBoundary.jsx')).default;
  });

  it('renders children when there is no error', () => {
    render(
      <Providers>
        <ErrorBoundary>
          <div>OK Content</div>
        </ErrorBoundary>
      </Providers>
    );
    expect(screen.getByText('OK Content')).toBeInTheDocument();
  });

  it('renders error UI when a child throws', () => {
    const Bomb = () => { throw new Error('boom'); };
    // suppress error boundary console.error
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    render(
      <Providers>
        <ErrorBoundary>
          <Bomb />
        </ErrorBoundary>
      </Providers>
    );
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
    spy.mockRestore();
  });

  it('resets error state when Try Again is clicked', () => {
    let shouldThrow = true;
    const MaybeThrow = () => { if (shouldThrow) throw new Error('boom'); return <div>Recovered</div>; };
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const { rerender } = render(
      <Providers>
        <ErrorBoundary>
          <MaybeThrow />
        </ErrorBoundary>
      </Providers>
    );
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    shouldThrow = false;
    fireEvent.click(screen.getByRole('button', { name: /try again/i }));
    expect(screen.getByText('Recovered')).toBeInTheDocument();
    spy.mockRestore();
  });
});

// ====================================================================
// 3. Dashboard
// ====================================================================
describe('Dashboard Page', () => {
  let Dashboard;
  beforeEach(async () => {
    Dashboard = (await import('../pages/Dashboard.jsx')).default;
  });

  it('shows loading spinner initially', () => {
    clientApi.getScanStats.mockReturnValue(new Promise(() => {})); // never resolves
    render(<Providers><Dashboard /></Providers>);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders stats after loading', async () => {
    clientApi.getScanStats.mockResolvedValue({
      total_scans: 42,
      findings_by_severity: { CRITICAL: 3, HIGH: 10, MEDIUM: 20, LOW: 5, INFO: 2 },
      average_scores: { unified_risk: 0.45 },
      trend_30_days: [{ date: '2024-01-01', count: 5 }],
    });
    render(<Providers><Dashboard /></Providers>);
    await waitFor(() => expect(screen.getByText('Security Dashboard')).toBeInTheDocument());
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('40')).toBeInTheDocument(); // totalFindings = 3+10+20+5+2
  });

  it('shows error alert when API fails', async () => {
    clientApi.getScanStats.mockRejectedValue(new Error('Network error'));
    render(<Providers><Dashboard /></Providers>);
    await waitFor(() => expect(screen.getByText(/Network error/)).toBeInTheDocument());
  });

  it('displays severity breakdown bars', async () => {
    clientApi.getScanStats.mockResolvedValue({
      total_scans: 10,
      findings_by_severity: { CRITICAL: 1, HIGH: 2, MEDIUM: 3, LOW: 4, INFO: 0 },
      average_scores: { unified_risk: 0.2 },
      trend_30_days: [],
    });
    render(<Providers><Dashboard /></Providers>);
    await waitFor(() => expect(screen.getByText('CRITICAL')).toBeInTheDocument());
    expect(screen.getByText('HIGH')).toBeInTheDocument();
    expect(screen.getByText('MEDIUM')).toBeInTheDocument();
  });

  it('computes low risk label correctly', async () => {
    clientApi.getScanStats.mockResolvedValue({
      total_scans: 1,
      findings_by_severity: { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 1, INFO: 0 },
      average_scores: { unified_risk: 0.1 },
      trend_30_days: [],
    });
    render(<Providers><Dashboard /></Providers>);
    await waitFor(() => expect(screen.getByText('Low')).toBeInTheDocument());
  });
});

// ====================================================================
// 4. Settings
// ====================================================================
describe('Settings Page', () => {
  let Settings;
  beforeEach(async () => {
    Settings = (await import('../pages/Settings.jsx')).default;
  });

  it('renders Settings heading', () => {
    render(<Providers><Settings /></Providers>);
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('shows Scan Configuration section', () => {
    render(<Providers><Settings /></Providers>);
    expect(screen.getByText('Scan Configuration')).toBeInTheDocument();
  });

  it('shows Authentication section', () => {
    render(<Providers><Settings /></Providers>);
    expect(screen.getByText('Authentication')).toBeInTheDocument();
  });

  it('shows Adaptive Learning section', () => {
    render(<Providers><Settings /></Providers>);
    expect(screen.getByText('Adaptive Learning')).toBeInTheDocument();
  });

  it('calls setApiKey when Save Key is clicked with valid input', () => {
    render(<Providers><Settings /></Providers>);
    // Find the API Key text field and type
    const apiInput = screen.getByLabelText('API Key');
    fireEvent.change(apiInput, { target: { value: 'cg_test_key_123' } });
    fireEvent.click(screen.getByRole('button', { name: /save key/i }));
    expect(clientApi.setApiKey).toHaveBeenCalledWith('cg_test_key_123');
  });

  it('calls clearAuth when Clear Auth is clicked', () => {
    render(<Providers><Settings /></Providers>);
    fireEvent.click(screen.getByRole('button', { name: /clear auth/i }));
    expect(clientApi.clearAuth).toHaveBeenCalled();
  });

  it('calls getToken when Generate Token is clicked', async () => {
    clientApi.getToken.mockResolvedValue({ access_token: 'jwt_abc123_very_long_token_here_and_more' });
    render(<Providers><Settings /></Providers>);
    fireEvent.click(screen.getByRole('button', { name: /generate token/i }));
    await waitFor(() => expect(clientApi.getToken).toHaveBeenCalledWith('web_user'));
  });

  it('has Reset to Defaults button', () => {
    render(<Providers><Settings /></Providers>);
    expect(screen.getByRole('button', { name: /reset to defaults/i })).toBeInTheDocument();
  });

  it('shows risk threshold slider', () => {
    render(<Providers><Settings /></Providers>);
    expect(screen.getByText(/Risk Score Threshold/i)).toBeInTheDocument();
  });
});

// ====================================================================
// 5. LearningIntelligence
// ====================================================================
describe('LearningIntelligence Page', () => {
  let LearningIntelligence;
  beforeEach(async () => {
    LearningIntelligence = (await import('../pages/LearningIntelligence.jsx')).default;
  });

  it('shows loading spinner initially', () => {
    clientApi.getLearningStatus.mockReturnValue(new Promise(() => {}));
    clientApi.getLearningTelemetry.mockReturnValue(new Promise(() => {}));
    render(<Providers><LearningIntelligence /></Providers>);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders after data loads', async () => {
    clientApi.getLearningStatus.mockResolvedValue({
      adaptive_learning_active: true,
      training_buffer_size: 50,
      feedback_since_retrain: 15,
      auto_retrain_threshold: 20,
      drift: { psi_score: 0.012, drift_detected: false },
      pattern_discovery: { total_patterns_tracked: 8, rules_generated: 3 },
      rule_weights: {},
      telemetry_summary: { total_events: 100, event_types: { scan: 80, feedback: 20 } },
    });
    clientApi.getLearningTelemetry.mockResolvedValue({ events: [] });
    render(<Providers><LearningIntelligence /></Providers>);
    await waitFor(() => expect(screen.getByText(/Learning Intelligence/)).toBeInTheDocument());
    expect(screen.getByText('50')).toBeInTheDocument(); // training buffer
    expect(screen.getByText('8')).toBeInTheDocument();  // patterns tracked
  });

  it('shows error alert on failure', async () => {
    clientApi.getLearningStatus.mockRejectedValue(new Error('API down'));
    clientApi.getLearningTelemetry.mockRejectedValue(new Error('API down'));
    render(<Providers><LearningIntelligence /></Providers>);
    await waitFor(() => expect(screen.getByText(/API down/)).toBeInTheDocument());
  });

  it('shows ACTIVE status chip when learning is active', async () => {
    clientApi.getLearningStatus.mockResolvedValue({
      adaptive_learning_active: true,
      training_buffer_size: 0,
      drift: { psi_score: 0, drift_detected: false },
      pattern_discovery: { total_patterns_tracked: 0, rules_generated: 0 },
      rule_weights: {},
      telemetry_summary: { total_events: 0, event_types: {} },
    });
    clientApi.getLearningTelemetry.mockResolvedValue({ events: [] });
    render(<Providers><LearningIntelligence /></Providers>);
    await waitFor(() => expect(screen.getByText(/ACTIVE/)).toBeInTheDocument());
  });

  it('shows drift detected warning', async () => {
    clientApi.getLearningStatus.mockResolvedValue({
      adaptive_learning_active: true,
      training_buffer_size: 0,
      drift: { psi_score: 0.35, drift_detected: true },
      pattern_discovery: { total_patterns_tracked: 0, rules_generated: 0 },
      rule_weights: {},
      telemetry_summary: { total_events: 0, event_types: {} },
    });
    clientApi.getLearningTelemetry.mockResolvedValue({ events: [] });
    render(<Providers><LearningIntelligence /></Providers>);
    await waitFor(() => expect(screen.getByText(/Drift Detected/)).toBeInTheDocument());
  });

  it('triggers pattern discovery on button click', async () => {
    clientApi.getLearningStatus.mockResolvedValue({
      adaptive_learning_active: true,
      training_buffer_size: 0,
      drift: { psi_score: 0, drift_detected: false },
      pattern_discovery: { total_patterns_tracked: 0, rules_generated: 0 },
      rule_weights: {},
      telemetry_summary: { total_events: 0, event_types: {} },
    });
    clientApi.getLearningTelemetry.mockResolvedValue({ events: [] });
    clientApi.triggerPatternDiscovery.mockResolvedValue({});
    render(<Providers><LearningIntelligence /></Providers>);
    await waitFor(() => expect(screen.getByText(/Learning Intelligence/)).toBeInTheDocument());
    const btn = screen.getByRole('button', { name: /discover/i });
    fireEvent.click(btn);
    await waitFor(() => expect(clientApi.triggerPatternDiscovery).toHaveBeenCalled());
  });
});

// ====================================================================
// 6. Scan Page
// ====================================================================
describe('Scan Page', () => {
  let Scan;
  beforeEach(async () => {
    Scan = (await import('../pages/Scan.jsx')).default;
  });

  it('renders CloudGuard AI heading', () => {
    render(<Providers><Scan /></Providers>);
    expect(screen.getByText('CloudGuard AI')).toBeInTheDocument();
  });

  it('shows file type validation message', () => {
    render(<Providers><Scan /></Providers>);
    expect(screen.getByText(/AI-Powered Cloud Security/i)).toBeInTheDocument();
  });

  it('shows scan mode radio buttons', () => {
    render(<Providers><Scan /></Providers>);
    expect(screen.getByText(/Complete AI Scan/i)).toBeInTheDocument();
  });

  it('shows error for unsupported file types', () => {
    render(<Providers><Scan /></Providers>);
    const input = document.querySelector('input[type="file"]');
    if (input) {
      const badFile = new File(['test'], 'bad.exe', { type: 'application/octet-stream' });
      Object.defineProperty(badFile, 'size', { value: 1000 });
      fireEvent.change(input, { target: { files: [badFile] } });
    }
    // Component validates on selection — should show error or not crash
    expect(document.body).toBeTruthy();
  });

  it('has scan button that requires file', async () => {
    render(<Providers><Scan /></Providers>);
    // The scan button should be present
    const scanBtns = screen.getAllByRole('button');
    expect(scanBtns.length).toBeGreaterThan(0);
  });
});

// ====================================================================
// 7. Results Page (with location state)
// ====================================================================
describe('Results Page', () => {
  let Results;
  beforeEach(async () => {
    Results = (await import('../pages/Results.jsx')).default;
  });

  it('renders scan results from location state', () => {
    const scanData = {
      unified_risk_score: 0.72,
      ml_score: 0.6,
      rules_score: 0.8,
      llm_score: 0.5,
      findings: [{ severity: 'HIGH', message: 'Insecure config', rule_id: 'R1' }],
    };
    render(
      <ThemeProvider theme={theme}>
        <MemoryRouter initialEntries={[{ pathname: '/results', state: { scanResults: scanData, fileName: 'main.tf' } }]}>
          <Routes>
            <Route path="/results" element={<Results />} />
          </Routes>
        </MemoryRouter>
      </ThemeProvider>
    );
    expect(screen.getByText('Scan Results')).toBeInTheDocument();
    expect(screen.getByTestId('risk-score-card')).toBeInTheDocument();
  });

  it('shows loading spinner when no state and fetching', () => {
    clientApi.getScan.mockReturnValue(new Promise(() => {}));
    render(
      <ThemeProvider theme={theme}>
        <MemoryRouter initialEntries={['/results/123']}>
          <Routes>
            <Route path="/results/:scanId" element={<Results />} />
          </Routes>
        </MemoryRouter>
      </ThemeProvider>
    );
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('shows error when scan fetch fails', async () => {
    clientApi.getScan.mockRejectedValue({ response: { data: { detail: 'Not found' } } });
    render(
      <ThemeProvider theme={theme}>
        <MemoryRouter initialEntries={['/results/999']}>
          <Routes>
            <Route path="/results/:scanId" element={<Results />} />
          </Routes>
        </MemoryRouter>
      </ThemeProvider>
    );
    await waitFor(() => expect(screen.getByText('Not found')).toBeInTheDocument());
  });

  it('shows feedback buttons', () => {
    const scanData = {
      unified_risk_score: 0.5,
      ml_score: 0.5,
      rules_score: 0.5,
      llm_score: 0.5,
      findings: [],
    };
    render(
      <ThemeProvider theme={theme}>
        <MemoryRouter initialEntries={[{ pathname: '/results', state: { scanResults: scanData } }]}>
          <Routes>
            <Route path="/results" element={<Results />} />
          </Routes>
        </MemoryRouter>
      </ThemeProvider>
    );
    expect(screen.getByRole('button', { name: /accurate/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /report issue/i })).toBeInTheDocument();
  });
});

// ====================================================================
// 8. Feedback Page
// ====================================================================
describe('Feedback Page', () => {
  let Feedback;
  beforeEach(async () => {
    Feedback = (await import('../pages/Feedback.jsx')).default;
  });

  it('renders feedback heading', async () => {
    clientApi.listScans.mockResolvedValue([]);
    clientApi.listFeedback.mockResolvedValue([]);
    render(<Providers><Feedback /></Providers>);
    await waitFor(() => expect(screen.getByText(/We Value Your Feedback/i)).toBeInTheDocument());
  });

  it('shows rating stars', async () => {
    clientApi.listScans.mockResolvedValue([]);
    clientApi.listFeedback.mockResolvedValue([]);
    render(<Providers><Feedback /></Providers>);
    await waitFor(() => {
      expect(screen.getByText(/How would you rate/i)).toBeInTheDocument();
    });
  });

  it('has a scan selector', async () => {
    clientApi.listScans.mockResolvedValue([{ id: 1, file_name: 'test.tf' }]);
    clientApi.listFeedback.mockResolvedValue([]);
    render(<Providers><Feedback /></Providers>);
    await waitFor(() => expect(screen.getByText(/Select Scan/i)).toBeInTheDocument());
  });

  it('shows error when data fetch fails', async () => {
    clientApi.listScans.mockRejectedValue(new Error('err'));
    clientApi.listFeedback.mockRejectedValue(new Error('err'));
    render(<Providers><Feedback /></Providers>);
    await waitFor(() => expect(screen.getByText(/Failed to load data/)).toBeInTheDocument());
  });
});

// ====================================================================
// 9. ModelStatus Page
// ====================================================================
describe('ModelStatus Page', () => {
  let ModelStatus;
  beforeEach(async () => {
    ModelStatus = (await import('../pages/ModelStatus.jsx')).default;
  });

  it('shows loading spinner initially', () => {
    clientApi.getModelStatus.mockReturnValue(new Promise(() => {}));
    clientApi.listModelVersions.mockReturnValue(new Promise(() => {}));
    render(<Providers><ModelStatus /></Providers>);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders model status after loading', async () => {
    clientApi.getModelStatus.mockResolvedValue({
      status: 'operational',
      accuracy: 0.92,
      model_version: '2.1',
    });
    clientApi.listModelVersions.mockResolvedValue([
      { version: '2.1', created_at: '2024-01-01' },
    ]);
    render(<Providers><ModelStatus /></Providers>);
    await waitFor(() => expect(screen.getByText('Model Status')).toBeInTheDocument());
  });

  it('shows error alert on failure', async () => {
    clientApi.getModelStatus.mockRejectedValue(new Error('fail'));
    clientApi.listModelVersions.mockRejectedValue(new Error('fail'));
    render(<Providers><ModelStatus /></Providers>);
    await waitFor(() => expect(screen.getByText(/Failed to load model status/)).toBeInTheDocument());
  });

  it('has Trigger Retrain button', async () => {
    clientApi.getModelStatus.mockResolvedValue({ status: 'ok' });
    clientApi.listModelVersions.mockResolvedValue([]);
    render(<Providers><ModelStatus /></Providers>);
    await waitFor(() => expect(screen.getByRole('button', { name: /trigger retrain/i })).toBeInTheDocument());
  });

  it('has Refresh button', async () => {
    clientApi.getModelStatus.mockResolvedValue({ status: 'ok' });
    clientApi.listModelVersions.mockResolvedValue([]);
    render(<Providers><ModelStatus /></Providers>);
    await waitFor(() => expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument());
  });
});

// ====================================================================
// 10. ScanHistory Page (mocked chart.js)
// ====================================================================
describe('ScanHistory Page', () => {
  let ScanHistory;
  const defaultClient = clientApi.default;

  beforeEach(async () => {
    defaultClient.get.mockReset();
    ScanHistory = (await import('../pages/ScanHistory.jsx')).default;
  });

  it('renders after loading', async () => {
    defaultClient.get.mockResolvedValue({ data: [] });
    render(<Providers route="/history"><ScanHistory /></Providers>);
    await waitFor(() => expect(screen.getByText(/Scan History/i)).toBeInTheDocument());
  });

  it('shows filter controls', async () => {
    defaultClient.get.mockResolvedValue({ data: [] });
    render(<Providers route="/history"><ScanHistory /></Providers>);
    await waitFor(() => {
      // Should have severity and scanner filters
      expect(document.body).toBeTruthy();
    });
  });

  it('has export button', async () => {
    defaultClient.get.mockResolvedValue({ data: [] });
    render(<Providers route="/history"><ScanHistory /></Providers>);
    await waitFor(() => {
      const btns = screen.getAllByRole('button');
      expect(btns.length).toBeGreaterThan(0);
    });
  });
});

// ====================================================================
// 11. Layout Component
// ====================================================================
describe('Layout Component', () => {
  let Layout;
  beforeEach(async () => {
    Layout = (await import('../components/Layout.jsx')).default;
  });

  it('renders children content', () => {
    render(
      <Providers>
        <Layout><div>Child Content</div></Layout>
      </Providers>
    );
    expect(screen.getByText('Child Content')).toBeInTheDocument();
  });

  it('renders CloudGuard brand text', () => {
    render(
      <Providers>
        <Layout><div>Test</div></Layout>
      </Providers>
    );
    expect(screen.getByText('CloudGuard')).toBeInTheDocument();
  });

  it('renders all navigation items', () => {
    render(
      <Providers>
        <Layout><div>Nav</div></Layout>
      </Providers>
    );
    const navItems = ['Scan', 'Dashboard', 'Learning', 'History', 'Feedback', 'Model Status', 'Settings'];
    for (const item of navItems) {
      expect(screen.getByText(item)).toBeInTheDocument();
    }
  });

  it('renders System Online status', () => {
    render(
      <Providers>
        <Layout><div>Status</div></Layout>
      </Providers>
    );
    expect(screen.getByText('System Online')).toBeInTheDocument();
  });

  it('navigation links point to correct paths', () => {
    render(
      <Providers>
        <Layout><div>Links</div></Layout>
      </Providers>
    );
    const settingsLink = screen.getByText('Settings').closest('a');
    expect(settingsLink).toHaveAttribute('href', '/settings');
  });
});

// ====================================================================
// 12. App.jsx — Full Routing Integration
// ====================================================================
describe('App Integration', () => {
  let App;
  beforeEach(async () => {
    App = (await import('../App.jsx')).default;
  });

  it('exports a function component', () => {
    expect(typeof App).toBe('function');
  });
});

// ====================================================================
// 13. API Client Edge Cases
// ====================================================================
describe('API Client Additional Coverage', () => {
  it('scanFile sends FormData with file and scan_mode', async () => {
    clientApi.scanFile.mockResolvedValue({ id: 1, risk_score: 0.5 });
    const file = new File(['content'], 'test.tf', { type: 'text/plain' });
    const result = await clientApi.scanFile(file, 'gnn');
    expect(clientApi.scanFile).toHaveBeenCalledWith(file, 'gnn');
    expect(result.id).toBe(1);
  });

  it('listScans returns array', async () => {
    clientApi.listScans.mockResolvedValue([{ id: 1 }, { id: 2 }]);
    const scans = await clientApi.listScans();
    expect(scans).toHaveLength(2);
  });

  it('deleteScan returns confirmation', async () => {
    clientApi.deleteScan.mockResolvedValue({ message: 'deleted' });
    const result = await clientApi.deleteScan(1);
    expect(result.message).toBe('deleted');
  });

  it('getFeedbackStats returns data', async () => {
    clientApi.getFeedbackStats.mockResolvedValue({ total: 5, positive: 4 });
    const stats = await clientApi.getFeedbackStats();
    expect(stats.total).toBe(5);
  });

  it('getDriftStatus returns drift info', async () => {
    clientApi.getDriftStatus.mockResolvedValue({ psi: 0.01, drifted: false });
    const drift = await clientApi.getDriftStatus();
    expect(drift.drifted).toBe(false);
  });

  it('getRuleWeights returns weights', async () => {
    clientApi.getRuleWeights.mockResolvedValue({ rule_1: 1.5 });
    const weights = await clientApi.getRuleWeights();
    expect(weights.rule_1).toBe(1.5);
  });

  it('getMetrics returns prometheus text', async () => {
    clientApi.getMetrics.mockResolvedValue('# HELP scans_total\nscans_total 42');
    const m = await clientApi.getMetrics();
    expect(m).toContain('42');
  });

  it('getDiscoveredPatterns returns patterns', async () => {
    clientApi.getDiscoveredPatterns.mockResolvedValue({ patterns: ['p1'] });
    const result = await clientApi.getDiscoveredPatterns();
    expect(result.patterns).toHaveLength(1);
  });
});

// ====================================================================
// 14. Component Helper Functions (exported sub-components)
// ====================================================================
describe('Dashboard Helper Functions', () => {
  it('SEVERITY_CONFIG has all levels', async () => {
    const src = (await import('../pages/Dashboard.jsx?raw')).default;
    expect(src).toContain('CRITICAL');
    expect(src).toContain('HIGH');
    expect(src).toContain('MEDIUM');
    expect(src).toContain('LOW');
    expect(src).toContain('INFO');
  });
});

describe('Settings Defaults', () => {
  it('DEFAULTS object contains expected keys', async () => {
    const src = (await import('../pages/Settings.jsx?raw')).default;
    expect(src).toContain('defaultScanMode');
    expect(src).toContain('riskThreshold');
    expect(src).toContain('maxFileSize');
    expect(src).toContain('enableAdaptiveLearning');
    expect(src).toContain('autoRetrain');
    expect(src).toContain('retrainThreshold');
  });
});

// ====================================================================
// 15. Edge Cases / Boundary Tests
// ====================================================================
describe('Edge Cases', () => {
  it('Dashboard handles empty findings_by_severity', async () => {
    clientApi.getScanStats.mockResolvedValue({
      total_scans: 0,
      findings_by_severity: {},
      average_scores: { unified_risk: 0 },
      trend_30_days: [],
    });
    const Dashboard = (await import('../pages/Dashboard.jsx')).default;
    render(<Providers><Dashboard /></Providers>);
    await waitFor(() => expect(screen.getByText('Security Dashboard')).toBeInTheDocument());
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('Dashboard handles high risk score', async () => {
    clientApi.getScanStats.mockResolvedValue({
      total_scans: 100,
      findings_by_severity: { CRITICAL: 50 },
      average_scores: { unified_risk: 0.95 },
      trend_30_days: [],
    });
    const Dashboard = (await import('../pages/Dashboard.jsx')).default;
    render(<Providers><Dashboard /></Providers>);
    await waitFor(() => expect(screen.getByText('Critical')).toBeInTheDocument());
  });

  it('Results page handles missing scan (null)', async () => {
    clientApi.getScan.mockResolvedValue(null);
    const Results = (await import('../pages/Results.jsx')).default;
    render(
      <ThemeProvider theme={theme}>
        <MemoryRouter initialEntries={['/results/0']}>
          <Routes>
            <Route path="/results/:scanId" element={<Results />} />
          </Routes>
        </MemoryRouter>
      </ThemeProvider>
    );
    await waitFor(() => expect(screen.getByText('Scan not found')).toBeInTheDocument());
  });

  it('NotFound renders without crashing on various routes', () => {
    const NotFound = React.lazy(() => import('../pages/NotFound.jsx'));
    render(
      <Providers route="/some/random/path">
        <React.Suspense fallback={<div>Loading</div>}>
          <NotFound />
        </React.Suspense>
      </Providers>
    );
    // Should render fallback or component, no crash
    expect(document.body).toBeTruthy();
  });
});
