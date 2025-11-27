import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Alert,
  CircularProgress,
  Paper,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { scanFile, getScan } from '../api/client';

export default function Scan() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
    setError(null);
  };

  const handleSubmit = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Submit scan
      const response = await scanFile(file);
      
      // Poll for completion
      const scanId = response.job_id.split('-')[0]; // Extract scan ID from job ID
      
      // Wait a bit for processing
      setTimeout(() => {
        navigate(`/results/${scanId}`);
      }, 2000);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to scan file');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Security Scan
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Upload an Infrastructure as Code (IaC) file for security analysis.
      </Typography>

      <Card sx={{ maxWidth: 600, mt: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Paper
              variant="outlined"
              sx={{
                p: 3,
                textAlign: 'center',
                cursor: 'pointer',
                '&:hover': { bgcolor: 'action.hover' },
              }}
              onClick={() => document.getElementById('file-input').click()}
            >
              <input
                accept=".tf,.yaml,.yml,.json"
                style={{ display: 'none' }}
                id="file-input"
                type="file"
                onChange={handleFileChange}
              />
              <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
              <Typography variant="body1">
                {file ? file.name : 'Click to select file'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Supported: .tf, .yaml, .yml, .json
              </Typography>
            </Paper>

            {error && (
              <Alert severity="error">{error}</Alert>
            )}

            <Button
              variant="contained"
              size="large"
              onClick={handleSubmit}
              disabled={!file || loading}
              startIcon={loading ? <CircularProgress size={20} /> : <CloudUploadIcon />}
            >
              {loading ? 'Scanning...' : 'Start Scan'}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
