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
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
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
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Model Status
        </Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchData}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            onClick={() => setDialogOpen(true)}
          >
            Trigger Retrain
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      <Grid container spacing={3}>
        {/* Active Model */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Active Model
              </Typography>
              {status?.active_version ? (
                <Box display="flex" flexDirection="column" gap={1}>
                  <Box display="flex" justifyContent="space-between">
                    <Typography>Version:</Typography>
                    <Typography fontWeight="bold">{status.active_version}</Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography>Type:</Typography>
                    <Typography fontWeight="bold">{status.model_type}</Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography>Accuracy:</Typography>
                    <Typography fontWeight="bold">{status.accuracy?.toFixed(4) || 'N/A'}</Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography>Precision:</Typography>
                    <Typography fontWeight="bold">{status.precision?.toFixed(4) || 'N/A'}</Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography>Recall:</Typography>
                    <Typography fontWeight="bold">{status.recall?.toFixed(4) || 'N/A'}</Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography>F1 Score:</Typography>
                    <Typography fontWeight="bold">{status.f1_score?.toFixed(4) || 'N/A'}</Typography>
                  </Box>
                </Box>
              ) : (
                <Alert severity="info">No active model</Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Statistics */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Statistics
              </Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                <Box display="flex" justifyContent="space-between">
                  <Typography>Total Scans:</Typography>
                  <Chip label={status?.total_scans || 0} color="primary" />
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography>Total Feedback:</Typography>
                  <Chip label={status?.total_feedback || 0} color="secondary" />
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography>Pending Retraining:</Typography>
                  <Chip label={status?.pending_retraining_samples || 0} color="warning" />
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography>Training Samples:</Typography>
                  <Chip label={status?.training_samples || 0} color="success" />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Version History */}
        <Grid item xs={12}>
          <Typography variant="h5" gutterBottom sx={{ mt: 2 }}>
            Version History
          </Typography>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Version</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Accuracy</TableCell>
                  <TableCell>Precision</TableCell>
                  <TableCell>Recall</TableCell>
                  <TableCell>F1 Score</TableCell>
                  <TableCell>Samples</TableCell>
                  <TableCell>Created</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {versions.map((version) => (
                  <TableRow key={version.active_version}>
                    <TableCell>{version.active_version}</TableCell>
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
        </Grid>
      </Grid>

      {/* Retrain Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogTitle>Trigger Model Retraining</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} pt={1}>
            <Alert severity="info">
              Retraining will use feedback data to update the model using online learning.
            </Alert>
            <TextField
              label="Minimum Samples"
              type="number"
              value={minSamples}
              onChange={(e) => setMinSamples(parseInt(e.target.value))}
              helperText="Minimum number of feedback samples required"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleRetrain}
            variant="contained"
            disabled={retraining}
          >
            {retraining ? <CircularProgress size={24} /> : 'Start Retraining'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
