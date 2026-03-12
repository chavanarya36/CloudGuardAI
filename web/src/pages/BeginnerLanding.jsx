import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

/* ─── Tiny animated terminal component ─── */
function Terminal({ lines }) {
  const [displayed, setDisplayed] = useState([]);
  const [currentLine, setCurrentLine] = useState(0);
  const [currentChar, setCurrentChar] = useState(0);

  useEffect(() => {
    if (currentLine >= lines.length) return;
    const line = lines[currentLine];
    if (currentChar < line.length) {
      const t = setTimeout(() => setCurrentChar((c) => c + 1), 22);
      return () => clearTimeout(t);
    } else {
      const t = setTimeout(() => {
        setDisplayed((prev) => [...prev, line]);
        setCurrentLine((l) => l + 1);
        setCurrentChar(0);
      }, 280);
      return () => clearTimeout(t);
    }
  }, [currentLine, currentChar, lines]);

  const partial = currentLine < lines.length ? lines[currentLine].slice(0, currentChar) : '';

  return (
    <div style={{
      background: '#020c17',
      border: '1px solid rgba(66,165,245,0.2)',
      borderRadius: '10px',
      overflow: 'hidden',
      fontFamily: '"JetBrains Mono", "Fira Code", monospace',
      fontSize: '12px',
    }}>
      {/* Window bar */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '6px',
        padding: '10px 14px',
        background: 'rgba(255,255,255,0.03)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
      }}>
        <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#ef5350', opacity: 0.8 }} />
        <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#ffa726', opacity: 0.8 }} />
        <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#66bb6a', opacity: 0.8 }} />
        <span style={{ marginLeft: '8px', color: 'rgba(255,255,255,0.3)', fontSize: '11px' }}>cloudguard — scan</span>
      </div>
      {/* Output */}
      <div style={{ padding: '14px', minHeight: '120px', lineHeight: 1.7 }}>
        {displayed.map((line, i) => (
          <div key={i} style={{ color: line.startsWith('✓') ? '#66bb6a' : line.startsWith('⚠') ? '#ffa726' : line.startsWith('$') ? 'rgba(255,255,255,0.4)' : 'rgba(255,255,255,0.7)' }}>
            {line}
          </div>
        ))}
        {currentLine < lines.length && (
          <div style={{ color: 'rgba(255,255,255,0.7)' }}>
            {partial}<span style={{ animation: 'blink 1s step-end infinite', borderLeft: '1.5px solid #42a5f5', marginLeft: '1px' }}>&nbsp;</span>
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Threat category card ─── */
function ThreatCard({ icon, title, desc, color, delay }) {
  const [visible, setVisible] = useState(false);
  const ref = useRef();

  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setVisible(true); }, { threshold: 0.1 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);

  return (
    <div ref={ref} style={{
      opacity: visible ? 1 : 0,
      transform: visible ? 'translateY(0)' : 'translateY(20px)',
      transition: `opacity 0.5s ease ${delay}s, transform 0.5s ease ${delay}s`,
      background: 'rgba(10,22,38,0.8)',
      border: `1px solid ${color}26`,
      borderRadius: '14px',
      padding: '24px',
      backdropFilter: 'blur(8px)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      <div style={{
        position: 'absolute', top: 0, right: 0,
        width: '80px', height: '80px',
        background: `radial-gradient(circle at top right, ${color}12, transparent 70%)`,
      }} />
      <div style={{
        width: '44px', height: '44px', borderRadius: '10px',
        background: `${color}15`,
        border: `1px solid ${color}30`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        marginBottom: '14px',
        fontSize: '20px',
      }}>
        {icon}
      </div>
      <div style={{
        fontFamily: '"Syne", sans-serif',
        fontSize: '16px', fontWeight: 700, color: '#fff', marginBottom: '8px',
      }}>
        {title}
      </div>
      <div style={{ color: 'rgba(255,255,255,0.45)', fontSize: '13.5px', lineHeight: 1.65 }}>
        {desc}
      </div>
    </div>
  );
}

/* ─── Step item ─── */
function StepItem({ number, text, delay }) {
  const [visible, setVisible] = useState(false);
  const ref = useRef();
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setVisible(true); }, { threshold: 0.1 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);

  return (
    <div ref={ref} style={{
      display: 'flex', alignItems: 'flex-start', gap: '16px',
      opacity: visible ? 1 : 0, transform: visible ? 'translateX(0)' : 'translateX(-16px)',
      transition: `opacity 0.5s ease ${delay}s, transform 0.5s ease ${delay}s`,
    }}>
      <div style={{
        width: '32px', height: '32px', borderRadius: '50%', flexShrink: 0,
        background: 'linear-gradient(135deg, #1565c0, #42a5f5)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '13px', fontWeight: 700, color: '#fff',
        boxShadow: '0 0 16px rgba(66,165,245,0.3)',
      }}>
        {number}
      </div>
      <div style={{
        paddingTop: '6px',
        color: 'rgba(255,255,255,0.65)', fontSize: '14.5px', lineHeight: 1.6,
      }}>
        {text}
      </div>
    </div>
  );
}

/* ─── Main page ─── */
export default function BeginnerLanding() {
  const navigate = useNavigate();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 60);
    return () => clearTimeout(t);
  }, []);

  const handleStartScan = () => navigate('/scan');

  const handleTryDemo = () => {
    const demoTf = `resource "aws_s3_bucket" "demo" {
  bucket = "my-demo-bucket"
  acl    = "public-read"
}

resource "aws_security_group" "demo" {
  name = "demo-sg"
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "demo" {
  engine         = "mysql"
  instance_class = "db.t3.micro"
  password       = "SuperSecret123!"
  publicly_accessible = true
  storage_encrypted   = false
}
`;
    const file = new File([new Blob([demoTf], { type: 'text/plain' })], 'demo_insecure.tf', { type: 'text/plain' });
    window.__cloudguard_demo_file = file;
    localStorage.setItem('demo_scan_file', 'pending');
    navigate('/scan', { state: { demoFile: true } });
  };

  const THREATS = [
    { icon: '🔓', title: 'Misconfigurations', color: '#ef5350', desc: 'Open security groups, public S3 buckets, missing encryption — the classic cloud mistakes attackers exploit in minutes.', delay: 0 },
    { icon: '📋', title: 'Compliance Violations', color: '#ffa726', desc: 'CIS Benchmark, SOC 2, HIPAA — detect policy violations before your auditors and regulators do.', delay: 0.1 },
    { icon: '🔑', title: 'Secret Exposure', color: '#42a5f5', desc: 'Hard-coded API keys, passwords, and tokens that ended up embedded in your infrastructure code.', delay: 0.2 },
  ];

  const TERMINAL_LINES = [
    '$ cloudguard scan ./infrastructure/',
    'Scanning 3 files...',
    '✓ Rule engine: 47 checks passed',
    '⚠  CRITICAL  aws_s3_bucket.app — Public ACL enabled',
    '⚠  HIGH      aws_db_instance.prod — Password in plaintext',
    '⚠  HIGH      aws_security_group.web — Port 0-65535 open',
    '✓ Scan complete: 3 findings in 1.2s',
  ];

  return (
    <div style={{
      minHeight: '100vh',
      background: '#060e1a',
      fontFamily: '"DM Sans", "Helvetica Neue", sans-serif',
      position: 'relative',
      overflow: 'hidden',
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&family=Syne:wght@700;800&family=JetBrains+Mono:wght@400;500&display=swap');

        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
        @keyframes heroReveal {
          from { opacity: 0; transform: translateY(30px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-8px); }
        }
        @keyframes shimmer {
          0% { background-position: -200% center; }
          100% { background-position: 200% center; }
        }
        .hero-btn {
          cursor: pointer;
          transition: all 0.25s cubic-bezier(0.34,1.56,0.64,1);
        }
        .hero-btn:hover {
          transform: translateY(-3px) scale(1.03);
          box-shadow: 0 12px 40px rgba(66,165,245,0.35);
        }
        .hero-btn-outline {
          cursor: pointer;
          transition: all 0.25s cubic-bezier(0.34,1.56,0.64,1);
        }
        .hero-btn-outline:hover {
          transform: translateY(-3px) scale(1.03);
          background: rgba(206,147,216,0.12) !important;
          border-color: #ce93d8 !important;
        }
        .switch-link {
          cursor: pointer;
          transition: color 0.2s;
        }
        .switch-link:hover {
          color: rgba(255,255,255,0.6) !important;
        }
      `}</style>

      {/* Background layers */}
      <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0 }}>
        {/* Grid lines */}
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: `
            linear-gradient(rgba(66,165,245,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(66,165,245,0.03) 1px, transparent 1px)
          `,
          backgroundSize: '48px 48px',
        }} />
        {/* Glow orbs */}
        <div style={{
          position: 'absolute', top: '-120px', left: '20%',
          width: '500px', height: '500px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(66,165,245,0.07) 0%, transparent 70%)',
        }} />
        <div style={{
          position: 'absolute', top: '40%', right: '-100px',
          width: '400px', height: '400px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(206,147,216,0.05) 0%, transparent 70%)',
        }} />
      </div>

      {/* Nav bar */}
      <nav style={{
        position: 'sticky', top: 0, zIndex: 100,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 32px', height: '60px',
        background: 'rgba(6,14,26,0.8)', backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '28px', height: '28px',
            background: 'linear-gradient(135deg, #1565c0, #42a5f5)',
            borderRadius: '7px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 1L2 3.5v4.5c0 3.59 2.55 6.95 6 7.77 3.45-.82 6-4.18 6-7.77V3.5L8 1z" fill="white" opacity="0.9"/>
            </svg>
          </div>
          <span style={{
            fontFamily: '"Syne", sans-serif',
            fontWeight: 700, fontSize: '16px', color: '#fff',
          }}>
            CloudGuard <span style={{ color: '#42a5f5' }}>AI</span>
          </span>
        </div>
        <button
          className="switch-link"
          onClick={() => { localStorage.setItem('user_mode', 'expert'); navigate('/scan'); }}
          style={{
            background: 'none', border: '1px solid rgba(255,255,255,0.12)',
            borderRadius: '7px', padding: '6px 14px',
            color: 'rgba(255,255,255,0.35)', fontSize: '12px',
            fontFamily: '"DM Sans", sans-serif', cursor: 'pointer',
          }}
        >
          Switch to Expert mode →
        </button>
      </nav>

      <div style={{ position: 'relative', zIndex: 1 }}>

        {/* ── HERO ── */}
        <section style={{
          maxWidth: '900px', margin: '0 auto',
          padding: 'clamp(48px, 8vh, 96px) 24px 64px',
          textAlign: 'center',
          animation: mounted ? 'heroReveal 0.8s ease both' : 'none',
        }}>
          {/* Badge */}
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: '8px',
            padding: '6px 16px', borderRadius: '99px', marginBottom: '32px',
            background: 'rgba(66,165,245,0.08)',
            border: '1px solid rgba(66,165,245,0.2)',
          }}>
            <div style={{
              width: '6px', height: '6px', borderRadius: '50%',
              background: '#66bb6a', boxShadow: '0 0 6px #66bb6a',
            }} />
            <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.6)', fontWeight: 500, letterSpacing: '0.05em' }}>
              Guided Security Overview
            </span>
          </div>

          {/* Headline */}
          <h1 style={{
            fontFamily: '"Syne", sans-serif',
            fontSize: 'clamp(36px, 6vw, 64px)',
            fontWeight: 800, color: '#fff', margin: '0 0 20px',
            lineHeight: 1.08, letterSpacing: '-0.03em',
          }}>
            Catch cloud security issues
            <br />
            <span style={{
              background: 'linear-gradient(90deg, #42a5f5, #80d6ff, #42a5f5)',
              backgroundSize: '200% auto',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              animation: 'shimmer 3s linear infinite',
            }}>
              before they become incidents.
            </span>
          </h1>

          <p style={{
            color: 'rgba(255,255,255,0.45)', fontSize: 'clamp(15px, 2vw, 18px)',
            maxWidth: '560px', margin: '0 auto 40px', lineHeight: 1.7,
            fontWeight: 400,
          }}>
            CloudGuard scans your Infrastructure-as-Code files — Terraform, CloudFormation, Kubernetes YAML —
            and finds security problems <em style={{ color: 'rgba(255,255,255,0.65)', fontStyle: 'italic' }}>before</em> you deploy.
          </p>

          {/* CTAs */}
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button className="hero-btn" onClick={handleStartScan} style={{
              padding: '14px 32px',
              background: 'linear-gradient(135deg, #1976d2, #42a5f5)',
              border: 'none', borderRadius: '10px',
              color: '#fff', fontSize: '15px', fontWeight: 600,
              fontFamily: '"DM Sans", sans-serif',
              display: 'flex', alignItems: 'center', gap: '8px',
            }}>
              Start Security Scan
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M3.5 8h9M8.5 5l3.5 3-3.5 3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
            <button className="hero-btn-outline" onClick={handleTryDemo} style={{
              padding: '14px 32px',
              background: 'rgba(206,147,216,0.07)',
              border: '1px solid rgba(206,147,216,0.3)',
              borderRadius: '10px',
              color: '#ce93d8', fontSize: '15px', fontWeight: 600,
              fontFamily: '"DM Sans", sans-serif',
              display: 'flex', alignItems: 'center', gap: '8px',
            }}>
              Try Demo Infrastructure
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M2 10l2-2 2 2 4-6 2 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
        </section>

        {/* ── TERMINAL DEMO ── */}
        <section style={{ maxWidth: '680px', margin: '0 auto', padding: '0 24px 80px' }}>
          <Terminal lines={TERMINAL_LINES} />
        </section>

        {/* ── WHAT WE DETECT ── */}
        <section style={{ maxWidth: '900px', margin: '0 auto', padding: '0 24px 80px' }}>
          <div style={{ marginBottom: '32px' }}>
            <div style={{
              fontSize: '11px', letterSpacing: '0.2em', textTransform: 'uppercase',
              color: 'rgba(66,165,245,0.7)', fontWeight: 600, marginBottom: '10px',
            }}>
              Threat Detection
            </div>
            <h2 style={{
              fontFamily: '"Syne", sans-serif',
              fontSize: 'clamp(22px, 3vw, 28px)', fontWeight: 700,
              color: '#fff', margin: 0, letterSpacing: '-0.02em',
            }}>
              What does CloudGuard detect?
            </h2>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '16px',
          }}>
            {THREATS.map((t) => (
              <ThreatCard key={t.title} {...t} />
            ))}
          </div>
        </section>

        {/* ── HOW IT WORKS ── */}
        <section style={{ maxWidth: '900px', margin: '0 auto', padding: '0 24px 80px' }}>
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '40px', alignItems: 'center',
          }}>
            {/* Left: steps */}
            <div>
              <div style={{
                fontSize: '11px', letterSpacing: '0.2em', textTransform: 'uppercase',
                color: 'rgba(66,165,245,0.7)', fontWeight: 600, marginBottom: '10px',
              }}>
                How it works
              </div>
              <h2 style={{
                fontFamily: '"Syne", sans-serif',
                fontSize: 'clamp(22px, 3vw, 28px)', fontWeight: 700,
                color: '#fff', margin: '0 0 28px', letterSpacing: '-0.02em',
              }}>
                Three steps to a secure infrastructure
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {[
                  { n: '1', text: 'Upload a Terraform, CloudFormation, or Kubernetes YAML file.' },
                  { n: '2', text: 'CloudGuard runs rule-based, ML, and LLM scanners simultaneously.' },
                  { n: '3', text: 'Review prioritized findings with AI-generated, plain-language explanations.' },
                ].map((step, i) => (
                  <StepItem key={step.n} number={step.n} text={step.text} delay={i * 0.1} />
                ))}
              </div>
            </div>

            {/* Right: IaC explainer card */}
            <div style={{
              background: 'rgba(10,22,38,0.8)',
              border: '1px solid rgba(206,147,216,0.15)',
              borderRadius: '14px',
              padding: '28px',
              backdropFilter: 'blur(8px)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
                <div style={{
                  width: '34px', height: '34px', borderRadius: '8px',
                  background: 'rgba(206,147,216,0.12)',
                  border: '1px solid rgba(206,147,216,0.25)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '16px',
                }}>
                  📄
                </div>
                <span style={{
                  fontFamily: '"Syne", sans-serif',
                  fontWeight: 700, color: '#ce93d8', fontSize: '15px',
                }}>
                  What is Infrastructure-as-Code?
                </span>
              </div>
              <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '13.5px', lineHeight: 1.7, margin: 0 }}>
                Instead of clicking through the AWS console, teams define cloud resources in code files —
                Terraform <code style={{ color: '#ce93d8', background: 'rgba(206,147,216,0.1)', padding: '1px 5px', borderRadius: '4px' }}>.tf</code>,
                CloudFormation YAML, or Kubernetes manifests.
                <br /><br />
                This makes infrastructure reproducible — but a single mistake can create a real vulnerability.
                CloudGuard catches those mistakes before they reach production.
              </p>
            </div>
          </div>
        </section>

        {/* ── FINAL CTA ── */}
        <section style={{ maxWidth: '900px', margin: '0 auto', padding: '0 24px 96px' }}>
          <div style={{
            background: 'linear-gradient(135deg, rgba(21,101,192,0.15) 0%, rgba(10,22,38,0.8) 100%)',
            border: '1px solid rgba(66,165,245,0.2)',
            borderRadius: '20px', padding: '48px 40px',
            textAlign: 'center',
            position: 'relative', overflow: 'hidden',
          }}>
            <div style={{
              position: 'absolute', top: '-60px', left: '50%', transform: 'translateX(-50%)',
              width: '300px', height: '200px',
              background: 'radial-gradient(ellipse, rgba(66,165,245,0.12), transparent 70%)',
            }} />
            <h2 style={{
              fontFamily: '"Syne", sans-serif',
              fontSize: 'clamp(24px, 3vw, 32px)', fontWeight: 800,
              color: '#fff', margin: '0 0 12px', letterSpacing: '-0.02em',
            }}>
              Ready to scan your infrastructure?
            </h2>
            <p style={{ color: 'rgba(255,255,255,0.45)', margin: '0 0 32px', fontSize: '15px' }}>
              No setup required. Upload a file and get results in seconds.
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
              <button className="hero-btn" onClick={handleStartScan} style={{
                padding: '14px 36px',
                background: 'linear-gradient(135deg, #1976d2, #42a5f5)',
                border: 'none', borderRadius: '10px',
                color: '#fff', fontSize: '15px', fontWeight: 600,
                fontFamily: '"DM Sans", sans-serif',
              }}>
                Start Security Scan →
              </button>
              <button className="hero-btn-outline" onClick={handleTryDemo} style={{
                padding: '14px 28px',
                background: 'transparent',
                border: '1px solid rgba(255,255,255,0.15)',
                borderRadius: '10px',
                color: 'rgba(255,255,255,0.5)', fontSize: '15px', fontWeight: 500,
                fontFamily: '"DM Sans", sans-serif',
              }}>
                Try demo file
              </button>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
