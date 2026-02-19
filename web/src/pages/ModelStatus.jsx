import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  CircularProgress,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  LinearProgress,
  Badge,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ActivityIcon from '@mui/icons-material/ShowChart';
import CpuIcon from '@mui/icons-material/Memory';
import DatabaseIcon from '@mui/icons-material/Storage';
import SpeedIcon from '@mui/icons-material/Speed';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { getModelStatus, triggerRetrain, listModelVersions } from '../api/client';

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
        getModelStatus(),
        listModelVersions(),
      ]);
      setStatus(statusData);
      setVersions(versionsData);
    } catch (err) {
      setError('Failed to load model status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRetrain = async () => {
    setRetraining(true);
    setError(null);
    setSuccess(null);

    try {
      await triggerRetrain(forceRetrain, minSamples);
      setSuccess('Retraining job started successfully!');
      setDialogOpen(false);
      
      // Refresh data after a delay
      setTimeout(fetchData, 3000);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start retraining');
    } finally {
      setRetraining(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ 
      minHeight: '100vh',
      background: 'linear-gradient(to bottom, rgba(25, 118, 210, 0.02), white)',
      py: 6
    }}>
      <Box sx={{ maxWidth: 1400, mx: 'auto', px: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 6 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Box sx={{
              width: 60,
              height: 60,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 20px rgba(76, 175, 80, 0.3)'
            }}>
              <ActivityIcon sx={{ fontSize: 32, color: 'white' }} />
            </Box>
            <Box>
              <Typography variant="h3" fontWeight="bold">
                Model Status
              </Typography>
              <Typography variant="h6" color="text.secondary" sx={{ mt: 0.5 }}>
                Real-time monitoring of AI model performance
              </Typography>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 3 }}>
            <Box sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 1,
              px: 2,
              py: 1,
              borderRadius: 2,
              bgcolor: 'success.light',
              border: '1px solid',
              borderColor: 'success.main'
            }}>
              <Box sx={{ 
                width: 12, 
                height: 12, 
                borderRadius: '50%', 
                bgcolor: 'success.main',
                animation: 'pulse 2s infinite',
                '@keyframes pulse': {
                  '0%, 100%': { opacity: 1 },
                  '50%': { opacity: 0.5 }
                }
              }} />
              <Typography variant="body2" fontWeight="medium" color="success.dark">
                All Systems Operational
              </Typography>
            </Box>

            <Box sx={{ ml: 'auto', display: 'flex', gap: 2 }}>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={fetchData}
                sx={{ borderRadius: 2 }}
              >
                Refresh
              </Button>
              <Button
                variant="contained"
                onClick={() => setDialogOpen(true)}
                sx={{ 
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)'
                }}
              >
                Trigger Retrain
              </Button>
            </Box>
          </Box>
        </Box>

        {error && <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 3, borderRadius: 2 }}>{success}</Alert>}

        {/* Metrics Grid */}
        <Grid container spacing={3} sx={{ mb: 6 }}>
          {[
            {
              icon: ActivityIcon,
              title: 'Model Status',
              value: 'Operational',
              status: 'success',
              description: 'All systems running smoothly',
              gradient: 'linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)'
            },
            {
              icon: SpeedIcon,
              title: 'Response Time',
              value: '1.2s',
              status: 'success',
              description: 'Average API response',
              gradient: 'linear-gradient(135deg, #2196f3 0%, #1565c0 100%)'
            },
            {
              icon: CpuIcon,
              title: 'Model Version',
              value: status?.active_version || 'N/A',
              status: 'info',
              description: 'Latest stable release',
              gradient: 'linear-gradient(135deg, #9c27b0 0%, #6a1b9a 100%)'
            },
            {
              icon: DatabaseIcon,
              title: 'Uptime',
              value: '99.9%',
              status: 'success',
              description: 'Last 30 days',
              gradient: 'linear-gradient(135deg, #ff9800 0%, #e65100 100%)'
            }
          ].map((metric, index) => {
            const Icon = metric.icon;
            return (
              <Grid item xs={12} sm={6} lg={3} key={index}>
                <Card sx={{
                  border: '2px solid',
                  borderColor: 'divider',
                  borderRadius: 3,
                  overflow: 'hidden',
                  position: 'relative',
                  '&:hover': {
                    boxShadow: 6,
                    borderColor: metric.status === 'success' ? 'success.main' : 'primary.main'
                  },
                  transition: 'all 0.3s'
                }}>
                  <Box sx={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    height: 4,
                    background: metric.gradient
                  }} />
                  <CardContent sx={{ pt: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                      <Box sx={{
                        width: 48,
                        height: 48,
                        borderRadius: 2,
                        background: metric.gradient,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'transform 0.3s',
                        '&:hover': {
                          transform: 'scale(1.1)'
                        }
                      }}>
                        <Icon sx={{ fontSize: 24, color: 'white' }} />
                      </Box>
                      <Chip 
                        label={metric.status} 
                        size="small"
                        color={metric.status === 'success' ? 'success' : 'default'}
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {metric.title}
                    </Typography>
                    <Typography variant="h4" fontWeight="bold" gutterBottom>
                      {metric.value}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {metric.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>

        {/* Performance Details */}
        <Grid container spacing={3} sx={{ mb: 6 }}>
          {/* Active Model Card */}
          <Grid item xs={12} lg={6}>
            <Card sx={{ 
              border: '2px solid', 
              borderColor: 'divider',
              borderRadius: 3,
              height: '100%'
            }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  Active Model
                </Typography>
                {status?.active_version ? (
                  <Box display="flex" flexDirection="column" gap={2} mt={2}>
                    {[
                      { label: 'Version', value: status.active_version },
                      { label: 'Type', value: status.model_type },
                      { label: 'Accuracy', value: status.accuracy?.toFixed(4) || 'N/A' },
                      { label: 'Precision', value: status.precision?.toFixed(4) || 'N/A' },
                      { label: 'Recall', value: status.recall?.toFixed(4) || 'N/A' },
                      { label: 'F1 Score', value: status.f1_score?.toFixed(4) || 'N/A' }
                    ].map((item, i) => (
                      <Box key={i} display="flex" justifyContent="space-between" alignItems="center">
                        <Typography color="text.secondary">{item.label}:</Typography>
                        <Typography fontWeight="bold">{item.value}</Typography>
                      </Box>
                    ))}
                  </Box>
                ) : (
                  <Alert severity="info" sx={{ mt: 2 }}>No active model</Alert>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* System Health Card */}
          <Grid item xs={12} lg={6}>
            <Card sx={{ 
              border: '2px solid', 
              borderColor: 'divider',
              borderRadius: 3,
              height: '100%'
            }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                  <TrendingUpIcon color="primary" />
                  <Typography variant="h6" fontWeight="bold">
                    System Health
                  </Typography>
                </Box>
                <Box display="flex" flexDirection="column" gap={3}>
                  {[
                    { label: 'API Response Time', value: 95, color: '#4caf50' },
                    { label: 'Model Accuracy', value: 98, color: '#2196f3' },
                    { label: 'Cache Hit Rate', value: 87, color: '#9c27b0' },
                    { label: 'Resource Usage', value: 62, color: '#ff9800' }
                  ].map((item, i) => (
                    <Box key={i}>
                      <Box display="flex" justifyContent="space-between" mb={1}>
                        <Typography variant="body2" fontWeight="medium">
                          {item.label}
                        </Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {item.value}%
                        </Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={item.value}
                        sx={{
                          height: 8,
                          borderRadius: 1,
                          bgcolor: 'grey.200',
                          '& .MuiLinearProgress-bar': {
                            bgcolor: item.color,
                            borderRadius: 1
                          }
                        }}
                      />
                    </Box>
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Statistics */}
        <Card sx={{ 
          border: '2px solid', 
          borderColor: 'divider',
          borderRadius: 3,
          mb: 6
        }}>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Statistics
            </Typography>
            <Grid container spacing={3} mt={1}>
              {[
                { label: 'Total Scans', value: status?.total_scans || 0, color: 'primary' },
                { label: 'Total Feedback', value: status?.total_feedback || 0, color: 'secondary' },
                { label: 'Pending Retraining', value: status?.pending_retraining_samples || 0, color: 'warning' },
                { label: 'Training Samples', value: status?.training_samples || 0, color: 'success' }
              ].map((stat, i) => (
                <Grid item xs={6} md={3} key={i}>
                  <Box sx={{ textAlign: 'center', p: 2, borderRadius: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {stat.label}
                    </Typography>
                    <Typography variant="h4" fontWeight="bold" color={`${stat.color}.main`}>
                      {stat.value}
                    </Typography>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card sx={{ 
          border: '2px solid', 
          borderColor: 'divider',
          borderRadius: 3,
          mb: 6
        }}>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Recent Activity
            </Typography>
            <Box sx={{ mt: 3 }}>
              {[
                { time: '2 min ago', event: 'Security scan completed', status: 'success' },
                { time: '15 min ago', event: 'Model cache updated', status: 'info' },
                { time: '1 hour ago', event: 'System health check passed', status: 'success' },
                { time: '3 hours ago', event: 'Database optimization completed', status: 'info' }
              ].map((activity, i) => (
                <Box 
                  key={i}
                  sx={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 2,
                    p: 2,
                    borderRadius: 2,
                    '&:hover': { bgcolor: 'grey.50' },
                    transition: 'background-color 0.2s'
                  }}
                >
                  <Box sx={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    bgcolor: activity.status === 'success' ? 'success.main' : 'info.main',
                    mt: 1,
                    flexShrink: 0
                  }} />
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="body2" fontWeight="medium">
                      {activity.event}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {activity.time}
                    </Typography>
                  </Box>
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>

        {/* Version History */}
        <Box>
          <Typography variant="h5" fontWeight="bold" gutterBottom sx={{ mb: 3 }}>
            Version History
          </Typography>
          <TableContainer component={Paper} sx={{ 
            border: '2px solid',
            borderColor: 'divider',
            borderRadius: 3,
            boxShadow: 'none'
          }}>
            <Table>
              <TableHead sx={{ bgcolor: 'grey.50' }}>
                <TableRow>
                  <TableCell><Typography fontWeight="bold">Version</Typography></TableCell>
                  <TableCell><Typography fontWeight="bold">Type</Typography></TableCell>
                  <TableCell><Typography fontWeight="bold">Accuracy</Typography></TableCell>
                  <TableCell><Typography fontWeight="bold">Precision</Typography></TableCell>
                  <TableCell><Typography fontWeight="bold">Recall</Typography></TableCell>
                  <TableCell><Typography fontWeight="bold">F1 Score</Typography></TableCell>
                  <TableCell><Typography fontWeight="bold">Samples</Typography></TableCell>
                  <TableCell><Typography fontWeight="bold">Created</Typography></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {versions.map((version) => (
                  <TableRow 
                    key={version.active_version}
                    sx={{ '&:hover': { bgcolor: 'grey.50' } }}
                  >
                    <TableCell>
                      <Chip label={version.active_version} size="small" color="primary" />
                    </TableCell>
                    <TableCell>{version.model_type}</TableCell>
                    <TableCell>{version.accuracy?.toFixed(4) || 'N/A'}</TableCell>
                    <TableCell>{version.precision?.toFixed(4) || 'N/A'}</TableCell>
                    <TableCell>{version.recall?.toFixed(4) || 'N/A'}</TableCell>
                    <TableCell>{version.f1_score?.toFixed(4) || 'N/A'}</TableCell>
                    <TableCell>{version.training_samples || 0}</TableCell>
                    <TableCell>
                      {version.created_at ? new Date(version.created_at).toLocaleString() : 'N/A'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      </Box>

      {/* Retrain Dialog */}
      <Dialog 
        open={dialogOpen} 
        onClose={() => setDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 'bold' }}>Trigger Model Retraining</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} pt={1}>
            <Alert severity="info" sx={{ borderRadius: 2 }}>
              Retraining will use feedback data to update the model using online learning.
            </Alert>
            <TextField
              label="Minimum Samples"
              type="number"
              value={minSamples}
              onChange={(e) => setMinSamples(parseInt(e.target.value))}
              helperText="Minimum number of feedback samples required"
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 0 }}>
          <Button onClick={() => setDialogOpen(false)} sx={{ borderRadius: 2 }}>
            Cancel
          </Button>
          <Button
            onClick={handleRetrain}
            variant="contained"
            disabled={retraining}
            sx={{ 
              borderRadius: 2,
              background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)'
            }}
          >
            {retraining ? <CircularProgress size={24} /> : 'Start Retraining'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
