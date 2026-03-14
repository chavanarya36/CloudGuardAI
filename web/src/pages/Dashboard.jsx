import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CircularProgress } from '@mui/material';
import { getScanStats } from '../api/client';
import CurrentScanBanner from '../components/enhanced/CurrentScanBanner';

const SEVERITY_CONFIG = {
  CRITICAL: { color: '#ef5350', icon: '🔴' },
  HIGH: { color: '#ffa726', icon: '🟠' },
  MEDIUM: { color: '#f9a825', icon: '🟡' },
  LOW: { color: '#66bb6a', icon: '🟢' },
  INFO: { color: '#42a5f5', icon: '🔵' },
};

function GlassCard({ children, style, hoverBorder }) {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: 'rgba(10,22,38,0.8)',
        border: `1px solid ${hovered && hoverBorder ? hoverBorder : 'rgba(255,255,255,0.06)'}`,
        borderRadius: '14px', padding: '24px',
        backdropFilter: 'blur(8px)',
        transition: 'all 0.3s ease',
        boxShadow: hovered ? '0 8px 32px rgba(0,0,0,0.3)' : 'none',
        ...style,
      }}
    >
      {children}
    </div>
  );
}

function StatCard({ title, value, subtitle, icon, color, gradient }) {
  return (
    <GlassCard hoverBorder={color} style={{ position: 'relative', overflow: 'hidden' }}>
      <div style={{
        position: 'absolute', top: 0, right: 0,
        width: '80px', height: '80px',
        background: `radial-gradient(circle at top right, ${color}15, transparent 70%)`,
      }} />
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.4)', marginBottom: '8px', fontWeight: 500 }}>
            {title}
          </div>
          <div style={{
            fontFamily: '"Syne", sans-serif',
            fontSize: '32px', fontWeight: 800, color: '#fff',
            lineHeight: 1, marginBottom: '6px',
          }}>
            {value}
          </div>
          {subtitle && (
            <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.3)' }}>{subtitle}</div>
          )}
        </div>
        <div style={{
          width: '44px', height: '44px', borderRadius: '10px',
          background: gradient || `${color}15`,
          border: `1px solid ${color}30`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '20px',
        }}>
          {icon}
        </div>
      </div>
    </GlassCard>
  );
}

function SeverityBar({ label, count, total, config }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div style={{ marginBottom: '14px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
        <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.6)', fontWeight: 500 }}>
          {config.icon} {label}
        </span>
        <span style={{ fontSize: '13px', fontWeight: 700, color: '#fff' }}>{count}</span>
      </div>
      <div style={{
        height: '6px', borderRadius: '3px',
        background: 'rgba(255,255,255,0.06)',
        overflow: 'hidden',
      }}>
        <div style={{
          height: '100%', borderRadius: '3px',
          width: `${pct}%`,
          background: config.color,
          transition: 'width 0.6s ease',
        }} />
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getScanStats();
        setStats(data);
      } catch (err) {
        setError(err.message || 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress size={48} sx={{ color: '#42a5f5' }} />
      </div>
    );
  }

  if (error) {
    return (
      <GlassCard hoverBorder="#ffa726" style={{ border: '1px solid rgba(255,167,38,0.3)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '20px' }}>⚠️</span>
          <span style={{ color: 'rgba(255,255,255,0.7)', fontSize: '14px' }}>{error}</span>
          <button
            onClick={() => window.location.reload()}
            style={{
              marginLeft: 'auto', background: 'rgba(255,167,38,0.15)',
              border: '1px solid rgba(255,167,38,0.3)', borderRadius: '8px',
              color: '#ffa726', padding: '6px 16px', cursor: 'pointer',
              fontSize: '13px', fontWeight: 600,
            }}
          >
            Retry
          </button>
        </div>
      </GlassCard>
    );
  }

  const totalFindings = stats
    ? Object.values(stats.findings_by_severity).reduce((a, b) => a + b, 0)
    : 0;

  const avgRisk = stats?.average_scores?.unified_risk ?? 0;
  const riskLabel = avgRisk >= 0.7 ? 'Critical' : avgRisk >= 0.4 ? 'Medium' : 'Low';
  const riskColor = avgRisk >= 0.7 ? '#ef5350' : avgRisk >= 0.4 ? '#ffa726' : '#66bb6a';

  const trendScans = stats?.trend_30_days?.reduce((sum, d) => sum + d.count, 0) ?? 0;

  return (
    <div style={{ fontFamily: '"DM Sans", sans-serif' }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Syne:wght@700;800&display=swap');
        .action-btn { cursor:pointer; transition:all 0.25s ease; }
        .action-btn:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(66,165,245,0.3); }
      `}</style>

      <CurrentScanBanner />

      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{
          fontSize: '11px', letterSpacing: '0.2em', textTransform: 'uppercase',
          color: 'rgba(66,165,245,0.7)', fontWeight: 600, marginBottom: '8px',
        }}>
          Overview
        </div>
        <h1 style={{
          fontFamily: '"Syne", sans-serif',
          fontSize: '28px', fontWeight: 800, color: '#fff',
          margin: '0 0 8px', letterSpacing: '-0.02em',
        }}>
          Security Dashboard
        </h1>
        <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '14px', margin: 0 }}>
          Real-time overview of your infrastructure security posture
        </p>
      </div>

      {/* Stats Grid */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px', marginBottom: '28px',
      }}>
        <StatCard title="Total Scans" value={stats?.total_scans ?? 0} subtitle="All-time" icon="🔍" color="#42a5f5" />
        <StatCard title="Total Findings" value={totalFindings} subtitle="Across all scans" icon="🐛" color="#ef5350" />
        <StatCard title="Avg Risk Score" value={`${(avgRisk * 100).toFixed(0)}%`} subtitle={riskLabel} icon="🛡️" color={riskColor} />
        <StatCard title="Active Scanners" value={Object.values(stats?.findings_by_scanner ?? {}).filter(v => v > 0).length} subtitle="Out of 6" icon="⚡" color="#66bb6a" />
      </div>

      {/* Two-column row */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
        gap: '16px', marginBottom: '28px',
      }}>
        {/* Severity Breakdown */}
        <GlassCard>
          <div style={{
            fontFamily: '"Syne", sans-serif',
            fontSize: '16px', fontWeight: 700, color: '#fff', marginBottom: '6px',
          }}>
            Findings by Severity
          </div>
          <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', margin: '12px 0 16px' }} />
          {Object.entries(SEVERITY_CONFIG).map(([severity, config]) => (
            <SeverityBar
              key={severity}
              label={severity}
              count={stats?.findings_by_severity?.[severity] ?? 0}
              total={totalFindings || 1}
              config={config}
            />
          ))}
          {totalFindings === 0 && (
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <div style={{ fontSize: '36px', marginBottom: '8px' }}>✅</div>
              <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: '13px' }}>
                No findings — run a scan to get started
              </div>
            </div>
          )}
        </GlassCard>

        {/* Scanner Breakdown */}
        <GlassCard>
          <div style={{
            fontFamily: '"Syne", sans-serif',
            fontSize: '16px', fontWeight: 700, color: '#fff', marginBottom: '6px',
          }}>
            Findings by Scanner
          </div>
          <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', margin: '12px 0 16px' }} />
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px',
          }}>
            {Object.entries(stats?.findings_by_scanner ?? {}).map(([scanner, count]) => (
              <div key={scanner} style={{
                textAlign: 'center', padding: '14px',
                borderRadius: '10px',
                background: count > 0 ? 'rgba(255,167,38,0.08)' : 'rgba(255,255,255,0.03)',
                border: `1px solid ${count > 0 ? 'rgba(255,167,38,0.2)' : 'rgba(255,255,255,0.06)'}`,
              }}>
                <div style={{ fontSize: '22px', fontWeight: 800, color: '#fff', fontFamily: '"Syne", sans-serif' }}>
                  {count}
                </div>
                <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)', marginTop: '4px' }}>
                  {scanner}
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Average Scanner Scores */}
      <GlassCard style={{ marginBottom: '28px' }}>
        <div style={{
          fontFamily: '"Syne", sans-serif',
          fontSize: '16px', fontWeight: 700, color: '#fff', marginBottom: '6px',
        }}>
          Average Scanner Scores
        </div>
        <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', margin: '12px 0 16px' }} />
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))',
          gap: '16px',
        }}>
          {[
            { label: 'ML Model', key: 'ml_score', color: '#42a5f5' },
            { label: 'Rules Engine', key: 'rules_score', color: '#ce93d8' },
            { label: 'LLM Reasoning', key: 'llm_score', color: '#26c6da' },
            { label: 'Secrets', key: 'secrets_score', color: '#ef5350' },
            { label: 'CVE', key: 'cve_score', color: '#ffa726' },
            { label: 'Compliance', key: 'compliance_score', color: '#66bb6a' },
          ].map(({ label, key, color }) => {
            const score = stats?.average_scores?.[key] ?? 0;
            const pct = (score * 100).toFixed(0);
            return (
              <div key={key} style={{ textAlign: 'center' }}>
                <div style={{
                  width: '64px', height: '64px', borderRadius: '50%',
                  border: `3px solid ${color}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  margin: '0 auto 8px',
                  background: `conic-gradient(${color} ${pct}%, rgba(255,255,255,0.06) ${pct}%)`,
                  position: 'relative',
                }}>
                  <div style={{
                    width: '52px', height: '52px', borderRadius: '50%',
                    background: '#0a1622', display: 'flex',
                    alignItems: 'center', justifyContent: 'center',
                  }}>
                    <span style={{ fontSize: '14px', fontWeight: 700, color: '#fff' }}>{pct}%</span>
                  </div>
                </div>
                <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.45)' }}>{label}</div>
              </div>
            );
          })}
        </div>
      </GlassCard>

      {/* Quick Actions */}
      <GlassCard style={{ marginBottom: '28px' }}>
        <div style={{
          fontFamily: '"Syne", sans-serif',
          fontSize: '16px', fontWeight: 700, color: '#fff', marginBottom: '6px',
        }}>
          Quick Actions
        </div>
        <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', margin: '12px 0 16px' }} />
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <button className="action-btn" onClick={() => navigate('/')} style={{
            padding: '10px 22px', borderRadius: '10px', border: 'none',
            background: 'linear-gradient(135deg, #1976d2, #42a5f5)',
            color: '#fff', fontSize: '13px', fontWeight: 600,
            fontFamily: '"DM Sans", sans-serif',
            display: 'flex', alignItems: 'center', gap: '8px',
          }}>
            🔍 New Scan
          </button>
          <button className="action-btn" onClick={() => navigate('/history')} style={{
            padding: '10px 22px', borderRadius: '10px',
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.12)',
            color: 'rgba(255,255,255,0.7)', fontSize: '13px', fontWeight: 500,
            fontFamily: '"DM Sans", sans-serif', cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: '8px',
          }}>
            📋 Scan History
          </button>
          <button className="action-btn" onClick={() => navigate('/model-status')} style={{
            padding: '10px 22px', borderRadius: '10px',
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.12)',
            color: 'rgba(255,255,255,0.7)', fontSize: '13px', fontWeight: 500,
            fontFamily: '"DM Sans", sans-serif', cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: '8px',
          }}>
            🛡️ Model Status
          </button>
        </div>
      </GlassCard>

      {/* 30-Day Trend */}
      {stats?.trend_30_days?.length > 0 && (
        <GlassCard>
          <div style={{
            fontFamily: '"Syne", sans-serif',
            fontSize: '16px', fontWeight: 700, color: '#fff', marginBottom: '6px',
          }}>
            Scan Activity (Last 30 Days)
          </div>
          <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', margin: '12px 0 16px' }} />
          <div style={{ display: 'flex', gap: '3px', alignItems: 'flex-end', height: '80px' }}>
            {stats.trend_30_days.map((day, i) => {
              const max = Math.max(...stats.trend_30_days.map(d => d.count), 1);
              const height = (day.count / max) * 100;
              return (
                <div
                  key={i}
                  title={`${day.date}: ${day.count} scans`}
                  style={{
                    flex: 1, minWidth: '3px',
                    height: `${Math.max(height, 4)}%`,
                    background: 'linear-gradient(180deg, #42a5f5, #1565c0)',
                    borderRadius: '2px 2px 0 0',
                    transition: 'all 0.2s',
                    opacity: 0.8,
                  }}
                />
              );
            })}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px' }}>
            <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.3)' }}>
              {stats.trend_30_days[0]?.date}
            </span>
            <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.3)' }}>
              {stats.trend_30_days[stats.trend_30_days.length - 1]?.date}
            </span>
          </div>
        </GlassCard>
      )}
    </div>
  );
}
