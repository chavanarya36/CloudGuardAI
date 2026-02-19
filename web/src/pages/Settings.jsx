import { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Grid, TextField, Button, Switch, FormControlLabel,
  Divider, Alert, Snackbar, Card, CardContent, Chip, IconButton, Tooltip,
  Table, TableBody, TableCell, TableRow, Slider, Select, MenuItem, InputLabel,
  FormControl,
} from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import SecurityIcon from '@mui/icons-material/Security';
import TuneIcon from '@mui/icons-material/Tune';
import SaveIcon from '@mui/icons-material/Save';
import RestoreIcon from '@mui/icons-material/Restore';
import { setApiKey, clearAuth, getToken } from '../api/client';

const DEFAULTS = {
  defaultScanMode: 'all',
  riskThreshold: 0.7,
  maxFileSize: 10,            // MB
  enableAdaptiveLearning: true,
  autoRetrain: true,
  retrainThreshold: 50,
  enableNotifications: true,
  darkMode: false,
};

export default function Settings() {
  const [settings, setSettings] = useState(() => {
    const saved = localStorage.getItem('cg_settings');
    return saved ? { ...DEFAULTS, ...JSON.parse(saved) } : DEFAULTS;
  });
  const [apiKey, setApiKeyInput] = useState('');
  const [generatedKey, setGeneratedKey] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [jwtToken, setJwtToken] = useState('');

  useEffect(() => {
    localStorage.setItem('cg_settings', JSON.stringify(settings));
  }, [settings]);

  const handleChange = (key) => (event) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  const handleSliderChange = (key) => (_, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  const handleSaveApiKey = () => {
    if (apiKey.trim()) {
      setApiKey(apiKey.trim());
      setSnackbar({ open: true, message: 'API key saved successfully', severity: 'success' });
      setApiKeyInput('');
    }
  };

  const handleGenerateToken = async () => {
    try {
      const data = await getToken('web_user');
      setJwtToken(data.access_token);
      setSnackbar({ open: true, message: 'JWT token generated', severity: 'success' });
    } catch {
      setSnackbar({ open: true, message: 'Failed to generate token', severity: 'error' });
    }
  };

  const handleClearAuth = () => {
    clearAuth();
    setSnackbar({ open: true, message: 'Authentication cleared', severity: 'info' });
  };

  const handleReset = () => {
    setSettings(DEFAULTS);
    setSnackbar({ open: true, message: 'Settings reset to defaults', severity: 'info' });
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setSnackbar({ open: true, message: 'Copied to clipboard', severity: 'success' });
  };

  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        Settings
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Configure scanning preferences, authentication, and system settings.
      </Typography>

      <Grid container spacing={3}>
        {/* Scan Configuration */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <TuneIcon color="primary" />
              <Typography variant="h6">Scan Configuration</Typography>
            </Box>
            <Divider sx={{ mb: 2 }} />

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Default Scan Mode</InputLabel>
              <Select value={settings.defaultScanMode} label="Default Scan Mode" onChange={handleChange('defaultScanMode')}>
                <MenuItem value="all">Complete AI Scan</MenuItem>
                <MenuItem value="gnn">GNN Attack Path Only</MenuItem>
                <MenuItem value="checkov">Checkov Compliance Only</MenuItem>
                <MenuItem value="rules">Rules Engine Only</MenuItem>
              </Select>
            </FormControl>

            <Typography gutterBottom>Risk Score Threshold: {settings.riskThreshold}</Typography>
            <Slider
              value={settings.riskThreshold}
              onChange={handleSliderChange('riskThreshold')}
              min={0} max={1} step={0.05}
              marks={[{ value: 0.3, label: 'Low' }, { value: 0.7, label: 'High' }, { value: 1, label: 'Critical' }]}
              sx={{ mb: 2 }}
            />

            <Typography gutterBottom>Max File Size: {settings.maxFileSize} MB</Typography>
            <Slider
              value={settings.maxFileSize}
              onChange={handleSliderChange('maxFileSize')}
              min={1} max={50} step={1}
              sx={{ mb: 2 }}
            />
          </Paper>
        </Grid>

        {/* Authentication */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <VpnKeyIcon color="primary" />
              <Typography variant="h6">Authentication</Typography>
            </Box>
            <Divider sx={{ mb: 2 }} />

            <TextField
              fullWidth label="API Key" placeholder="cg_..." variant="outlined"
              value={apiKey} onChange={(e) => setApiKeyInput(e.target.value)}
              type="password" sx={{ mb: 1 }}
            />
            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <Button variant="contained" size="small" onClick={handleSaveApiKey} startIcon={<SaveIcon />}>
                Save Key
              </Button>
              <Button variant="outlined" size="small" color="warning" onClick={handleClearAuth}>
                Clear Auth
              </Button>
            </Box>

            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" gutterBottom>Generate JWT Token</Typography>
            <Button variant="outlined" size="small" onClick={handleGenerateToken} sx={{ mb: 1 }}>
              Generate Token
            </Button>
            {jwtToken && (
              <Box sx={{ mt: 1, p: 1, bgcolor: 'grey.100', borderRadius: 1, display: 'flex', alignItems: 'center' }}>
                <Typography variant="caption" sx={{ flex: 1, wordBreak: 'break-all', fontFamily: 'monospace' }}>
                  {jwtToken.substring(0, 40)}...
                </Typography>
                <Tooltip title="Copy token">
                  <IconButton size="small" onClick={() => copyToClipboard(jwtToken)}>
                    <ContentCopyIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Learning Settings */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <SecurityIcon color="primary" />
              <Typography variant="h6">Adaptive Learning</Typography>
            </Box>
            <Divider sx={{ mb: 2 }} />

            <FormControlLabel
              control={<Switch checked={settings.enableAdaptiveLearning} onChange={handleChange('enableAdaptiveLearning')} />}
              label="Enable Adaptive Learning"
              sx={{ mb: 1 }}
            />
            <FormControlLabel
              control={<Switch checked={settings.autoRetrain} onChange={handleChange('autoRetrain')} disabled={!settings.enableAdaptiveLearning} />}
              label="Auto-Retrain on Drift"
              sx={{ mb: 2 }}
            />

            <Typography gutterBottom>Retrain Sample Threshold: {settings.retrainThreshold}</Typography>
            <Slider
              value={settings.retrainThreshold}
              onChange={handleSliderChange('retrainThreshold')}
              min={10} max={500} step={10}
              disabled={!settings.autoRetrain}
            />
          </Paper>
        </Grid>

        {/* General Settings */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <TuneIcon color="primary" />
              <Typography variant="h6">General</Typography>
            </Box>
            <Divider sx={{ mb: 2 }} />

            <FormControlLabel
              control={<Switch checked={settings.enableNotifications} onChange={handleChange('enableNotifications')} />}
              label="Enable Toast Notifications"
              sx={{ mb: 1 }}
            />

            <Box sx={{ mt: 3, display: 'flex', gap: 1 }}>
              <Button variant="outlined" startIcon={<RestoreIcon />} onClick={handleReset}>
                Reset to Defaults
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* System Info */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>System Information</Typography>
            <Divider sx={{ mb: 2 }} />
            <Table size="small">
              <TableBody>
                <TableRow><TableCell sx={{ fontWeight: 'bold' }}>Version</TableCell><TableCell>2.0.0</TableCell></TableRow>
                <TableRow><TableCell sx={{ fontWeight: 'bold' }}>API URL</TableCell><TableCell>{import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}</TableCell></TableRow>
                <TableRow><TableCell sx={{ fontWeight: 'bold' }}>AI Models</TableCell><TableCell>GNN (114K), RL (31K), Transformer (4.9M), XGBoost Ensemble</TableCell></TableRow>
                <TableRow><TableCell sx={{ fontWeight: 'bold' }}>Scanners</TableCell><TableCell>7 — GNN, Secrets, CVE (OSV), Compliance, Rules, ML, LLM</TableCell></TableRow>
                <TableRow><TableCell sx={{ fontWeight: 'bold' }}>Adaptive Learning</TableCell><TableCell><Chip label="8 Subsystems" color="success" size="small" /></TableCell></TableRow>
              </TableBody>
            </Table>
          </Paper>
        </Grid>
      </Grid>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
      >
        <Alert severity={snackbar.severity} variant="filled" onClose={() => setSnackbar((s) => ({ ...s, open: false }))}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
