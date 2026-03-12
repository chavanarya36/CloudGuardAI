import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const GRID_COLS = 24;
const GRID_ROWS = 14;

function HexGrid() {
  const [active, setActive] = useState([]);

  useEffect(() => {
    const interval = setInterval(() => {
      const count = Math.floor(Math.random() * 4) + 1;
      const next = [];
      for (let i = 0; i < count; i++) {
        next.push({
          id: Math.random(),
          col: Math.floor(Math.random() * GRID_COLS),
          row: Math.floor(Math.random() * GRID_ROWS),
        });
      }
      setActive((prev) => [...prev.slice(-20), ...next]);
    }, 400);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{
      position: 'absolute', inset: 0, overflow: 'hidden', opacity: 0.35,
      display: 'grid',
      gridTemplateColumns: `repeat(${GRID_COLS}, 1fr)`,
      gridTemplateRows: `repeat(${GRID_ROWS}, 1fr)`,
      gap: '1px',
      pointerEvents: 'none',
    }}>
      {Array.from({ length: GRID_COLS * GRID_ROWS }).map((_, i) => {
        const col = i % GRID_COLS;
        const row = Math.floor(i / GRID_COLS);
        const isActive = active.some((a) => a.col === col && a.row === row);
        return (
          <div key={i} style={{
            border: '1px solid rgba(66,165,245,0.08)',
            borderRadius: '2px',
            background: isActive ? 'rgba(66,165,245,0.18)' : 'transparent',
            transition: 'background 0.6s ease',
          }} />
        );
      })}
    </div>
  );
}

export default function UserModeSelection() {
  const navigate = useNavigate();
  const [hoveredCard, setHoveredCard] = useState(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 60);
    return () => clearTimeout(t);
  }, []);

  const selectMode = (mode) => {
    localStorage.setItem('user_mode', mode);
    navigate(mode === 'expert' ? '/scan' : '/landing');
  };

  const cards = [
    {
      id: 'expert',
      label: 'Security Engineer',
      sublabel: 'Expert Mode',
      description: 'Jump straight to scanning. Upload Terraform, CloudFormation, or Kubernetes files and get comprehensive security findings instantly.',
      cta: 'Open Scanner',
      accent: '#42a5f5',
      accentDim: 'rgba(66,165,245,0.12)',
      accentBorder: 'rgba(66,165,245,0.35)',
      accentGlow: 'rgba(66,165,245,0.2)',
      icon: (
        <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
          <path d="M18 3L4 9v9c0 8.28 5.96 16.02 14 18 8.04-1.98 14-9.72 14-18V9L18 3z" fill="rgba(66,165,245,0.15)" stroke="#42a5f5" strokeWidth="1.5"/>
          <path d="M13 18l3.5 3.5L23 15" stroke="#42a5f5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      ),
      tags: ['Terraform', 'K8s', 'CloudFormation'],
    },
    {
      id: 'beginner',
      label: 'Developer',
      sublabel: 'Guided Mode',
      description: 'New to infrastructure security? Get a guided walkthrough of what CloudGuard detects, why it matters, and how to act on findings.',
      cta: 'Start Learning',
      accent: '#ce93d8',
      accentDim: 'rgba(206,147,216,0.12)',
      accentBorder: 'rgba(206,147,216,0.35)',
      accentGlow: 'rgba(206,147,216,0.2)',
      icon: (
        <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
          <circle cx="18" cy="18" r="14" fill="rgba(206,147,216,0.12)" stroke="#ce93d8" strokeWidth="1.5"/>
          <path d="M14 13c0-2.21 1.79-4 4-4s4 1.79 4 4c0 1.86-1.27 3.43-3 3.87V19h-2v-2.13C15.27 16.43 14 14.86 14 13z" fill="#ce93d8"/>
          <rect x="17" y="22" width="2" height="2" rx="1" fill="#ce93d8"/>
        </svg>
      ),
      tags: ['Guided', 'Explained', 'Beginner-friendly'],
    },
  ];

  return (
    <div style={{
      minHeight: '100vh',
      background: '#060e1a',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: '"DM Sans", "Helvetica Neue", sans-serif',
      position: 'relative',
      overflow: 'hidden',
      padding: '32px 16px',
    }}>
      {/* Google Fonts */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Syne:wght@700;800&display=swap');

        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(24px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes scanline {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(400%); }
        }
        @keyframes pulse-ring {
          0%, 100% { transform: scale(1); opacity: 0.6; }
          50% { transform: scale(1.08); opacity: 1; }
        }
        @keyframes orbit {
          from { transform: rotate(0deg) translateX(52px) rotate(0deg); }
          to { transform: rotate(360deg) translateX(52px) rotate(-360deg); }
        }
        .mode-card {
          cursor: pointer;
          transition: transform 0.35s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.35s ease;
          animation: fadeUp 0.7s ease both;
        }
        .mode-card:hover {
          transform: translateY(-6px) scale(1.01);
        }
        .cta-btn {
          transition: all 0.22s ease;
          cursor: pointer;
        }
        .cta-btn:hover {
          filter: brightness(1.15);
          transform: scale(1.03);
        }
        .tag-pill {
          font-size: 11px;
          padding: 3px 10px;
          border-radius: 99px;
          font-weight: 500;
          letter-spacing: 0.03em;
        }
      `}</style>

      {/* Background effects */}
      <div style={{ position: 'absolute', inset: 0 }}>
        {/* Radial glow center */}
        <div style={{
          position: 'absolute', top: '40%', left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '600px', height: '400px',
          background: 'radial-gradient(ellipse, rgba(66,165,245,0.06) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />
        {/* Top edge line */}
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, height: '1px',
          background: 'linear-gradient(90deg, transparent, rgba(66,165,245,0.4), transparent)',
        }} />
        <HexGrid />
      </div>

      <div style={{ position: 'relative', zIndex: 1, width: '100%', maxWidth: '820px' }}>

        {/* Logo mark */}
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          marginBottom: '48px',
          opacity: mounted ? 1 : 0,
          transition: 'opacity 0.6s ease',
        }}>
          {/* Animated shield logo */}
          <div style={{ position: 'relative', width: '80px', height: '80px', marginBottom: '24px' }}>
            <div style={{
              position: 'absolute', inset: 0,
              borderRadius: '50%',
              border: '1px solid rgba(66,165,245,0.25)',
              animation: 'pulse-ring 3s ease-in-out infinite',
            }} />
            <div style={{
              position: 'absolute', inset: '8px',
              borderRadius: '50%',
              border: '1px solid rgba(66,165,245,0.15)',
              animation: 'pulse-ring 3s ease-in-out infinite 0.5s',
            }} />
            <div style={{
              position: 'absolute', inset: '16px',
              background: 'linear-gradient(135deg, #0d47a1, #1976d2)',
              borderRadius: '50%',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 0 24px rgba(66,165,245,0.35)',
            }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L3 6v6c0 5.52 3.97 10.68 9 12 5.03-1.32 9-6.48 9-12V6L12 2z" fill="white" opacity="0.9"/>
                <path d="M9 12l2 2 4-4" stroke="#1976d2" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          </div>

          <div style={{
            fontSize: '11px', letterSpacing: '0.25em', textTransform: 'uppercase',
            color: 'rgba(66,165,245,0.7)', fontWeight: 600, marginBottom: '10px',
          }}>
            Infrastructure Security
          </div>
          <h1 style={{
            fontFamily: '"Syne", sans-serif',
            fontSize: 'clamp(32px, 5vw, 48px)',
            fontWeight: 800, color: '#fff', margin: 0,
            letterSpacing: '-0.02em', lineHeight: 1.1,
            textAlign: 'center',
          }}>
            CloudGuard <span style={{ color: '#42a5f5' }}>AI</span>
          </h1>
          <p style={{
            color: 'rgba(255,255,255,0.45)', fontSize: '15px', marginTop: '10px',
            fontWeight: 400, textAlign: 'center',
          }}>
            Choose how you'd like to get started
          </p>
        </div>

        {/* Cards */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '20px',
          marginBottom: '32px',
        }}>
          {cards.map((card, i) => (
            <div
              key={card.id}
              className="mode-card"
              style={{ animationDelay: `${0.15 + i * 0.12}s` }}
              onClick={() => selectMode(card.id)}
              onMouseEnter={() => setHoveredCard(card.id)}
              onMouseLeave={() => setHoveredCard(null)}
            >
              <div style={{
                background: hoveredCard === card.id
                  ? `linear-gradient(135deg, #0c1f38 0%, #0f2744 100%)`
                  : 'rgba(10,22,38,0.9)',
                border: `1px solid ${hoveredCard === card.id ? card.accentBorder : 'rgba(255,255,255,0.07)'}`,
                borderRadius: '16px',
                padding: '32px',
                position: 'relative',
                overflow: 'hidden',
                backdropFilter: 'blur(12px)',
                boxShadow: hoveredCard === card.id
                  ? `0 20px 60px ${card.accentGlow}, 0 0 0 1px ${card.accentBorder}`
                  : '0 4px 24px rgba(0,0,0,0.4)',
                transition: 'all 0.35s ease',
                minHeight: '280px',
                display: 'flex', flexDirection: 'column',
              }}>
                {/* Scanning line effect on hover */}
                {hoveredCard === card.id && (
                  <div style={{
                    position: 'absolute', left: 0, right: 0, height: '60px',
                    background: `linear-gradient(180deg, transparent, ${card.accentDim}, transparent)`,
                    animation: 'scanline 2s linear infinite',
                    pointerEvents: 'none',
                  }} />
                )}

                {/* Top corner accent */}
                <div style={{
                  position: 'absolute', top: 0, right: 0,
                  width: '100px', height: '100px',
                  background: `radial-gradient(circle at top right, ${card.accentDim}, transparent 70%)`,
                  borderRadius: '0 16px 0 0',
                }} />

                {/* Badge */}
                <div style={{
                  display: 'inline-flex', alignItems: 'center', gap: '6px',
                  marginBottom: '20px', alignSelf: 'flex-start',
                }}>
                  <div style={{
                    width: '6px', height: '6px', borderRadius: '50%',
                    background: card.accent, boxShadow: `0 0 6px ${card.accent}`,
                  }} />
                  <span style={{
                    fontSize: '11px', fontWeight: 600, color: card.accent,
                    letterSpacing: '0.1em', textTransform: 'uppercase',
                  }}>
                    {card.sublabel}
                  </span>
                </div>

                {/* Icon + Title */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '16px' }}>
                  <div style={{
                    width: '56px', height: '56px', borderRadius: '12px',
                    background: card.accentDim,
                    border: `1px solid ${card.accentBorder}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0,
                  }}>
                    {card.icon}
                  </div>
                  <div>
                    <div style={{
                      fontFamily: '"Syne", sans-serif',
                      fontSize: '20px', fontWeight: 700, color: '#fff',
                      lineHeight: 1.2,
                    }}>
                      {card.label}
                    </div>
                  </div>
                </div>

                {/* Description */}
                <p style={{
                  color: 'rgba(255,255,255,0.5)', fontSize: '14px',
                  lineHeight: 1.65, margin: '0 0 24px 0', flex: 1,
                }}>
                  {card.description}
                </p>

                {/* Tags */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '24px' }}>
                  {card.tags.map((tag) => (
                    <span key={tag} className="tag-pill" style={{
                      background: card.accentDim,
                      border: `1px solid ${card.accentBorder}`,
                      color: card.accent,
                    }}>
                      {tag}
                    </span>
                  ))}
                </div>

                {/* CTA */}
                <button className="cta-btn" style={{
                  width: '100%', padding: '12px',
                  background: hoveredCard === card.id
                    ? `linear-gradient(135deg, ${card.accent}, ${card.accent}cc)`
                    : card.accentDim,
                  border: `1px solid ${card.accentBorder}`,
                  borderRadius: '10px',
                  color: hoveredCard === card.id ? '#fff' : card.accent,
                  fontSize: '14px', fontWeight: 600,
                  fontFamily: '"DM Sans", sans-serif',
                  letterSpacing: '0.02em',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                }}>
                  {card.cta}
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <path d="M3 7h8M7.5 4l3.5 3-3.5 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Footer note */}
        <div style={{
          textAlign: 'center',
          opacity: mounted ? 1 : 0, transition: 'opacity 0.8s ease 0.6s',
        }}>
          <span style={{ color: 'rgba(255,255,255,0.2)', fontSize: '13px' }}>
            You can switch modes anytime from{' '}
            <span style={{ color: 'rgba(255,255,255,0.35)', textDecoration: 'underline', cursor: 'pointer' }}>
              Settings
            </span>
          </span>
        </div>
      </div>
    </div>
  );
}
