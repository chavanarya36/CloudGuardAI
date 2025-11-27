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
} from '@mui/material';
import { listScans, submitFeedback, listFeedback } from '../api/client';

export default function Feedback() {
  const [scans, setScans] = useState([]);
  const [feedbacks, setFeedbacks] = useState([]);
  const [selectedScan, setSelectedScan] = useState('');
  const [isCorrect, setIsCorrect] = useState('');
  const [adjustedSeverity, setAdjustedSeverity] = useState('');
  const [comment, setComment] = useState('');
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);

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
      
      // Reset form
      setSelectedScan('');
      setIsCorrect('');
      setAdjustedSeverity('');
      setComment('');
      
      // Refresh feedback list
      const feedbacksData = await listFeedback();
      setFeedbacks(feedbacksData);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit feedback');
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Provide Feedback
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Help improve the model by providing feedback on scan results.
      </Typography>

      <Card sx={{ maxWidth: 800, mt: 3, mb: 4 }}>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <Box display="flex" flexDirection="column" gap={2}>
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
                label="Comment (optional)"
                multiline
                rows={4}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
              />

              {error && <Alert severity="error">{error}</Alert>}
              {success && <Alert severity="success">{success}</Alert>}

              <Button type="submit" variant="contained" size="large">
                Submit Feedback
              </Button>
            </Box>
          </form>
        </CardContent>
      </Card>

      <Typography variant="h5" gutterBottom>
        Recent Feedback
      </Typography>
      <Card>
        <List>
          {feedbacks.slice(0, 10).map((fb) => (
            <ListItem key={fb.id} divider>
              <ListItemText
                primary={`Scan #${fb.scan_id}`}
                secondary={
                  <>
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
                    {fb.user_comment && <Box mt={1}>{fb.user_comment}</Box>}
                  </>
                }
              />
            </ListItem>
          ))}
        </List>
      </Card>
    </Box>
  );
}
