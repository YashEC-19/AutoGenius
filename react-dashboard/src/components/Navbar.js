import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function Navbar() {
  const location = useLocation();
  const links = [
    { path: '/fleet', label: 'Fleet' },
    { path: '/agents', label: 'Agents' },
    { path: '/vision', label: 'Vision Lab' },
  ];

  return (
    <nav style={{
      background: '#02020c',
      borderBottom: '1px solid rgba(0,229,255,0.1)',
      padding: '0 2rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      height: 56,
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      <Link to="/" style={{ textDecoration: 'none' }}>
        <span style={{ fontSize: '1rem', fontWeight: 900, letterSpacing: 4, color: '#fff' }}>
          AUTO<span style={{ color: '#00e5ff' }}>GENIUS</span>
        </span>
      </Link>

      <div style={{ display: 'flex', gap: '0.25rem' }}>
        {links.map(link => {
          const active = location.pathname === link.path;
          return (
            <Link key={link.path} to={link.path} style={{ textDecoration: 'none' }}>
              <div style={{
                padding: '6px 18px',
                borderRadius: 4,
                fontSize: '0.78rem',
                fontWeight: 600,
                letterSpacing: 2,
                textTransform: 'uppercase',
                color: active ? '#00e5ff' : '#3a4a6a',
                background: active ? 'rgba(0,229,255,0.08)' : 'transparent',
                border: active ? '1px solid rgba(0,229,255,0.2)' : '1px solid transparent',
                transition: 'all 0.2s',
              }}>
                {link.label}
              </div>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}