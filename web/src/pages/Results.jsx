import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
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
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { getScan } from '../api/client';

const severityColors = {
  critical: 'error',
  high: 'warning',
  medium: 'info',
  low: 'success',
};

export default function Results() {
  const { scanId } = useParams();
  const [scan, setScan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
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
    
    // Poll if scan is still processing
    const interval = setInterval(() => {
      if (scan?.status === 'processing' || scan?.status === 'pending') {
        fetchScan();
      } else {
        clearInterval(interval);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [scanId, scan?.status]);

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

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Scan Results
      </Typography>

      <Grid container spacing={3}>
        {/* Risk Score Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Unified Risk Score
              </Typography>
              <Box display="flex" alignItems="center" gap={2}>
                <Typography variant="h2">
                  {scan.unified_risk_score?.toFixed(2) || 'N/A'}
                </Typography>
                <Chip
                  label={getRiskLevel(scan.unified_risk_score)}
                  color={severityColors[getRiskLevel(scan.unified_risk_score).toLowerCase()]}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Component Scores */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Component Scores
              </Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                <Box display="flex" justifyContent="space-between">
                  <Typography>ML Score:</Typography>
                  <Typography fontWeight="bold">{scan.ml_score?.toFixed(2) || 'N/A'}</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography>Rules Score:</Typography>
                  <Typography fontWeight="bold">{scan.rules_score?.toFixed(2) || 'N/A'}</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography>LLM Score:</Typography>
                  <Typography fontWeight="bold">{scan.llm_score?.toFixed(2) || 'N/A'}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Findings */}
        <Grid item xs={12}>
          <Typography variant="h5" gutterBottom sx={{ mt: 2 }}>
            Findings ({scan.findings?.length || 0})
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
    </Box>
  );
}
