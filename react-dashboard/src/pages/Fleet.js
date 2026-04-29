import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import AnimatedBg from '../components/AnimatedBg';

const C = {
  bg: '#02020c',
  surface: '#07071a',
  card: '#0a0a20',
  border: 'rgba(0,229,255,0.1)',
  borderHover: 'rgba(0,229,255,0.25)',
  cyan: '#00e5ff',
  indigo: '#6366f1',
  muted: '#3a4a6a',
  text: '#c8d8f0',
  white: '#fff',
};

const Card = ({ children, style = {} }) => (
  <div style={{
    background: C.card,
    border: `1px solid ${C.border}`,
    borderRadius: 12,
    padding: '1.5rem',
    ...style
  }}>
    {children}
  </div>
);

const Label = ({ children }) => (
  <div style={{
    fontSize: '0.68rem', fontWeight: 700, letterSpacing: 3,
    textTransform: 'uppercase', color: C.muted, marginBottom: '0.75rem'
  }}>
    {children}
  </div>
);

export default function Fleet() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);

    localStorage.setItem('agent_steps', JSON.stringify([]));
    localStorage.setItem('agent_query', query);
    localStorage.setItem('agent_status', 'running');
    localStorage.setItem('agent_current_step', '0');

    try {
      const response = await fetch('http://localhost:8000/research/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const lines = decoder.decode(value).split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              const existing = JSON.parse(localStorage.getItem('agent_steps') || '[]');
              existing.push({ step: data.step, message: data.message, time: new Date().toLocaleTimeString() });
              localStorage.setItem('agent_steps', JSON.stringify(existing));
              localStorage.setItem('agent_current_step', String(data.step));
              if (data.status === 'COMPLETE') localStorage.setItem('agent_status', 'complete');
            } catch (e) {}
          }
        }
      }

      const res = await fetch('http://localhost:8000/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError('Failed to connect. Make sure the backend is running.');
      localStorage.setItem('agent_status', 'error');
    }
    setLoading(false);
  };

  return (
    <div style={{ background: C.bg, minHeight: '100vh', padding: '2rem', position: 'relative' }}>
      <AnimatedBg />
      <div style={{ position: 'relative', zIndex: 1 }}>

        {/* Header */}
        <div style={{ marginBottom: '2rem' }}>
          <h1 style={{ color: C.white, fontSize: '1.4rem', fontWeight: 800,
            letterSpacing: 2, textTransform: 'uppercase', margin: '0 0 0.3rem' }}>
            Fleet Research
          </h1>
          <p style={{ color: C.muted, fontSize: '0.82rem', margin: 0 }}>
            Enter any car to get an AI-generated research report and image
          </p>
        </div>

        {/* Search */}
        <Card style={{ marginBottom: '1.5rem', padding: '1.25rem' }}>
          <Label>Search</Label>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !loading && handleSearch()}
              placeholder="e.g. BMW M3 Competition 2024"
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
              onClick={handleSearch}
              disabled={loading}
              style={{
                padding: '10px 28px', borderRadius: 6, border: 'none',
                background: loading ? C.surface : `linear-gradient(135deg, ${C.indigo}, ${C.cyan})`,
                color: loading ? C.muted : C.white,
                fontWeight: 700, fontSize: '0.82rem', letterSpacing: 2,
                textTransform: 'uppercase', cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s', whiteSpace: 'nowrap',
              }}>
              {loading ? 'Researching...' : 'Research'}
            </button>
          </div>
        </Card>

        {/* Error */}
        {error && (
          <Card style={{ marginBottom: '1.5rem', borderColor: 'rgba(239,68,68,0.3)', background: 'rgba(239,68,68,0.05)' }}>
            <p style={{ color: '#ef4444', margin: 0, fontSize: '0.85rem' }}>{error}</p>
          </Card>
        )}

        {/* Loading */}
        {loading && (
          <Card style={{ textAlign: 'center', padding: '3rem' }}>
            <div style={{ width: 36, height: 36, border: `2px solid ${C.border}`,
              borderTop: `2px solid ${C.cyan}`, borderRadius: '50%',
              animation: 'spin 0.8s linear infinite', margin: '0 auto 1rem' }} />
            <p style={{ color: C.muted, margin: '0 0 0.3rem', fontSize: '0.88rem' }}>
              Researching {query}...
            </p>
            <p style={{ color: '#1a2a4a', fontSize: '0.75rem', margin: 0 }}>
              Switch to Agents tab to watch the pipeline live
            </p>
          </Card>
        )}

        {/* Results */}
        {result && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

            <Card style={{ padding: '1rem 1.5rem', display: 'flex',
              justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
              <span style={{ color: C.white, fontWeight: 700, fontSize: '1rem' }}>{result.query}</span>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {[
                  { label: result.status, color: '#10b981', bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.2)' },
                  { label: `${result.duration}s`, color: C.cyan, bg: 'rgba(0,229,255,0.06)', border: C.border },
                  { label: `#${result.run_id}`, color: C.muted, bg: C.surface, border: C.border },
                ].map(({ label, color, bg, border }) => (
                  <span key={label} style={{
                    background: bg, border: `1px solid ${border}`,
                    color, padding: '3px 12px', borderRadius: 20,
                    fontSize: '0.72rem', fontWeight: 600, letterSpacing: 1
                  }}>{label}</span>
                ))}
              </div>
            </Card>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
              <Card style={{ padding: 0, overflow: 'hidden' }}>
                <div style={{ padding: '1rem 1.25rem', borderBottom: `1px solid ${C.border}` }}>
                  <Label>Car Image</Label>
                </div>
                {result.image_url ? (
                  <img src={result.image_url} alt={result.query}
                    style={{ width: '100%', height: 280, objectFit: 'cover', display: 'block', background: C.surface }} />
                ) : (
                  <div style={{ height: 280, display: 'flex', alignItems: 'center',
                    justifyContent: 'center', color: C.muted, fontSize: '0.82rem' }}>
                    No image available
                  </div>
                )}
              </Card>

              <Card>
                <Label>Research Summary</Label>
                <div style={{ color: C.text, lineHeight: 1.75, fontSize: '0.84rem',
                  maxHeight: 300, overflowY: 'auto' }}>
                  <ReactMarkdown>{result.research}</ReactMarkdown>
                </div>
              </Card>
            </div>

            <Card>
              <Label>Full Report</Label>
              <div style={{ color: C.text, lineHeight: 1.85, fontSize: '0.88rem' }}>
                <ReactMarkdown>{result.report}</ReactMarkdown>
              </div>
            </Card>
          </div>
        )}

        <style>{`
          @keyframes spin { to { transform: rotate(360deg); } }
          ::-webkit-scrollbar { width: 4px; }
          ::-webkit-scrollbar-track { background: transparent; }
          ::-webkit-scrollbar-thumb { background: rgba(0,229,255,0.2); border-radius: 4px; }
        `}</style>

      </div>
    </div>
  );
}