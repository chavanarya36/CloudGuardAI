import { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  CircularProgress,
  Alert,
  Paper,
  Divider,
  Button,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
} from '@mui/material';
import PsychologyIcon from '@mui/icons-material/Psychology';
import AutorenewIcon from '@mui/icons-material/Autorenew';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import PatternIcon from '@mui/icons-material/Pattern';
import ScaleIcon from '@mui/icons-material/Scale';
import TimelineIcon from '@mui/icons-material/Timeline';
import RuleIcon from '@mui/icons-material/Rule';
import {
  getLearningStatus,
  triggerPatternDiscovery,
  getLearningTelemetry,
} from '../api/client';

function StatusChip({ active }) {
  return (
    <Chip
      label={active ? 'ACTIVE — Learning' : 'OFFLINE'}
      color={active ? 'success' : 'error'}
      variant="outlined"
      icon={active ? <PsychologyIcon /> : <WarningAmberIcon />}
      sx={{ fontWeight: 'bold' }}
    />
  );
}

function MetricCard({ title, value, subtitle, icon, color = 'primary.main' }) {
  return (
    <Card variant="outlined" sx={{ height: '100%', borderRadius: 3, border: '2px solid', borderColor: 'divider', transition: 'all 0.3s', '&:hover': { borderColor: color, boxShadow: 4 } }}>
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>{title}</Typography>
            <Typography variant="h3" fontWeight="bold" color={color}>{value}</Typography>
            {subtitle && <Typography variant="caption" color="text.secondary">{subtitle}</Typography>}
          </Box>
          <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: `${color}15`, display: 'flex', alignItems: 'center' }}>
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

export default function LearningIntelligence() {
  const [status, setStatus] = useState(null);
  const [telemetry, setTelemetry] = useState(null);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [s, t] = await Promise.all([getLearningStatus(), getLearningTelemetry(20)]);
      setStatus(s);
      setTelemetry(t);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load learning status');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Auto-refresh every 15s
  useEffect(() => {
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleDiscover = async () => {
    setDiscovering(true);
    try {
      await triggerPatternDiscovery();
      await fetchData();
    } catch (err) {
      setError(err.message);
    } finally {
      setDiscovering(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress size={48} />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="warning" sx={{ borderRadius: 2 }}>{error} — <Button size="small" onClick={fetchData}>Retry</Button></Alert>;
  }

  const drift = status?.drift ?? {};
  const patterns = status?.pattern_discovery ?? {};
  const ruleWeights = status?.rule_weights ?? {};
  const tel = status?.telemetry_summary ?? {};

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            🧠 Learning Intelligence
          </Typography>
          <Typography variant="body1" color="text.secondary">
            The system learns from every scan and every feedback event — patterns are discovered, models are retrained, and rules adapt automatically.
          </Typography>
        </Box>
        <StatusChip active={status?.adaptive_learning_active} />
      </Box>

      {/* Top Metric Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Training Buffer"
            value={status?.training_buffer_size ?? 0}
            subtitle={`${status?.feedback_since_retrain ?? 0} / ${status?.auto_retrain_threshold ?? 20} to auto-retrain`}
            icon={<TrendingUpIcon sx={{ color: 'primary.main' }} />}
            color="primary.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Drift Score"
            value={drift.psi_score?.toFixed(4) ?? '0.0000'}
            subtitle={drift.drift_detected ? '⚠️ Drift Detected' : '✅ Stable'}
            icon={<TimelineIcon sx={{ color: drift.drift_detected ? 'error.main' : 'success.main' }} />}
            color={drift.drift_detected ? 'error.main' : 'success.main'}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Patterns Tracked"
            value={patterns.total_patterns_tracked ?? 0}
            subtitle={`${patterns.rules_generated ?? 0} rules auto-generated`}
            icon={<PatternIcon sx={{ color: 'secondary.main' }} />}
            color="secondary.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Learning Events"
            value={tel.total_events ?? 0}
            subtitle={Object.keys(tel.event_types ?? {}).length + ' event types'}
            icon={<PsychologyIcon sx={{ color: 'info.main' }} />}
            color="info.main"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Auto-Retrain Status */}
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 3, borderRadius: 3, border: '2px solid', borderColor: 'divider' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              <AutorenewIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Auto-Retrain Pipeline
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                <Typography variant="body2">Feedback progress</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {status?.feedback_since_retrain ?? 0} / {status?.auto_retrain_threshold ?? 20}
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={Math.min(((status?.feedback_since_retrain ?? 0) / (status?.auto_retrain_threshold ?? 20)) * 100, 100)}
                sx={{ height: 10, borderRadius: 1 }}
              />
            </Box>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
              <Chip
                label={status?.should_retrain ? `Retrain needed: ${status.retrain_reason}` : 'No retrain needed'}
                color={status?.should_retrain ? 'warning' : 'success'}
                size="small"
                variant="outlined"
              />
            </Box>
            <Typography variant="body2" color="text.secondary">
              The system automatically triggers retraining when feedback volume reaches the threshold
              or when prediction drift exceeds PSI {drift.threshold ?? 0.15}. Every new data point
              makes the model smarter.
            </Typography>
          </Paper>
        </Grid>

        {/* Drift Monitor */}
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 3, borderRadius: 3, border: '2px solid', borderColor: 'divider' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              <TimelineIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Model Drift Monitor (PSI)
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                <Typography variant="body2">Population Stability Index</Typography>
                <Typography variant="body2" fontWeight="bold" color={drift.drift_detected ? 'error.main' : 'success.main'}>
                  {(drift.psi_score ?? 0).toFixed(4)}
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={Math.min((drift.psi_score ?? 0) / 0.3 * 100, 100)}
                color={drift.drift_detected ? 'error' : 'success'}
                sx={{ height: 10, borderRadius: 1 }}
              />
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                <Typography variant="caption" color="text.secondary">0.00 (stable)</Typography>
                <Typography variant="caption" color="text.secondary">0.15 (threshold)</Typography>
                <Typography variant="caption" color="text.secondary">0.30 (critical)</Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Chip label={`Reference: ${drift.reference_size ?? 0} predictions`} size="small" variant="outlined" />
              <Chip label={`Recent: ${drift.recent_size ?? 0} predictions`} size="small" variant="outlined" />
            </Box>
          </Paper>
        </Grid>

        {/* Rule Weights */}
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 3, borderRadius: 3, border: '2px solid', borderColor: 'divider' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              <ScaleIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Adaptive Rule Weights
            </Typography>
            <Divider sx={{ mb: 2 }} />
            {ruleWeights.total_rules_tracked > 0 ? (
              <>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  Tracking <strong>{ruleWeights.total_rules_tracked}</strong> rules —
                  avg confidence <strong>{(ruleWeights.avg_confidence ?? 0).toFixed(2)}</strong>
                </Typography>
                {(ruleWeights.low_confidence_rules?.length > 0) && (
                  <Alert severity="info" sx={{ mb: 1 }}>
                    {ruleWeights.low_confidence_rules.length} rule(s) flagged as noisy (confidence &lt; 0.4)
                  </Alert>
                )}
                <TableContainer sx={{ maxHeight: 200 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Rule ID</TableCell>
                        <TableCell align="right">Confidence</TableCell>
                        <TableCell align="right">TP</TableCell>
                        <TableCell align="right">FP</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(ruleWeights.rules ?? {}).slice(0, 10).map(([ruleId, data]) => (
                        <TableRow key={ruleId}>
                          <TableCell sx={{ fontFamily: 'monospace', fontSize: 12 }}>{ruleId}</TableCell>
                          <TableCell align="right">
                            <Chip
                              label={data.confidence?.toFixed(2)}
                              size="small"
                              color={data.confidence >= 0.7 ? 'success' : data.confidence >= 0.4 ? 'warning' : 'error'}
                            />
                          </TableCell>
                          <TableCell align="right">{data.true_positives}</TableCell>
                          <TableCell align="right">{data.false_positives}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            ) : (
              <Box sx={{ textAlign: 'center', py: 3 }}>
                <RuleIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                <Typography color="text.secondary">No rule feedback yet — submit scan feedback to start learning</Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Pattern Discovery */}
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 3, borderRadius: 3, border: '2px solid', borderColor: 'divider' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              <PatternIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Pattern Discovery
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <Chip label={`${patterns.total_patterns_tracked ?? 0} patterns tracked`} variant="outlined" size="small" />
              <Chip label={`${patterns.rules_generated ?? 0} rules generated`} color="success" variant="outlined" size="small" />
              <Chip label={`${patterns.pending_patterns ?? 0} pending`} color="warning" variant="outlined" size="small" />
            </Box>
            {(patterns.top_patterns ?? []).length > 0 ? (
              <TableContainer sx={{ maxHeight: 180 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Pattern</TableCell>
                      <TableCell align="right">Count</TableCell>
                      <TableCell align="right">Scans</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {patterns.top_patterns.map((p, i) => (
                      <TableRow key={i}>
                        <Tooltip title={p.sample_description || ''}>
                          <TableCell sx={{ fontSize: 12, maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {p.sample_description?.slice(0, 40) || p.signature}
                          </TableCell>
                        </Tooltip>
                        <TableCell align="right">{p.count}</TableCell>
                        <TableCell align="right">{p.scan_ids?.length ?? 0}</TableCell>
                        <TableCell>
                          {p.rule_generated
                            ? <Chip label="Rule Created" size="small" color="success" />
                            : <Chip label="Tracking" size="small" variant="outlined" />
                          }
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No patterns discovered yet — run more scans to build data.
              </Typography>
            )}
            <Box sx={{ mt: 2 }}>
              <Button
                variant="outlined"
                size="small"
                startIcon={<PatternIcon />}
                onClick={handleDiscover}
                disabled={discovering}
              >
                {discovering ? 'Discovering…' : 'Run Discovery Cycle'}
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Telemetry Feed */}
        <Grid item xs={12}>
          <Paper variant="outlined" sx={{ p: 3, borderRadius: 3, border: '2px solid', borderColor: 'divider' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              📡 Learning Telemetry (Live)
            </Typography>
            <Divider sx={{ mb: 2 }} />
            {(telemetry?.recent_events ?? []).length > 0 ? (
              <TableContainer sx={{ maxHeight: 300 }}>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>Time</TableCell>
                      <TableCell>Event</TableCell>
                      <TableCell>Details</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {telemetry.recent_events.slice().reverse().map((evt, i) => (
                      <TableRow key={i} sx={{ '&:last-child td': { borderBottom: 0 } }}>
                        <TableCell sx={{ fontSize: 11, whiteSpace: 'nowrap', color: 'text.secondary' }}>
                          {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : '—'}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={evt.type}
                            size="small"
                            color={
                              evt.type === 'retrain_completed' ? 'success' :
                              evt.type === 'drift_detected' ? 'error' :
                              evt.type === 'feedback_processed' ? 'info' : 'default'
                            }
                            variant="outlined"
                            sx={{ fontFamily: 'monospace', fontSize: 11 }}
                          />
                        </TableCell>
                        <TableCell sx={{ fontSize: 12, fontFamily: 'monospace', maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {JSON.stringify(Object.fromEntries(
                            Object.entries(evt).filter(([k]) => !['type', 'timestamp'].includes(k))
                          )).slice(0, 120)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Box sx={{ textAlign: 'center', py: 3 }}>
                <PsychologyIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                <Typography color="text.secondary">
                  No learning events yet — scan a file to see the system start learning.
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* How It Works */}
        <Grid item xs={12}>
          <Paper variant="outlined" sx={{ p: 3, borderRadius: 3, border: '2px solid', borderColor: 'divider', bgcolor: 'grey.50' }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              🔄 How Adaptive Learning Works
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={2}>
              {[
                { step: '1', title: 'Scan Ingestion', desc: 'Every scan result feeds the drift detector and pattern engine. New vulnerability signatures are tracked automatically.' },
                { step: '2', title: 'Feedback Learning', desc: 'User feedback (accurate / false positive / false negative) trains the model with correct labels and adjusts rule confidence weights.' },
                { step: '3', title: 'Drift Detection', desc: 'PSI-based monitoring compares recent predictions vs historical baseline. When the world changes, the system notices.' },
                { step: '4', title: 'Auto-Retrain', desc: `After ${status?.auto_retrain_threshold ?? 20} feedback events or significant drift, the model automatically retrains with new data.` },
                { step: '5', title: 'Pattern Discovery', desc: 'Recurring findings are clustered. When a pattern appears in 3+ scans with no matching rule, a YAML rule is auto-generated.' },
                { step: '6', title: 'Model Evaluation', desc: 'New models are compared against the champion using holdout data. Only improvements get promoted — no regressions.' },
              ].map(({ step, title, desc }) => (
                <Grid item xs={12} sm={6} md={4} key={step}>
                  <Box sx={{ display: 'flex', gap: 1.5 }}>
                    <Box sx={{ width: 32, height: 32, borderRadius: '50%', bgcolor: 'primary.main', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', flexShrink: 0 }}>
                      {step}
                    </Box>
                    <Box>
                      <Typography variant="subtitle2" fontWeight="bold">{title}</Typography>
                      <Typography variant="caption" color="text.secondary">{desc}</Typography>
                    </Box>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
