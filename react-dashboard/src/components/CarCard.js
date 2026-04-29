import React from 'react';

export default function CarCard({ car }) {
  return (
    <div style={{ background: '#111', border: '1px solid #222', borderRadius: 12, overflow: 'hidden', transition: 'transform 0.2s', cursor: 'pointer' }}
      onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-4px)'}
      onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}>
      <img src={car.image} alt={car.name} style={{ width: '100%', height: 180, objectFit: 'cover' }} onError={e => e.target.style.display='none'} />
      <div style={{ padding: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <h3 style={{ color: '#fff', margin: 0, fontSize: '1rem' }}>{car.name}</h3>
          <span style={{ background: '#e63946', color: '#fff', borderRadius: 20, padding: '2px 10px', fontSize: '0.8rem' }}>{car.rating}/10</span>
        </div>
        <div style={{ color: '#aaa', fontSize: '0.85rem', marginBottom: 8 }}>{car.year} • {car.type}</div>
        <div style={{ display: 'flex', justifyContent: 'space-between', color: '#fff', fontSize: '0.9rem' }}>
          <span>⚡ {car.hp} HP</span>
          {car.range > 0 && <span>🔋 {car.range} mi</span>}
          <span style={{ color: '#e63946' }}>${car.price.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
