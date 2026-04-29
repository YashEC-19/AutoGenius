import React, { useState, useEffect } from 'react';
import AnimatedBg from '../components/AnimatedBg';

const C = {
  bg: '#02020c', surface: '#07071a', card: '#0a0a20',
  border: 'rgba(0,229,255,0.1)', cyan: '#00e5ff',
  indigo: '#6366f1', muted: '#3a4a6a', text: '#c8d8f0', white: '#fff',
  green: '#10b981', red: '#ef4444',
};

const STEPS = [
  { id: 1, label: 'Initializing',         agent: 'Orchestrator',     llm: 'System' },
  { id: 2, label: 'Researching car specs', agent: 'Researcher Agent', llm: 'llama-3.3-70b' },
  { id: 3, label: 'Research complete',     agent: 'Researcher Agent', llm: 'llama-3.3-70b' },
  { id: 4, label: 'Writing report',        agent: 'Writer Agent',     llm: 'llama-3.3-70b' },
  { id: 5, label: 'Report complete',       agent: 'Writer Agent',     llm: 'llama-3.3-70b' },
  { id: 6, label: 'Fetching image',        agent: 'Vision Agent',     llm: 'Unsplash API' },
  { id: 7, label: 'Pipeline complete',     agent: 'Orchestrator',     llm: 'System' },
];

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

export default function Agents() {
  const [steps, setSteps] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [status, setStatus] = useState('idle');
  const [agentQuery, setAgentQuery] = useState('');

  useEffect(() => {
    const interval = setInterval(() => {
      setSteps(JSON.parse(localStorage.getItem('agent_steps') || '[]'));
      setCurrentStep(parseInt(localStorage.getItem('agent_current_step') || '0'));
      setStatus(localStorage.getItem('agent_status') || 'idle');
      setAgentQuery(localStorage.getItem('agent_query') || '');
    }, 500);
    return () => clearInterval(interval);
  }, []);

  const running = status === 'running';
  const done = status === 'complete';
  const activeStep = STEPS.find(s => s.id === currentStep);

  return (
    <div style={{ background: C.bg, minHeight: '100vh', padding: '2rem', position: 'relative' }}>
      <AnimatedBg />
      <div style={{ position: 'relative', zIndex: 1 }}>

        <div style={{ marginBottom: '2rem' }}>
          <h1 style={{ color: C.white, fontSize: '1.4rem', fontWeight: 800,
            letterSpacing: 2, textTransform: 'uppercase', margin: '0 0 0.3rem' }}>
            Live Agent Pipeline
          </h1>
          <p style={{ color: C.muted, fontSize: '0.82rem', margin: 0 }}>
            Agents update in real time as Fleet runs a query
          </p>
        </div>

        {/* Idle */}
        {status === 'idle' && (
          <Card style={{ textAlign: 'center', padding: '3rem' }}>
            <div style={{ width: 48, height: 48, borderRadius: '50%',
              border: `1px solid ${C.border}`, margin: '0 auto 1rem',
              display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ width: 16, height: 16, borderRadius: '50%', background: C.muted }} />
            </div>
            <p style={{ color: C.muted, margin: '0 0 0.4rem', fontSize: '0.9rem', fontWeight: 600 }}>
              No agents running
            </p>
            <p style={{ color: '#1a2a4a', fontSize: '0.78rem', margin: 0 }}>
              Run a search on the Fleet page to see agents work here
            </p>
          </Card>
        )}

        {/* Active agent card */}
        {running && activeStep && (
          <Card style={{
            marginBottom: '1.25rem',
            borderColor: 'rgba(0,229,255,0.25)',
            background: 'rgba(0,229,255,0.04)',
            display: 'flex', alignItems: 'center', gap: '1.5rem', padding: '1.25rem 1.5rem'
          }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '0.65rem', fontWeight: 700, letterSpacing: 3,
                color: C.cyan, textTransform: 'uppercase', marginBottom: 6 }}>
                Currently Running
              </div>
              <div style={{ color: C.white, fontWeight: 700, fontSize: '1rem', marginBottom: 4 }}>
                {activeStep.agent}
              </div>
              <div style={{ fontSize: '0.75rem', color: C.muted }}>
                LLM: <span style={{ color: C.cyan }}>{activeStep.llm}</span>
                {agentQuery && <span style={{ marginLeft: 12 }}>
                  Query: <span style={{ color: C.text }}>{agentQuery}</span>
                </span>}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 5 }}>
              {[0, 1, 2].map(i => (
                <div key={i} style={{
                  width: 7, height: 7, borderRadius: '50%', background: C.cyan,
                  animation: `pulse 1s ease-in-out ${i * 0.2}s infinite`
                }} />
              ))}
            </div>
          </Card>
        )}

        {/* Done */}
        {done && (
          <Card style={{
            marginBottom: '1.25rem',
            borderColor: 'rgba(16,185,129,0.25)',
            background: 'rgba(16,185,129,0.04)',
            display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem 1.5rem'
          }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: C.green }} />
            <div>
              <div style={{ color: C.green, fontWeight: 700, fontSize: '0.88rem' }}>Pipeline complete</div>
              <div style={{ color: C.muted, fontSize: '0.75rem' }}>Check Fleet for full results</div>
            </div>
          </Card>
        )}

        {/* Pipeline steps */}
        {status !== 'idle' && (
          <Card>
            <Label>Pipeline Steps</Label>
            <div style={{ background: C.surface, borderRadius: 4, height: 3, marginBottom: '1.5rem' }}>
              <div style={{
                background: `linear-gradient(90deg, ${C.indigo}, ${C.cyan})`,
                height: 3, borderRadius: 4,
                width: `${(currentStep / 7) * 100}%`,
                transition: 'width 0.5s ease'
              }} />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {STEPS.map(s => {
                const completed = steps.find(st => st.step === s.id);
                const active = currentStep === s.id && running;

                return (
                  <div key={s.id} style={{
                    display: 'flex', alignItems: 'center', gap: '1rem',
                    padding: '0.75rem 1rem', borderRadius: 8,
                    background: active ? 'rgba(0,229,255,0.05)' : 'transparent',
                    border: active ? `1px solid rgba(0,229,255,0.2)` : '1px solid transparent',
                    opacity: !completed && !active ? 0.3 : 1,
                    transition: 'all 0.3s',
                  }}>
                    <div style={{
                      width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      background: completed ? 'rgba(16,185,129,0.15)' : active ? 'rgba(0,229,255,0.1)' : C.surface,
                      border: `1px solid ${completed ? 'rgba(16,185,129,0.4)' : active ? C.cyan : C.border}`,
                    }}>
                      {completed ? (
                        <div style={{ width: 8, height: 8, borderRadius: '50%', background: C.green }} />
                      ) : active ? (
                        <div style={{ width: 10, height: 10, border: `2px solid ${C.cyan}`,
                          borderTop: '2px solid transparent', borderRadius: '50%',
                          animation: 'spin 0.8s linear infinite' }} />
                      ) : (
                        <div style={{ width: 6, height: 6, borderRadius: '50%', background: C.muted }} />
                      )}
                    </div>

                    <div style={{ flex: 1 }}>
                      <div style={{ color: completed || active ? C.white : C.muted,
                        fontWeight: 600, fontSize: '0.85rem' }}>
                        {s.label}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: C.muted, marginTop: 2 }}>
                        {s.agent} &nbsp;·&nbsp;
                        <span style={{ color: completed ? C.green : active ? C.cyan : C.muted }}>
                          {s.llm}
                        </span>
                      </div>
                    </div>

                    {completed && (
                      <span style={{ fontSize: '0.7rem', color: '#1a3a5a' }}>{completed.time}</span>
                    )}
                  </div>
                );
              })}
            </div>
          </Card>
        )}

        <style>{`
          @keyframes spin { to { transform: rotate(360deg); } }
          @keyframes pulse { 0%,100% { opacity:0.3; transform:scale(0.8); } 50% { opacity:1; transform:scale(1.2); } }
        `}</style>

      </div>
    </div>
  );
}