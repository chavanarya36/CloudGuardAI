import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function NotFound() {
  const navigate = useNavigate();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 60);
    return () => clearTimeout(t);
  }, []);

  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      minHeight: '60vh', textAlign: 'center',
      fontFamily: '"DM Sans", sans-serif',
      opacity: mounted ? 1 : 0,
      transform: mounted ? 'translateY(0)' : 'translateY(20px)',
      transition: 'opacity 0.6s ease, transform 0.6s ease',
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Syne:wght@700;800&display=swap');
        @keyframes float404 { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
        .home-btn { cursor:pointer; transition:all 0.25s cubic-bezier(0.34,1.56,0.64,1); }
        .home-btn:hover { transform:translateY(-3px) scale(1.03); box-shadow:0 12px 40px rgba(66,165,245,0.3); }
      `}</style>

      {/* Glowing 404 */}
      <div style={{
        fontSize: '120px', fontFamily: '"Syne", sans-serif',
        fontWeight: 800, color: '#fff',
        textShadow: '0 0 60px rgba(66,165,245,0.3), 0 0 120px rgba(66,165,245,0.15)',
        animation: 'float404 3s ease-in-out infinite',
        lineHeight: 1, marginBottom: '16px',
        letterSpacing: '-0.05em',
      }}>
        404
      </div>

      <div style={{
        fontFamily: '"Syne", sans-serif',
        fontSize: '20px', fontWeight: 700, color: '#fff',
        marginBottom: '12px',
      }}>
        Page not found
      </div>

      <p style={{
        color: 'rgba(255,255,255,0.4)', fontSize: '15px',
        maxWidth: '420px', lineHeight: 1.6, margin: '0 0 32px',
      }}>
        The page you&apos;re looking for doesn&apos;t exist or has been moved.
      </p>

      <button className="home-btn" onClick={() => navigate('/')} style={{
        padding: '14px 32px',
        background: 'linear-gradient(135deg, #1976d2, #42a5f5)',
        border: 'none', borderRadius: '10px',
        color: '#fff', fontSize: '15px', fontWeight: 600,
        fontFamily: '"DM Sans", sans-serif',
        display: 'flex', alignItems: 'center', gap: '8px',
      }}>
        Back to Home
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M3.5 8h9M8.5 5l3.5 3-3.5 3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>
    </div>
  );
}
