import { useState, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import {
  CircularProgress,
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Rating,
} from '@mui/material';
import {
  BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { getScan, submitFeedback } from '../api/client';
import { useLastScan } from '../context/ScanContext';
import RiskScoreCard from '../components/enhanced/RiskScoreCard';
import FindingsCard from '../components/enhanced/FindingsCard';
import AttackGraph from '../components/enhanced/AttackGraph';

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

const SEV = {
  CRITICAL: { color: '#ef5350', bg: 'rgba(239,83,80,0.12)', border: 'rgba(239,83,80,0.3)' },
  HIGH:     { color: '#ffa726', bg: 'rgba(255,167,38,0.12)', border: 'rgba(255,167,38,0.3)' },
  MEDIUM:   { color: '#f9a825', bg: 'rgba(249,168,37,0.12)', border: 'rgba(249,168,37,0.3)' },
  LOW:      { color: '#66bb6a', bg: 'rgba(102,187,106,0.12)', border: 'rgba(102,187,106,0.3)' },
};

export default function Results() {
  const { scanId } = useParams();
  const location = useLocation();
  const { lastScan } = useLastScan();
  const initialData = location.state?.scanResults || lastScan?.data || null;
  const [scan, setScan] = useState(initialData);
  const [loading, setLoading] = useState(!initialData && !!scanId);
  const [error, setError] = useState(null);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [feedbackRating, setFeedbackRating] = useState(3);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [feedbackType, setFeedbackType] = useState('accurate');
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false);
  const [expandedFinding, setExpandedFinding] = useState(null);

  useEffect(() => {
    if (scanId) {
      if (!scan) setLoading(true);
      const fetchScan = async () => {
        try {
          const data = await getScan(scanId);
          setScan(data);
        } catch (err) {
          if (!scan) setError(err.response?.data?.detail || err.message || 'Failed to load scan results');
        } finally { setLoading(false); }
      };
      fetchScan();
    }
  }, [scanId]);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress sx={{ color: '#42a5f5' }} />
      </div>
    );
  }

  if (error) {
    return (
      <GlassCard style={{ border: '1px solid rgba(239,83,80,0.3)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '20px' }}>⚠️</span>
          <span style={{ color: '#ef5350', fontSize: '14px' }}>{error}</span>
        </div>
      </GlassCard>
    );
  }

  if (!scan) {
    return (
      <GlassCard>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '20px' }}>📋</span>
          <span style={{ color: 'rgba(255,255,255,0.6)', fontSize: '14px' }}>Scan not found</span>
        </div>
      </GlassCard>
    );
  }

  const handleFeedbackSubmit = async () => {
    setFeedbackSubmitting(true);
    try {
      await submitFeedback({
        scan_id: parseInt(scanId) || 0,
        rating: feedbackRating,
        user_comment: feedbackComment,
        feedback_type: feedbackType,
        accepted_prediction: feedbackType === 'accurate',
      });
      setFeedbackOpen(false); setFeedbackRating(3); setFeedbackComment(''); setFeedbackType('accurate');
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    } finally { setFeedbackSubmitting(false); }
  };

  const componentScoresData = [
    { name: 'ML', score: (scan?.ml_score || 0) * 100 },
    { name: 'Rules', score: (scan?.rules_score || 0) * 100 },
    { name: 'LLM', score: (scan?.llm_score || 0) * 100 },
    { name: 'Unified', score: (scan?.unified_risk_score || 0) * 100 },
  ];

  const radarData = [
    { metric: 'Secrets', value: (scan?.secrets_score || 0) * 100 },
    { metric: 'CVE', value: (scan?.cve_score || 0) * 100 },
    { metric: 'Compliance', value: scan?.compliance_score != null ? (100 - scan.compliance_score) : 0 },
    { metric: 'Rules', value: (scan?.rules_score || 0) * 100 },
    { metric: 'ML', value: (scan?.ml_score || 0) * 100 },
    { metric: 'LLM', value: (scan?.llm_score || 0) * 100 },
  ];

  const componentScores = {
    ml_score: ((scan?.ml_score || 0) * 100).toFixed(0),
    rules_score: ((scan?.rules_score || 0) * 100).toFixed(0),
    llm_score: ((scan?.llm_score || 0) * 100).toFixed(0),
  };

  return (
    <div style={{ fontFamily: '"DM Sans", sans-serif' }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Syne:wght@700;800&display=swap');
        .rs-btn { cursor:pointer; transition:all 0.2s ease; }
        .rs-btn:hover { transform:translateY(-1px); filter:brightness(1.15); }
        .finding-row { cursor:pointer; transition:all 0.2s ease; }
        .finding-row:hover { background:rgba(66,165,245,0.06)!important; }
      `}</style>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '28px' }}>
        <div>
          <div style={{
            fontSize: '11px', letterSpacing: '0.2em', textTransform: 'uppercase',
            color: 'rgba(66,165,245,0.7)', fontWeight: 600, marginBottom: '8px',
          }}>Analysis Complete</div>
          <h1 style={{
            fontFamily: '"Syne", sans-serif',
            fontSize: '28px', fontWeight: 800, color: '#fff',
            margin: '0 0 4px', letterSpacing: '-0.02em',
          }}>
            Scan Results
          </h1>
          <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '13px', margin: 0 }}>
            {location.state?.fileName || scan?.filename || 'Unknown file'} • {scan?.findings?.length || 0} findings
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="rs-btn" onClick={() => { setFeedbackType('accurate'); setFeedbackOpen(true); }} style={{
            padding: '8px 16px', borderRadius: '8px', border: 'none',
            background: 'rgba(102,187,106,0.12)', color: '#66bb6a',
            fontSize: '13px', fontWeight: 600, fontFamily: '"DM Sans", sans-serif',
            display: 'flex', alignItems: 'center', gap: '6px',
          }}>👍 Accurate</button>
          <button className="rs-btn" onClick={() => { setFeedbackType('false_positive'); setFeedbackOpen(true); }} style={{
            padding: '8px 16px', borderRadius: '8px', border: 'none',
            background: 'rgba(239,83,80,0.12)', color: '#ef5350',
            fontSize: '13px', fontWeight: 600, fontFamily: '"DM Sans", sans-serif',
            display: 'flex', alignItems: 'center', gap: '6px',
          }}>👎 Report Issue</button>
        </div>
      </div>

      {/* Top Row: Risk Score + Component Scores */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
        <RiskScoreCard score={Math.round((scan.unified_risk_score || 0) * 100)} componentScores={componentScores} />
        <GlassCard>
          <div style={{ fontFamily: '"Syne", sans-serif', fontSize: '16px', fontWeight: 700, color: '#fff', marginBottom: '12px' }}>
            Component Scores
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={componentScoresData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="name" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 12 }} />
              <YAxis domain={[0, 100]} tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }} />
              <Tooltip
                formatter={(value) => `${value.toFixed(1)}%`}
                contentStyle={{ backgroundColor: '#0f2744', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#fff' }}
              />
              <Bar dataKey="score" fill="#42a5f5" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </GlassCard>
      </div>

      {/* Radar Chart */}
      <GlassCard style={{ marginBottom: '20px' }}>
        <div style={{ fontFamily: '"Syne", sans-serif', fontSize: '16px', fontWeight: 700, color: '#fff', marginBottom: '12px' }}>
          Multi-Dimensional Risk Analysis
        </div>
        <ResponsiveContainer width="100%" height={420}>
          <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="75%">
            <PolarGrid stroke="rgba(255,255,255,0.08)" gridType="polygon" />
            <PolarAngleAxis dataKey="metric" tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 13, fontWeight: 600 }} />
            <PolarRadiusAxis domain={[0, 100]} angle={90} tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11 }} tickCount={5} axisLine={false} />
            <Radar name="Risk Score" dataKey="value" stroke="#ef5350" fill="#ef5350" fillOpacity={0.2} strokeWidth={2.5}
              dot={{ r: 4, fill: '#ef5350', stroke: '#fff', strokeWidth: 1 }} />
            <Tooltip
              formatter={(value) => [`${value.toFixed(1)}%`, 'Risk']}
              contentStyle={{ backgroundColor: '#0f2744', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#fff' }}
              labelStyle={{ color: '#42a5f5', fontWeight: 600 }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </GlassCard>

      {/* Enhanced Findings */}
      <div style={{ marginBottom: '20px' }}>
        <FindingsCard findings={scan.findings || []} scannerBreakdown={scan.scanner_breakdown} complianceScore={scan.compliance_score} />
      </div>

      {/* GNN Attack Paths */}
      {scan.gnn_graph_data && (scan.gnn_graph_data.attack_paths?.length > 0 || scan.gnn_graph_data.graph?.nodes?.length > 0) && (
        <GlassCard style={{ marginBottom: '20px', border: '1px solid rgba(255,167,38,0.2)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <span style={{ fontSize: '24px' }}>🔗</span>
            <span style={{ fontFamily: '"Syne", sans-serif', fontSize: '18px', fontWeight: 700, color: '#fff' }}>
              GNN Attack Path Detection
            </span>
            {scan.gnn_graph_data.summary && (
              <span style={{
                padding: '3px 10px', borderRadius: '99px', fontSize: '11px', fontWeight: 600,
                background: scan.gnn_graph_data.summary.critical_paths > 0 ? 'rgba(239,83,80,0.15)' : 'rgba(255,167,38,0.15)',
                color: scan.gnn_graph_data.summary.critical_paths > 0 ? '#ef5350' : '#ffa726',
                border: `1px solid ${scan.gnn_graph_data.summary.critical_paths > 0 ? 'rgba(239,83,80,0.3)' : 'rgba(255,167,38,0.3)'}`,
              }}>
                {scan.gnn_graph_data.summary.total_paths || 0} path(s) detected
              </span>
            )}
          </div>

          {scan.gnn_graph_data.summary && (
            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
              {[
                { label: `${scan.gnn_graph_data.summary.total_resources || 0} resources`, color: 'rgba(255,255,255,0.5)' },
                { label: `${scan.gnn_graph_data.summary.total_edges || 0} connections`, color: 'rgba(255,255,255,0.5)' },
                { label: `${scan.gnn_graph_data.summary.total_vulnerabilities || 0} vulnerabilities`, color: '#ef5350' },
              ].map((t, i) => (
                <span key={i} style={{
                  padding: '3px 10px', borderRadius: '6px', fontSize: '11px',
                  background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)',
                  color: t.color,
                }}>{t.label}</span>
              ))}
            </div>
          )}

          {scan.gnn_graph_data.graph?.nodes?.length > 0 && (
            <div style={{ marginBottom: '16px' }}>
              <AttackGraph graphData={scan.gnn_graph_data.graph} attackPaths={scan.gnn_graph_data.attack_paths} />
            </div>
          )}

          {scan.gnn_graph_data.attack_paths?.map((path, pathIdx) => {
            const sevConfig = SEV[path.severity] || SEV.MEDIUM;
            return (
              <div key={pathIdx} style={{
                marginBottom: '12px', borderRadius: '10px', overflow: 'hidden',
                border: `1px solid ${sevConfig.border}`,
              }}>
                <div
                  className="finding-row"
                  onClick={() => setExpandedFinding(expandedFinding === `path-${pathIdx}` ? null : `path-${pathIdx}`)}
                  style={{
                    padding: '12px 16px', display: 'flex', alignItems: 'center', gap: '10px',
                    background: 'rgba(255,255,255,0.02)',
                  }}
                >
                  <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 700, background: sevConfig.bg, color: sevConfig.color, border: `1px solid ${sevConfig.border}` }}>
                    {path.severity}
                  </span>
                  <span style={{ flex: 1, fontSize: '13px', color: '#fff', fontWeight: 500 }}>{path.path_string}</span>
                  <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)' }}>{path.hops} hops</span>
                  <span style={{ fontSize: '16px', color: 'rgba(255,255,255,0.3)' }}>{expandedFinding === `path-${pathIdx}` ? '▲' : '▼'}</span>
                </div>
                {expandedFinding === `path-${pathIdx}` && (
                  <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                    {path.chain && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '14px', padding: '12px', borderRadius: '8px', background: 'rgba(255,255,255,0.02)' }}>
                        {path.chain.map((node, ni) => (
                          <div key={ni} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            {ni > 0 && <span style={{ color: '#ef5350', fontSize: '18px', fontWeight: 700 }}>→</span>}
                            <div style={{
                              padding: '8px 12px', borderRadius: '8px',
                              border: `2px solid ${node.is_entry ? '#ef5350' : node.is_target ? '#ffa726' : 'rgba(66,165,245,0.3)'}`,
                              background: node.is_entry ? 'rgba(239,83,80,0.1)' : node.is_target ? 'rgba(255,167,38,0.1)' : 'rgba(255,255,255,0.02)',
                              textAlign: 'center', minWidth: '90px',
                            }}>
                              <div style={{ fontSize: '11px', fontWeight: 700, color: '#fff', fontFamily: '"JetBrains Mono", monospace' }}>
                                {node.resource_name || node.resource}
                              </div>
                              <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)' }}>
                                {node.resource_type?.replace('aws_', '')}
                              </div>
                              {ni > 0 && node.relationship && (
                                <div style={{ fontSize: '9px', color: '#42a5f5', fontStyle: 'italic', marginTop: '2px' }}>via {node.relationship}</div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    {path.narrative && (
                      <div style={{ padding: '12px', borderRadius: '8px', background: 'rgba(255,255,255,0.02)', marginBottom: '12px' }}>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: '#fff', marginBottom: '6px' }}>Attack Narrative</div>
                        <pre style={{ fontSize: '11px', color: 'rgba(255,255,255,0.55)', whiteSpace: 'pre-wrap', fontFamily: '"JetBrains Mono", monospace', margin: 0 }}>
                          {path.narrative}
                        </pre>
                      </div>
                    )}
                    {path.remediation?.length > 0 && (
                      <div style={{ padding: '12px', borderRadius: '8px', background: 'rgba(102,187,106,0.06)', border: '1px solid rgba(102,187,106,0.15)' }}>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: '#66bb6a', marginBottom: '8px' }}>Remediation to Break This Path</div>
                        {path.remediation.map((step, si) => (
                          <div key={si} style={{ fontSize: '12px', color: 'rgba(255,255,255,0.55)', marginBottom: '4px' }}>
                            {si + 1}. {step}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </GlassCard>
      )}

      {/* Detailed Analysis */}
      <GlassCard style={{ marginBottom: '20px' }}>
        <div style={{ fontFamily: '"Syne", sans-serif', fontSize: '18px', fontWeight: 700, color: '#fff', marginBottom: '16px' }}>
          Detailed Analysis ({scan.findings?.length || 0})
        </div>
        {scan.findings && scan.findings.length > 0 ? (
          scan.findings.map((finding, index) => {
            const sevConfig = SEV[finding.severity] || SEV.LOW;
            const isOpen = expandedFinding === `finding-${index}`;
            return (
              <div key={index} style={{ marginBottom: '8px', borderRadius: '10px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.06)' }}>
                <div
                  className="finding-row"
                  onClick={() => setExpandedFinding(isOpen ? null : `finding-${index}`)}
                  style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(255,255,255,0.02)' }}
                >
                  <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 700, background: sevConfig.bg, color: sevConfig.color, border: `1px solid ${sevConfig.border}` }}>
                    {finding.severity}
                  </span>
                  <span style={{ flex: 1, fontSize: '13px', color: '#fff', fontWeight: 600 }}>{finding.title}</span>
                  <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.3)', fontFamily: '"JetBrains Mono", monospace' }}>{finding.rule_id}</span>
                  <span style={{ fontSize: '16px', color: 'rgba(255,255,255,0.3)' }}>{isOpen ? '▲' : '▼'}</span>
                </div>
                {isOpen && (
                  <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                    <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '13px', lineHeight: 1.6, marginBottom: '12px' }}>{finding.description}</p>
                    {finding.llm_explanation && (
                      <div style={{ padding: '12px', borderRadius: '8px', background: 'rgba(66,165,245,0.06)', border: '1px solid rgba(66,165,245,0.15)', marginBottom: '10px' }}>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: '#42a5f5', marginBottom: '4px' }}>Explanation</div>
                        <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.55)' }}>{finding.llm_explanation}</div>
                      </div>
                    )}
                    {finding.llm_remediation && (
                      <div style={{ padding: '12px', borderRadius: '8px', background: 'rgba(102,187,106,0.06)', border: '1px solid rgba(102,187,106,0.15)', marginBottom: '10px' }}>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: '#66bb6a', marginBottom: '4px' }}>Remediation</div>
                        <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.55)' }}>{finding.llm_remediation}</div>
                      </div>
                    )}
                    {finding.code_snippet && (
                      <pre style={{
                        padding: '12px', borderRadius: '8px',
                        background: 'rgba(255,255,255,0.03)',
                        border: '1px solid rgba(255,255,255,0.06)',
                        fontFamily: '"JetBrains Mono", monospace', fontSize: '11px',
                        color: 'rgba(255,255,255,0.5)', whiteSpace: 'pre-wrap', margin: 0,
                      }}>
                        {finding.code_snippet}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div style={{ textAlign: 'center', padding: '32px' }}>
            <div style={{ fontSize: '36px', marginBottom: '8px' }}>✅</div>
            <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: '14px' }}>No security issues found!</div>
          </div>
        )}
      </GlassCard>

      {/* Feedback Dialog */}
      <Dialog open={feedbackOpen} onClose={() => setFeedbackOpen(false)} maxWidth="sm" fullWidth
        PaperProps={{ sx: { bgcolor: '#0f2744', backgroundImage: 'none', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 3 } }}
      >
        <DialogTitle sx={{ fontWeight: 700, color: '#fff' }}>Provide Feedback</DialogTitle>
        <DialogContent>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', paddingTop: '8px' }}>
            <div>
              <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.5)', marginBottom: '6px' }}>Overall Rating</div>
              <Rating value={feedbackRating} onChange={(e, v) => setFeedbackRating(v)} size="large" sx={{ '& .MuiRating-iconFilled': { color: '#42a5f5' } }} />
            </div>
            <div>
              <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.5)', marginBottom: '8px' }}>Feedback Type</div>
              {['accurate', 'false_positive', 'false_negative'].map((type) => (
                <div key={type} onClick={() => setFeedbackType(type)} style={{
                  padding: '10px 14px', borderRadius: '8px', marginBottom: '6px', cursor: 'pointer',
                  background: feedbackType === type ? 'rgba(66,165,245,0.12)' : 'rgba(255,255,255,0.02)',
                  border: `1px solid ${feedbackType === type ? 'rgba(66,165,245,0.3)' : 'rgba(255,255,255,0.06)'}`,
                  display: 'flex', alignItems: 'center', gap: '10px',
                }}>
                  <div style={{
                    width: '16px', height: '16px', borderRadius: '50%',
                    border: `2px solid ${feedbackType === type ? '#42a5f5' : 'rgba(255,255,255,0.2)'}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    {feedbackType === type && <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#42a5f5' }} />}
                  </div>
                  <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.7)' }}>
                    {type === 'accurate' ? 'Prediction was accurate' : type === 'false_positive' ? 'False positive (flagged incorrectly)' : 'False negative (missed an issue)'}
                  </span>
                </div>
              ))}
            </div>
            <TextField
              label="Comments (optional)" multiline rows={4}
              value={feedbackComment} onChange={(e) => setFeedbackComment(e.target.value)}
              placeholder="Tell us more..."
              sx={{
                '& .MuiOutlinedInput-root': { color: 'rgba(255,255,255,0.8)', '& fieldset': { borderColor: 'rgba(255,255,255,0.12)' } },
                '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.4)' },
              }}
            />
          </div>
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 0 }}>
          <button onClick={() => setFeedbackOpen(false)} style={{
            padding: '8px 20px', borderRadius: '8px',
            background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.12)',
            color: 'rgba(255,255,255,0.6)', cursor: 'pointer', fontFamily: '"DM Sans", sans-serif',
          }}>Cancel</button>
          <button onClick={handleFeedbackSubmit} disabled={feedbackSubmitting} style={{
            padding: '8px 20px', borderRadius: '8px', border: 'none',
            background: 'linear-gradient(135deg, #1976d2, #42a5f5)',
            color: '#fff', fontWeight: 600, cursor: 'pointer', fontFamily: '"DM Sans", sans-serif',
          }}>
            {feedbackSubmitting ? 'Submitting...' : 'Submit'}
          </button>
        </DialogActions>
      </Dialog>
    </div>
  );
}
