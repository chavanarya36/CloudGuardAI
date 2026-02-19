import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Layout from './components/Layout';
import ErrorBoundary from './components/ErrorBoundary';
import Dashboard from './pages/Dashboard';
import LearningIntelligence from './pages/LearningIntelligence';
import Scan from './pages/Scan';
import Results from './pages/Results';
import ScanHistory from './pages/ScanHistory';
import Feedback from './pages/Feedback';
import ModelStatus from './pages/ModelStatus';
import NotFound from './pages/NotFound';
import Settings from './pages/Settings';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ErrorBoundary>
        <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Layout>
            <Routes>
              <Route path="/" element={<Scan />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/learning" element={<LearningIntelligence />} />
              <Route path="/results/:scanId" element={<Results />} />
              <Route path="/results" element={<Results />} />
              <Route path="/history" element={<ScanHistory />} />
              <Route path="/feedback" element={<Feedback />} />
              <Route path="/model-status" element={<ModelStatus />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Layout>
        </Router>
      </ErrorBoundary>
    </ThemeProvider>
  );
}

export default App;
