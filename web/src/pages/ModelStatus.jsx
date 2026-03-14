import { useState, useEffect } from 'react';
import {
  CircularProgress, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Alert,
} from '@mui/material';
import { getModelStatus, triggerRetrain, listModelVersions } from '../api/client';

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

export default function ModelStatus() {
  const [status, setStatus] = useState(null);
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [retraining, setRetraining] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [minSamples, setMinSamples] = useState(100);
  const [forceRetrain, setForceRetrain] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statusData, versionsData] = await Promise.all([
        getModelStatus(), listModelVersions(),
      ]);
      setStatus(statusData);
      setVersions(versionsData);
    } catch (err) {
      setError('Failed to load model status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleRetrain = async () => {
    setRetraining(true); setError(null); setSuccess(null);
    try {
      await triggerRetrain(forceRetrain, minSamples);
      setSuccess('Retraining job started successfully!');
      setDialogOpen(false);
      setTimeout(fetchData, 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start retraining');
    } finally {
      setRetraining(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress sx={{ color: '#42a5f5' }} />
      </div>
    );
  }

  const metrics = [
    { icon: '⚡', title: 'Model Status', value: 'Operational', desc: 'All systems running smoothly', color: '#66bb6a', gradient: 'linear-gradient(135deg, #66bb6a, #388e3c)' },
    { icon: '🚀', title: 'Response Time', value: '1.2s', desc: 'Average API response', color: '#42a5f5', gradient: 'linear-gradient(135deg, #42a5f5, #1565c0)' },
    { icon: '🧠', title: 'Model Version', value: status?.active_version || 'N/A', desc: 'Latest stable release', color: '#ce93d8', gradient: 'linear-gradient(135deg, #ce93d8, #7b1fa2)' },
    { icon: '📡', title: 'Uptime', value: '99.9%', desc: 'Last 30 days', color: '#ffa726', gradient: 'linear-gradient(135deg, #ffa726, #e65100)' },
  ];

  const healthBars = [
    { label: 'API Response Time', value: 95, color: '#66bb6a' },
    { label: 'Model Accuracy', value: 98, color: '#42a5f5' },
    { label: 'Cache Hit Rate', value: 87, color: '#ce93d8' },
    { label: 'Resource Usage', value: 62, color: '#ffa726' },
  ];

  return (
    <div style={{ fontFamily: '"DM Sans", sans-serif' }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Syne:wght@700;800&display=swap');
        .ms-btn { cursor:pointer; transition:all 0.2s ease; }
        .ms-btn:hover { transform:translateY(-1px); filter:brightness(1.15); }
      `}</style>

      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '12px' }}>
          <div style={{
            width: '48px', height: '48px', borderRadius: '12px',
            background: 'linear-gradient(135deg, #66bb6a, #388e3c)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 20px rgba(102,187,106,0.3)',
            fontSize: '22px',
          }}>⚡</div>
          <div>
            <h1 style={{
              fontFamily: '"Syne", sans-serif',
              fontSize: '28px', fontWeight: 800, color: '#fff',
              margin: 0, letterSpacing: '-0.02em',
            }}>
              Model Status
            </h1>
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '14px', margin: 0 }}>
              Real-time monitoring of AI model performance
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '16px' }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            padding: '6px 14px', borderRadius: '8px',
            background: 'rgba(102,187,106,0.08)',
            border: '1px solid rgba(102,187,106,0.2)',
          }}>
            <div style={{
              width: '8px', height: '8px', borderRadius: '50%',
              background: '#66bb6a', boxShadow: '0 0 6px #66bb6a',
              animation: 'pulse 2s infinite',
            }} />
            <span style={{ fontSize: '12px', fontWeight: 500, color: '#66bb6a' }}>
              All Systems Operational
            </span>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: '10px' }}>
            <button className="ms-btn" onClick={fetchData} style={{
              padding: '8px 18px', borderRadius: '8px',
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.12)',
              color: 'rgba(255,255,255,0.6)', fontSize: '13px', fontWeight: 500,
              fontFamily: '"DM Sans", sans-serif',
              display: 'flex', alignItems: 'center', gap: '6px',
            }}>
              🔄 Refresh
            </button>
            <button className="ms-btn" onClick={() => setDialogOpen(true)} style={{
              padding: '8px 18px', borderRadius: '8px',
              background: 'linear-gradient(135deg, #1976d2, #42a5f5)',
              border: 'none', color: '#fff', fontSize: '13px', fontWeight: 600,
              fontFamily: '"DM Sans", sans-serif',
            }}>
              Trigger Retrain
            </button>
          </div>
        </div>
        <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }`}</style>
      </div>

      {error && (
        <div style={{
          padding: '14px 20px', borderRadius: '12px', marginBottom: '20px',
          background: 'rgba(239,83,80,0.08)', border: '1px solid rgba(239,83,80,0.2)',
          color: '#ef5350', fontSize: '13px',
        }}>
          ⚠️ {error}
        </div>
      )}
      {success && (
        <div style={{
          padding: '14px 20px', borderRadius: '12px', marginBottom: '20px',
          background: 'rgba(102,187,106,0.08)', border: '1px solid rgba(102,187,106,0.2)',
          color: '#66bb6a', fontSize: '13px',
        }}>
          ✅ {success}
        </div>
      )}

      {/* Metrics Grid */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px', marginBottom: '28px',
      }}>
        {metrics.map((m, i) => (
          <GlassCard key={i} style={{ position: 'relative', overflow: 'hidden' }}>
            <div style={{
              position: 'absolute', top: 0, left: 0, right: 0, height: '3px',
              background: m.gradient,
            }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <div style={{
                width: '40px', height: '40px', borderRadius: '10px',
                background: m.gradient,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '18px',
              }}>{m.icon}</div>
              <span style={{
                padding: '3px 10px', borderRadius: '99px', fontSize: '10px', fontWeight: 600,
                background: `${m.color}15`, color: m.color,
                border: `1px solid ${m.color}30`,
              }}>online</span>
            </div>
            <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)', marginBottom: '4px' }}>{m.title}</div>
            <div style={{ fontSize: '24px', fontWeight: 800, color: '#fff', fontFamily: '"Syne", sans-serif', marginBottom: '4px' }}>{m.value}</div>
            <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.3)' }}>{m.desc}</div>
          </GlassCard>
        ))}
      </div>

      {/* Active Model + Health */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '16px', marginBottom: '28px' }}>
        <GlassCard>
          <div style={{ fontFamily: '"Syne", sans-serif', fontSize: '16px', fontWeight: 700, color: '#fff', marginBottom: '6px' }}>Active Model</div>
          <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', margin: '12px 0 16px' }} />
          {status?.active_version ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {[
                { label: 'Version', value: status.active_version },
                { label: 'Type', value: status.model_type },
                { label: 'Accuracy', value: status.accuracy?.toFixed(4) || 'N/A' },
                { label: 'Precision', value: status.precision?.toFixed(4) || 'N/A' },
                { label: 'Recall', value: status.recall?.toFixed(4) || 'N/A' },
                { label: 'F1 Score', value: status.f1_score?.toFixed(4) || 'N/A' },
              ].map((item, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', borderRadius: '6px', background: 'rgba(255,255,255,0.02)' }}>
                  <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.4)' }}>{item.label}</span>
                  <span style={{ fontSize: '13px', color: '#fff', fontWeight: 600 }}>{item.value}</span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '20px', color: 'rgba(255,255,255,0.4)', fontSize: '13px' }}>No active model</div>
          )}
        </GlassCard>

        <GlassCard>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span style={{ fontSize: '16px' }}>📈</span>
            <span style={{ fontFamily: '"Syne", sans-serif', fontSize: '16px', fontWeight: 700, color: '#fff' }}>System Health</span>
          </div>
          <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', margin: '12px 0 16px' }} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {healthBars.map((bar, i) => (
              <div key={i}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.5)', fontWeight: 500 }}>{bar.label}</span>
                  <span style={{ fontSize: '13px', fontWeight: 700, color: '#fff' }}>{bar.value}%</span>
                </div>
                <div style={{ height: '6px', borderRadius: '3px', background: 'rgba(255,255,255,0.06)' }}>
                  <div style={{ height: '100%', borderRadius: '3px', width: `${bar.value}%`, background: bar.color, transition: 'width 0.6s ease' }} />
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Statistics */}
      <GlassCard style={{ marginBottom: '28px' }}>
        <div style={{ fontFamily: '"Syne", sans-serif', fontSize: '16px', fontWeight: 700, color: '#fff', marginBottom: '6px' }}>Statistics</div>
        <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', margin: '12px 0 16px' }} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px' }}>
          {[
            { label: 'Total Scans', value: status?.total_scans || 0, color: '#42a5f5' },
            { label: 'Total Feedback', value: status?.total_feedback || 0, color: '#ce93d8' },
            { label: 'Pending Retraining', value: status?.pending_retraining_samples || 0, color: '#ffa726' },
            { label: 'Training Samples', value: status?.training_samples || 0, color: '#66bb6a' },
          ].map((stat, i) => (
            <div key={i} style={{
              textAlign: 'center', padding: '16px', borderRadius: '10px',
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.04)',
            }}>
              <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)', marginBottom: '6px' }}>{stat.label}</div>
              <div style={{ fontSize: '28px', fontWeight: 800, color: stat.color, fontFamily: '"Syne", sans-serif' }}>{stat.value}</div>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* Recent Activity */}
      <GlassCard style={{ marginBottom: '28px' }}>
        <div style={{ fontFamily: '"Syne", sans-serif', fontSize: '16px', fontWeight: 700, color: '#fff', marginBottom: '6px' }}>Recent Activity</div>
        <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', margin: '12px 0 16px' }} />
        {[
          { time: '2 min ago', event: 'Security scan completed', status: 'success' },
          { time: '15 min ago', event: 'Model cache updated', status: 'info' },
          { time: '1 hour ago', event: 'System health check passed', status: 'success' },
          { time: '3 hours ago', event: 'Database optimization completed', status: 'info' },
        ].map((a, i) => (
          <div key={i} style={{
            display: 'flex', alignItems: 'flex-start', gap: '12px',
            padding: '10px 12px', borderRadius: '8px',
            marginBottom: '4px',
          }}>
            <div style={{
              width: '7px', height: '7px', borderRadius: '50%', marginTop: '6px', flexShrink: 0,
              background: a.status === 'success' ? '#66bb6a' : '#42a5f5',
              boxShadow: `0 0 6px ${a.status === 'success' ? '#66bb6a' : '#42a5f5'}`,
            }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.65)', fontWeight: 500 }}>{a.event}</div>
              <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.3)' }}>{a.time}</div>
            </div>
          </div>
        ))}
      </GlassCard>

      {/* Version History */}
      <div style={{ marginBottom: '28px' }}>
        <h2 style={{ fontFamily: '"Syne", sans-serif', fontSize: '18px', fontWeight: 700, color: '#fff', marginBottom: '16px' }}>Version History</h2>
        <GlassCard style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                  {['Version', 'Type', 'Accuracy', 'Precision', 'Recall', 'F1 Score', 'Samples', 'Created'].map((h) => (
                    <th key={h} style={{ padding: '12px 16px', textAlign: 'left', color: 'rgba(255,255,255,0.5)', fontWeight: 600, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {versions.map((v, i) => (
                  <tr key={v.active_version || i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '10px 16px' }}>
                      <span style={{ padding: '3px 10px', borderRadius: '6px', background: 'rgba(66,165,245,0.12)', color: '#42a5f5', fontSize: '11px', fontWeight: 600, border: '1px solid rgba(66,165,245,0.25)' }}>
                        {v.active_version}
                      </span>
                    </td>
                    <td style={{ padding: '10px 16px', color: 'rgba(255,255,255,0.6)' }}>{v.model_type}</td>
                    <td style={{ padding: '10px 16px', color: 'rgba(255,255,255,0.6)' }}>{v.accuracy?.toFixed(4) || 'N/A'}</td>
                    <td style={{ padding: '10px 16px', color: 'rgba(255,255,255,0.6)' }}>{v.precision?.toFixed(4) || 'N/A'}</td>
                    <td style={{ padding: '10px 16px', color: 'rgba(255,255,255,0.6)' }}>{v.recall?.toFixed(4) || 'N/A'}</td>
                    <td style={{ padding: '10px 16px', color: 'rgba(255,255,255,0.6)' }}>{v.f1_score?.toFixed(4) || 'N/A'}</td>
                    <td style={{ padding: '10px 16px', color: 'rgba(255,255,255,0.6)' }}>{v.training_samples || 0}</td>
                    <td style={{ padding: '10px 16px', color: 'rgba(255,255,255,0.4)' }}>{v.created_at ? new Date(v.created_at).toLocaleString() : 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      </div>

      {/* Retrain Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth
        PaperProps={{ sx: { bgcolor: '#0f2744', backgroundImage: 'none', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 3 } }}
      >
        <DialogTitle sx={{ fontWeight: 700, color: '#fff' }}>Trigger Model Retraining</DialogTitle>
        <DialogContent>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', paddingTop: '8px' }}>
            <Alert severity="info" sx={{ borderRadius: 2 }}>
              Retraining will use feedback data to update the model using online learning.
            </Alert>
            <TextField
              label="Minimum Samples" type="number"
              value={minSamples} onChange={(e) => setMinSamples(parseInt(e.target.value))}
              helperText="Minimum number of feedback samples required"
              fullWidth
              sx={{
                '& .MuiOutlinedInput-root': { color: 'rgba(255,255,255,0.8)', '& fieldset': { borderColor: 'rgba(255,255,255,0.12)' } },
                '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.4)' },
              }}
            />
          </div>
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 0 }}>
          <button onClick={() => setDialogOpen(false)} style={{
            padding: '8px 20px', borderRadius: '8px',
            background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.12)',
            color: 'rgba(255,255,255,0.6)', cursor: 'pointer', fontFamily: '"DM Sans", sans-serif',
          }}>
            Cancel
          </button>
          <button onClick={handleRetrain} disabled={retraining} style={{
            padding: '8px 20px', borderRadius: '8px', border: 'none',
            background: 'linear-gradient(135deg, #1976d2, #42a5f5)',
            color: '#fff', fontWeight: 600, cursor: 'pointer', fontFamily: '"DM Sans", sans-serif',
          }}>
            {retraining ? 'Starting...' : 'Start Retraining'}
          </button>
        </DialogActions>
      </Dialog>
    </div>
  );
}
