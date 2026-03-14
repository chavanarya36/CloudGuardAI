import { useState, useEffect } from 'react';
import {
  Select, MenuItem, TextField, Rating, Alert,
} from '@mui/material';
import { listScans, submitFeedback, listFeedback } from '../api/client';

function GlassCard({ children, style }) {
  return (
    <div style={{
      background: 'rgba(10,22,38,0.8)',
      border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: '14px', padding: '28px',
      backdropFilter: 'blur(8px)',
      ...style,
    }}>
      {children}
    </div>
  );
}

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
          listScans(), listFeedback(),
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
    setError(null); setSuccess(null);
    try {
      await submitFeedback({
        scan_id: parseInt(selectedScan),
        is_correct: isCorrect === '' ? null : parseInt(isCorrect),
        adjusted_severity: adjustedSeverity || null,
        user_comment: comment || null,
      });
      setSuccess('Feedback submitted successfully!');
      setSubmitted(true);
      setTimeout(() => {
        setSelectedScan(''); setIsCorrect(''); setAdjustedSeverity('');
        setComment(''); setRating(0); setSubmitted(false); setSuccess(null);
      }, 3000);
      const feedbacksData = await listFeedback();
      setFeedbacks(feedbacksData);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit feedback');
    }
  };

  const muiDarkSx = {
    '& .MuiOutlinedInput-root': {
      color: 'rgba(255,255,255,0.8)',
      '& fieldset': { borderColor: 'rgba(255,255,255,0.12)' },
      '&:hover fieldset': { borderColor: 'rgba(66,165,245,0.4)' },
      '&.Mui-focused fieldset': { borderColor: '#42a5f5' },
    },
    '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.4)' },
    '& .MuiSelect-icon': { color: 'rgba(255,255,255,0.4)' },
  };

  return (
    <div style={{ fontFamily: '"DM Sans", sans-serif' }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Syne:wght@700;800&display=swap');
        .feedback-btn { cursor:pointer; transition:all 0.25s ease; }
        .feedback-btn:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(66,165,245,0.3); }
        .contact-card { transition:all 0.3s ease; }
        .contact-card:hover { border-color:rgba(66,165,245,0.3)!important; transform:translateY(-2px); }
      `}</style>

      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '48px' }}>
        <div style={{
          width: '64px', height: '64px', borderRadius: '50%',
          background: 'linear-gradient(135deg, #1976d2, #42a5f5)',
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          marginBottom: '20px',
          boxShadow: '0 0 32px rgba(66,165,245,0.3)',
        }}>
          <span style={{ fontSize: '28px' }}>💬</span>
        </div>
        <h1 style={{
          fontFamily: '"Syne", sans-serif',
          fontSize: 'clamp(28px, 4vw, 36px)', fontWeight: 800,
          color: '#fff', margin: '0 0 10px', letterSpacing: '-0.02em',
        }}>
          We Value Your Feedback
        </h1>
        <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '15px', maxWidth: '500px', margin: '0 auto' }}>
          Help us improve CloudGuard AI by sharing your thoughts and suggestions
        </p>
      </div>

      {/* Form */}
      <div style={{ maxWidth: '700px', margin: '0 auto' }}>
        {submitted ? (
          <GlassCard style={{ textAlign: 'center', padding: '48px', border: '1px solid rgba(102,187,106,0.3)' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>✅</div>
            <div style={{
              fontFamily: '"Syne", sans-serif',
              fontSize: '24px', fontWeight: 800, color: '#fff', marginBottom: '8px',
            }}>
              Thank You!
            </div>
            <p style={{ color: 'rgba(255,255,255,0.45)', fontSize: '14px' }}>
              Your feedback has been submitted successfully
            </p>
          </GlassCard>
        ) : (
          <GlassCard>
            <div style={{
              fontFamily: '"Syne", sans-serif',
              fontSize: '18px', fontWeight: 700, color: '#fff', marginBottom: '6px',
            }}>
              Share Your Experience
            </div>
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '13px', marginBottom: '24px' }}>
              Tell us what you think about CloudGuard AI
            </p>

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Rating */}
              <div>
                <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.5)', marginBottom: '8px', fontWeight: 500 }}>
                  How would you rate your experience?
                </div>
                <Rating
                  value={rating}
                  onChange={(event, newValue) => setRating(newValue)}
                  size="large"
                  sx={{ '& .MuiRating-iconFilled': { color: '#42a5f5' } }}
                />
              </div>

              <Select value={selectedScan} onChange={(e) => setSelectedScan(e.target.value)} displayEmpty fullWidth size="small" sx={muiDarkSx} required>
                <MenuItem value="" disabled>Select Scan</MenuItem>
                {scans.map((scan) => (
                  <MenuItem key={scan.id} value={scan.id}>
                    {scan.filename} - Score: {scan.unified_risk_score?.toFixed(2) || 'N/A'}
                  </MenuItem>
                ))}
              </Select>

              <Select value={isCorrect} onChange={(e) => setIsCorrect(e.target.value)} displayEmpty fullWidth size="small" sx={muiDarkSx}>
                <MenuItem value="">Was the assessment correct?</MenuItem>
                <MenuItem value="1">Correct</MenuItem>
                <MenuItem value="0">Incorrect</MenuItem>
              </Select>

              <Select value={adjustedSeverity} onChange={(e) => setAdjustedSeverity(e.target.value)} displayEmpty fullWidth size="small" sx={muiDarkSx}>
                <MenuItem value="">Adjusted Severity (optional)</MenuItem>
                <MenuItem value="critical">Critical</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="low">Low</MenuItem>
              </Select>

              <TextField
                label="Your Feedback"
                multiline rows={5}
                value={comment} onChange={(e) => setComment(e.target.value)}
                placeholder="Tell us about your experience, suggestions for improvement, or report any issues..."
                helperText={`${comment.length} characters`}
                fullWidth sx={muiDarkSx}
              />

              {error && <Alert severity="error" sx={{ borderRadius: 2 }}>{error}</Alert>}
              {success && <Alert severity="success" sx={{ borderRadius: 2 }}>{success}</Alert>}

              <button type="submit" className="feedback-btn" disabled={!selectedScan} style={{
                padding: '14px 28px', borderRadius: '10px', border: 'none',
                background: selectedScan ? 'linear-gradient(135deg, #1976d2, #42a5f5)' : 'rgba(255,255,255,0.08)',
                color: selectedScan ? '#fff' : 'rgba(255,255,255,0.3)',
                fontSize: '15px', fontWeight: 600,
                fontFamily: '"DM Sans", sans-serif',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                cursor: selectedScan ? 'pointer' : 'not-allowed',
              }}>
                Submit Feedback
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M2 14l12-6L2 2v4.67l8 1.33-8 1.33V14z" fill="currentColor"/>
                </svg>
              </button>
            </form>
          </GlassCard>
        )}

        {/* Contact Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginTop: '28px' }}>
          <div className="contact-card" style={{
            background: 'rgba(10,22,38,0.8)', border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: '14px', padding: '20px', backdropFilter: 'blur(8px)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <span style={{ fontSize: '20px' }}>📧</span>
              <span style={{ fontFamily: '"Syne", sans-serif', fontWeight: 700, color: '#fff', fontSize: '15px' }}>
                Email Support
              </span>
            </div>
            <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.4)' }}>support@cloudguardai.com</span>
          </div>

          <div className="contact-card" style={{
            background: 'rgba(10,22,38,0.8)', border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: '14px', padding: '20px', backdropFilter: 'blur(8px)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <span style={{ fontSize: '20px' }}>💬</span>
              <span style={{ fontFamily: '"Syne", sans-serif', fontWeight: 700, color: '#fff', fontSize: '15px' }}>
                Community
              </span>
            </div>
            <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.4)' }}>Join our Discord server for discussions</span>
          </div>
        </div>

        {/* Recent Feedback */}
        {feedbacks.length > 0 && (
          <div style={{ marginTop: '40px' }}>
            <h2 style={{
              fontFamily: '"Syne", sans-serif',
              fontSize: '18px', fontWeight: 700, color: '#fff', marginBottom: '16px',
            }}>
              Recent Feedback
            </h2>
            <GlassCard style={{ padding: 0, overflow: 'hidden' }}>
              {feedbacks.slice(0, 10).map((fb, index) => (
                <div key={fb.id} style={{
                  padding: '16px 24px',
                  borderBottom: index < 9 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                }}>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: '#fff', marginBottom: '8px' }}>
                    Scan #{fb.scan_id}
                  </div>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {fb.is_correct !== null && (
                      <span style={{
                        padding: '3px 10px', borderRadius: '99px', fontSize: '11px', fontWeight: 500,
                        background: fb.is_correct === 1 ? 'rgba(102,187,106,0.15)' : 'rgba(239,83,80,0.15)',
                        color: fb.is_correct === 1 ? '#66bb6a' : '#ef5350',
                        border: `1px solid ${fb.is_correct === 1 ? 'rgba(102,187,106,0.3)' : 'rgba(239,83,80,0.3)'}`,
                      }}>
                        {fb.is_correct === 1 ? 'Correct' : 'Incorrect'}
                      </span>
                    )}
                    {fb.adjusted_severity && (
                      <span style={{
                        padding: '3px 10px', borderRadius: '99px', fontSize: '11px', fontWeight: 500,
                        background: 'rgba(66,165,245,0.12)', color: '#42a5f5',
                        border: '1px solid rgba(66,165,245,0.25)',
                      }}>
                        Adjusted: {fb.adjusted_severity}
                      </span>
                    )}
                  </div>
                  {fb.user_comment && (
                    <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.45)', marginTop: '8px', lineHeight: 1.5 }}>
                      {fb.user_comment}
                    </div>
                  )}
                </div>
              ))}
            </GlassCard>
          </div>
        )}
      </div>
    </div>
  );
}
