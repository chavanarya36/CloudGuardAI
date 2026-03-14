import { useState, useEffect } from 'react';
import {
  Switch, Slider, Select, MenuItem, TextField, Snackbar, Alert,
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
} from '@mui/material';
import { setApiKey, clearAuth, getToken } from '../api/client';

const DEFAULTS = {
  defaultScanMode: 'all',
  riskThreshold: 0.7,
  maxFileSize: 10,
  enableAdaptiveLearning: true,
  autoRetrain: true,
  retrainThreshold: 50,
  enableNotifications: true,
  darkMode: false,
};

function GlassCard({ children, style }) {
  return (
    <div style={{
      background: 'rgba(10,22,38,0.8)',
      border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: '14px', padding: '24px',
      backdropFilter: 'blur(8px)',
      ...style,
    }}>
      {children}
    </div>
  );
}

function SectionTitle({ icon, title }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
      <div style={{
        width: '34px', height: '34px', borderRadius: '8px',
        background: 'rgba(66,165,245,0.12)',
        border: '1px solid rgba(66,165,245,0.2)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '16px',
      }}>
        {icon}
      </div>
      <span style={{
        fontFamily: '"Syne", sans-serif',
        fontWeight: 700, fontSize: '16px', color: '#fff',
      }}>
        {title}
      </span>
    </div>
  );
}

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

  const muiDarkSx = {
    '& .MuiOutlinedInput-root': {
      color: 'rgba(255,255,255,0.8)',
      '& fieldset': { borderColor: 'rgba(255,255,255,0.12)' },
      '&:hover fieldset': { borderColor: 'rgba(66,165,245,0.4)' },
      '&.Mui-focused fieldset': { borderColor: '#42a5f5' },
    },
    '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.4)' },
    '& .MuiSelect-icon': { color: 'rgba(255,255,255,0.4)' },
  };

  return (
    <div style={{ fontFamily: '"DM Sans", sans-serif' }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Syne:wght@700;800&display=swap');
        .settings-btn { cursor:pointer; transition:all 0.2s ease; }
        .settings-btn:hover { transform:translateY(-1px); filter:brightness(1.15); }
      `}</style>

      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{
          fontSize: '11px', letterSpacing: '0.2em', textTransform: 'uppercase',
          color: 'rgba(66,165,245,0.7)', fontWeight: 600, marginBottom: '8px',
        }}>
          Configuration
        </div>
        <h1 style={{
          fontFamily: '"Syne", sans-serif',
          fontSize: '28px', fontWeight: 800, color: '#fff',
          margin: '0 0 8px', letterSpacing: '-0.02em',
        }}>
          Settings
        </h1>
        <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '14px', margin: 0 }}>
          Configure scanning preferences, authentication, and system settings.
        </p>
      </div>

      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
        gap: '16px', marginBottom: '20px',
      }}>
        {/* Scan Configuration */}
        <GlassCard>
          <SectionTitle icon="🎛️" title="Scan Configuration" />
          <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', marginBottom: '20px' }} />

          <div style={{ marginBottom: '20px' }}>
            <label style={{ fontSize: '13px', color: 'rgba(255,255,255,0.5)', display: 'block', marginBottom: '8px' }}>
              Default Scan Mode
            </label>
            <Select
              value={settings.defaultScanMode}
              onChange={handleChange('defaultScanMode')}
              fullWidth size="small"
              sx={muiDarkSx}
            >
              <MenuItem value="all">Complete AI Scan</MenuItem>
              <MenuItem value="gnn">GNN Attack Path Only</MenuItem>
              <MenuItem value="checkov">Checkov Compliance Only</MenuItem>
              <MenuItem value="rules">Rules Engine Only</MenuItem>
            </Select>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.5)', marginBottom: '8px' }}>
              Risk Score Threshold: <span style={{ color: '#42a5f5', fontWeight: 600 }}>{settings.riskThreshold}</span>
            </div>
            <Slider
              value={settings.riskThreshold}
              onChange={handleSliderChange('riskThreshold')}
              min={0} max={1} step={0.05}
              marks={[{ value: 0.3, label: 'Low' }, { value: 0.7, label: 'High' }, { value: 1, label: 'Critical' }]}
              sx={{
                color: '#42a5f5',
                '& .MuiSlider-markLabel': { color: 'rgba(255,255,255,0.3)', fontSize: '10px' },
              }}
            />
          </div>

          <div>
            <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.5)', marginBottom: '8px' }}>
              Max File Size: <span style={{ color: '#42a5f5', fontWeight: 600 }}>{settings.maxFileSize} MB</span>
            </div>
            <Slider
              value={settings.maxFileSize}
              onChange={handleSliderChange('maxFileSize')}
              min={1} max={50} step={1}
              sx={{ color: '#42a5f5' }}
            />
          </div>
        </GlassCard>

        {/* Authentication */}
        <GlassCard>
          <SectionTitle icon="🔑" title="Authentication" />
          <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', marginBottom: '20px' }} />

          <TextField
            fullWidth label="API Key" placeholder="cg_..."
            value={apiKey} onChange={(e) => setApiKeyInput(e.target.value)}
            type="password" size="small"
            sx={{ ...muiDarkSx, mb: 1.5 }}
          />
          <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
            <button className="settings-btn" onClick={handleSaveApiKey} style={{
              padding: '8px 16px', borderRadius: '8px', border: 'none',
              background: 'linear-gradient(135deg, #1976d2, #42a5f5)',
              color: '#fff', fontSize: '12px', fontWeight: 600,
              fontFamily: '"DM Sans", sans-serif',
              display: 'flex', alignItems: 'center', gap: '6px',
            }}>
              💾 Save Key
            </button>
            <button className="settings-btn" onClick={handleClearAuth} style={{
              padding: '8px 16px', borderRadius: '8px',
              background: 'rgba(255,167,38,0.1)',
              border: '1px solid rgba(255,167,38,0.3)',
              color: '#ffa726', fontSize: '12px', fontWeight: 500,
              fontFamily: '"DM Sans", sans-serif',
            }}>
              Clear Auth
            </button>
          </div>

          <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', marginBottom: '16px' }} />
          <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.5)', marginBottom: '10px', fontWeight: 500 }}>
            Generate JWT Token
          </div>
          <button className="settings-btn" onClick={handleGenerateToken} style={{
            padding: '8px 16px', borderRadius: '8px',
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.12)',
            color: 'rgba(255,255,255,0.6)', fontSize: '12px', fontWeight: 500,
            fontFamily: '"DM Sans", sans-serif', marginBottom: '10px',
          }}>
            Generate Token
          </button>
          {jwtToken && (
            <div style={{
              padding: '10px 12px', borderRadius: '8px',
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.08)',
              display: 'flex', alignItems: 'center', gap: '8px',
            }}>
              <span style={{
                flex: 1, fontSize: '11px', color: 'rgba(255,255,255,0.5)',
                fontFamily: '"JetBrains Mono", monospace', wordBreak: 'break-all',
              }}>
                {jwtToken.substring(0, 40)}...
              </span>
              <button onClick={() => copyToClipboard(jwtToken)} style={{
                background: 'none', border: 'none', cursor: 'pointer',
                color: '#42a5f5', fontSize: '14px',
              }}>
                📋
              </button>
            </div>
          )}
        </GlassCard>

        {/* Adaptive Learning */}
        <GlassCard>
          <SectionTitle icon="🛡️" title="Adaptive Learning" />
          <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', marginBottom: '20px' }} />

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.6)' }}>Enable Adaptive Learning</span>
            <Switch checked={settings.enableAdaptiveLearning} onChange={handleChange('enableAdaptiveLearning')} sx={{ '& .MuiSwitch-switchBase.Mui-checked': { color: '#42a5f5' }, '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#42a5f5' } }} />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.6)' }}>Auto-Retrain on Drift</span>
            <Switch checked={settings.autoRetrain} onChange={handleChange('autoRetrain')} disabled={!settings.enableAdaptiveLearning} sx={{ '& .MuiSwitch-switchBase.Mui-checked': { color: '#42a5f5' }, '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#42a5f5' } }} />
          </div>

          <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.5)', marginBottom: '8px' }}>
            Retrain Sample Threshold: <span style={{ color: '#42a5f5', fontWeight: 600 }}>{settings.retrainThreshold}</span>
          </div>
          <Slider
            value={settings.retrainThreshold}
            onChange={handleSliderChange('retrainThreshold')}
            min={10} max={500} step={10}
            disabled={!settings.autoRetrain}
            sx={{ color: '#42a5f5' }}
          />
        </GlassCard>

        {/* General */}
        <GlassCard>
          <SectionTitle icon="⚙️" title="General" />
          <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', marginBottom: '20px' }} />

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.6)' }}>Enable Toast Notifications</span>
            <Switch checked={settings.enableNotifications} onChange={handleChange('enableNotifications')} sx={{ '& .MuiSwitch-switchBase.Mui-checked': { color: '#42a5f5' }, '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#42a5f5' } }} />
          </div>

          <button className="settings-btn" onClick={handleReset} style={{
            padding: '10px 20px', borderRadius: '8px',
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.12)',
            color: 'rgba(255,255,255,0.6)', fontSize: '13px', fontWeight: 500,
            fontFamily: '"DM Sans", sans-serif',
            display: 'flex', alignItems: 'center', gap: '8px',
          }}>
            🔄 Reset to Defaults
          </button>
        </GlassCard>
      </div>

      {/* System Info */}
      <GlassCard>
        <SectionTitle icon="📡" title="System Information" />
        <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', marginBottom: '20px' }} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {[
            { label: 'Version', value: '2.0.0' },
            { label: 'API URL', value: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000' },
            { label: 'AI Models', value: 'GNN (114K), RL (31K), Transformer (4.9M), XGBoost Ensemble' },
            { label: 'Scanners', value: '7 — GNN, Secrets, CVE (OSV), Compliance, Rules, ML, LLM' },
            { label: 'Adaptive Learning', value: '8 Subsystems' },
          ].map((row, i) => (
            <div key={i} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '10px 14px', borderRadius: '8px',
              background: 'rgba(255,255,255,0.02)',
            }}>
              <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.4)', fontWeight: 600 }}>{row.label}</span>
              <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.7)', textAlign: 'right', maxWidth: '60%' }}>{row.value}</span>
            </div>
          ))}
        </div>
      </GlassCard>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
      >
        <Alert severity={snackbar.severity} variant="filled" onClose={() => setSnackbar((s) => ({ ...s, open: false }))}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </div>
  );
}
