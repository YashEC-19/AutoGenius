import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Landing() {
  const canvasRef = useRef(null);
  const navigate = useNavigate();
  const [entered, setEntered] = useState(false);

  const playUISound = () => {
    const actx = new (window.AudioContext || window.webkitAudioContext)();
    const master = actx.createGain();
    master.gain.value = 0.4;
    master.connect(actx.destination);
    const tone = (freq, startT, endT, vol) => {
      const osc = actx.createOscillator();
      const gain = actx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, actx.currentTime + startT);
      gain.gain.setValueAtTime(0, actx.currentTime + startT);
      gain.gain.linearRampToValueAtTime(vol, actx.currentTime + startT + 0.05);
      gain.gain.exponentialRampToValueAtTime(0.001, actx.currentTime + endT);
      osc.connect(gain); gain.connect(master);
      osc.start(actx.currentTime + startT);
      osc.stop(actx.currentTime + endT);
    };
    tone(80, 0.0, 0.5, 0.5);
    tone(160, 0.1, 0.7, 0.3);
    tone(320, 0.3, 1.0, 0.2);
    tone(640, 0.6, 1.3, 0.15);
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    // ── Lillian particle system ──────────────────────────────────────
    const NUM = 1800;
    const COLORS = [
      [0, 229, 255],   // cyan
      [99, 102, 241],  // indigo
      [168, 85, 247],  // purple
      [0, 180, 220],   // light cyan
    ];

    // Bloom centres — particles orbit / scatter around these
    const blooms = [
      { x: 0.25, y: 0.5,  r: 0.28, phase: 0,    speed: 0.0008 },
      { x: 0.72, y: 0.45, r: 0.22, phase: 2.1,  speed: 0.0011 },
      { x: 0.5,  y: 0.75, r: 0.18, phase: 4.3,  speed: 0.0007 },
    ];

    const particles = Array.from({ length: NUM }, (_, i) => {
      const bloom = blooms[i % blooms.length];
      const angle = Math.random() * Math.PI * 2;
      const dist  = Math.random() * bloom.r * Math.min(canvas.width, canvas.height);
      const col   = COLORS[Math.floor(Math.random() * COLORS.length)];
      return {
        // Position
        x: bloom.x * canvas.width  + Math.cos(angle) * dist,
        y: bloom.y * canvas.height + Math.sin(angle) * dist,
        // Velocity
        vx: (Math.random() - 0.5) * 0.6,
        vy: (Math.random() - 0.5) * 0.6,
        // Chaos / drift
        ax: 0, ay: 0,
        // Bloom assignment
        bloomIdx: i % blooms.length,
        // Visual
        size: 2.5 + Math.random() * 3.5,
        rotation: Math.random() * Math.PI * 2,
        rotSpeed: (Math.random() - 0.5) * 0.08,
        col,
        alpha: 0.4 + Math.random() * 0.6,
        // Chaos timer
        chaosTimer: Math.random() * 200,
      };
    });

    let frame = 0;
    let animId;

    const drawTriangle = (x, y, size, rotation, alpha, col) => {
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(rotation);
      ctx.globalAlpha = alpha;
      ctx.fillStyle = `rgb(${col[0]},${col[1]},${col[2]})`;
      ctx.shadowColor = `rgba(${col[0]},${col[1]},${col[2]},0.6)`;
      ctx.shadowBlur = 6;
      ctx.beginPath();
      ctx.moveTo(0, -size);
      ctx.lineTo(size * 0.866, size * 0.5);
      ctx.lineTo(-size * 0.866, size * 0.5);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    };

    const animate = () => {
      frame++;

      // Trail fade — not full clear to get motion blur
      ctx.fillStyle = 'rgba(2,2,12,0.18)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Update bloom positions (they slowly drift)
      blooms.forEach(b => {
        b.phase += b.speed;
        b.x = 0.5 + Math.sin(b.phase)       * 0.3;
        b.y = 0.5 + Math.cos(b.phase * 1.3) * 0.25;
      });

      // Update and draw particles
      particles.forEach(p => {
        const bloom = blooms[p.bloomIdx];
        const bx = bloom.x * canvas.width;
        const by = bloom.y * canvas.height;

        const dx = bx - p.x;
        const dy = by - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;

        // Attraction toward bloom centre
        const attraction = 0.012;
        p.ax = (dx / dist) * attraction;
        p.ay = (dy / dist) * attraction;

        // Chaos — random bursts
        p.chaosTimer--;
        if (p.chaosTimer <= 0) {
          p.vx += (Math.random() - 0.5) * 2.5;
          p.vy += (Math.random() - 0.5) * 2.5;
          p.chaosTimer = 60 + Math.random() * 180;
        }

        // Orbital tangent push (makes it swirl not just collapse)
        const tangentStrength = 0.008;
        p.ax += (-dy / dist) * tangentStrength;
        p.ay += ( dx / dist) * tangentStrength;

        p.vx = (p.vx + p.ax) * 0.985;
        p.vy = (p.vy + p.ay) * 0.985;

        p.x += p.vx;
        p.y += p.vy;
        p.rotation += p.rotSpeed;

        // Wrap around edges
        if (p.x < -20) p.x = canvas.width + 20;
        if (p.x > canvas.width + 20) p.x = -20;
        if (p.y < -20) p.y = canvas.height + 20;
        if (p.y > canvas.height + 20) p.y = -20;

        // Pulse alpha
        const pulseAlpha = p.alpha * (0.7 + 0.3 * Math.sin(frame * 0.03 + p.x * 0.01));

        drawTriangle(p.x, p.y, p.size, p.rotation, pulseAlpha, p.col);
      });

      // Subtle bloom glow overlays
      blooms.forEach(b => {
        const grd = ctx.createRadialGradient(
          b.x * canvas.width, b.y * canvas.height, 0,
          b.x * canvas.width, b.y * canvas.height, canvas.width * 0.2
        );
        grd.addColorStop(0, 'rgba(0,229,255,0.04)');
        grd.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grd;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
      });

      animId = requestAnimationFrame(animate);
    };

    animate();
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
    };
  }, []);

  const handleEnter = () => {
    playUISound();
    setEntered(true);
    setTimeout(() => navigate('/fleet'), 2000);
  };

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh', overflow: 'hidden' }}>
      <canvas ref={canvasRef} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }} />

      {/* Top & bottom accent lines */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '1px',
        background: 'linear-gradient(90deg, transparent, #6366f1, #00e5ff, #6366f1, transparent)' }} />
      <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: '1px',
        background: 'linear-gradient(90deg, transparent, #6366f1, #00e5ff, #6366f1, transparent)' }} />

      {/* Vignette */}
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none',
        background: 'radial-gradient(ellipse at center, rgba(2,2,12,0.0) 0%, rgba(2,2,12,0.75) 100%)' }} />

      {/* Flash on enter */}
      {entered && (
        <div style={{ position: 'absolute', inset: 0, background: '#00e5ff',
          opacity: 0, animation: 'flash 0.4s ease-out forwards', zIndex: 20, pointerEvents: 'none' }} />
      )}

      {/* Content */}
      <div style={{ position: 'absolute', top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)', textAlign: 'center',
        zIndex: 10, width: '90%', maxWidth: 480 }}>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center',
          gap: '0.5rem', marginBottom: '0.6rem' }}>
          <span style={{ fontSize: '1.4rem', fontWeight: 900, letterSpacing: 5,
            color: '#fff', textTransform: 'uppercase' }}>
            Auto<span style={{ color: '#00e5ff' }}>Genius</span>
          </span>
        </div>

        <div style={{ width: 40, height: 1, margin: '0 auto 1.2rem',
          background: 'linear-gradient(90deg, transparent, #00e5ff, transparent)' }} />

        <h1 style={{ color: '#fff', fontSize: 'clamp(1.8rem, 4vw, 2.6rem)',
          fontWeight: 900, margin: '0 0 0.75rem', letterSpacing: 1,
          textTransform: 'uppercase', lineHeight: 1.15,
          textShadow: '0 0 40px rgba(0,229,255,0.2)' }}>
          AI Meets<br />Horsepower
        </h1>

        <p style={{ color: '#4a5a7a', fontSize: '0.82rem',
          margin: '0 0 2rem', lineHeight: 1.7 }}>
          Research any car · Watch live AI agents · Visualize experiments
        </p>

        {!entered ? (
          <button
            onClick={handleEnter}
            style={{
              padding: '11px 36px', fontSize: '0.78rem', fontWeight: 700,
              letterSpacing: 4, textTransform: 'uppercase',
              background: 'transparent', color: '#00e5ff',
              border: '1px solid rgba(0,229,255,0.5)',
              borderRadius: 4, cursor: 'pointer', transition: 'all 0.25s',
            }}
            onMouseEnter={e => {
              e.target.style.background = 'rgba(0,229,255,0.1)';
              e.target.style.borderColor = '#00e5ff';
              e.target.style.boxShadow = '0 0 24px rgba(0,229,255,0.25)';
            }}
            onMouseLeave={e => {
              e.target.style.background = 'transparent';
              e.target.style.borderColor = 'rgba(0,229,255,0.5)';
              e.target.style.boxShadow = 'none';
            }}
          >
            Enter Platform
          </button>
        ) : (
          <div style={{ color: '#00e5ff', fontSize: '0.75rem', fontWeight: 700,
            letterSpacing: 5, textTransform: 'uppercase',
            animation: 'fadeUp 0.4s ease forwards' }}>
            Initializing...
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center',
          gap: '0.5rem', marginTop: '2rem' }}>
          {['Fleet', 'Agents', 'Vision Lab'].map((tag, i) => (
            <React.Fragment key={tag}>
              {i > 0 && <span style={{ color: '#1a2a4a', fontSize: '0.6rem' }}>◆</span>}
              <span style={{ color: '#1e3a5a', fontSize: '0.68rem',
                letterSpacing: 2, textTransform: 'uppercase' }}>
                {tag}
              </span>
            </React.Fragment>
          ))}
        </div>
      </div>

      <style>{`
        @keyframes flash { 0% { opacity: 0.4; } 100% { opacity: 0; } }
        @keyframes fadeUp { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
      `}</style>
    </div>
  );
}