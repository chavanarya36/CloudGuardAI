import { useState, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Rating,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import {
  BarChart,
  Bar,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { getScan, submitFeedback } from '../api/client';
import RiskScoreCard from '../components/enhanced/RiskScoreCard';
import FindingsCard from '../components/enhanced/FindingsCard';

const severityColors = {
  CRITICAL: 'error',
  HIGH: 'warning',
  MEDIUM: 'info',
  LOW: 'success',
};

export default function Results() {
  const { scanId } = useParams();
  const location = useLocation();
  const [scan, setScan] = useState(location.state?.scanResults || null);
  const [loading, setLoading] = useState(!location.state?.scanResults);
  const [error, setError] = useState(null);
  
  // Feedback dialog state
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [feedbackRating, setFeedbackRating] = useState(3);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [feedbackType, setFeedbackType] = useState('accurate');
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false);

  useEffect(() => {
    // If we don't have scan results from navigation state, try to fetch
    if (!scan) {
      const fetchScan = async () => {
        try {
          const data = await getScan(scanId);
          setScan(data);
        } catch (err) {
          setError(err.response?.data?.detail || 'Failed to load scan results');
        } finally {
          setLoading(false);
        }
      };
      fetchScan();
    }
  }, [scanId, scan]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!scan) {
    return <Alert severity="info">Scan not found</Alert>;
  }

  const getRiskLevel = (score) => {
    if (score >= 0.8) return 'Critical';
    if (score >= 0.6) return 'High';
    if (score >= 0.4) return 'Medium';
    return 'Low';
  };
  
  const handleFeedbackSubmit = async () => {
    setFeedbackSubmitting(true);
    try {
      // Submit feedback using centralized API client
      await submitFeedback({
        scan_id: parseInt(scanId) || 0,
        rating: feedbackRating,
        user_comment: feedbackComment,
        feedback_type: feedbackType,
        accepted_prediction: feedbackType === 'accurate',
      });
      
      setFeedbackOpen(false);
      setFeedbackRating(3);
      setFeedbackComment('');
      setFeedbackType('accurate');
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    } finally {
      setFeedbackSubmitting(false);
    }
  };
  
  // Prepare chart data
  const componentScoresData = [
    { name: 'ML', score: (scan?.ml_score || 0) * 100 },
    { name: 'Rules', score: (scan?.rules_score || 0) * 100 },
    { name: 'LLM', score: (scan?.llm_score || 0) * 100 },
    { name: 'Unified', score: (scan?.unified_risk_score || 0) * 100 },
  ];
  
  const radarData = [
    { metric: 'Supervised ML', value: (scan?.supervised_probability || 0) * 100 },
    { metric: 'Unsupervised ML', value: (scan?.unsupervised_probability || 0) * 100 },
    { metric: 'Rules Engine', value: (scan?.rules_score || 0) * 100 },
    { metric: 'LLM Reasoning', value: (scan?.llm_score || 0) * 100 },
  ];

  // Prepare component scores for RiskScoreCard
  const componentScores = {
    ml_score: ((scan?.ml_score || 0) * 100).toFixed(0),
    rules_score: ((scan?.rules_score || 0) * 100).toFixed(0),
    llm_score: ((scan?.llm_score || 0) * 100).toFixed(0),
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Scan Results
        </Typography>
        <Box display="flex" gap={1}>
          <Button
            variant="outlined"
            startIcon={<ThumbUpIcon />}
            onClick={() => { setFeedbackType('accurate'); setFeedbackOpen(true); }}
          >
            Accurate
          </Button>
          <Button
            variant="outlined"
            startIcon={<ThumbDownIcon />}
            onClick={() => { setFeedbackType('false_positive'); setFeedbackOpen(true); }}
          >
            Report Issue
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Enhanced Risk Score Card */}
        <Grid item xs={12} md={6}>
          <RiskScoreCard 
            score={Math.round((scan.unified_risk_score || 0) * 100)} 
            componentScores={componentScores}
          />
        </Grid>

        {/* Component Scores Chart */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Component Scores
              </Typography>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={componentScoresData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
                  <Bar dataKey="score" fill="#1976d2" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Risk Analysis Radar */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Multi-Dimensional Risk Analysis
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="metric" />
                  <PolarRadiusAxis domain={[0, 100]} />
                  <Radar
                    name="Risk Score"
                    dataKey="value"
                    stroke="#8884d8"
                    fill="#8884d8"
                    fillOpacity={0.6}
                  />
                  <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
                </RadarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Enhanced Findings */}
        <Grid item xs={12}>
          <FindingsCard 
            findings={scan.findings || []} 
            scannerBreakdown={scan.scanner_breakdown}
            complianceScore={scan.compliance_score}
          />
        </Grid>

        {/* GNN Attack Path Visualization */}
        {scan.gnn_graph_data && (scan.gnn_graph_data.attack_paths?.length > 0 || scan.gnn_graph_data.graph?.nodes?.length > 0) && (
          <Grid item xs={12}>
            <Card sx={{ borderRadius: 3, border: '2px solid', borderColor: 'warning.main' }}>
              <CardContent>
                <Typography variant="h5" fontWeight="bold" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  🔗 GNN Attack Path Detection
                  {scan.gnn_graph_data.summary && (
                    <Chip
                      label={`${scan.gnn_graph_data.summary.total_paths || 0} path(s) detected`}
                      color={scan.gnn_graph_data.summary.critical_paths > 0 ? 'error' : scan.gnn_graph_data.summary.total_paths > 0 ? 'warning' : 'success'}
                      size="small"
                      sx={{ ml: 1 }}
                    />
                  )}
                </Typography>

                {/* Summary stats */}
                {scan.gnn_graph_data.summary && (
                  <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
                    <Chip label={`${scan.gnn_graph_data.summary.total_resources || 0} resources`} variant="outlined" size="small" />
                    <Chip label={`${scan.gnn_graph_data.summary.total_edges || 0} connections`} variant="outlined" size="small" />
                    <Chip label={`${scan.gnn_graph_data.summary.total_vulnerabilities || 0} vulnerabilities`} color="error" variant="outlined" size="small" />
                    {scan.gnn_graph_data.summary.critical_paths > 0 && (
                      <Chip label={`${scan.gnn_graph_data.summary.critical_paths} CRITICAL paths`} color="error" size="small" />
                    )}
                  </Box>
                )}

                {/* Infrastructure Graph Visualization */}
                {scan.gnn_graph_data.graph?.nodes?.length > 0 && (
                  <Paper variant="outlined" sx={{ p: 2, mb: 3, borderRadius: 2, bgcolor: '#f8f9fa' }}>
                    <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                      Infrastructure Dependency Graph
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, justifyContent: 'center', py: 2 }}>
                      {scan.gnn_graph_data.graph.nodes.map((node, idx) => (
                        <Paper
                          key={idx}
                          elevation={node.is_entry_point || node.is_target ? 4 : 1}
                          sx={{
                            p: 1.5, borderRadius: 2, minWidth: 140, textAlign: 'center',
                            border: '2px solid',
                            borderColor: node.is_entry_point ? 'error.main' : node.is_target ? 'warning.main' : node.vulnerabilities > 0 ? 'warning.light' : 'grey.300',
                            bgcolor: node.is_entry_point ? 'error.50' : node.is_target ? 'warning.50' : 'white',
                          }}
                        >
                          <Typography variant="body2" fontWeight="bold" sx={{ fontFamily: 'monospace', fontSize: 11 }}>
                            {node.label}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                            {node.type?.replace('aws_', '')}
                          </Typography>
                          {node.vulnerabilities > 0 && (
                            <Chip
                              label={`${node.vulnerabilities} vuln${node.vulnerabilities > 1 ? 's' : ''}`}
                              size="small"
                              color={node.max_severity === 'CRITICAL' ? 'error' : node.max_severity === 'HIGH' ? 'warning' : 'info'}
                              sx={{ mt: 0.5, fontSize: 10 }}
                            />
                          )}
                          {node.is_entry_point && <Chip label="ENTRY" size="small" color="error" sx={{ mt: 0.5, ml: 0.5, fontSize: 10 }} />}
                          {node.is_target && <Chip label="TARGET" size="small" color="warning" sx={{ mt: 0.5, ml: 0.5, fontSize: 10 }} />}
                        </Paper>
                      ))}
                    </Box>
                    {/* Connection legend */}
                    <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 1 }}>
                      <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Box sx={{ width: 12, height: 12, bgcolor: 'error.main', borderRadius: '50%' }} /> Entry Point
                      </Typography>
                      <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Box sx={{ width: 12, height: 12, bgcolor: 'warning.main', borderRadius: '50%' }} /> Target
                      </Typography>
                      <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Box sx={{ width: 12, height: 12, border: '2px solid', borderColor: 'grey.400', borderRadius: '50%' }} /> Resource
                      </Typography>
                    </Box>
                  </Paper>
                )}

                {/* Attack Paths */}
                {scan.gnn_graph_data.attack_paths?.map((path, pathIdx) => (
                  <Accordion key={pathIdx} sx={{ mb: 1.5, borderRadius: 2, overflow: 'hidden', border: '1px solid', borderColor: path.severity === 'CRITICAL' ? 'error.main' : path.severity === 'HIGH' ? 'warning.main' : 'divider' }}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Box display="flex" alignItems="center" gap={1.5} width="100%">
                        <Chip
                          label={path.severity}
                          size="small"
                          color={path.severity === 'CRITICAL' ? 'error' : path.severity === 'HIGH' ? 'warning' : 'info'}
                          sx={{ fontWeight: 'bold' }}
                        />
                        <Typography variant="body2" fontWeight="bold" sx={{ flex: 1 }}>
                          {path.path_string}
                        </Typography>
                        <Chip label={`${path.hops} hops`} size="small" variant="outlined" />
                        <Typography variant="caption" color="text.secondary">{path.path_id}</Typography>
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails sx={{ bgcolor: 'grey.50' }}>
                      {/* Visual chain */}
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', mb: 2, p: 2, bgcolor: 'white', borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
                        {path.chain?.map((node, ni) => (
                          <Box key={ni} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {ni > 0 && (
                              <Typography variant="h5" color="error.main" sx={{ mx: 0.5 }}>→</Typography>
                            )}
                            <Paper
                              elevation={1}
                              sx={{
                                p: 1, borderRadius: 1.5, textAlign: 'center', minWidth: 100,
                                border: '2px solid',
                                borderColor: node.is_entry ? 'error.main' : node.is_target ? 'warning.main' : 'primary.light',
                                bgcolor: node.is_entry ? 'error.50' : node.is_target ? 'warning.50' : 'white',
                              }}
                            >
                              <Typography variant="body2" fontWeight="bold" sx={{ fontFamily: 'monospace', fontSize: 11 }}>
                                {node.resource_name || node.resource}
                              </Typography>
                              <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                {node.resource_type?.replace('aws_', '')}
                              </Typography>
                              {node.vulnerabilities?.map((v, vi) => (
                                <Chip key={vi} label={v.vuln} size="small" color="error" variant="outlined" sx={{ mt: 0.5, fontSize: 9 }} />
                              ))}
                              {ni > 0 && (
                                <Typography variant="caption" color="primary.main" sx={{ display: 'block', mt: 0.5, fontStyle: 'italic' }}>
                                  via {node.relationship}
                                </Typography>
                              )}
                            </Paper>
                          </Box>
                        ))}
                      </Box>

                      {/* Narrative */}
                      <Paper sx={{ p: 2, mb: 2, bgcolor: 'white', borderRadius: 1.5 }}>
                        <Typography variant="subtitle2" gutterBottom fontWeight="bold">Attack Narrative</Typography>
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-line', fontFamily: 'monospace', fontSize: 12 }}>
                          {path.narrative}
                        </Typography>
                      </Paper>

                      {/* Remediation */}
                      {path.remediation?.length > 0 && (
                        <Paper sx={{ p: 2, bgcolor: 'success.50', borderRadius: 1.5, border: '1px solid', borderColor: 'success.light' }}>
                          <Typography variant="subtitle2" gutterBottom fontWeight="bold" color="success.dark">
                            Remediation to Break This Path
                          </Typography>
                          {path.remediation.map((step, si) => (
                            <Typography key={si} variant="body2" sx={{ fontSize: 12, mb: 0.5 }}>
                              {si + 1}. {step}
                            </Typography>
                          ))}
                        </Paper>
                      )}
                    </AccordionDetails>
                  </Accordion>
                ))}
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Keep traditional Material-UI findings for additional details */}
        <Grid item xs={12}>
          <Typography variant="h5" gutterBottom sx={{ mt: 2 }}>
            Detailed Analysis ({scan.findings?.length || 0})
          </Typography>
          
          {scan.findings && scan.findings.length > 0 ? (
            scan.findings.map((finding, index) => (
              <Accordion key={index} sx={{ mb: 1 }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box display="flex" alignItems="center" gap={2} width="100%">
                    <Chip
                      label={finding.severity}
                      color={severityColors[finding.severity]}
                      size="small"
                    />
                    <Typography fontWeight="bold">{finding.title}</Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
                      {finding.rule_id}
                    </Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Box>
                    <Typography paragraph>{finding.description}</Typography>
                    
                    {finding.llm_explanation && (
                      <Paper sx={{ p: 2, mb: 2, bgcolor: 'info.light' }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Explanation:
                        </Typography>
                        <Typography variant="body2">{finding.llm_explanation}</Typography>
                      </Paper>
                    )}
                    
                    {finding.llm_remediation && (
                      <Paper sx={{ p: 2, bgcolor: 'success.light' }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Remediation:
                        </Typography>
                        <Typography variant="body2">{finding.llm_remediation}</Typography>
                      </Paper>
                    )}
                    
                    {finding.code_snippet && (
                      <Paper sx={{ p: 2, mt: 2, bgcolor: 'grey.100' }}>
                        <Typography variant="caption" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                          {finding.code_snippet}
                        </Typography>
                      </Paper>
                    )}
                  </Box>
                </AccordionDetails>
              </Accordion>
            ))
          ) : (
            <Alert severity="success">No security issues found!</Alert>
          )}
        </Grid>
      </Grid>
      
      {/* Feedback Dialog */}
      <Dialog open={feedbackOpen} onClose={() => setFeedbackOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Provide Feedback</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={3} mt={1}>
            <Box>
              <Typography component="legend">Overall Rating</Typography>
              <Rating
                value={feedbackRating}
                onChange={(e, newValue) => setFeedbackRating(newValue)}
                size="large"
              />
            </Box>
            
            <FormControl>
              <FormLabel>Feedback Type</FormLabel>
              <RadioGroup value={feedbackType} onChange={(e) => setFeedbackType(e.target.value)}>
                <FormControlLabel value="accurate" control={<Radio />} label="Prediction was accurate" />
                <FormControlLabel value="false_positive" control={<Radio />} label="False positive (flagged incorrectly)" />
                <FormControlLabel value="false_negative" control={<Radio />} label="False negative (missed an issue)" />
              </RadioGroup>
            </FormControl>
            
            <TextField
              label="Comments (optional)"
              multiline
              rows={4}
              value={feedbackComment}
              onChange={(e) => setFeedbackComment(e.target.value)}
              placeholder="Tell us more about your experience..."
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFeedbackOpen(false)}>Cancel</Button>
          <Button
            onClick={handleFeedbackSubmit}
            variant="contained"
            disabled={feedbackSubmitting}
          >
            {feedbackSubmitting ? 'Submitting...' : 'Submit'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
