import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  List,
  ListItem,
  ListItemText,
  Chip,
  Paper,
  Rating,
} from '@mui/material';
import MessageIcon from '@mui/icons-material/Message';
import SendIcon from '@mui/icons-material/Send';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import StarIcon from '@mui/icons-material/Star';
import EmailIcon from '@mui/icons-material/Email';
import ForumIcon from '@mui/icons-material/Forum';
import { listScans, submitFeedback, listFeedback } from '../api/client';

export default function Feedback() {
  const [scans, setScans] = useState([]);
  const [feedbacks, setFeedbacks] = useState([]);
  const [selectedScan, setSelectedScan] = useState('');
  const [isCorrect, setIsCorrect] = useState('');
  const [adjustedSeverity, setAdjustedSeverity] = useState('');
  const [comment, setComment] = useState('');
  const [rating, setRating] = useState(0);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [scansData, feedbacksData] = await Promise.all([
          listScans(),
          listFeedback(),
        ]);
        setScans(scansData);
        setFeedbacks(feedbacksData);
      } catch (err) {
        setError('Failed to load data');
      }
    };

    fetchData();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      const feedbackData = {
        scan_id: parseInt(selectedScan),
        is_correct: isCorrect === '' ? null : parseInt(isCorrect),
        adjusted_severity: adjustedSeverity || null,
        user_comment: comment || null,
      };

      await submitFeedback(feedbackData);
      setSuccess('Feedback submitted successfully!');
      setSubmitted(true);
      
      // Reset form after delay
      setTimeout(() => {
        setSelectedScan('');
        setIsCorrect('');
        setAdjustedSeverity('');
        setComment('');
        setRating(0);
        setSubmitted(false);
        setSuccess(null);
      }, 3000);
      
      // Refresh feedback list
      const feedbacksData = await listFeedback();
      setFeedbacks(feedbacksData);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit feedback');
    }
  };

  return (
    <Box sx={{ 
      minHeight: '100vh',
      background: 'linear-gradient(to bottom, rgba(25, 118, 210, 0.02), white)',
      py: 6
    }}>
      <Box sx={{ maxWidth: 1200, mx: 'auto', px: 3 }}>
        {/* Header */}
        <Box sx={{ textAlign: 'center', mb: 8 }}>
          <Box sx={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 80,
            height: 80,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
            mb: 3,
            boxShadow: '0 8px 24px rgba(25, 118, 210, 0.3)'
          }}>
            <MessageIcon sx={{ fontSize: 40, color: 'white' }} />
          </Box>
          <Typography variant="h3" fontWeight="bold" gutterBottom>
            We Value Your Feedback
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto' }}>
            Help us improve CloudGuard AI by sharing your thoughts and suggestions
          </Typography>
        </Box>

        {/* Feedback Form */}
        {submitted ? (
          <Card sx={{
            maxWidth: 800,
            mx: 'auto',
            border: '2px solid',
            borderColor: 'success.main',
            background: 'linear-gradient(135deg, rgba(46, 125, 50, 0.05), rgba(76, 175, 80, 0.05))',
            boxShadow: 3
          }}>
            <CardContent sx={{ p: 8, textAlign: 'center' }}>
              <Box sx={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 80,
                height: 80,
                borderRadius: '50%',
                bgcolor: 'success.light',
                mb: 3
              }}>
                <CheckCircleIcon sx={{ fontSize: 48, color: 'success.main' }} />
              </Box>
              <Typography variant="h4" fontWeight="bold" gutterBottom>
                Thank You!
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Your feedback has been submitted successfully
              </Typography>
            </CardContent>
          </Card>
        ) : (
          <Card sx={{
            maxWidth: 800,
            mx: 'auto',
            border: '2px solid',
            borderColor: 'divider',
            boxShadow: 4,
            '&:hover': {
              boxShadow: 8,
              borderColor: 'primary.main'
            },
            transition: 'all 0.3s'
          }}>
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h5" fontWeight="bold" gutterBottom>
                Share Your Experience
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Tell us what you think about CloudGuard AI
              </Typography>

              <form onSubmit={handleSubmit}>
                <Box display="flex" flexDirection="column" gap={3} mt={3}>
                  {/* Rating */}
                  <Box>
                    <Typography variant="body1" fontWeight="medium" gutterBottom>
                      How would you rate your experience?
                    </Typography>
                    <Rating
                      value={rating}
                      onChange={(event, newValue) => setRating(newValue)}
                      size="large"
                      icon={<StarIcon sx={{ fontSize: 32 }} />}
                      emptyIcon={<StarIcon sx={{ fontSize: 32 }} />}
                    />
                  </Box>

                  <FormControl fullWidth>
                    <InputLabel>Select Scan</InputLabel>
                    <Select
                      value={selectedScan}
                      onChange={(e) => setSelectedScan(e.target.value)}
                      required
                    >
                      {scans.map((scan) => (
                        <MenuItem key={scan.id} value={scan.id}>
                          {scan.filename} - Score: {scan.unified_risk_score?.toFixed(2) || 'N/A'}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl fullWidth>
                    <InputLabel>Was the assessment correct?</InputLabel>
                    <Select
                      value={isCorrect}
                      onChange={(e) => setIsCorrect(e.target.value)}
                    >
                      <MenuItem value="">Not evaluated</MenuItem>
                      <MenuItem value="1">Correct</MenuItem>
                      <MenuItem value="0">Incorrect</MenuItem>
                    </Select>
                  </FormControl>

                  <FormControl fullWidth>
                    <InputLabel>Adjusted Severity (optional)</InputLabel>
                    <Select
                      value={adjustedSeverity}
                      onChange={(e) => setAdjustedSeverity(e.target.value)}
                    >
                      <MenuItem value="">None</MenuItem>
                      <MenuItem value="critical">Critical</MenuItem>
                      <MenuItem value="high">High</MenuItem>
                      <MenuItem value="medium">Medium</MenuItem>
                      <MenuItem value="low">Low</MenuItem>
                    </Select>
                  </FormControl>

                  <TextField
                    label="Your Feedback"
                    multiline
                    rows={6}
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="Tell us about your experience, suggestions for improvement, or report any issues..."
                    helperText={`${comment.length} characters`}
                  />

                  {error && <Alert severity="error">{error}</Alert>}
                  {success && <Alert severity="success">{success}</Alert>}

                  <Button 
                    type="submit" 
                    variant="contained" 
                    size="large"
                    disabled={!selectedScan}
                    startIcon={<SendIcon />}
                    sx={{ 
                      py: 1.5,
                      background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #1565c0 0%, #0d47a1 100%)',
                      }
                    }}
                  >
                    Submit Feedback
                  </Button>
                </Box>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Contact Cards */}
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mt: 6, maxWidth: 800, mx: 'auto' }}>
          <Card sx={{ 
            border: '2px solid',
            borderColor: 'divider',
            '&:hover': {
              borderColor: 'primary.main',
              boxShadow: 4
            },
            transition: 'all 0.3s'
          }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                <EmailIcon color="primary" />
                <Typography variant="h6" fontWeight="bold">
                  Email Support
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                support@cloudguardai.com
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ 
            border: '2px solid',
            borderColor: 'divider',
            '&:hover': {
              borderColor: 'primary.main',
              boxShadow: 4
            },
            transition: 'all 0.3s'
          }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                <ForumIcon color="primary" />
                <Typography variant="h6" fontWeight="bold">
                  Community
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Join our Discord server for discussions
              </Typography>
            </CardContent>
          </Card>
        </Box>

        {/* Recent Feedback */}
        {feedbacks.length > 0 && (
          <Box sx={{ mt: 8, maxWidth: 800, mx: 'auto' }}>
            <Typography variant="h5" fontWeight="bold" gutterBottom>
              Recent Feedback
            </Typography>
            <Card sx={{ mt: 2, border: '2px solid', borderColor: 'divider' }}>
              <List>
                {feedbacks.slice(0, 10).map((fb, index) => (
                  <ListItem key={fb.id} divider={index < 9}>
                    <ListItemText
                      primary={`Scan #${fb.scan_id}`}
                      secondary={
                        <Box sx={{ mt: 1 }}>
                          {fb.is_correct !== null && (
                            <Chip
                              label={fb.is_correct === 1 ? 'Correct' : 'Incorrect'}
                              color={fb.is_correct === 1 ? 'success' : 'error'}
                              size="small"
                              sx={{ mr: 1 }}
                            />
                          )}
                          {fb.adjusted_severity && (
                            <Chip
                              label={`Adjusted: ${fb.adjusted_severity}`}
                              size="small"
                              sx={{ mr: 1 }}
                            />
                          )}
                          {fb.user_comment && (
                            <Typography variant="body2" sx={{ mt: 1 }}>
                              {fb.user_comment}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Card>
          </Box>
        )}
      </Box>
    </Box>
  );
}
