import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Layout from './components/Layout';
import Scan from './pages/Scan';
import Results from './pages/Results';
import Feedback from './pages/Feedback';
import ModelStatus from './pages/ModelStatus';

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
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Scan />} />
            <Route path="/results/:scanId" element={<Results />} />
            <Route path="/feedback" element={<Feedback />} />
            <Route path="/model-status" element={<ModelStatus />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;
