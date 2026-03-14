import { useState, useEffect, useCallback } from 'react';
import { CircularProgress, LinearProgress } from '@mui/material';
import {
  getLearningStatus,
  triggerPatternDiscovery,
  getLearningTelemetry,
  getPatternDetail,
} from '../api/client';
import CurrentScanBanner from '../components/enhanced/CurrentScanBanner';

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

function StatusChip({ active }) {
  return (
    <span style={{
      padding: '5px 14px', borderRadius: '99px', fontSize: '12px', fontWeight: 600,
      background: active ? 'rgba(102,187,106,0.12)' : 'rgba(239,83,80,0.12)',
      color: active ? '#66bb6a' : '#ef5350',
      border: `1px solid ${active ? 'rgba(102,187,106,0.3)' : 'rgba(239,83,80,0.3)'}`,
      display: 'inline-flex', alignItems: 'center', gap: '6px',
    }}>
      <span style={{
        width: '7px', height: '7px', borderRadius: '50%',
        background: active ? '#66bb6a' : '#ef5350',
        boxShadow: `0 0 6px ${active ? '#66bb6a' : '#ef5350'}`,
      }} />
      {active ? 'ACTIVE — Learning' : 'OFFLINE'}
    </span>
  );
}

function MetricCard({ title, value, subtitle, icon, color }) {
  return (
    <GlassCard style={{ position: 'relative', overflow: 'hidden' }}>
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '3px',
        background: color,
      }} />
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)', marginBottom: '6px' }}>{title}</div>
          <div style={{ fontFamily: '"Syne", sans-serif', fontSize: '32px', fontWeight: 800, color, lineHeight: 1 }}>{value}</div>
          {subtitle && <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.35)', marginTop: '6px' }}>{subtitle}</div>}
        </div>
        <div style={{
          width: '40px', height: '40px', borderRadius: '10px',
          background: `${color}15`, border: `1px solid ${color}30`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '18px',
        }}>{icon}</div>
      </div>
    </GlassCard>
  );
}

export default function LearningIntelligence() {
  const [status, setStatus] = useState(null);
  const [telemetry, setTelemetry] = useState(null);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [error, setError] = useState(null);
  const [expandedPattern, setExpandedPattern] = useState(null);
  const [patternDetail, setPatternDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [s, t] = await Promise.all([getLearningStatus(), getLearningTelemetry(20)]);
      setStatus(s); setTelemetry(t); setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load learning status');
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => { const id = setInterval(fetchData, 15000); return () => clearInterval(id); }, [fetchData]);

  const handleDiscover = async () => {
    setDiscovering(true);
    try { await triggerPatternDiscovery(); await fetchData(); } catch (err) { setError(err.message); }
    finally { setDiscovering(false); }
  };

  const handleTogglePattern = async (sig) => {
    if (expandedPattern === sig) { setExpandedPattern(null); setPatternDetail(null); return; }
    setExpandedPattern(sig); setLoadingDetail(true);
    try { const detail = await getPatternDetail(sig); setPatternDetail(detail); }
    catch { setPatternDetail(null); }
    finally { setLoadingDetail(false); }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress size={48} sx={{ color: '#42a5f5' }} />
      </div>
    );
  }

  if (error) {
    return (
      <GlassCard style={{ border: '1px solid rgba(255,167,38,0.3)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '20px' }}>⚠️</span>
          <span style={{ color: 'rgba(255,255,255,0.7)', fontSize: '14px' }}>{error}</span>
          <button onClick={fetchData} style={{
            marginLeft: 'auto', background: 'rgba(66,165,245,0.12)', border: '1px solid rgba(66,165,245,0.3)',
            borderRadius: '8px', color: '#42a5f5', padding: '6px 16px', cursor: 'pointer', fontSize: '13px', fontWeight: 600,
          }}>Retry</button>
        </div>
      </GlassCard>
    );
  }

  const drift = status?.drift ?? {};
  const patterns = status?.pattern_discovery ?? {};
  const ruleWeights = status?.rule_weights ?? {};
  const tel = status?.telemetry_summary ?? {};

  const SEV_COLOR = { CRITICAL: '#ef5350', HIGH: '#ffa726', MEDIUM: '#f9a825', LOW: '#66bb6a' };

  return (
    <div style={{ fontFamily: '"DM Sans", sans-serif' }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Syne:wght@700;800&display=swap');
        .li-btn { cursor:pointer; transition:all 0.2s ease; }
        .li-btn:hover { transform:translateY(-1px); filter:brightness(1.15); }
        .pattern-row { cursor:pointer; transition:all 0.15s ease; }
        .pattern-row:hover { background:rgba(66,165,245,0.06)!important; }
      `}</style>

      <CurrentScanBanner />

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontFamily: '"Syne", sans-serif', fontSize: '28px', fontWeight: 800, color: '#fff', margin: '0 0 8px', letterSpacing: '-0.02em' }}>
            🧠 Learning Intelligence
          </h1>
          <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '14px', margin: 0, maxWidth: '600px', lineHeight: 1.5 }}>
            The system learns from every scan and every feedback event — patterns are discovered, models are retrained, and rules adapt automatically.
          </p>
        </div>
        <StatusChip active={status?.adaptive_learning_active} />
      </div>

      {/* Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', marginBottom: '24px' }}>
        <MetricCard
          title="Training Buffer" value={status?.training_buffer_size ?? 0}
          subtitle={`${status?.feedback_since_retrain ?? 0} / ${status?.auto_retrain_threshold ?? 20} to auto-retrain`}
          icon="📈" color="#42a5f5"
        />
        <MetricCard
          title="Drift Score" value={drift.psi_score?.toFixed(4) ?? '0.0000'}
          subtitle={drift.drift_detected ? '⚠️ Drift Detected' : '✅ Stable'}
          icon="📊" color={drift.drift_detected ? '#ef5350' : '#66bb6a'}
        />
        <MetricCard
          title="Patterns Tracked" value={patterns.total_patterns_tracked ?? 0}
          subtitle={`${patterns.rules_generated ?? 0} rules auto-generated`}
          icon="🔬" color="#ce93d8"
        />
        <MetricCard
          title="Learning Events" value={tel.total_events ?? 0}
          subtitle={`${Object.keys(tel.event_types ?? {}).length} event types`}
          icon="🧠" color="#26c6da"
        />
      </div>

      {/* Two-column row: Auto-Retrain + Drift Monitor */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
        <GlassCard>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <span style={{ fontSize: '16px' }}>🔄</span>
            <span style={{ fontFamily: '"Syne", sans-serif', fontSize: '16px', fontWeight: 700, color: '#fff' }}>Auto-Retrain Pipeline</span>
          </div>
          <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', marginBottom: '16px' }} />
          <div style={{ marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>Feedback progress</span>
              <span style={{ fontSize: '12px', fontWeight: 700, color: '#fff' }}>
                {status?.feedback_since_retrain ?? 0} / {status?.auto_retrain_threshold ?? 20}
              </span>
            </div>
            <LinearProgress variant="determinate"
              value={Math.min(((status?.feedback_since_retrain ?? 0) / (status?.auto_retrain_threshold ?? 20)) * 100, 100)}
              sx={{ height: 6, borderRadius: 3, bgcolor: 'rgba(255,255,255,0.06)', '& .MuiLinearProgress-bar': { background: 'linear-gradient(90deg, #1976d2, #42a5f5)', borderRadius: 3 } }}
            />
          </div>
          <span style={{
            padding: '4px 12px', borderRadius: '6px', fontSize: '11px', fontWeight: 500,
            background: status?.should_retrain ? 'rgba(255,167,38,0.12)' : 'rgba(102,187,106,0.12)',
            color: status?.should_retrain ? '#ffa726' : '#66bb6a',
            border: `1px solid ${status?.should_retrain ? 'rgba(255,167,38,0.3)' : 'rgba(102,187,106,0.3)'}`,
          }}>
            {status?.should_retrain ? `Retrain needed: ${status.retrain_reason}` : 'No retrain needed'}
          </span>
          <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: '12px', lineHeight: 1.5, marginTop: '12px' }}>
            Automatically triggers retraining when feedback reaches threshold or drift exceeds PSI {drift.threshold ?? 0.15}.
          </p>
        </GlassCard>

        <GlassCard>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <span style={{ fontSize: '16px' }}>📊</span>
            <span style={{ fontFamily: '"Syne", sans-serif', fontSize: '16px', fontWeight: 700, color: '#fff' }}>Model Drift Monitor (PSI)</span>
          </div>
          <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', marginBottom: '16px' }} />
          <div style={{ marginBottom: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>Population Stability Index</span>
              <span style={{ fontSize: '12px', fontWeight: 700, color: drift.drift_detected ? '#ef5350' : '#66bb6a' }}>
                {(drift.psi_score ?? 0).toFixed(4)}
              </span>
            </div>
            <LinearProgress variant="determinate"
              value={Math.min((drift.psi_score ?? 0) / 0.3 * 100, 100)}
              sx={{ height: 6, borderRadius: 3, bgcolor: 'rgba(255,255,255,0.06)', '& .MuiLinearProgress-bar': { background: drift.drift_detected ? '#ef5350' : '#66bb6a', borderRadius: 3 } }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '4px' }}>
              <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.25)' }}>0.00 (stable)</span>
              <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.25)' }}>0.15 (threshold)</span>
              <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.25)' }}>0.30 (critical)</span>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <span style={{ padding: '3px 10px', borderRadius: '6px', fontSize: '10px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.4)' }}>
              Reference: {drift.reference_size ?? 0} predictions
            </span>
            <span style={{ padding: '3px 10px', borderRadius: '6px', fontSize: '10px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.4)' }}>
              Recent: {drift.recent_size ?? 0} predictions
            </span>
          </div>
        </GlassCard>
      </div>

      {/* Rule Weights + Pattern Discovery */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
        <GlassCard>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <span style={{ fontSize: '16px' }}>⚖️</span>
            <span style={{ fontFamily: '"Syne", sans-serif', fontSize: '16px', fontWeight: 700, color: '#fff' }}>Adaptive Rule Weights</span>
          </div>
          <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', marginBottom: '16px' }} />
          {ruleWeights.total_rules_tracked > 0 ? (
            <>
              <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)', marginBottom: '12px' }}>
                Tracking <strong style={{ color: '#fff' }}>{ruleWeights.total_rules_tracked}</strong> rules — avg confidence <strong style={{ color: '#fff' }}>{(ruleWeights.avg_confidence ?? 0).toFixed(2)}</strong>
              </p>
              {(ruleWeights.low_confidence_rules?.length > 0) && (
                <div style={{ padding: '8px 12px', borderRadius: '8px', background: 'rgba(66,165,245,0.08)', border: '1px solid rgba(66,165,245,0.15)', fontSize: '12px', color: '#42a5f5', marginBottom: '12px' }}>
                  ℹ️ {ruleWeights.low_confidence_rules.length} rule(s) flagged as noisy (confidence &lt; 0.4)
                </div>
              )}
              <div style={{ overflowX: 'auto', maxHeight: '200px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                      {['Rule ID', 'Confidence', 'TP', 'FP'].map(h => (
                        <th key={h} style={{ padding: '8px 12px', textAlign: h === 'Rule ID' ? 'left' : 'right', color: 'rgba(255,255,255,0.4)', fontWeight: 600, fontSize: '10px', textTransform: 'uppercase' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(ruleWeights.rules ?? {}).slice(0, 10).map(([ruleId, data]) => (
                      <tr key={ruleId} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                        <td style={{ padding: '6px 12px', fontFamily: '"JetBrains Mono", monospace', fontSize: '11px', color: 'rgba(255,255,255,0.6)' }}>{ruleId}</td>
                        <td style={{ padding: '6px 12px', textAlign: 'right' }}>
                          <span style={{
                            padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 700,
                            background: data.confidence >= 0.7 ? 'rgba(102,187,106,0.15)' : data.confidence >= 0.4 ? 'rgba(255,167,38,0.15)' : 'rgba(239,83,80,0.15)',
                            color: data.confidence >= 0.7 ? '#66bb6a' : data.confidence >= 0.4 ? '#ffa726' : '#ef5350',
                          }}>{data.confidence?.toFixed(2)}</span>
                        </td>
                        <td style={{ padding: '6px 12px', textAlign: 'right', color: 'rgba(255,255,255,0.5)' }}>{data.true_positives}</td>
                        <td style={{ padding: '6px 12px', textAlign: 'right', color: 'rgba(255,255,255,0.5)' }}>{data.false_positives}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: '24px' }}>
              <div style={{ fontSize: '36px', marginBottom: '8px' }}>⚖️</div>
              <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '13px' }}>No rule feedback yet — submit scan feedback to start learning</p>
            </div>
          )}
        </GlassCard>

        <GlassCard style={{ overflow: 'visible' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <span style={{ fontSize: '16px' }}>🔬</span>
            <span style={{ fontFamily: '"Syne", sans-serif', fontSize: '16px', fontWeight: 700, color: '#fff' }}>Pattern Discovery</span>
          </div>
          <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', marginBottom: '16px' }} />
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '14px' }}>
            {[
              { label: `${patterns.total_patterns_tracked ?? 0} patterns tracked`, color: 'rgba(255,255,255,0.4)' },
              { label: `${patterns.rules_generated ?? 0} rules generated`, color: '#66bb6a' },
              { label: `${patterns.pending_patterns ?? 0} pending`, color: '#ffa726' },
            ].map((t, i) => (
              <span key={i} style={{ padding: '3px 10px', borderRadius: '6px', fontSize: '10px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)', color: t.color }}>{t.label}</span>
            ))}
          </div>
          {(patterns.top_patterns ?? []).length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {patterns.top_patterns.map((p, i) => {
                const isExpanded = expandedPattern === p.signature;
                const detail = isExpanded ? patternDetail : null;
                const sevColor = SEV_COLOR[p.severity] || '#42a5f5';
                const cleanDesc = (p.sample_description || '').replace(/\*\*Impact:?\*\*.*$/s, '').replace(/\*\*(.*?)\*\*/g, '$1').trim() || p.signature;
                return (
                  <div key={i} style={{
                    borderRadius: '8px',
                    border: `1px solid ${isExpanded ? 'rgba(66,165,245,0.3)' : 'rgba(255,255,255,0.06)'}`,
                    transition: 'border-color 0.25s ease, box-shadow 0.25s ease',
                    boxShadow: isExpanded ? '0 4px 20px rgba(66,165,245,0.08)' : 'none',
                  }}>
                    <div className="pattern-row" onClick={() => handleTogglePattern(p.signature)}
                      style={{
                        padding: '10px 14px', display: 'flex', alignItems: 'center', gap: '8px',
                        background: isExpanded ? 'rgba(66,165,245,0.04)' : 'rgba(255,255,255,0.02)',
                        borderRadius: isExpanded ? '8px 8px 0 0' : '8px',
                        transition: 'background 0.2s ease',
                        userSelect: 'none',
                      }}>
                      <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 700, background: `${sevColor}20`, color: sevColor, minWidth: '60px', textAlign: 'center', flexShrink: 0 }}>{p.severity}</span>
                      <span style={{ flex: 1, fontSize: '12px', color: 'rgba(255,255,255,0.6)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{cleanDesc}</span>
                      <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.3)', flexShrink: 0 }}>{p.count}×</span>
                      {p.rule_generated
                        ? <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '9px', fontWeight: 600, background: 'rgba(102,187,106,0.15)', color: '#66bb6a', flexShrink: 0 }}>Rule Created</span>
                        : <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '9px', background: 'rgba(255,255,255,0.04)', color: 'rgba(255,255,255,0.3)', flexShrink: 0 }}>Tracking</span>
                      }
                      <span style={{
                        fontSize: '10px', color: 'rgba(255,255,255,0.3)', flexShrink: 0,
                        transition: 'transform 0.25s ease',
                        transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                        display: 'inline-block',
                      }}>▼</span>
                    </div>
                    <div style={{
                      maxHeight: isExpanded ? '500px' : '0px',
                      overflow: 'hidden',
                      transition: 'max-height 0.35s ease, opacity 0.25s ease',
                      opacity: isExpanded ? 1 : 0,
                    }}>
                      <div style={{ padding: '14px', background: 'rgba(255,255,255,0.015)', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                        {loadingDetail ? (
                          <div style={{ display: 'flex', justifyContent: 'center', padding: '12px' }}><CircularProgress size={20} sx={{ color: '#42a5f5' }} /></div>
                        ) : detail ? (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            {detail.risk_explanation && (
                              <div style={{ padding: '10px 12px', borderRadius: '8px', background: 'rgba(66,165,245,0.06)', border: '1px solid rgba(66,165,245,0.15)', fontSize: '12px', color: 'rgba(255,255,255,0.55)', lineHeight: 1.5 }}>
                                ℹ️ {detail.risk_explanation}
                              </div>
                            )}
                            {detail.affected_resources?.length > 0 && (
                              <div>
                                <div style={{ fontSize: '11px', fontWeight: 600, color: 'rgba(255,255,255,0.5)', marginBottom: '6px' }}>Affected Resources ({detail.affected_resources.length})</div>
                                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                                  {detail.affected_resources.map((r, ri) => (
                                    <span key={ri} style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontFamily: '"JetBrains Mono", monospace', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.5)' }}>{r}</span>
                                  ))}
                                </div>
                              </div>
                            )}
                            {detail.remediation_guidance?.length > 0 && (
                              <div style={{ padding: '10px 12px', borderRadius: '8px', background: 'rgba(102,187,106,0.06)', border: '1px solid rgba(102,187,106,0.15)' }}>
                                <div style={{ fontSize: '11px', fontWeight: 700, color: '#66bb6a', marginBottom: '6px' }}>Remediation</div>
                                {detail.remediation_guidance.map((step, si) => (
                                  <div key={si} style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', marginBottom: '3px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <span style={{ color: '#66bb6a', fontSize: '12px' }}>✓</span> {step}
                                  </div>
                                ))}
                              </div>
                            )}
                            <div style={{ display: 'flex', gap: '12px' }}>
                              <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.25)' }}>First: {detail.first_seen ? new Date(detail.first_seen).toLocaleDateString() : '—'}</span>
                              <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.25)' }}>Last: {detail.last_seen ? new Date(detail.last_seen).toLocaleDateString() : '—'}</span>
                              <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.25)' }}>Files: {detail.affected_files?.length ?? 0}</span>
                            </div>
                          </div>
                        ) : (
                          <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '12px', margin: 0 }}>No detail available.</p>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '13px' }}>No patterns discovered yet — run more scans.</p>
          )}
          <button className="li-btn" onClick={handleDiscover} disabled={discovering} style={{
            marginTop: '14px', padding: '8px 18px', borderRadius: '8px',
            background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.12)',
            color: 'rgba(255,255,255,0.6)', fontSize: '12px', fontWeight: 500,
            fontFamily: '"DM Sans", sans-serif',
            display: 'flex', alignItems: 'center', gap: '6px',
          }}>
            🔬 {discovering ? 'Discovering…' : 'Run Discovery Cycle'}
          </button>
        </GlassCard>
      </div>

      {/* Telemetry Feed */}
      <GlassCard style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <span style={{ fontSize: '16px' }}>📡</span>
          <span style={{ fontFamily: '"Syne", sans-serif', fontSize: '16px', fontWeight: 700, color: '#fff' }}>Learning Telemetry (Live)</span>
        </div>
        <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', marginBottom: '14px' }} />
        {(telemetry?.recent_events ?? []).length > 0 ? (
          <div style={{ overflowX: 'auto', maxHeight: '280px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                  {['Time', 'Event', 'Details'].map(h => (
                    <th key={h} style={{ padding: '8px 14px', textAlign: 'left', color: 'rgba(255,255,255,0.4)', fontWeight: 600, fontSize: '10px', textTransform: 'uppercase' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {telemetry.recent_events.slice().reverse().map((evt, i) => {
                  const evtColor = evt.type === 'retrain_completed' ? '#66bb6a' : evt.type === 'drift_detected' ? '#ef5350' : evt.type === 'feedback_processed' ? '#42a5f5' : 'rgba(255,255,255,0.4)';
                  return (
                    <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                      <td style={{ padding: '6px 14px', whiteSpace: 'nowrap', color: 'rgba(255,255,255,0.35)', fontSize: '11px' }}>
                        {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : '—'}
                      </td>
                      <td style={{ padding: '6px 14px' }}>
                        <span style={{
                          padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 600,
                          fontFamily: '"JetBrains Mono", monospace',
                          background: `${evtColor}15`, color: evtColor,
                          border: `1px solid ${evtColor}30`,
                        }}>{evt.type}</span>
                      </td>
                      <td style={{ padding: '6px 14px', fontSize: '11px', fontFamily: '"JetBrains Mono", monospace', color: 'rgba(255,255,255,0.35)', maxWidth: '400px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {JSON.stringify(Object.fromEntries(Object.entries(evt).filter(([k]) => !['type', 'timestamp'].includes(k)))).slice(0, 120)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '32px' }}>
            <div style={{ fontSize: '36px', marginBottom: '8px' }}>🧠</div>
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '13px' }}>No learning events yet — scan a file to start.</p>
          </div>
        )}
      </GlassCard>

      {/* How It Works */}
      <GlassCard>
        <div style={{ fontFamily: '"Syne", sans-serif', fontSize: '16px', fontWeight: 700, color: '#fff', marginBottom: '16px' }}>
          🔄 How Adaptive Learning Works
        </div>
        <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)', marginBottom: '20px' }} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '18px' }}>
          {[
            { step: '1', title: 'Scan Ingestion', desc: 'Every scan feeds the drift detector and pattern engine.' },
            { step: '2', title: 'Feedback Learning', desc: 'User feedback trains the model and adjusts rule weights.' },
            { step: '3', title: 'Drift Detection', desc: 'PSI monitoring compares predictions vs baseline.' },
            { step: '4', title: 'Auto-Retrain', desc: `After ${status?.auto_retrain_threshold ?? 20} feedback events or drift.` },
            { step: '5', title: 'Pattern Discovery', desc: 'Recurring patterns auto-generate YAML rules.' },
            { step: '6', title: 'Model Evaluation', desc: 'New models must improve on champion to be promoted.' },
          ].map(({ step, title, desc }) => (
            <div key={step} style={{ display: 'flex', gap: '12px' }}>
              <div style={{
                width: '28px', height: '28px', borderRadius: '50%', flexShrink: 0,
                background: 'linear-gradient(135deg, #1976d2, #42a5f5)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '12px', fontWeight: 700, color: '#fff',
              }}>{step}</div>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 700, color: '#fff', marginBottom: '3px' }}>{title}</div>
                <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.35)', lineHeight: 1.4 }}>{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
}
