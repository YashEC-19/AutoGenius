import React, { useState } from 'react';
import AnimatedBg from '../components/AnimatedBg';

const C = {
  bg: '#02020c', surface: '#07071a', card: '#0a0a20',
  border: 'rgba(0,229,255,0.1)', cyan: '#00e5ff',
  indigo: '#6366f1', muted: '#3a4a6a', text: '#c8d8f0', white: '#fff',
};

const Card = ({ children, style = {} }) => (
  <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: '1.5rem', ...style }}>
    {children}
  </div>
);

const Label = ({ children }) => (
  <div style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: 3,
    textTransform: 'uppercase', color: C.muted, marginBottom: '0.75rem' }}>
    {children}
  </div>
);

export default function VisionLab() {
  const [prompt, setPrompt] = useState('');
  const [imageUrl, setImageUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const generateImage = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setImageUrl(null);
    setError(null);
    try {
      const encoded = encodeURIComponent(prompt);
      const response = await fetch(`http://localhost:8000/vision/generate?prompt=${encoded}`);
      if (!response.ok) throw new Error('Generation failed');
      const blob = await response.blob();
      setImageUrl(URL.createObjectURL(blob));
    } catch (err) {
      setError('Failed to generate. Make sure the backend is running.');
    }
    setLoading(false);
  };

  return (
    <div style={{ background: C.bg, minHeight: '100vh', padding: '2rem', position: 'relative' }}>
      <AnimatedBg />
      <div style={{ position: 'relative', zIndex: 1 }}>

        <div style={{ marginBottom: '2rem' }}>
          <h1 style={{ color: C.white, fontSize: '1.4rem', fontWeight: 800,
            letterSpacing: 2, textTransform: 'uppercase', margin: '0 0 0.3rem' }}>
            Vision Lab
          </h1>
          <p style={{ color: C.muted, fontSize: '0.82rem', margin: 0 }}>
            Describe any car modification and AI will visualize it
          </p>
        </div>

        {/* Prompt input */}
        <Card style={{ marginBottom: '1.5rem', padding: '1.25rem' }}>
          <Label>Prompt</Label>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <input
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !loading && generateImage()}
              placeholder="e.g. Ferrari F40 with angel wings floating in space"
              style={{
                flex: 1, padding: '10px 16px', borderRadius: 6,
                border: `1px solid ${C.border}`, background: C.surface,
                color: C.white, fontSize: '0.88rem', outline: 'none',
                transition: 'border 0.2s',
              }}
              onFocus={e => e.target.style.borderColor = C.cyan}
              onBlur={e => e.target.style.borderColor = C.border}
            />
            <button
              onClick={generateImage}
              disabled={loading}
              style={{
                padding: '10px 28px', borderRadius: 6, border: 'none',
                background: loading ? C.surface : `linear-gradient(135deg, ${C.indigo}, ${C.cyan})`,
                color: loading ? C.muted : C.white,
                fontWeight: 700, fontSize: '0.82rem', letterSpacing: 2,
                textTransform: 'uppercase', cursor: loading ? 'not-allowed' : 'pointer',
              }}>
              {loading ? 'Generating...' : 'Generate'}
            </button>
          </div>
        </Card>

        {/* Error */}
        {error && (
          <Card style={{ marginBottom: '1.5rem', borderColor: 'rgba(239,68,68,0.3)', background: 'rgba(239,68,68,0.05)' }}>
            <p style={{ color: '#ef4444', margin: 0, fontSize: '0.85rem' }}>{error}</p>
            <button onClick={generateImage} style={{
              marginTop: '0.75rem', padding: '7px 20px', borderRadius: 4,
              border: `1px solid rgba(239,68,68,0.3)`, background: 'transparent',
              color: '#ef4444', fontSize: '0.78rem', cursor: 'pointer', letterSpacing: 2
            }}>Try Again</button>
          </Card>
        )}

        {/* Image area */}
        <Card style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '1rem 1.5rem', borderBottom: `1px solid ${C.border}`,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Label>Generated Image</Label>
            {imageUrl && (
              <a href={imageUrl} download="vision-lab.png" style={{
                fontSize: '0.72rem', color: C.cyan, textDecoration: 'none',
                letterSpacing: 2, textTransform: 'uppercase'
              }}>Download</a>
            )}
          </div>

          {!loading && !imageUrl && !error && (
            <div style={{ height: 440, display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center', gap: '0.75rem' }}>
              <div style={{ width: 48, height: 48, borderRadius: '50%',
                border: `1px solid ${C.border}`, display: 'flex',
                alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ width: 18, height: 18, borderRadius: '50%', background: C.surface,
                  border: `1px solid ${C.muted}` }} />
              </div>
              <p style={{ color: C.muted, margin: 0, fontSize: '0.82rem' }}>
                Your image will appear here
              </p>
              <p style={{ color: '#1a2a4a', margin: 0, fontSize: '0.74rem' }}>
                Try: "BMW M3 with rocket boosters on Mars"
              </p>
            </div>
          )}

          {loading && (
            <div style={{ height: 440, display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center', gap: '1rem' }}>
              <div style={{ width: 36, height: 36, border: `2px solid ${C.border}`,
                borderTop: `2px solid ${C.cyan}`, borderRadius: '50%',
                animation: 'spin 0.8s linear infinite' }} />
              <p style={{ color: C.muted, margin: 0, fontSize: '0.85rem' }}>Generating image...</p>
              <p style={{ color: '#1a2a4a', margin: 0, fontSize: '0.75rem' }}>Usually 15–30 seconds</p>
            </div>
          )}

          {!loading && imageUrl && (
            <>
              <img src={imageUrl} alt="Generated"
                style={{ width: '100%', maxHeight: 500, objectFit: 'contain',
                  background: C.surface, display: 'block' }} />
              <div style={{ padding: '1rem 1.5rem', borderTop: `1px solid ${C.border}`,
                display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: C.muted, fontSize: '0.78rem' }}>"{prompt}"</span>
                <button onClick={generateImage} style={{
                  padding: '6px 18px', borderRadius: 4,
                  border: `1px solid ${C.border}`, background: 'transparent',
                  color: C.muted, fontSize: '0.75rem', cursor: 'pointer',
                  letterSpacing: 2, textTransform: 'uppercase'
                }}>Regenerate</button>
              </div>
            </>
          )}
        </Card>

        <style>{`
          @keyframes spin { to { transform: rotate(360deg); } }
        `}</style>

      </div>
    </div>
  );
}