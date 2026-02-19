import { useState, useCallback } from 'react';
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
  Chip,
  LinearProgress,
  Grid,
  Container,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import DeleteIcon from '@mui/icons-material/Delete';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ShieldIcon from '@mui/icons-material/Shield';
import BoltIcon from '@mui/icons-material/Bolt';
import LockIcon from '@mui/icons-material/Lock';
import PsychologyIcon from '@mui/icons-material/Psychology';
import BugReportIcon from '@mui/icons-material/BugReport';
import { scanFile, getScan } from '../api/client';
import EnhancedUpload from '../components/enhanced/EnhancedUpload';

export default function Scan() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [progress, setProgress] = useState(0);
  const [scanMode, setScanMode] = useState('all');
  const navigate = useNavigate();

  const handleFileSelect = (selectedFile) => {
    validateAndSetFile(selectedFile);
  };

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      validateAndSetFile(selectedFile);
    }
  };

  const validateAndSetFile = (selectedFile) => {
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = ['.tf', '.yaml', '.yml', '.json', '.bicep'];
    const fileExt = '.' + selectedFile.name.split('.').pop().toLowerCase();

    if (selectedFile.size > maxSize) {
      setError('File size must be less than 10MB');
      return;
    }

    if (!allowedTypes.includes(fileExt)) {
      setError('Invalid file type. Supported: .tf, .yaml, .yml, .json, .bicep');
      return;
    }

    setFile(selectedFile);
    setError(null);
  };

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  }, []);

  const removeFile = () => {
    setFile(null);
    setError(null);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const handleSubmit = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError(null);
    setProgress(10);

    try {
      setProgress(30);
      
      // Use the centralized API client
      const data = await scanFile(file, scanMode);
      
      setProgress(90);
      setTimeout(() => {
        setProgress(100);
        navigate(`/results`, { 
          state: { 
            scanResults: data,
            fileName: file.name,
            scanMode: scanMode
          } 
        });
      }, 500);
      
    } catch (err) {
      setError(err.message || 'Failed to scan file');
      setProgress(0);
    } finally {
      setTimeout(() => {
        setLoading(false);
        setProgress(0);
      }, 2000);
    }
  };

  return (
    <Box>
      {/* Hero Section */}
      <Box sx={{ 
        textAlign: 'center', 
        mb: 6,
        py: 4,
        borderRadius: 3,
        background: 'linear-gradient(135deg, rgba(25, 118, 210, 0.05) 0%, rgba(21, 101, 192, 0.08) 100%)',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <Box sx={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 1,
          px: 3,
          py: 1,
          borderRadius: 10,
          bgcolor: 'primary.light',
          border: '1px solid',
          borderColor: 'primary.main',
          mb: 3
        }}>
          <BoltIcon sx={{ fontSize: 18, color: 'primary.dark' }} />
          <Typography variant="body2" fontWeight="medium" color="primary.dark">
            AI-Powered Cloud Security
          </Typography>
        </Box>

        <Typography variant="h2" fontWeight="bold" gutterBottom sx={{
          background: 'linear-gradient(135deg, #1976d2 0%, #0d47a1 100%)',
          backgroundClip: 'text',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          mb: 2
        }}>
          CloudGuard AI
        </Typography>
        
        <Typography variant="h5" color="text.secondary" sx={{ maxWidth: 700, mx: 'auto', mb: 4 }}>
          Secure your cloud infrastructure with intelligent, automated security scanning
          and real-time threat detection
        </Typography>

        {/* Feature Badges */}
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap', mb: 2 }}>
          {[
            { icon: ShieldIcon, text: 'Advanced Security' },
            { icon: BoltIcon, text: 'Real-time Analysis' },
            { icon: LockIcon, text: 'Best Practices' }
          ].map((feature, i) => (
            <Chip
              key={i}
              icon={<feature.icon sx={{ fontSize: 18 }} />}
              label={feature.text}
              sx={{
                py: 2.5,
                px: 1,
                fontWeight: 'medium',
                bgcolor: 'white',
                border: '2px solid',
                borderColor: 'divider',
                '&:hover': {
                  borderColor: 'primary.main',
                  boxShadow: 2
                }
              }}
            />
          ))}
        </Box>
      </Box>

      {/* Main Content */}
      <Grid container spacing={4}>
        <Grid item xs={12} md={8}>
          {/* Enhanced Upload Component */}
          <EnhancedUpload 
            onFileSelect={handleFileSelect}
            isScanning={loading}
          />

          {/* File Preview */}
          {file && (
            <Card 
              variant="outlined" 
              sx={{ 
                mt: 3,
                border: '2px solid',
                borderColor: 'success.light',
                bgcolor: 'success.lighter',
                '&:hover': {
                  borderColor: 'success.main',
                  boxShadow: 3
                },
                transition: 'all 0.3s'
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box sx={{
                    p: 1.5,
                    borderRadius: 2,
                    bgcolor: 'success.main',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <InsertDriveFileIcon sx={{ color: 'white' }} />
                  </Box>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="body1" fontWeight="bold">
                      {file.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {formatFileSize(file.size)}
                    </Typography>
                  </Box>
                  <Button
                    size="small"
                    color="error"
                    variant="outlined"
                    startIcon={<DeleteIcon />}
                    onClick={removeFile}
                    disabled={loading}
                    sx={{ borderRadius: 2 }}
                  >
                    Remove
                  </Button>
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Error Alert */}
          {error && (
            <Alert 
              severity="error" 
              onClose={() => setError(null)} 
              sx={{ mt: 3, borderRadius: 2 }}
            >
              {error}
            </Alert>
          )}
          
          {/* Scan Mode Selection */}
          {file && !loading && (
            <Paper sx={{ mt: 3, p: 3, borderRadius: 2 }}>
              <FormControl component="fieldset">
                <FormLabel sx={{ mb: 2, fontWeight: 'bold' }}>
                  🤖 Select AI Scan Mode
                </FormLabel>
                <RadioGroup value={scanMode} onChange={(e) => setScanMode(e.target.value)}>
                  <FormControlLabel 
                    value="all" 
                    control={<Radio />} 
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <ShieldIcon fontSize="small" color="primary" />
                        <Typography>Complete AI Scan (GNN + RL + Checkov + CVE)</Typography>
                      </Box>
                    }
                  />
                  <FormControlLabel 
                    value="gnn" 
                    control={<Radio />} 
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <PsychologyIcon fontSize="small" color="secondary" />
                        <Typography>GNN Attack Path Detection (114K params)</Typography>
                      </Box>
                    }
                  />
                  <FormControlLabel 
                    value="checkov" 
                    control={<Radio />} 
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <BugReportIcon fontSize="small" color="warning" />
                        <Typography>Checkov Compliance Only</Typography>
                      </Box>
                    }
                  />
                </RadioGroup>
              </FormControl>
            </Paper>
          )}

          {/* Progress Bar */}
          {loading && (
            <Box sx={{ width: '100%', mt: 3 }}>
              <LinearProgress 
                variant="determinate" 
                value={progress}
                sx={{
                  height: 8,
                  borderRadius: 1,
                  bgcolor: 'grey.200',
                  '& .MuiLinearProgress-bar': {
                    background: 'linear-gradient(90deg, #1976d2 0%, #2196f3 100%)',
                    borderRadius: 1
                  }
                }}
              />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Analyzing security vulnerabilities... {progress}%
              </Typography>
            </Box>
          )}

          {/* Submit Button */}
          <Button
            variant="contained"
            size="large"
            fullWidth
            onClick={handleSubmit}
            disabled={!file || loading}
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <CheckCircleIcon />}
            sx={{ 
              py: 2, 
              mt: 3,
              borderRadius: 2,
              fontSize: '1.1rem',
              fontWeight: 'bold',
              background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #1565c0 0%, #0d47a1 100%)',
                boxShadow: 4
              },
              '&:disabled': {
                background: 'grey.300'
              }
            }}
          >
            {loading ? 'Scanning...' : 'Start Security Scan'}
          </Button>
        </Grid>

        <Grid item xs={12} md={4}>
          {/* What We Check Card */}
          <Card sx={{ 
            border: '2px solid',
            borderColor: 'divider',
            borderRadius: 3,
            '&:hover': {
              borderColor: 'primary.main',
              boxShadow: 4
            },
            transition: 'all 0.3s'
          }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom fontWeight="bold">
                What we check
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 3 }}>
                {[
                  { label: 'ML', text: 'Machine Learning Analysis', color: 'primary' },
                  { label: 'Rules', text: '500+ Security Rules', color: 'secondary' },
                  { label: 'LLM', text: 'AI-Powered Insights', color: 'success' },
                  { label: 'Risk', text: 'Unified Risk Scoring', color: 'warning' }
                ].map((item, i) => (
                  <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Chip 
                      label={item.label} 
                      color={item.color} 
                      size="small"
                      sx={{ fontWeight: 'bold', minWidth: 60 }}
                    />
                    <Typography variant="body2">{item.text}</Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>

          {/* Detection Categories Card */}
          <Card sx={{ 
            mt: 3,
            border: '2px solid',
            borderColor: 'divider',
            borderRadius: 3,
            background: 'linear-gradient(135deg, rgba(25, 118, 210, 0.02) 0%, rgba(21, 101, 192, 0.05) 100%)',
            '&:hover': {
              borderColor: 'primary.main',
              boxShadow: 4
            },
            transition: 'all 0.3s'
          }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom fontWeight="bold">
                Detection Categories
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mt: 2 }}>
                {[
                  'Misconfigurations',
                  'Exposed Secrets',
                  'Insecure Defaults',
                  'Compliance Violations',
                  'Access Control Issues',
                  'Network Security'
                ].map((category, i) => (
                  <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      bgcolor: 'primary.main'
                    }} />
                    <Typography variant="body2" color="text.secondary">
                      {category}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>

          {/* Stats Card */}
          <Card sx={{ 
            mt: 3,
            border: '2px solid',
            borderColor: 'success.light',
            borderRadius: 3,
            background: 'linear-gradient(135deg, rgba(76, 175, 80, 0.05) 0%, rgba(46, 125, 50, 0.08) 100%)',
            '&:hover': {
              borderColor: 'success.main',
              boxShadow: 4
            },
            transition: 'all 0.3s'
          }}>
            <CardContent sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Why Choose CloudGuard AI?
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 3 }}>
                {[
                  { icon: CheckCircleIcon, text: 'Multi-cloud support' },
                  { icon: CheckCircleIcon, text: 'IaC scanning' },
                  { icon: CheckCircleIcon, text: 'Compliance validation' },
                  { icon: CheckCircleIcon, text: 'Actionable remediation' }
                ].map((item, i) => (
                  <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <item.icon sx={{ color: 'success.main', fontSize: 20 }} />
                    <Typography variant="body2">{item.text}</Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
