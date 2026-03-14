import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Layout from './components/Layout';
import ErrorBoundary from './components/ErrorBoundary';
import { ScanProvider } from './context/ScanContext';
import Dashboard from './pages/Dashboard';
import LearningIntelligence from './pages/LearningIntelligence';
import Scan from './pages/Scan';
import Results from './pages/Results';
import ScanHistory from './pages/ScanHistory';
import Feedback from './pages/Feedback';
import ModelStatus from './pages/ModelStatus';
import NotFound from './pages/NotFound';
import Settings from './pages/Settings';
import UserModeSelection from './pages/UserModeSelection';
import BeginnerLanding from './pages/BeginnerLanding';
import CloudSecurityOverview from './pages/CloudSecurityOverview';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#42a5f5',
      light: '#80d6ff',
      dark: '#0077c2',
    },
    secondary: {
      main: '#ce93d8',
    },
    background: {
      default: '#0a1929',
      paper: '#0f2744',
    },
    success: {
      main: '#66bb6a',
      light: '#1b3a2a',
      dark: '#388e3c',
    },
    warning: {
      main: '#ffa726',
      light: '#3a2e1b',
    },
    error: {
      main: '#ef5350',
      light: '#3a1b1b',
    },
    info: {
      main: '#29b6f6',
      light: '#1b2e3a',
    },
    divider: 'rgba(255,255,255,0.08)',
  },
  shape: { borderRadius: 10 },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          borderColor: 'rgba(255,255,255,0.08)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});

function HomeRedirect() {
  return <Navigate to="/welcome" replace />;
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ErrorBoundary>
        <ScanProvider>
        <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Routes>
            {/* Standalone pages — no Layout wrapper */}
            <Route path="/" element={<HomeRedirect />} />
            <Route path="/welcome" element={<UserModeSelection />} />
            <Route path="/security-overview" element={<CloudSecurityOverview />} />
            <Route path="/landing" element={<BeginnerLanding />} />

            {/* Main app pages — wrapped in Layout */}
            <Route element={<Layout />}>
              <Route path="/scan" element={<Scan />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/learning" element={<LearningIntelligence />} />
              <Route path="/results/:scanId" element={<Results />} />
              <Route path="/results" element={<Results />} />
              <Route path="/history" element={<ScanHistory />} />
              <Route path="/feedback" element={<Feedback />} />
              <Route path="/model-status" element={<ModelStatus />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<NotFound />} />
            </Route>
          </Routes>
        </Router>
        </ScanProvider>
      </ErrorBoundary>
    </ThemeProvider>
  );
}

export default App;
