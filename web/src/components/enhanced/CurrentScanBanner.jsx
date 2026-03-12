import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Button,
  Divider,
  Grid,
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import CloseIcon from '@mui/icons-material/Close';
import { useLastScan } from '../../context/ScanContext';

const SEV_COLORS = {
  CRITICAL: '#d32f2f',
  HIGH: '#e65100',
  MEDIUM: '#f9a825',
  LOW: '#2e7d32',
};

export default function CurrentScanBanner() {
  const { lastScan, clearLastScan } = useLastScan();
  const navigate = useNavigate();

  if (!lastScan) return null;

  const { data, fileName, timestamp } = lastScan;
  const findings = data?.findings || [];
  const riskScore = Math.round((data?.unified_risk_score || 0) * 100);

  // Severity counts
  const sevCounts = {};
  findings.forEach((f) => {
    const s = f.severity || 'MEDIUM';
    sevCounts[s] = (sevCounts[s] || 0) + 1;
  });

  // Scanner counts
  const scannerCounts = {};
  findings.forEach((f) => {
    const s = f.scanner || f.source || 'unknown';
    scannerCounts[s] = (scannerCounts[s] || 0) + 1;
  });

  const timeDiff = () => {
    const ms = Date.now() - new Date(timestamp).getTime();
    if (ms < 60000) return 'just now';
    if (ms < 3600000) return `${Math.round(ms / 60000)}m ago`;
    return `${Math.round(ms / 3600000)}h ago`;
  };

  return (
    <Paper
      elevation={0}
      sx={{
        mb: 3,
        p: 2.5,
        borderRadius: 3,
        border: '2px solid',
        borderColor: 'primary.main',
        background: 'linear-gradient(135deg, rgba(66,165,245,0.08) 0%, rgba(13,71,161,0.04) 100%)',
        position: 'relative',
      }}
    >
      {/* Dismiss button */}
      <Button
        size="small"
        onClick={clearLastScan}
        sx={{ position: 'absolute', top: 8, right: 8, minWidth: 28, p: 0.5, color: 'text.secondary' }}
      >
        <CloseIcon fontSize="small" />
      </Button>

      {/* Header row */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
        <InsertDriveFileIcon sx={{ color: 'primary.main' }} />
        <Typography variant="subtitle1" fontWeight="bold" color="primary.main">
          Current Scan — {fileName}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {timeDiff()}
        </Typography>
      </Box>

      <Grid container spacing={2} alignItems="center">
        {/* Risk Score */}
        <Grid item xs={12} sm={2}>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h3" fontWeight="bold" color={riskScore >= 70 ? 'error.main' : riskScore >= 40 ? 'warning.main' : 'success.main'}>
              {riskScore}%
            </Typography>
            <Typography variant="caption" color="text.secondary">Risk Score</Typography>
          </Box>
        </Grid>

        <Divider orientation="vertical" flexItem sx={{ display: { xs: 'none', sm: 'block' } }} />

        {/* Severity Breakdown */}
        <Grid item xs={12} sm={4}>
          <Typography variant="caption" fontWeight="bold" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
            Findings ({findings.length})
          </Typography>
          <Box sx={{ display: 'flex', gap: 0.75, flexWrap: 'wrap' }}>
            {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) =>
              sevCounts[sev] ? (
                <Chip
                  key={sev}
                  label={`${sev[0]}${sev.slice(1).toLowerCase()}: ${sevCounts[sev]}`}
                  size="small"
                  sx={{
                    bgcolor: `${SEV_COLORS[sev]}18`,
                    color: SEV_COLORS[sev],
                    fontWeight: 'bold',
                    fontSize: 11,
                  }}
                />
              ) : null
            )}
            {findings.length === 0 && (
              <Chip label="No issues" size="small" color="success" variant="outlined" />
            )}
          </Box>
        </Grid>

        <Divider orientation="vertical" flexItem sx={{ display: { xs: 'none', sm: 'block' } }} />

        {/* Scanner Breakdown */}
        <Grid item xs={12} sm={3}>
          <Typography variant="caption" fontWeight="bold" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
            Scanners
          </Typography>
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            {Object.entries(scannerCounts).map(([scanner, count]) => (
              <Chip
                key={scanner}
                label={`${scanner}: ${count}`}
                size="small"
                variant="outlined"
                sx={{ fontSize: 10, textTransform: 'capitalize' }}
              />
            ))}
          </Box>
        </Grid>

        {/* View button */}
        <Grid item xs={12} sm={2} sx={{ textAlign: 'center' }}>
          <Button
            variant="contained"
            size="small"
            startIcon={<VisibilityIcon />}
            onClick={() => navigate('/results', { state: { scanResults: data, fileName } })}
            sx={{ borderRadius: 2, textTransform: 'none' }}
          >
            View Results
          </Button>
        </Grid>
      </Grid>
    </Paper>
  );
}
