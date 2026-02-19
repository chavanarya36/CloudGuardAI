import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  CircularProgress,
  Alert,
  Chip,
  Paper,
  Divider,
  Button,
  LinearProgress,
} from '@mui/material';
import SecurityIcon from '@mui/icons-material/Security';
import BugReportIcon from '@mui/icons-material/BugReport';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import ScannerIcon from '@mui/icons-material/Scanner';
import HistoryIcon from '@mui/icons-material/History';
import ShieldIcon from '@mui/icons-material/Shield';
import { getScanStats } from '../api/client';

// Severity color mapping
const SEVERITY_CONFIG = {
  CRITICAL: { color: '#d32f2f', bg: '#ffebee', icon: '🔴' },
  HIGH: { color: '#e65100', bg: '#fff3e0', icon: '🟠' },
  MEDIUM: { color: '#f9a825', bg: '#fffde7', icon: '🟡' },
  LOW: { color: '#2e7d32', bg: '#e8f5e9', icon: '🟢' },
  INFO: { color: '#1565c0', bg: '#e3f2fd', icon: '🔵' },
};

function StatCard({ title, value, subtitle, icon, color = 'primary.main', trend }) {
  return (
    <Card
      variant="outlined"
      sx={{
        height: '100%',
        border: '2px solid',
        borderColor: 'divider',
        borderRadius: 3,
        transition: 'all 0.3s',
        '&:hover': { borderColor: color, boxShadow: 4 },
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h3" fontWeight="bold" color={color}>
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="caption" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              p: 1.5,
              borderRadius: 2,
              bgcolor: `${color}15`,
              display: 'flex',
              alignItems: 'center',
            }}
          >
            {icon}
          </Box>
        </Box>
        {trend !== undefined && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 1 }}>
            <TrendingUpIcon sx={{ fontSize: 16, color: trend >= 0 ? 'success.main' : 'error.main' }} />
            <Typography variant="caption" color={trend >= 0 ? 'success.main' : 'error.main'}>
              {trend >= 0 ? '+' : ''}{trend} this month
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

function SeverityBar({ label, count, total, config }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <Box sx={{ mb: 1.5 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
        <Typography variant="body2" fontWeight="medium">
          {config.icon} {label}
        </Typography>
        <Typography variant="body2" fontWeight="bold">
          {count}
        </Typography>
      </Box>
      <LinearProgress
        variant="determinate"
        value={pct}
        sx={{
          height: 8,
          borderRadius: 1,
          bgcolor: config.bg,
          '& .MuiLinearProgress-bar': {
            bgcolor: config.color,
            borderRadius: 1,
          },
        }}
      />
    </Box>
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
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress size={48} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="warning" sx={{ borderRadius: 2 }}>
        {error} — <Button size="small" onClick={() => window.location.reload()}>Retry</Button>
      </Alert>
    );
  }

  const totalFindings = stats
    ? Object.values(stats.findings_by_severity).reduce((a, b) => a + b, 0)
    : 0;

  const avgRisk = stats?.average_scores?.unified_risk ?? 0;
  const riskLabel = avgRisk >= 0.7 ? 'Critical' : avgRisk >= 0.4 ? 'Medium' : 'Low';
  const riskColor = avgRisk >= 0.7 ? 'error.main' : avgRisk >= 0.4 ? 'warning.main' : 'success.main';

  const trendScans = stats?.trend_30_days?.reduce((sum, d) => sum + d.count, 0) ?? 0;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Security Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Real-time overview of your infrastructure security posture
        </Typography>
      </Box>

      {/* Top Stats Row */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Scans"
            value={stats?.total_scans ?? 0}
            subtitle="All-time"
            icon={<ScannerIcon sx={{ color: 'primary.main' }} />}
            color="primary.main"
            trend={trendScans}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Findings"
            value={totalFindings}
            subtitle="Across all scans"
            icon={<BugReportIcon sx={{ color: 'error.main' }} />}
            color="error.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Avg Risk Score"
            value={`${(avgRisk * 100).toFixed(0)}%`}
            subtitle={riskLabel}
            icon={<SecurityIcon sx={{ color: riskColor }} />}
            color={riskColor}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Scanners"
            value={Object.values(stats?.findings_by_scanner ?? {}).filter(v => v > 0).length}
            subtitle="Out of 6"
            icon={<ShieldIcon sx={{ color: 'success.main' }} />}
            color="success.main"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Severity Breakdown */}
        <Grid item xs={12} md={6}>
          <Paper
            variant="outlined"
            sx={{ p: 3, borderRadius: 3, height: '100%', border: '2px solid', borderColor: 'divider' }}
          >
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Findings by Severity
            </Typography>
            <Divider sx={{ mb: 2 }} />
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
              <Box sx={{ textAlign: 'center', py: 3 }}>
                <CheckCircleIcon sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
                <Typography color="text.secondary">No findings — run a scan to get started</Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Scanner Breakdown */}
        <Grid item xs={12} md={6}>
          <Paper
            variant="outlined"
            sx={{ p: 3, borderRadius: 3, height: '100%', border: '2px solid', borderColor: 'divider' }}
          >
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Findings by Scanner
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={1.5}>
              {Object.entries(stats?.findings_by_scanner ?? {}).map(([scanner, count]) => (
                <Grid item xs={6} key={scanner}>
                  <Card
                    variant="outlined"
                    sx={{
                      p: 2,
                      textAlign: 'center',
                      borderRadius: 2,
                      bgcolor: count > 0 ? 'warning.lighter' : 'grey.50',
                      borderColor: count > 0 ? 'warning.light' : 'divider',
                    }}
                  >
                    <Typography variant="h5" fontWeight="bold">
                      {count}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {scanner}
                    </Typography>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>

        {/* Score Breakdown */}
        <Grid item xs={12}>
          <Paper
            variant="outlined"
            sx={{ p: 3, borderRadius: 3, border: '2px solid', borderColor: 'divider' }}
          >
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Average Scanner Scores
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={2}>
              {[
                { label: 'ML Model', key: 'ml_score', color: '#1976d2' },
                { label: 'Rules Engine', key: 'rules_score', color: '#7b1fa2' },
                { label: 'LLM Reasoning', key: 'llm_score', color: '#00838f' },
                { label: 'Secrets', key: 'secrets_score', color: '#c62828' },
                { label: 'CVE', key: 'cve_score', color: '#e65100' },
                { label: 'Compliance', key: 'compliance_score', color: '#2e7d32' },
              ].map(({ label, key, color }) => {
                const score = stats?.average_scores?.[key] ?? 0;
                return (
                  <Grid item xs={6} sm={4} md={2} key={key}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                        <CircularProgress
                          variant="determinate"
                          value={score * 100}
                          size={72}
                          thickness={5}
                          sx={{ color }}
                        />
                        <Box
                          sx={{
                            top: 0, left: 0, bottom: 0, right: 0,
                            position: 'absolute',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                          }}
                        >
                          <Typography variant="body2" fontWeight="bold">
                            {(score * 100).toFixed(0)}%
                          </Typography>
                        </Box>
                      </Box>
                      <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                        {label}
                      </Typography>
                    </Box>
                  </Grid>
                );
              })}
            </Grid>
          </Paper>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Paper
            variant="outlined"
            sx={{ p: 3, borderRadius: 3, border: '2px solid', borderColor: 'divider' }}
          >
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Quick Actions
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                startIcon={<ScannerIcon />}
                onClick={() => navigate('/')}
                sx={{ borderRadius: 2 }}
              >
                New Scan
              </Button>
              <Button
                variant="outlined"
                startIcon={<HistoryIcon />}
                onClick={() => navigate('/history')}
                sx={{ borderRadius: 2 }}
              >
                Scan History
              </Button>
              <Button
                variant="outlined"
                startIcon={<ShieldIcon />}
                onClick={() => navigate('/model-status')}
                sx={{ borderRadius: 2 }}
              >
                Model Status
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* 30-Day Trend */}
        {stats?.trend_30_days?.length > 0 && (
          <Grid item xs={12}>
            <Paper
              variant="outlined"
              sx={{ p: 3, borderRadius: 3, border: '2px solid', borderColor: 'divider' }}
            >
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Scan Activity (Last 30 Days)
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'flex-end', height: 80 }}>
                {stats.trend_30_days.map((day, i) => {
                  const max = Math.max(...stats.trend_30_days.map(d => d.count), 1);
                  const height = (day.count / max) * 100;
                  return (
                    <Box
                      key={i}
                      title={`${day.date}: ${day.count} scans`}
                      sx={{
                        flex: 1,
                        height: `${Math.max(height, 4)}%`,
                        bgcolor: 'primary.main',
                        borderRadius: '2px 2px 0 0',
                        minWidth: 4,
                        transition: 'all 0.2s',
                        '&:hover': { bgcolor: 'primary.dark', transform: 'scaleY(1.1)' },
                      }}
                    />
                  );
                })}
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                <Typography variant="caption" color="text.secondary">
                  {stats.trend_30_days[0]?.date}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {stats.trend_30_days[stats.trend_30_days.length - 1]?.date}
                </Typography>
              </Box>
            </Paper>
          </Grid>
        )}
      </Grid>
    </Box>
  );
}
