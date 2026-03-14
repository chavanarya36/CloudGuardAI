import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TextField, MenuItem, Dialog, DialogTitle, DialogContent, DialogActions,
  LinearProgress,
} from '@mui/material';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend, Filler,
} from 'chart.js';
import apiClient, { listScans, getScan } from '../api/client';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const severityColors = { CRITICAL: '#ef5350', HIGH: '#ffa726', MEDIUM: '#f9a825', LOW: '#66bb6a', INFO: '#42a5f5' };
const scannerColors = { ML: '#ce93d8', Rules: '#ffa726', LLM: '#26c6da', Secrets: '#ab47bc', CVE: '#ef5350', Compliance: '#42a5f5' };

function GlassCard({ children, style }) {
  return (
    <div style={{
      background: 'rgba(10,22,38,0.8)',
      border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: '14px', padding: '24px',
      backdropFilter: 'blur(8px)',
      ...style,
    }}>{children}</div>
  );
}

function ScanHistory() {
  const [scans, setScans] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedScan, setSelectedScan] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [scanToDelete, setScanToDelete] = useState(null);
  const [severity, setSeverity] = useState('');
  const [scanner, setScanner] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const navigate = useNavigate();

  useEffect(() => { fetchScans(); fetchStats(); }, [severity, scanner, startDate, endDate]);

  const fetchScans = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (severity) params.append('severity', severity);
      if (scanner) params.append('scanner', scanner);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      const response = await apiClient.get(`/scans?${params}`);
      setScans(response.data);
    } catch (error) {
      console.error('Failed to fetch scans:', error);
    } finally { setLoading(false); }
  };

  const fetchStats = async () => {
    try { const r = await apiClient.get('/scans/stats'); setStats(r.data); } catch (e) { /* ignore */ }
  };

  const handleViewScan = async (scanId) => {
    try { const data = await getScan(scanId); setSelectedScan(data); setDialogOpen(true); } catch (e) { /* ignore */ }
  };

  const handleDeleteScan = async () => {
    if (!scanToDelete) return;
    try { await apiClient.delete(`/scans/${scanToDelete}`); setDeleteDialogOpen(false); setScanToDelete(null); fetchScans(); fetchStats(); } catch (e) { /* ignore */ }
  };

  const confirmDelete = (scanId) => { setScanToDelete(scanId); setDeleteDialogOpen(true); };

  const exportScans = () => {
    const blob = new Blob([JSON.stringify(scans, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a'); link.href = url;
    link.download = `scan-history-${new Date().toISOString()}.json`;
    link.click();
  };

  const getRiskColor = (score) => {
    if (score >= 80) return '#ef5350';
    if (score >= 60) return '#ffa726';
    if (score >= 40) return '#f9a825';
    return '#66bb6a';
  };

  const getTrendChartData = () => {
    if (!stats?.trend_30_days) return null;
    return {
      labels: stats.trend_30_days.map(d => d.date),
      datasets: [{
        label: 'Scans', data: stats.trend_30_days.map(d => d.count),
        borderColor: '#42a5f5', backgroundColor: 'rgba(66,165,245,0.08)',
        fill: true, tension: 0.4, pointRadius: 2,
      }],
    };
  };

  const chartOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { backgroundColor: '#0f2744', padding: 12, borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1 } },
    scales: {
      y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: 'rgba(255,255,255,0.3)', font: { size: 11 } } },
      x: { grid: { display: false }, ticks: { color: 'rgba(255,255,255,0.3)', font: { size: 10 } } },
    },
  };

  const muiDarkSx = {
    '& .MuiOutlinedInput-root': { color: 'rgba(255,255,255,0.8)', '& fieldset': { borderColor: 'rgba(255,255,255,0.12)' }, '&:hover fieldset': { borderColor: 'rgba(66,165,245,0.4)' } },
    '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.4)' },
    '& .MuiSelect-icon': { color: 'rgba(255,255,255,0.4)' },
  };

  return (
    <div style={{ fontFamily: '"DM Sans", sans-serif' }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Syne:wght@700;800&display=swap');
        .sh-btn { cursor:pointer; transition:all 0.2s ease; }
        .sh-btn:hover { transform:translateY(-1px); filter:brightness(1.15); }
        .scan-row { cursor:pointer; transition:all 0.15s ease; }
        .scan-row:hover { background:rgba(66,165,245,0.06)!important; }
      `}</style>

      {/* Header */}
      <div style={{ marginBottom: '28px' }}>
        <div style={{ fontSize: '11px', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(66,165,245,0.7)', fontWeight: 600, marginBottom: '8px' }}>
          Historical Data
        </div>
        <h1 style={{ fontFamily: '"Syne", sans-serif', fontSize: '28px', fontWeight: 800, color: '#fff', margin: '0 0 8px', letterSpacing: '-0.02em' }}>
          Scan History
        </h1>
        <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '14px', margin: 0 }}>
          View and analyze past security scans
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px', marginBottom: '20px' }}>
            {[
              { label: 'Total Scans', value: stats.total_scans, icon: '🔍', color: '#42a5f5' },
              { label: 'Avg Risk Score', value: stats.average_scores?.unified_risk?.toFixed(1) || '0', icon: '⚡', color: '#ffa726' },
              { label: 'Critical Findings', value: stats.findings_by_severity?.CRITICAL || 0, icon: '🔴', color: '#ef5350' },
              { label: 'High Findings', value: stats.findings_by_severity?.HIGH || 0, icon: '🟠', color: '#ffa726' },
            ].map((s, i) => (
              <GlassCard key={i} style={{ position: 'relative', overflow: 'hidden', padding: '18px 20px' }}>
                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '3px', background: s.color }} />
                <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)', marginBottom: '4px' }}>{s.label}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontFamily: '"Syne", sans-serif', fontSize: '28px', fontWeight: 800, color: '#fff' }}>{s.value}</span>
                  <span style={{ fontSize: '16px' }}>{s.icon}</span>
                </div>
              </GlassCard>
            ))}
          </div>

          {/* Trend Chart */}
          {getTrendChartData() && (
            <GlassCard style={{ marginBottom: '20px' }}>
              <div style={{ fontFamily: '"Syne", sans-serif', fontSize: '16px', fontWeight: 700, color: '#fff', marginBottom: '14px' }}>
                Scan Trend (Last 30 Days)
              </div>
              <div style={{ height: '220px' }}>
                <Line data={getTrendChartData()} options={chartOptions} />
              </div>
            </GlassCard>
          )}

          {/* Scanner + Severity Distribution */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
            <GlassCard>
              <div style={{ fontFamily: '"Syne", sans-serif', fontSize: '15px', fontWeight: 700, color: '#fff', marginBottom: '14px' }}>
                Findings by Scanner
              </div>
              {Object.entries(stats.findings_by_scanner || {}).map(([sc, count]) => {
                const total = Object.values(stats.findings_by_scanner).reduce((a, b) => a + b, 0) || 1;
                return (
                  <div key={sc} style={{ marginBottom: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.55)', fontWeight: 500 }}>{sc}</span>
                      <span style={{ fontSize: '12px', color: '#fff', fontWeight: 600 }}>{count}</span>
                    </div>
                    <div style={{ height: '5px', borderRadius: '3px', background: 'rgba(255,255,255,0.06)' }}>
                      <div style={{ height: '100%', borderRadius: '3px', width: `${(count / total) * 100}%`, background: scannerColors[sc] || '#42a5f5', transition: 'width 0.4s ease' }} />
                    </div>
                  </div>
                );
              })}
            </GlassCard>
            <GlassCard>
              <div style={{ fontFamily: '"Syne", sans-serif', fontSize: '15px', fontWeight: 700, color: '#fff', marginBottom: '14px' }}>
                Findings by Severity
              </div>
              {Object.entries(stats.findings_by_severity || {}).map(([sev, count]) => {
                const total = Object.values(stats.findings_by_severity).reduce((a, b) => a + b, 0) || 1;
                return (
                  <div key={sev} style={{ marginBottom: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.55)', fontWeight: 500 }}>{sev}</span>
                      <span style={{ fontSize: '12px', color: '#fff', fontWeight: 600 }}>{count}</span>
                    </div>
                    <div style={{ height: '5px', borderRadius: '3px', background: 'rgba(255,255,255,0.06)' }}>
                      <div style={{ height: '100%', borderRadius: '3px', width: `${(count / total) * 100}%`, background: severityColors[sev] || '#42a5f5', transition: 'width 0.4s ease' }} />
                    </div>
                  </div>
                );
              })}
            </GlassCard>
          </div>
        </>
      )}

      {/* Filters */}
      <GlassCard style={{ marginBottom: '16px', padding: '16px 20px' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          <TextField select size="small" label="Severity" value={severity} onChange={(e) => setSeverity(e.target.value)} sx={{ ...muiDarkSx, minWidth: 130 }}>
            <MenuItem value="">All</MenuItem>
            {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'].map(s => <MenuItem key={s} value={s}>{s}</MenuItem>)}
          </TextField>
          <TextField select size="small" label="Scanner" value={scanner} onChange={(e) => setScanner(e.target.value)} sx={{ ...muiDarkSx, minWidth: 130 }}>
            <MenuItem value="">All</MenuItem>
            {['ML', 'Rules', 'LLM', 'Secrets', 'CVE', 'Compliance'].map(s => <MenuItem key={s} value={s}>{s}</MenuItem>)}
          </TextField>
          <TextField type="date" size="small" label="Start Date" value={startDate} onChange={(e) => setStartDate(e.target.value)} InputLabelProps={{ shrink: true }} sx={{ ...muiDarkSx, minWidth: 140 }} />
          <TextField type="date" size="small" label="End Date" value={endDate} onChange={(e) => setEndDate(e.target.value)} InputLabelProps={{ shrink: true }} sx={{ ...muiDarkSx, minWidth: 140 }} />
          <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
            <button className="sh-btn" onClick={fetchScans} style={{ padding: '6px 14px', borderRadius: '8px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.12)', color: 'rgba(255,255,255,0.5)', fontSize: '20px', fontFamily: '"DM Sans", sans-serif' }}>🔄</button>
            <button className="sh-btn" onClick={exportScans} style={{ padding: '6px 14px', borderRadius: '8px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.12)', color: 'rgba(255,255,255,0.5)', fontSize: '20px', fontFamily: '"DM Sans", sans-serif' }}>📥</button>
          </div>
        </div>
      </GlassCard>

      {/* Scan Table */}
      <GlassCard style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <LinearProgress sx={{ borderRadius: 0 }} />
        ) : scans.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div style={{ fontSize: '36px', marginBottom: '8px' }}>📋</div>
            <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: '14px' }}>No scans found matching the filters</div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                  {['ID', 'Filename', 'Date', 'Risk Score', 'Findings', 'Status', 'Actions'].map(h => (
                    <th key={h} style={{ padding: '12px 16px', textAlign: 'left', color: 'rgba(255,255,255,0.5)', fontWeight: 600, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {scans.map((scan) => (
                  <tr key={scan.id} className="scan-row" style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '10px 16px', color: 'rgba(255,255,255,0.4)' }}>#{scan.id}</td>
                    <td style={{ padding: '10px 16px', color: '#fff', fontWeight: 500 }}>{scan.filename}</td>
                    <td style={{ padding: '10px 16px', color: 'rgba(255,255,255,0.5)', fontSize: '12px' }}>{new Date(scan.created_at).toLocaleString()}</td>
                    <td style={{ padding: '10px 16px' }}>
                      <span style={{
                        padding: '3px 10px', borderRadius: '6px', fontSize: '11px', fontWeight: 700,
                        background: `${getRiskColor(scan.unified_risk_score)}20`,
                        color: getRiskColor(scan.unified_risk_score),
                        border: `1px solid ${getRiskColor(scan.unified_risk_score)}40`,
                      }}>
                        {scan.unified_risk_score?.toFixed(1) || 'N/A'}
                      </span>
                    </td>
                    <td style={{ padding: '10px 16px' }}>
                      <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                        {scan.critical_count > 0 && <span style={{ padding: '2px 6px', borderRadius: '4px', fontSize: '10px', fontWeight: 700, background: 'rgba(239,83,80,0.15)', color: '#ef5350' }}>C:{scan.critical_count}</span>}
                        {scan.high_count > 0 && <span style={{ padding: '2px 6px', borderRadius: '4px', fontSize: '10px', fontWeight: 700, background: 'rgba(255,167,38,0.15)', color: '#ffa726' }}>H:{scan.high_count}</span>}
                        {scan.medium_count > 0 && <span style={{ padding: '2px 6px', borderRadius: '4px', fontSize: '10px', fontWeight: 700, background: 'rgba(249,168,37,0.15)', color: '#f9a825' }}>M:{scan.medium_count}</span>}
                      </div>
                    </td>
                    <td style={{ padding: '10px 16px' }}>
                      <span style={{
                        padding: '3px 10px', borderRadius: '99px', fontSize: '10px', fontWeight: 600,
                        background: scan.status === 'completed' ? 'rgba(102,187,106,0.12)' : 'rgba(255,255,255,0.06)',
                        color: scan.status === 'completed' ? '#66bb6a' : 'rgba(255,255,255,0.4)',
                        border: `1px solid ${scan.status === 'completed' ? 'rgba(102,187,106,0.25)' : 'rgba(255,255,255,0.08)'}`,
                      }}>{scan.status}</span>
                    </td>
                    <td style={{ padding: '10px 16px' }}>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        <button onClick={() => handleViewScan(scan.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#42a5f5', fontSize: '16px', padding: '4px' }}>👁️</button>
                        <button onClick={() => confirmDelete(scan.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef5350', fontSize: '16px', padding: '4px' }}>🗑️</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </GlassCard>

      {/* View Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth
        PaperProps={{ sx: { bgcolor: '#0f2744', backgroundImage: 'none', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 3 } }}
      >
        <DialogTitle sx={{ fontWeight: 700, color: '#fff' }}>Scan Details</DialogTitle>
        <DialogContent>
          {selectedScan && (
            <div>
              <div style={{ fontFamily: '"Syne", sans-serif', fontSize: '18px', fontWeight: 700, color: '#fff', marginBottom: '16px' }}>
                {selectedScan.filename}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div style={{ padding: '14px', borderRadius: '10px', background: 'rgba(255,255,255,0.03)' }}>
                  <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)' }}>Risk Score</div>
                  <div style={{ fontSize: '28px', fontWeight: 800, color: '#fff', fontFamily: '"Syne", sans-serif' }}>{selectedScan.unified_risk_score?.toFixed(1)}</div>
                </div>
                <div style={{ padding: '14px', borderRadius: '10px', background: 'rgba(255,255,255,0.03)' }}>
                  <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)' }}>Total Findings</div>
                  <div style={{ fontSize: '28px', fontWeight: 800, color: '#fff', fontFamily: '"Syne", sans-serif' }}>{selectedScan.total_findings}</div>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 0 }}>
          <button onClick={() => setDialogOpen(false)} style={{ padding: '8px 20px', borderRadius: '8px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.12)', color: 'rgba(255,255,255,0.6)', cursor: 'pointer', fontFamily: '"DM Sans", sans-serif' }}>Close</button>
        </DialogActions>
      </Dialog>

      {/* Delete Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}
        PaperProps={{ sx: { bgcolor: '#0f2744', backgroundImage: 'none', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 3 } }}
      >
        <DialogTitle sx={{ fontWeight: 700, color: '#fff' }}>Confirm Delete</DialogTitle>
        <DialogContent><p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '14px' }}>Are you sure you want to delete this scan? This action cannot be undone.</p></DialogContent>
        <DialogActions sx={{ p: 3, pt: 0 }}>
          <button onClick={() => setDeleteDialogOpen(false)} style={{ padding: '8px 20px', borderRadius: '8px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.12)', color: 'rgba(255,255,255,0.6)', cursor: 'pointer', fontFamily: '"DM Sans", sans-serif' }}>Cancel</button>
          <button onClick={handleDeleteScan} style={{ padding: '8px 20px', borderRadius: '8px', border: 'none', background: 'linear-gradient(135deg, #ef5350, #c62828)', color: '#fff', fontWeight: 600, cursor: 'pointer', fontFamily: '"DM Sans", sans-serif' }}>Delete</button>
        </DialogActions>
      </Dialog>
    </div>
  );
}

export default ScanHistory;
