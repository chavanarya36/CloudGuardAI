import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { CircularProgress } from '@mui/material';
import { scanFile } from '../api/client';
import EnhancedUpload from '../components/enhanced/EnhancedUpload';
import { useLastScan } from '../context/ScanContext';

export default function Scan() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [progress, setProgress] = useState(0);
  const [scanMode, setScanMode] = useState('all');
  const navigate = useNavigate();
  const { recordScan } = useLastScan();

  const handleFileSelect = (selectedFile) => validateAndSetFile(selectedFile);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) validateAndSetFile(selectedFile);
  };

  const validateAndSetFile = (selectedFile) => {
    const maxSize = 10 * 1024 * 1024;
    const allowedTypes = ['.tf', '.yaml', '.yml', '.json', '.bicep'];
    const fileExt = '.' + selectedFile.name.split('.').pop().toLowerCase();
    if (selectedFile.size > maxSize) { setError('File size must be less than 10MB'); return; }
    if (!allowedTypes.includes(fileExt)) { setError('Invalid file type. Supported: .tf, .yaml, .yml, .json, .bicep'); return; }
    setFile(selectedFile); setError(null);
  };

  const handleDrag = useCallback((e) => {
    e.preventDefault(); e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault(); e.stopPropagation(); setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) validateAndSetFile(e.dataTransfer.files[0]);
  }, []);

  const removeFile = () => { setFile(null); setError(null); };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const handleSubmit = async () => {
    if (!file) { setError('Please select a file'); return; }
    setLoading(true); setError(null); setProgress(10);
    try {
      setProgress(30);
      const data = await scanFile(file, scanMode);
      setProgress(90);
      recordScan(data, file.name);
      setTimeout(() => {
        setProgress(100);
        navigate(`/results/${data.id}`, { state: { scanResults: data, fileName: file.name, scanMode } });
      }, 500);
    } catch (err) {
      setError(err.message || 'Failed to scan file'); setProgress(0);
    } finally {
      setTimeout(() => { setLoading(false); setProgress(0); }, 2000);
    }
  };

  const scanModes = [
    { value: 'all', icon: '🛡️', label: 'Complete AI Scan', desc: 'GNN + RL + Checkov + CVE', color: '#42a5f5' },
    { value: 'gnn', icon: '🧠', label: 'GNN Attack Path Detection', desc: '114K params model', color: '#ce93d8' },
    { value: 'checkov', icon: '🐛', label: 'Checkov Compliance Only', desc: 'Policy checks', color: '#ffa726' },
  ];

  return (
    <div style={{ fontFamily: '"DM Sans", sans-serif' }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Syne:wght@700;800&display=swap');
        @keyframes shimmer { 0%{background-position:-200% center} 100%{background-position:200% center} }
        .scan-btn { cursor:pointer; transition:all 0.25s cubic-bezier(0.34,1.56,0.64,1); }
        .scan-btn:hover { transform:translateY(-3px) scale(1.02); box-shadow:0 12px 40px rgba(66,165,245,0.35); }
        .mode-card { cursor:pointer; transition:all 0.25s ease; }
        .mode-card:hover { transform:translateY(-2px); }
      `}</style>

      {/* Hero */}
      <div style={{
        textAlign: 'center', padding: '40px 24px 48px',
        borderRadius: '16px', marginBottom: '32px',
        background: 'linear-gradient(135deg, rgba(21,101,192,0.1) 0%, rgba(10,22,38,0.8) 100%)',
        border: '1px solid rgba(66,165,245,0.1)',
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', top: '-60px', left: '50%', transform: 'translateX(-50%)',
          width: '400px', height: '200px',
          background: 'radial-gradient(ellipse, rgba(66,165,245,0.08), transparent 70%)',
        }} />

        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '8px',
          padding: '6px 16px', borderRadius: '99px', marginBottom: '20px',
          background: 'rgba(66,165,245,0.08)',
          border: '1px solid rgba(66,165,245,0.2)',
        }}>
          <span style={{ fontSize: '14px' }}>⚡</span>
          <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.6)', fontWeight: 500 }}>
            AI-Powered Cloud Security
          </span>
        </div>

        <h1 style={{
          fontFamily: '"Syne", sans-serif',
          fontSize: 'clamp(28px, 5vw, 40px)', fontWeight: 800,
          margin: '0 0 12px', letterSpacing: '-0.03em',
          background: 'linear-gradient(90deg, #42a5f5, #80d6ff, #42a5f5)',
          backgroundSize: '200% auto',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          animation: 'shimmer 3s linear infinite',
        }}>
          CloudGuard AI
        </h1>

        <p style={{
          color: 'rgba(255,255,255,0.4)', fontSize: '15px',
          maxWidth: '600px', margin: '0 auto 20px', lineHeight: 1.6,
        }}>
          Secure your cloud infrastructure with intelligent, automated security scanning and real-time threat detection
        </p>

        <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap' }}>
          {[
            { icon: '🛡️', text: 'Advanced Security' },
            { icon: '⚡', text: 'Real-time Analysis' },
            { icon: '🔒', text: 'Best Practices' },
          ].map((f, i) => (
            <div key={i} style={{
              padding: '6px 14px', borderRadius: '8px',
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.08)',
              fontSize: '12px', color: 'rgba(255,255,255,0.5)',
              display: 'flex', alignItems: 'center', gap: '6px',
            }}>
              {f.icon} {f.text}
            </div>
          ))}
        </div>
      </div>

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '24px', alignItems: 'start' }}>
        {/* Left Column */}
        <div>
          <EnhancedUpload onFileSelect={handleFileSelect} isScanning={loading} />

          {/* File Preview */}
          {file && (
            <div style={{
              marginTop: '16px', padding: '16px 20px', borderRadius: '12px',
              background: 'rgba(102,187,106,0.06)',
              border: '1px solid rgba(102,187,106,0.2)',
              display: 'flex', alignItems: 'center', gap: '14px',
            }}>
              <div style={{
                width: '38px', height: '38px', borderRadius: '8px',
                background: 'rgba(102,187,106,0.15)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '18px',
              }}>📄</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#fff' }}>{file.name}</div>
                <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)' }}>{formatFileSize(file.size)}</div>
              </div>
              <button onClick={removeFile} disabled={loading} style={{
                padding: '6px 14px', borderRadius: '8px',
                background: 'rgba(239,83,80,0.1)', border: '1px solid rgba(239,83,80,0.3)',
                color: '#ef5350', fontSize: '12px', fontWeight: 500, cursor: 'pointer',
                fontFamily: '"DM Sans", sans-serif',
              }}>
                Remove
              </button>
            </div>
          )}

          {error && (
            <div style={{
              marginTop: '16px', padding: '14px 20px', borderRadius: '12px',
              background: 'rgba(239,83,80,0.08)', border: '1px solid rgba(239,83,80,0.2)',
              color: '#ef5350', fontSize: '13px',
              display: 'flex', alignItems: 'center', gap: '10px',
            }}>
              <span>⚠️</span> {error}
              <button onClick={() => setError(null)} style={{
                marginLeft: 'auto', background: 'none', border: 'none',
                color: '#ef5350', cursor: 'pointer', fontSize: '16px',
              }}>×</button>
            </div>
          )}

          {/* Scan Mode */}
          {file && !loading && (
            <div style={{ marginTop: '16px' }}>
              <div style={{
                fontSize: '13px', fontWeight: 600, color: 'rgba(255,255,255,0.5)',
                marginBottom: '12px',
              }}>
                🤖 Select AI Scan Mode
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {scanModes.map((mode) => (
                  <div
                    key={mode.value}
                    className="mode-card"
                    onClick={() => setScanMode(mode.value)}
                    style={{
                      padding: '14px 18px', borderRadius: '10px',
                      background: scanMode === mode.value ? `${mode.color}12` : 'rgba(255,255,255,0.02)',
                      border: `1px solid ${scanMode === mode.value ? `${mode.color}40` : 'rgba(255,255,255,0.06)'}`,
                      display: 'flex', alignItems: 'center', gap: '14px',
                    }}
                  >
                    <div style={{
                      width: '18px', height: '18px', borderRadius: '50%',
                      border: `2px solid ${scanMode === mode.value ? mode.color : 'rgba(255,255,255,0.2)'}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      {scanMode === mode.value && (
                        <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: mode.color }} />
                      )}
                    </div>
                    <span style={{ fontSize: '16px' }}>{mode.icon}</span>
                    <div>
                      <div style={{ fontSize: '14px', color: '#fff', fontWeight: 500 }}>{mode.label}</div>
                      <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.35)' }}>{mode.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Progress */}
          {loading && (
            <div style={{ marginTop: '16px' }}>
              <div style={{
                height: '6px', borderRadius: '3px',
                background: 'rgba(255,255,255,0.06)', overflow: 'hidden',
              }}>
                <div style={{
                  height: '100%', borderRadius: '3px',
                  width: `${progress}%`,
                  background: 'linear-gradient(90deg, #1976d2, #42a5f5)',
                  transition: 'width 0.4s ease',
                }} />
              </div>
              <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.4)', marginTop: '8px' }}>
                Analyzing security vulnerabilities... {progress}%
              </div>
            </div>
          )}

          {/* Submit */}
          <button
            className="scan-btn"
            onClick={handleSubmit}
            disabled={!file || loading}
            style={{
              width: '100%', padding: '16px', marginTop: '20px',
              borderRadius: '12px', border: 'none',
              background: file && !loading
                ? 'linear-gradient(135deg, #1976d2, #42a5f5)'
                : 'rgba(255,255,255,0.06)',
              color: file && !loading ? '#fff' : 'rgba(255,255,255,0.3)',
              fontSize: '16px', fontWeight: 700,
              fontFamily: '"DM Sans", sans-serif',
              cursor: file && !loading ? 'pointer' : 'not-allowed',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px',
            }}
          >
            {loading ? (
              <><CircularProgress size={20} sx={{ color: 'inherit' }} /> Scanning...</>
            ) : (
              <>✅ Start Security Scan</>
            )}
          </button>
        </div>

        {/* Right Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* What we check */}
          <div style={{
            background: 'rgba(10,22,38,0.8)', border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: '14px', padding: '24px', backdropFilter: 'blur(8px)',
          }}>
            <div style={{
              fontFamily: '"Syne", sans-serif',
              fontSize: '15px', fontWeight: 700, color: '#fff', marginBottom: '16px',
            }}>
              What we check
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {[
                { tag: 'ML', text: 'Machine Learning Analysis', color: '#42a5f5' },
                { tag: 'Rules', text: '500+ Security Rules', color: '#ce93d8' },
                { tag: 'LLM', text: 'AI-Powered Insights', color: '#66bb6a' },
                { tag: 'Risk', text: 'Unified Risk Scoring', color: '#ffa726' },
              ].map((item, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{
                    padding: '2px 10px', borderRadius: '6px', fontSize: '11px', fontWeight: 700,
                    background: `${item.color}15`, color: item.color,
                    border: `1px solid ${item.color}30`,
                  }}>
                    {item.tag}
                  </span>
                  <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.55)' }}>{item.text}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Detection Categories */}
          <div style={{
            background: 'rgba(10,22,38,0.8)', border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: '14px', padding: '24px', backdropFilter: 'blur(8px)',
          }}>
            <div style={{
              fontFamily: '"Syne", sans-serif',
              fontSize: '15px', fontWeight: 700, color: '#fff', marginBottom: '16px',
            }}>
              Detection Categories
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[
                'Misconfigurations', 'Exposed Secrets', 'Insecure Defaults',
                'Compliance Violations', 'Access Control Issues', 'Network Security',
              ].map((cat, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{
                    width: '5px', height: '5px', borderRadius: '50%',
                    background: '#42a5f5', boxShadow: '0 0 6px rgba(66,165,245,0.4)',
                  }} />
                  <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.45)' }}>{cat}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Why Choose */}
          <div style={{
            background: 'linear-gradient(135deg, rgba(102,187,106,0.05), rgba(10,22,38,0.8))',
            border: '1px solid rgba(102,187,106,0.12)',
            borderRadius: '14px', padding: '24px', backdropFilter: 'blur(8px)',
          }}>
            <div style={{
              fontFamily: '"Syne", sans-serif',
              fontSize: '15px', fontWeight: 700, color: '#fff', marginBottom: '16px',
            }}>
              Why Choose CloudGuard AI?
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[
                'Multi-cloud support', 'IaC scanning', 'Compliance validation', 'Actionable remediation',
              ].map((item, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ color: '#66bb6a', fontSize: '14px' }}>✓</span>
                  <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.5)' }}>{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
