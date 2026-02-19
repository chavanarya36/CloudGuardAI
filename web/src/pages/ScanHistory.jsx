import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  MenuItem,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Alert
} from '@mui/material';
import {
  Visibility,
  Delete,
  FileDownload,
  FilterList,
  Refresh
} from '@mui/icons-material';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

import apiClient, { listScans, getScan } from '../api/client';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const severityColors = {
  CRITICAL: '#dc2626',
  HIGH: '#ea580c',
  MEDIUM: '#f59e0b',
  LOW: '#84cc16',
  INFO: '#3b82f6'
};

const scannerColors = {
  ML: '#8b5cf6',
  Rules: '#f97316',
  LLM: '#06b6d4',
  Secrets: '#a855f7',
  CVE: '#ef4444',
  Compliance: '#3b82f6'
};

function ScanHistory() {
  const [scans, setScans] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedScan, setSelectedScan] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [scanToDelete, setScanToDelete] = useState(null);
  
  // Filters
  const [severity, setSeverity] = useState('');
  const [scanner, setScanner] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  useEffect(() => {
    fetchScans();
    fetchStats();
  }, [severity, scanner, startDate, endDate]);

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
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await apiClient.get('/scans/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleViewScan = async (scanId) => {
    try {
      const data = await getScan(scanId);
      setSelectedScan(data);
      setDialogOpen(true);
    } catch (error) {
      console.error('Failed to fetch scan details:', error);
    }
  };

  const handleDeleteScan = async () => {
    if (!scanToDelete) return;
    
    try {
      await apiClient.delete(`/scans/${scanToDelete}`);
      setDeleteDialogOpen(false);
      setScanToDelete(null);
      fetchScans();
      fetchStats();
    } catch (error) {
      console.error('Failed to delete scan:', error);
    }
  };

  const confirmDelete = (scanId) => {
    setScanToDelete(scanId);
    setDeleteDialogOpen(true);
  };

  const exportScans = () => {
    const dataStr = JSON.stringify(scans, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `scan-history-${new Date().toISOString()}.json`;
    link.click();
  };

  const getRiskColor = (score) => {
    if (score >= 80) return '#dc2626';
    if (score >= 60) return '#ea580c';
    if (score >= 40) return '#f59e0b';
    if (score >= 20) return '#84cc16';
    return '#22c55e';
  };

  // Trend chart data
  const getTrendChartData = () => {
    if (!stats || !stats.trend_30_days) return null;

    return {
      labels: stats.trend_30_days.map(d => d.date),
      datasets: [
        {
          label: 'Scans',
          data: stats.trend_30_days.map(d => d.count),
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.4
        }
      ]
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        borderRadius: 8
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        }
      },
      x: {
        grid: {
          display: false
        }
      }
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Scan History
        </Typography>
        <Typography variant="body1" color="text.secondary">
          View and analyze past security scans
        </Typography>
      </Box>

      {/* Statistics Cards */}
      {stats && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {/* Total Scans */}
          <Grid item xs={12} md={3}>
            <Card sx={{ 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white'
            }}>
              <CardContent>
                <Typography variant="h3" sx={{ fontWeight: 700 }}>
                  {stats.total_scans}
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Total Scans
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Average Risk */}
          <Grid item xs={12} md={3}>
            <Card sx={{
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
              color: 'white'
            }}>
              <CardContent>
                <Typography variant="h3" sx={{ fontWeight: 700 }}>
                  {stats.average_scores.unified_risk.toFixed(1)}
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Avg Risk Score
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Critical Findings */}
          <Grid item xs={12} md={3}>
            <Card sx={{
              background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
              color: 'white'
            }}>
              <CardContent>
                <Typography variant="h3" sx={{ fontWeight: 700 }}>
                  {stats.findings_by_severity.CRITICAL}
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Critical Findings
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* High Findings */}
          <Grid item xs={12} md={3}>
            <Card sx={{
              background: 'linear-gradient(135deg, #30cfd0 0%, #330867 100%)',
              color: 'white'
            }}>
              <CardContent>
                <Typography variant="h3" sx={{ fontWeight: 700 }}>
                  {stats.findings_by_severity.HIGH}
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  High Findings
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Trend Chart */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                  Scan Trend (Last 30 Days)
                </Typography>
                <Box sx={{ height: 250 }}>
                  {getTrendChartData() && (
                    <Line data={getTrendChartData()} options={chartOptions} />
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Scanner Distribution */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                  Findings by Scanner
                </Typography>
                {Object.entries(stats.findings_by_scanner).map(([scanner, count]) => (
                  <Box key={scanner} sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {scanner}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {count}
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={(count / Object.values(stats.findings_by_scanner).reduce((a, b) => a + b, 0)) * 100}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        backgroundColor: 'rgba(0, 0, 0, 0.05)',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: scannerColors[scanner]
                        }
                      }}
                    />
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>

          {/* Severity Distribution */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                  Findings by Severity
                </Typography>
                {Object.entries(stats.findings_by_severity).map(([sev, count]) => (
                  <Box key={sev} sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {sev}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {count}
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={(count / Object.values(stats.findings_by_severity).reduce((a, b) => a + b, 0)) * 100}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        backgroundColor: 'rgba(0, 0, 0, 0.05)',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: severityColors[sev]
                        }
                      }}
                    />
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={2.5}>
              <TextField
                select
                fullWidth
                size="small"
                label="Severity"
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="CRITICAL">Critical</MenuItem>
                <MenuItem value="HIGH">High</MenuItem>
                <MenuItem value="MEDIUM">Medium</MenuItem>
                <MenuItem value="LOW">Low</MenuItem>
                <MenuItem value="INFO">Info</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} md={2.5}>
              <TextField
                select
                fullWidth
                size="small"
                label="Scanner"
                value={scanner}
                onChange={(e) => setScanner(e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="ML">ML</MenuItem>
                <MenuItem value="Rules">Rules</MenuItem>
                <MenuItem value="LLM">LLM</MenuItem>
                <MenuItem value="Secrets">Secrets</MenuItem>
                <MenuItem value="CVE">CVE</MenuItem>
                <MenuItem value="Compliance">Compliance</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} md={2.5}>
              <TextField
                type="date"
                fullWidth
                size="small"
                label="Start Date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} md={2.5}>
              <TextField
                type="date"
                fullWidth
                size="small"
                label="End Date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <IconButton onClick={fetchScans} color="primary">
                  <Refresh />
                </IconButton>
                <IconButton onClick={exportScans} color="primary">
                  <FileDownload />
                </IconButton>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Scan Table */}
      <Card>
        <CardContent>
          {loading ? (
            <LinearProgress />
          ) : scans.length === 0 ? (
            <Alert severity="info">No scans found matching the filters</Alert>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Filename</TableCell>
                    <TableCell>Date</TableCell>
                    <TableCell>Risk Score</TableCell>
                    <TableCell>Findings</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {scans.map((scan) => (
                    <TableRow key={scan.id} hover>
                      <TableCell>{scan.id}</TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {scan.filename}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {new Date(scan.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={scan.unified_risk_score?.toFixed(1) || 'N/A'}
                          size="small"
                          sx={{
                            backgroundColor: getRiskColor(scan.unified_risk_score),
                            color: 'white',
                            fontWeight: 600
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {scan.critical_count > 0 && (
                            <Chip
                              label={`C:${scan.critical_count}`}
                              size="small"
                              sx={{ 
                                backgroundColor: severityColors.CRITICAL,
                                color: 'white',
                                fontSize: '0.7rem'
                              }}
                            />
                          )}
                          {scan.high_count > 0 && (
                            <Chip
                              label={`H:${scan.high_count}`}
                              size="small"
                              sx={{ 
                                backgroundColor: severityColors.HIGH,
                                color: 'white',
                                fontSize: '0.7rem'
                              }}
                            />
                          )}
                          {scan.medium_count > 0 && (
                            <Chip
                              label={`M:${scan.medium_count}`}
                              size="small"
                              sx={{ 
                                backgroundColor: severityColors.MEDIUM,
                                color: 'white',
                                fontSize: '0.7rem'
                              }}
                            />
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={scan.status}
                          size="small"
                          color={scan.status === 'completed' ? 'success' : 'default'}
                        />
                      </TableCell>
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={() => handleViewScan(scan.id)}
                          color="primary"
                        >
                          <Visibility />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => confirmDelete(scan.id)}
                          color="error"
                        >
                          <Delete />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* View Scan Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Scan Details</DialogTitle>
        <DialogContent>
          {selectedScan && (
            <Box>
              <Typography variant="h6" sx={{ mb: 2 }}>
                {selectedScan.filename}
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Risk Score
                  </Typography>
                  <Typography variant="h5">
                    {selectedScan.unified_risk_score?.toFixed(1)}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Total Findings
                  </Typography>
                  <Typography variant="h5">
                    {selectedScan.total_findings}
                  </Typography>
                </Grid>
                {/* Add more scan details as needed */}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this scan? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteScan} color="error">Delete</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default ScanHistory;
