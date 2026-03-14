import { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';

const drawerWidth = 260;

const menuItems = [
  { text: 'Scan', path: '/scan', icon: '🔍' },
  { text: 'Dashboard', path: '/dashboard', icon: '📊' },
  { text: 'Learning', path: '/learning', icon: '🧠' },
  { text: 'History', path: '/history', icon: '📋' },
  { text: 'Feedback', path: '/feedback', icon: '💬' },
  { text: 'Model Status', path: '/model-status', icon: '⚡' },
  { text: 'Settings', path: '/settings', icon: '⚙️' },
];

export default function Layout({ children }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  const handleDrawerToggle = () => setMobileOpen(!mobileOpen);

  const sidebar = (
    <div style={{
      width: drawerWidth,
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: '#040b14',
      borderRight: '1px solid rgba(66,165,245,0.08)',
      fontFamily: '"DM Sans", "Helvetica Neue", sans-serif',
      position: 'fixed',
      top: 0,
      left: 0,
      zIndex: 1200,
      overflowY: 'auto',
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Syne:wght@700;800&display=swap');
        .nav-item { transition: all 0.2s ease; cursor: pointer; text-decoration: none; }
        .nav-item:hover { background: rgba(66,165,245,0.08) !important; }
      `}</style>

      {/* Logo */}
      <div style={{
        padding: '24px 24px 20px',
        borderBottom: '1px solid rgba(255,255,255,0.04)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '36px', height: '36px', borderRadius: '9px',
            background: 'linear-gradient(135deg, #0d47a1, #42a5f5)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 16px rgba(66,165,245,0.3)',
          }}>
            <svg width="18" height="18" viewBox="0 0 16 16" fill="none">
              <path d="M8 1L2 3.5v4.5c0 3.59 2.55 6.95 6 7.77 3.45-.82 6-4.18 6-7.77V3.5L8 1z" fill="white" opacity="0.9"/>
            </svg>
          </div>
          <div>
            <div style={{
              fontFamily: '"Syne", sans-serif',
              fontWeight: 700, fontSize: '16px', color: '#fff',
              lineHeight: 1.2,
            }}>
              CloudGuard
            </div>
            <div style={{
              fontSize: '11px', color: '#42a5f5',
              fontWeight: 500, letterSpacing: '0.05em',
            }}>
              AI Security
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div style={{ flex: 1, padding: '16px 12px' }}>
        <div style={{
          fontSize: '10px', letterSpacing: '0.15em', textTransform: 'uppercase',
          color: 'rgba(255,255,255,0.25)', fontWeight: 600,
          padding: '0 12px', marginBottom: '12px',
        }}>
          Navigation
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.text}
                to={item.path}
                className="nav-item"
                style={{
                  display: 'flex', alignItems: 'center', gap: '12px',
                  padding: '10px 14px', borderRadius: '8px',
                  background: isActive ? 'rgba(66,165,245,0.12)' : 'transparent',
                  border: isActive ? '1px solid rgba(66,165,245,0.2)' : '1px solid transparent',
                  color: isActive ? '#42a5f5' : 'rgba(255,255,255,0.55)',
                  fontSize: '14px', fontWeight: isActive ? 600 : 400,
                  textDecoration: 'none',
                }}
              >
                <span style={{ fontSize: '16px', width: '20px', textAlign: 'center' }}>{item.icon}</span>
                {item.text}
                {isActive && (
                  <div style={{
                    marginLeft: 'auto', width: '4px', height: '4px',
                    borderRadius: '50%', background: '#42a5f5',
                    boxShadow: '0 0 6px #42a5f5',
                  }} />
                )}
              </Link>
            );
          })}
        </div>
      </div>

      {/* Footer */}
      <div style={{
        padding: '16px',
        borderTop: '1px solid rgba(255,255,255,0.04)',
      }}>
        <div style={{
          padding: '12px 14px', borderRadius: '10px',
          background: 'rgba(102,187,106,0.06)',
          border: '1px solid rgba(102,187,106,0.15)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <div style={{
              width: '7px', height: '7px', borderRadius: '50%',
              background: '#66bb6a', boxShadow: '0 0 6px #66bb6a',
              animation: 'pulse 2s infinite',
            }} />
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#66bb6a' }}>
              System Online
            </span>
          </div>
          <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.3)' }}>
            All services operational
          </div>
        </div>
        <style>{`
          @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
        `}</style>
      </div>
    </div>
  );

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#060e1a' }}>
      {/* Mobile hamburger */}
      <div style={{
        position: 'fixed', top: 0, left: 0, right: 0, height: '56px',
        display: 'none', // hidden on desktop
        zIndex: 1300,
        background: 'rgba(6,14,26,0.9)', backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        alignItems: 'center', padding: '0 16px',
      }}>
        <button onClick={handleDrawerToggle} style={{
          background: 'none', border: 'none', color: '#42a5f5',
          fontSize: '24px', cursor: 'pointer',
        }}>
          ☰
        </button>
        <span style={{
          fontFamily: '"Syne", sans-serif',
          fontWeight: 700, fontSize: '15px', color: '#fff',
          marginLeft: '12px',
        }}>
          CloudGuard <span style={{ color: '#42a5f5' }}>AI</span>
        </span>
      </div>

      {/* Desktop Sidebar */}
      <nav>{sidebar}</nav>

      {/* Top Bar */}
      <div style={{
        position: 'fixed', top: 0,
        left: drawerWidth, right: 0, height: '56px',
        background: 'rgba(6,14,26,0.85)', backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        display: 'flex', alignItems: 'center',
        padding: '0 28px', zIndex: 1100,
        fontFamily: '"DM Sans", sans-serif',
      }}>
        <div style={{
          padding: '5px 14px', borderRadius: '6px',
          background: 'rgba(66,165,245,0.08)',
          border: '1px solid rgba(66,165,245,0.2)',
        }}>
          <span style={{
            fontFamily: '"Syne", sans-serif',
            fontWeight: 700, fontSize: '14px', color: '#42a5f5',
          }}>
            Security Scanning Platform
          </span>
        </div>
        <div style={{
          marginLeft: '12px', padding: '3px 10px', borderRadius: '99px',
          background: 'rgba(102,187,106,0.1)',
          border: '1px solid rgba(102,187,106,0.25)',
          fontSize: '11px', fontWeight: 600, color: '#66bb6a',
        }}>
          v2.5
        </div>
      </div>

      {/* Main Content */}
      <main style={{
        flex: 1,
        marginLeft: drawerWidth,
        marginTop: '56px',
        padding: '32px',
        background: '#060e1a',
        minHeight: 'calc(100vh - 56px)',
        fontFamily: '"DM Sans", "Helvetica Neue", sans-serif',
      }}>
        {children || <Outlet />}
      </main>
    </div>
  );
}
