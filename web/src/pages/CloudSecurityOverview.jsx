import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

/* ─── Floating particles background ─── */
function ParticleField() {
  const [particles] = useState(() =>
    Array.from({ length: 40 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 2.5 + 1,
      duration: Math.random() * 20 + 15,
      delay: Math.random() * 10,
      opacity: Math.random() * 0.15 + 0.05,
    }))
  );

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      {particles.map((p) => (
        <div key={p.id} style={{
          position: 'absolute',
          left: `${p.x}%`, top: `${p.y}%`,
          width: `${p.size}px`, height: `${p.size}px`,
          borderRadius: '50%',
          background: 'rgba(66,165,245,0.6)',
          boxShadow: '0 0 4px rgba(66,165,245,0.4)',
          opacity: p.opacity,
          animation: `float-particle ${p.duration}s ease-in-out ${p.delay}s infinite alternate`,
        }} />
      ))}
    </div>
  );
}

/* ─── Animated card with intersection observer ─── */
function ProblemCard({ icon, title, subtitle, description, threats, status, statusColor, cta, ctaAction, accent, delay, isHighlighted }) {
  const [visible, setVisible] = useState(false);
  const [hovered, setHovered] = useState(false);
  const ref = useRef();

  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setVisible(true); }, { threshold: 0.15 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={ctaAction}
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(30px)',
        transition: `opacity 0.6s ease ${delay}s, transform 0.6s ease ${delay}s, box-shadow 0.3s ease, border-color 0.3s ease`,
        cursor: ctaAction ? 'pointer' : 'default',
      }}
    >
      <div style={{
        position: 'relative', overflow: 'hidden',
        background: isHighlighted
          ? (hovered ? 'linear-gradient(135deg, rgba(13,71,161,0.25) 0%, rgba(10,22,38,0.95) 100%)' : 'linear-gradient(135deg, rgba(13,71,161,0.15) 0%, rgba(10,22,38,0.9) 100%)')
          : (hovered ? 'rgba(15,28,48,0.95)' : 'rgba(10,22,38,0.85)'),
        border: `1px solid ${isHighlighted
          ? (hovered ? 'rgba(66,165,245,0.5)' : 'rgba(66,165,245,0.3)')
          : (hovered ? `${accent}55` : 'rgba(255,255,255,0.07)')}`,
        borderRadius: '18px',
        padding: '32px',
        backdropFilter: 'blur(12px)',
        boxShadow: hovered
          ? `0 20px 60px ${accent}20, 0 0 0 1px ${accent}30`
          : isHighlighted ? `0 8px 32px rgba(66,165,245,0.1)` : '0 4px 24px rgba(0,0,0,0.3)',
        transition: 'all 0.35s ease',
        height: '100%',
        display: 'flex', flexDirection: 'column',
      }}>
        {/* Scanning line on hover */}
        {hovered && (
          <div style={{
            position: 'absolute', left: 0, right: 0, height: '80px',
            background: `linear-gradient(180deg, transparent, ${accent}12, transparent)`,
            animation: 'scanline 2.5s linear infinite',
            pointerEvents: 'none',
          }} />
        )}

        {/* Top corner glow */}
        <div style={{
          position: 'absolute', top: 0, right: 0,
          width: '120px', height: '120px',
          background: `radial-gradient(circle at top right, ${accent}18, transparent 70%)`,
          borderRadius: '0 18px 0 0',
        }} />

        {/* Highlighted badge */}
        {isHighlighted && (
          <div style={{
            position: 'absolute', top: '16px', right: '16px',
            display: 'flex', alignItems: 'center', gap: '5px',
            padding: '4px 12px', borderRadius: '99px',
            background: 'rgba(66,165,245,0.12)',
            border: '1px solid rgba(66,165,245,0.3)',
          }}>
            <span style={{ fontSize: '10px' }}>⭐</span>
            <span style={{ fontSize: '10px', fontWeight: 700, color: '#42a5f5', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              Our Solution
            </span>
          </div>
        )}

        {/* Icon */}
        <div style={{
          width: '56px', height: '56px', borderRadius: '14px',
          background: `${accent}15`,
          border: `1px solid ${accent}30`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          marginBottom: '20px', fontSize: '26px',
          transition: 'transform 0.3s ease',
          transform: hovered ? 'scale(1.08)' : 'scale(1)',
        }}>
          {icon}
        </div>

        {/* Title + Subtitle */}
        <div style={{
          fontFamily: '"Syne", sans-serif',
          fontSize: '20px', fontWeight: 700, color: '#fff',
          lineHeight: 1.2, marginBottom: '4px',
        }}>
          {title}
        </div>
        <div style={{
          fontSize: '12px', color: `${accent}`,
          fontWeight: 600, letterSpacing: '0.05em', marginBottom: '14px',
          textTransform: 'uppercase',
        }}>
          {subtitle}
        </div>

        {/* Description */}
        <p style={{
          color: 'rgba(255,255,255,0.5)', fontSize: '14px',
          lineHeight: 1.7, margin: '0 0 18px 0',
        }}>
          {description}
        </p>

        {/* Threat examples */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '20px', flex: 1 }}>
          {threats.map((t) => (
            <span key={t} style={{
              padding: '4px 12px', borderRadius: '99px',
              fontSize: '11px', fontWeight: 500,
              background: `${accent}10`,
              border: `1px solid ${accent}25`,
              color: `${accent}`,
              letterSpacing: '0.02em',
            }}>
              {t}
            </span>
          ))}
        </div>

        {/* Status or action */}
        <div style={{
          padding: '12px 16px', borderRadius: '10px',
          background: statusColor ? `${statusColor}08` : `${accent}08`,
          border: `1px solid ${statusColor ? `${statusColor}20` : `${accent}20`}`,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <span style={{ fontSize: '12px', color: statusColor || accent, fontWeight: 600 }}>
            {status}
          </span>
          {cta && (
            <span style={{
              fontSize: '12px', fontWeight: 600, color: accent,
              display: 'flex', alignItems: 'center', gap: '4px',
            }}>
              {cta}
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M3 7h8M7.5 4l3.5 3-3.5 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

/* ─── Main Page ─── */
export default function CloudSecurityOverview() {
  const navigate = useNavigate();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 60);
    return () => clearTimeout(t);
  }, []);

  const problems = [
    {
      icon: '💻',
      title: 'Application Security',
      subtitle: 'Code-level Vulnerabilities',
      description: 'Vulnerabilities inside application code — SQL injection, insecure APIs, cross-site scripting, and authentication flaws that attackers exploit to compromise your applications.',
      threats: ['SQL Injection', 'Cross-Site Scripting', 'Insecure Auth', 'API Abuse'],
      status: 'Handled by AppSec tools (SAST/DAST)',
      statusColor: 'rgba(255,255,255,0.35)',
      accent: '#ffa726',
      isHighlighted: false,
      delay: 0.1,
    },
    {
      icon: '🏗️',
      title: 'Infrastructure Security',
      subtitle: 'Pre-deployment Protection',
      description: 'Misconfigured cloud infrastructure that silently exposes resources to attackers. CloudGuardAI analyzes Infrastructure-as-Code files (Terraform, CloudFormation) to detect these vulnerabilities before deployment.',
      threats: ['Public S3 Buckets', 'Open Security Groups', 'Unencrypted DBs', 'Excessive IAM Perms'],
      status: 'CloudGuardAI Solution',
      cta: 'Explore Solution',
      accent: '#42a5f5',
      isHighlighted: true,
      delay: 0.2,
      action: () => navigate('/landing'),
    },
    {
      icon: '⚡',
      title: 'Runtime Security',
      subtitle: 'Live Environment Threats',
      description: 'Threats that occur after infrastructure is already running in the cloud — container escapes, lateral movement, runtime malware, and privilege escalation attacks.',
      threats: ['Container Escapes', 'Malware', 'Privilege Escalation', 'Lateral Movement'],
      status: 'Handled by runtime monitoring tools',
      statusColor: 'rgba(255,255,255,0.35)',
      accent: '#ef5350',
      isHighlighted: false,
      delay: 0.3,
    },
    {
      icon: '🔐',
      title: 'Identity & Access Security',
      subtitle: 'Authentication & Authorization',
      description: 'Issues with authentication, access control, and identity permissions — weak IAM policies, overly permissive roles, and credential leakage across cloud environments.',
      threats: ['Weak IAM Policies', 'Overpermissive Roles', 'Credential Leakage', 'MFA Bypass'],
      status: 'Handled by identity management systems',
      statusColor: 'rgba(255,255,255,0.35)',
      accent: '#ce93d8',
      isHighlighted: false,
      delay: 0.4,
    },
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
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Syne:wght@700;800&display=swap');

        @keyframes heroReveal {
          from { opacity: 0; transform: translateY(30px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes scanline {
          0%   { transform: translateY(-100%); }
          100% { transform: translateY(500%); }
        }
        @keyframes float-particle {
          0%   { transform: translate(0, 0); }
          100% { transform: translate(10px, -15px); }
        }
        @keyframes shimmer {
          0%   { background-position: -200% center; }
          100% { background-position: 200% center; }
        }
        @keyframes pulse-dot {
          0%, 100% { opacity: 0.6; transform: scale(1); }
          50%      { opacity: 1; transform: scale(1.3); }
        }
        .back-btn {
          cursor: pointer;
          transition: all 0.2s ease;
        }
        .back-btn:hover {
          background: rgba(255,255,255,0.06) !important;
          border-color: rgba(255,255,255,0.2) !important;
        }
      `}</style>

      {/* Background layers */}
      <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0 }}>
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: `
            linear-gradient(rgba(66,165,245,0.025) 1px, transparent 1px),
            linear-gradient(90deg, rgba(66,165,245,0.025) 1px, transparent 1px)
          `,
          backgroundSize: '56px 56px',
        }} />
        <div style={{
          position: 'absolute', top: '-100px', left: '30%',
          width: '600px', height: '600px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(66,165,245,0.06) 0%, transparent 70%)',
        }} />
        <div style={{
          position: 'absolute', bottom: '-150px', right: '10%',
          width: '500px', height: '500px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(206,147,216,0.04) 0%, transparent 70%)',
        }} />
        <ParticleField />
      </div>

      {/* Nav bar */}
      <nav style={{
        position: 'sticky', top: 0, zIndex: 100,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 32px', height: '60px',
        background: 'rgba(6,14,26,0.85)', backdropFilter: 'blur(20px)',
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
        <button className="back-btn" onClick={() => navigate('/welcome')} style={{
          background: 'none', border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '7px', padding: '6px 14px',
          color: 'rgba(255,255,255,0.4)', fontSize: '12px',
          fontFamily: '"DM Sans", sans-serif',
        }}>
          ← Back to Mode Selection
        </button>
      </nav>

      <div style={{ position: 'relative', zIndex: 1 }}>

        {/* ── HERO ── */}
        <section style={{
          maxWidth: '960px', margin: '0 auto',
          padding: 'clamp(48px, 6vh, 80px) 24px 56px',
          textAlign: 'center',
          animation: mounted ? 'heroReveal 0.8s ease both' : 'none',
        }}>
          {/* Badge */}
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: '8px',
            padding: '6px 16px', borderRadius: '99px', marginBottom: '28px',
            background: 'rgba(66,165,245,0.08)',
            border: '1px solid rgba(66,165,245,0.2)',
          }}>
            <div style={{
              width: '6px', height: '6px', borderRadius: '50%',
              background: '#66bb6a', boxShadow: '0 0 6px #66bb6a',
              animation: 'pulse-dot 2s ease-in-out infinite',
            }} />
            <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.6)', fontWeight: 500, letterSpacing: '0.06em' }}>
              Cloud Security Landscape
            </span>
          </div>

          <h1 style={{
            fontFamily: '"Syne", sans-serif',
            fontSize: 'clamp(32px, 5vw, 52px)',
            fontWeight: 800, color: '#fff', margin: '0 0 18px',
            lineHeight: 1.1, letterSpacing: '-0.03em',
          }}>
            Understanding{' '}
            <span style={{
              background: 'linear-gradient(90deg, #42a5f5, #80d6ff, #42a5f5)',
              backgroundSize: '200% auto',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              animation: 'shimmer 3s linear infinite',
            }}>
              Cloud Security Risks
            </span>
          </h1>

          <p style={{
            color: 'rgba(255,255,255,0.45)', fontSize: 'clamp(14px, 2vw, 17px)',
            maxWidth: '640px', margin: '0 auto 20px', lineHeight: 1.7,
          }}>
            Modern cloud environments face several categories of security risks.
            CloudGuardAI focuses on detecting infrastructure vulnerabilities{' '}
            <em style={{ color: 'rgba(255,255,255,0.6)', fontStyle: 'italic' }}>before</em> they are deployed.
          </p>

          {/* Category flow indicator */}
          <div style={{
            display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '12px',
            flexWrap: 'wrap', marginTop: '8px',
          }}>
            {['App Security', 'Infrastructure', 'Runtime', 'Identity'].map((label, i) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  padding: '4px 14px', borderRadius: '99px',
                  background: i === 1 ? 'rgba(66,165,245,0.15)' : 'rgba(255,255,255,0.04)',
                  border: `1px solid ${i === 1 ? 'rgba(66,165,245,0.3)' : 'rgba(255,255,255,0.06)'}`,
                  color: i === 1 ? '#42a5f5' : 'rgba(255,255,255,0.3)',
                  fontSize: '11px', fontWeight: 600,
                }}>
                  {label}
                </div>
                {i < 3 && <span style={{ color: 'rgba(255,255,255,0.1)', fontSize: '14px' }}>→</span>}
              </div>
            ))}
          </div>
        </section>

        {/* ── PROBLEM CARDS ── */}
        <section style={{ maxWidth: '1040px', margin: '0 auto', padding: '0 24px 64px' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '20px',
          }}>
            {problems.map((p) => (
              <ProblemCard
                key={p.title}
                icon={p.icon}
                title={p.title}
                subtitle={p.subtitle}
                description={p.description}
                threats={p.threats}
                status={p.status}
                statusColor={p.statusColor}
                cta={p.cta}
                ctaAction={p.action}
                accent={p.accent}
                delay={p.delay}
                isHighlighted={p.isHighlighted}
              />
            ))}
          </div>
        </section>

        {/* ── WHY THIS MATTERS ── */}
        <section style={{ maxWidth: '800px', margin: '0 auto', padding: '0 24px 80px' }}>
          <div style={{
            background: 'linear-gradient(135deg, rgba(21,101,192,0.12) 0%, rgba(10,22,38,0.85) 100%)',
            border: '1px solid rgba(66,165,245,0.18)',
            borderRadius: '20px', padding: '40px 36px',
            textAlign: 'center',
            position: 'relative', overflow: 'hidden',
          }}>
            <div style={{
              position: 'absolute', top: '-60px', left: '50%', transform: 'translateX(-50%)',
              width: '300px', height: '200px',
              background: 'radial-gradient(ellipse, rgba(66,165,245,0.10), transparent 70%)',
            }} />

            <div style={{
              fontSize: '11px', letterSpacing: '0.2em', textTransform: 'uppercase',
              color: 'rgba(66,165,245,0.7)', fontWeight: 600, marginBottom: '12px',
            }}>
              Problem → Solution
            </div>
            <h2 style={{
              fontFamily: '"Syne", sans-serif',
              fontSize: 'clamp(22px, 3vw, 30px)', fontWeight: 800,
              color: '#fff', margin: '0 0 14px', letterSpacing: '-0.02em',
            }}>
              Why Infrastructure Security Matters
            </h2>
            <p style={{
              color: 'rgba(255,255,255,0.45)', fontSize: '15px',
              maxWidth: '520px', margin: '0 auto 28px', lineHeight: 1.7,
            }}>
              A single misconfigured Terraform file can expose your entire cloud environment.
              CloudGuardAI catches these issues in your IaC files — before <code style={{
                color: '#42a5f5', background: 'rgba(66,165,245,0.1)',
                padding: '1px 6px', borderRadius: '4px', fontSize: '13px',
              }}>terraform apply</code> runs.
            </p>

            {/* Visual flow */}
            <div style={{
              display: 'flex', justifyContent: 'center', alignItems: 'center',
              gap: '16px', flexWrap: 'wrap', marginBottom: '32px',
            }}>
              {[
                { label: 'Write IaC', icon: '📝' },
                { label: 'Scan with CloudGuard', icon: '🔍' },
                { label: 'Fix Issues', icon: '🔧' },
                { label: 'Deploy Safely', icon: '🚀' },
              ].map((step, i) => (
                <div key={step.label} style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px',
                  }}>
                    <div style={{
                      width: '44px', height: '44px', borderRadius: '12px',
                      background: 'rgba(66,165,245,0.08)',
                      border: '1px solid rgba(66,165,245,0.2)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '20px',
                    }}>
                      {step.icon}
                    </div>
                    <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)', fontWeight: 500 }}>
                      {step.label}
                    </span>
                  </div>
                  {i < 3 && <span style={{ color: 'rgba(66,165,245,0.3)', fontSize: '18px', marginBottom: '16px' }}>→</span>}
                </div>
              ))}
            </div>

            <button
              onClick={() => navigate('/landing')}
              style={{
                padding: '14px 36px',
                background: 'linear-gradient(135deg, #1976d2, #42a5f5)',
                border: 'none', borderRadius: '10px',
                color: '#fff', fontSize: '15px', fontWeight: 600,
                fontFamily: '"DM Sans", sans-serif',
                cursor: 'pointer',
                transition: 'all 0.25s cubic-bezier(0.34,1.56,0.64,1)',
                display: 'inline-flex', alignItems: 'center', gap: '8px',
              }}
              onMouseEnter={(e) => { e.target.style.transform = 'translateY(-3px) scale(1.03)'; e.target.style.boxShadow = '0 12px 40px rgba(66,165,245,0.35)'; }}
              onMouseLeave={(e) => { e.target.style.transform = ''; e.target.style.boxShadow = ''; }}
            >
              Explore CloudGuardAI Solution
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M3.5 8h9M8.5 5l3.5 3-3.5 3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
