import React, { useEffect, useRef } from 'react';

export default function AnimatedBg() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    // Cyan/indigo palette matching your theme
    const CAR_COLORS = ['#00e5ff', '#6366f1', '#a855f7', '#0ea5e9', '#818cf8'];

    const cars = Array.from({ length: 6 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      speed: 0.6 + Math.random() * 1.0,
      angle: Math.random() * Math.PI * 2,
      color: CAR_COLORS[Math.floor(Math.random() * CAR_COLORS.length)],
      turnRate: (Math.random() - 0.5) * 0.04,
      length: 18 + Math.random() * 10,
    }));

    const smoke = [];

    const spawnSmoke = (x, y, color) => {
      if (Math.random() > 0.25) return; // sparse smoke
      smoke.push({
        x, y,
        size: 3 + Math.random() * 5,
        alpha: 0.12 + Math.random() * 0.1,
        dx: (Math.random() - 0.5) * 0.4,
        dy: -0.3 - Math.random() * 0.4,
        color,
      });
    };

    const drawSmoke = () => {
      for (let i = smoke.length - 1; i >= 0; i--) {
        const p = smoke[i];
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${hexToRgb(p.color)},${p.alpha})`;
        ctx.fill();
        p.x += p.dx;
        p.y += p.dy;
        p.size += 0.25;
        p.alpha -= 0.004;
        if (p.alpha <= 0) smoke.splice(i, 1);
      }
    };

    const hexToRgb = (hex) => {
      const r = parseInt(hex.slice(1, 3), 16);
      const g = parseInt(hex.slice(3, 5), 16);
      const b = parseInt(hex.slice(5, 7), 16);
      return `${r},${g},${b}`;
    };

    const drawCar = (c) => {
      ctx.save();
      ctx.translate(c.x, c.y);
      ctx.rotate(c.angle + Math.PI / 2);

      const w = c.length * 0.45;
      const h = c.length;

      // Glow
      ctx.shadowColor = c.color;
      ctx.shadowBlur = 14;

      // Body
      ctx.fillStyle = c.color;
      ctx.beginPath();
      ctx.roundRect(-w / 2, -h / 2, w, h, 4);
      ctx.fill();

      // Windshield
      ctx.shadowBlur = 0;
      ctx.fillStyle = 'rgba(0,0,0,0.5)';
      ctx.beginPath();
      ctx.roundRect(-w / 2 + 2, -h / 2 + 3, w - 4, h * 0.38, 2);
      ctx.fill();

      // Headlights
      ctx.shadowColor = '#ffffff';
      ctx.shadowBlur = 8;
      ctx.fillStyle = 'rgba(255,255,255,0.9)';
      ctx.fillRect(-w / 2 + 1, -h / 2, 3, 3);
      ctx.fillRect(w / 2 - 4, -h / 2, 3, 3);

      // Taillights
      ctx.shadowColor = '#ff0055';
      ctx.shadowBlur = 6;
      ctx.fillStyle = 'rgba(255,0,80,0.9)';
      ctx.fillRect(-w / 2 + 1, h / 2 - 3, 3, 3);
      ctx.fillRect(w / 2 - 4, h / 2 - 3, 3, 3);
      ctx.shadowBlur = 0;

      ctx.restore();
    };

    // Pit stop box — bottom right
    const drawPitStop = () => {
      const pw = 200, ph = 80;
      const px = canvas.width - pw - 32;
      const py = canvas.height - ph - 32;

      ctx.fillStyle = 'rgba(0,229,255,0.03)';
      ctx.strokeStyle = 'rgba(0,229,255,0.12)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.roundRect(px, py, pw, ph, 8);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = 'rgba(0,229,255,0.15)';
      ctx.font = '600 10px Inter, sans-serif';
      ctx.letterSpacing = '3px';
      ctx.fillText('PIT STOP', px + 16, py + 22);

      // Dashed lane lines inside pit
      ctx.strokeStyle = 'rgba(0,229,255,0.08)';
      ctx.setLineDash([6, 6]);
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(px + 16, py + 40);
      ctx.lineTo(px + pw - 16, py + 40);
      ctx.stroke();
      ctx.setLineDash([]);
    };

    // Road lane lines — subtle diagonal streaks
    const drawRoadLines = () => {
      ctx.strokeStyle = 'rgba(0,229,255,0.025)';
      ctx.lineWidth = 1;
      ctx.setLineDash([40, 80]);
      for (let i = -canvas.height; i < canvas.width + canvas.height; i += 120) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i + canvas.height, canvas.height);
        ctx.stroke();
      }
      ctx.setLineDash([]);
    };

    let animId;

    const draw = () => {
      // Deep bg — partial clear for subtle trail
      ctx.fillStyle = 'rgba(2,2,12,0.82)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      drawRoadLines();
      drawSmoke();
      drawPitStop();

      cars.forEach(c => {
        drawCar(c);
        spawnSmoke(c.x, c.y, c.color);

        c.angle += c.turnRate + (Math.random() - 0.5) * 0.015;
        c.x += Math.cos(c.angle) * c.speed;
        c.y += Math.sin(c.angle) * c.speed;

        // Wrap around
        if (c.x > canvas.width + 20)  c.x = -20;
        if (c.x < -20)                c.x = canvas.width + 20;
        if (c.y > canvas.height + 20) c.y = -20;
        if (c.y < -20)                c.y = canvas.height + 20;
      });

      animId = requestAnimationFrame(draw);
    };

    draw();
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0, left: 0,
        width: '100%', height: '100%',
        zIndex: 0,
        pointerEvents: 'none',
      }}
    />
  );
}