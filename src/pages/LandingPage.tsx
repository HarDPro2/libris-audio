import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';

export default function LandingPage() {
  const navigate = useNavigate();

  // Inject styles into the page
  useEffect(() => {
    document.title = 'LibrisAudio — Tu Biblioteca de Audiolibros con IA';
    // Intersection observer for reveal animations
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add('visible'); });
      },
      { threshold: 0.1 }
    );
    document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const goToApp = () => navigate('/library');

  return (
    <div className="landing-root">
      <style>{`
        .landing-root *, .landing-root *::before, .landing-root *::after { box-sizing: border-box; margin: 0; padding: 0; }
        .landing-root {
          font-family: 'Inter', system-ui, sans-serif;
          background: #05050f;
          color: #F8FAFC;
          overflow-x: hidden;
          min-height: 100vh;
        }
        .landing-root a { text-decoration: none; }
        .bg-orbs { position: fixed; inset: 0; pointer-events: none; z-index: 0; }
        .orb { position: absolute; border-radius: 50%; filter: blur(120px); opacity: 0.18; animation: float 12s ease-in-out infinite; }
        .orb-1 { width: 800px; height: 800px; background: #8B5CF6; top: -200px; left: -200px; animation-delay: 0s; }
        .orb-2 { width: 600px; height: 600px; background: #06B6D4; bottom: -100px; right: -100px; animation-delay: -4s; }
        .orb-3 { width: 400px; height: 400px; background: #EC4899; top: 40%; left: 40%; animation-delay: -8s; }
        @keyframes float { 0%,100%{transform:translate(0,0) scale(1);} 33%{transform:translate(30px,-30px) scale(1.05);} 66%{transform:translate(-20px,20px) scale(.97);} }
        .l-nav {
          position: fixed; top: 0; left: 0; right: 0; z-index: 100;
          display: flex; align-items: center; justify-content: space-between;
          padding: 1rem 2.5rem;
          background: rgba(5,5,15,0.7);
          backdrop-filter: blur(20px);
          border-bottom: 1px solid rgba(255,255,255,0.08);
        }
        .l-logo { display: flex; align-items: center; gap: 0.6rem; }
        .l-logo span { font-size: 1.25rem; font-weight: 800; background: linear-gradient(135deg,#A78BFA,#06B6D4); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
        .l-nav-links { display: flex; align-items: center; gap: 2.5rem; }
        .l-nav-links a { color: #94A3B8; font-size: 0.9rem; font-weight: 500; transition: color 0.2s; }
        .l-nav-links a:hover { color: #F8FAFC; }
        .btn-primary {
          background: linear-gradient(135deg,#8B5CF6,#6D28D9);
          color: #fff; border: none;
          padding: 0.7rem 1.5rem; border-radius: 999px;
          font-size: 0.9rem; font-weight: 600; cursor: pointer;
          box-shadow: 0 0 30px rgba(139,92,246,0.4);
          transition: transform 0.2s, box-shadow 0.2s;
          display: inline-flex; align-items: center; gap: 0.5rem;
        }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 0 50px rgba(139,92,246,0.55); }
        .btn-outline {
          background: rgba(255,255,255,0.04); color: #F8FAFC;
          border: 1px solid rgba(255,255,255,0.08);
          padding: 0.7rem 1.5rem; border-radius: 999px;
          font-size: 0.9rem; font-weight: 600; cursor: pointer;
          backdrop-filter: blur(12px); transition: background 0.2s, transform 0.2s;
          display: inline-flex; align-items: center; gap: 0.5rem;
        }
        .btn-outline:hover { background: rgba(255,255,255,0.09); transform: translateY(-2px); }
        section { position: relative; z-index: 1; }
        .hero {
          min-height: 100vh; display: flex; flex-direction: column;
          align-items: center; justify-content: center;
          text-align: center; padding: 8rem 2rem 6rem; gap: 1.5rem;
        }
        .hero-badge {
          display: inline-flex; align-items: center; gap: 0.5rem;
          background: rgba(139,92,246,0.15); border: 1px solid rgba(139,92,246,0.35);
          border-radius: 999px; padding: 0.35rem 1rem;
          font-size: 0.8rem; font-weight: 600; color: #A78BFA;
          animation: fadeUp 0.6s ease both;
        }
        .hero-badge .dot { width:6px;height:6px;background:#A78BFA;border-radius:50%;animation:pulse 2s infinite; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
        .hero h1 {
          font-size: clamp(2.8rem,7vw,5.5rem); font-weight: 900; line-height: 1.05;
          max-width: 900px; animation: fadeUp 0.7s ease 0.1s both;
        }
        .gradient-text { background: linear-gradient(135deg,#A78BFA 0%,#06B6D4 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
        .hero p { font-size: clamp(1rem,2vw,1.2rem); color: #94A3B8; max-width: 600px; line-height: 1.7; animation: fadeUp 0.7s ease 0.2s both; }
        .hero-buttons { display: flex; flex-wrap:wrap; gap:1rem; justify-content:center; animation: fadeUp 0.7s ease 0.3s both; }
        .hero-stats { display:flex; gap:2.5rem; flex-wrap:wrap; justify-content:center; padding-top:1rem; animation: fadeUp 0.7s ease 0.4s both; }
        .stat { display:flex; flex-direction:column; align-items:center; gap:0.25rem; }
        .stat-num { font-size:1.5rem; font-weight:800; }
        .stat-label { font-size:0.75rem; color:#94A3B8; font-weight:500; }
        @keyframes fadeUp { from{opacity:0;transform:translateY(24px)} to{opacity:1;transform:translateY(0)} }
        .reveal { opacity:0; transform:translateY(32px); transition: opacity 0.7s ease, transform 0.7s ease; }
        .reveal.visible { opacity:1; transform:translateY(0); }
        .section-header { text-align:center; margin-bottom:4rem; }
        .section-eyebrow { font-size:0.8rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; color:#A78BFA; margin-bottom:1rem; }
        .section-title { font-size: clamp(1.8rem,4vw,3rem); font-weight:800; }
        .section-sub { color:#94A3B8; font-size:1.05rem; max-width:520px; margin:0.75rem auto 0; line-height:1.7; }
        .features { padding:6rem 2rem; }
        .features-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:1.5rem; max-width:1100px; margin:0 auto; }
        .feature-card {
          background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08);
          border-radius:16px; padding:2rem;
          transition: transform 0.3s, border-color 0.3s, box-shadow 0.3s;
          position:relative;overflow:hidden;
        }
        .feature-card:hover { transform:translateY(-6px); border-color:rgba(139,92,246,0.4); box-shadow:0 24px 48px rgba(0,0,0,0.4); }
        .feature-icon { width:52px;height:52px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:1.5rem;margin-bottom:1.25rem; }
        .feature-card h3 { font-size:1.05rem;font-weight:700;margin-bottom:0.5rem; }
        .feature-card p { font-size:0.88rem;color:#94A3B8;line-height:1.65; }
        .how { padding:6rem 2rem; background:linear-gradient(180deg,transparent,rgba(139,92,246,0.04) 50%,transparent); }
        .steps { display:flex;flex-direction:column;gap:0;max-width:740px;margin:0 auto; }
        .step { display:flex;gap:2rem;align-items:flex-start;padding:2rem 0;position:relative; }
        .step:not(:last-child)::after { content:'';position:absolute;left:24px;top:72px;bottom:-8px;width:2px;background:linear-gradient(to bottom,#8B5CF6,transparent); }
        .step-num { flex-shrink:0;width:50px;height:50px;border-radius:50%;background:linear-gradient(135deg,#8B5CF6,#6D28D9);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:1.1rem;box-shadow:0 0 24px rgba(139,92,246,0.4); }
        .step h3 { font-size:1.15rem;font-weight:700;margin-bottom:0.4rem; }
        .step p { color:#94A3B8;font-size:0.9rem;line-height:1.65; }
        .voices { padding:6rem 2rem; }
        .voices-grid { display:flex;flex-wrap:wrap;gap:1rem;justify-content:center;max-width:900px;margin:0 auto; }
        .voice-chip { display:flex;align-items:center;gap:0.75rem;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:999px;padding:0.6rem 1.2rem;transition:border-color 0.2s,transform 0.2s; }
        .voice-chip:hover { border-color:#8B5CF6;transform:translateY(-2px); }
        .voice-name { font-size:0.85rem;font-weight:600;display:block; }
        .voice-country { font-size:0.72rem;color:#94A3B8;display:block; }
        .cta-section { padding:8rem 2rem;text-align:center; }
        .cta-card { max-width:800px;margin:0 auto;background:linear-gradient(135deg,rgba(139,92,246,0.12),rgba(6,182,212,0.06));border:1px solid rgba(139,92,246,0.3);border-radius:28px;padding:5rem 3rem;position:relative;overflow:hidden; }
        .cta-card::before { content:'';position:absolute;width:400px;height:400px;border-radius:50%;background:rgba(139,92,246,0.15);filter:blur(80px);top:-100px;left:50%;transform:translateX(-50%);pointer-events:none; }
        .cta-card h2 { font-size:clamp(1.8rem,4vw,2.8rem);font-weight:900;margin-bottom:1rem;position:relative; }
        .cta-card p { color:#94A3B8;font-size:1.05rem;max-width:480px;margin:0 auto 2rem;line-height:1.7;position:relative; }
        .l-footer { border-top:1px solid rgba(255,255,255,0.08);padding:2.5rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;position:relative;z-index:1; }
        .l-footer-logo { font-size:1rem;font-weight:800;background:linear-gradient(135deg,#A78BFA,#06B6D4);-webkit-background-clip:text;-webkit-text-fill-color:transparent; }
        .l-footer p { font-size:0.82rem;color:#94A3B8; }
        @media(max-width:768px) { .l-nav { padding:1rem; } .l-nav-links { display:none; } .cta-card { padding:3rem 1.5rem; } .l-footer { flex-direction:column;text-align:center; } }

        /* ── FLOATING BUTTON ── */
        .landing-floating-btn {
          position: fixed; bottom: 2rem; right: 2rem; z-index: 99;
          background: linear-gradient(135deg, #06B6D4, #8B5CF6);
          color: #fff; width: 60px; height: 60px; border-radius: 50%;
          display: flex; align-items: center; justify-content: center;
          text-decoration: none; box-shadow: 0 10px 25px rgba(6,182,212,0.4);
          transition: transform 0.2s, box-shadow 0.2s;
        }
        .landing-floating-btn:hover { transform: translateY(-4px) scale(1.05); box-shadow: 0 15px 35px rgba(6,182,212,0.6); }
        .landing-floating-btn svg { width: 26px; height: 26px; }
        .landing-floating-tooltip {
          position: absolute; right: 75px; background: #0d0d1f; border: 1px solid rgba(255,255,255,0.08);
          padding: 0.5rem 0.8rem; border-radius: 8px; font-size: 0.85rem; font-weight: 500;
          white-space: nowrap; opacity: 0; pointer-events: none; transition: opacity 0.2s, transform 0.2s;
          transform: translateX(10px);
        }
        .landing-floating-btn:hover .landing-floating-tooltip { opacity: 1; transform: translateX(0); }
      `}</style>

      {/* Background orbs */}
      <div className="bg-orbs">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />
      </div>

      {/* NAV */}
      <nav className="l-nav">
        <div className="l-logo">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="url(#g1)" />
            <path d="M9 10h9M9 14h12M9 18h8" stroke="white" strokeWidth="2" strokeLinecap="round"/>
            <circle cx="23" cy="22" r="5" fill="white" fillOpacity="0.2" stroke="white" strokeWidth="1.5"/>
            <polygon points="21.5,20.5 21.5,23.5 24,22" fill="white"/>
            <defs><linearGradient id="g1" x1="0" y1="0" x2="32" y2="32"><stop offset="0%" stopColor="#8B5CF6"/><stop offset="100%" stopColor="#06B6D4"/></linearGradient></defs>
          </svg>
          <span>LibrisAudio</span>
        </div>
        <div className="l-nav-links">
          <a href="#features">Características</a>
          <a href="#how">Cómo funciona</a>
          <a href="#voices">Voces</a>
        </div>
        <button className="btn-primary" onClick={goToApp}>Abrir App →</button>
      </nav>

      {/* HERO */}
      <section className="hero">
        <div className="hero-badge"><span className="dot" /> Biblioteca comunitaria de audiolibros generados por IA</div>
        <h1><span className="gradient-text">Convierte y Comparte</span> tus PDFs en Audiolibros</h1>
        <p>Aporta a nuestra comunidad subiendo tus libros favoritos en PDF, o explora los que otros ya han compartido. Crea tu cuenta gratis para guardar tu progreso en la nube y retoma tus lecturas exactamente donde las dejaste.</p>
        <div className="hero-buttons">
          <button className="btn-primary" onClick={goToApp}>
            ▶ Explorar la Biblioteca
          </button>
          <a href="#how" className="btn-outline">Ver cómo funciona →</a>
        </div>
        <div className="hero-stats">
          <div className="stat"><span className="stat-num">34+</span><span className="stat-label">Categorías</span></div>
          <div className="stat"><span className="stat-num">30+</span><span className="stat-label">Voces neurales</span></div>
          <div className="stat"><span className="stat-num">☁️</span><span className="stat-label">Progreso en la nube</span></div>
          <div className="stat"><span className="stat-num">0€</span><span className="stat-label">Costo total</span></div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="features" id="features">
        <div className="section-header reveal">
          <div className="section-eyebrow">Características</div>
          <h2 className="section-title">Todo lo que necesitas para escuchar</h2>
          <p className="section-sub">Diseñado para ser el reproductor de audiolibros más poderoso y elegante.</p>
        </div>
        <div className="features-grid">
          {[
            { icon: '🎙️', bg: 'rgba(139,92,246,0.15)', title: 'Voces Neurales de IA', desc: 'Integrado con la tecnología de voz de Microsoft Azure. Voces naturales en español, inglés, portugués y más de 30 idiomas.' },
            { icon: '⚡', bg: 'rgba(6,182,212,0.15)', title: 'Carga Instantánea (JIT)', desc: 'No esperarás a que procese todo el libro. La primera parte lista en segundos mientras el resto se genera en el fondo.' },
            { icon: '💾', bg: 'rgba(248,113,113,0.15)', title: 'Historial Persistente', desc: 'Tu progreso se guarda automáticamente. Vuelve al punto exacto donde lo dejaste, incluso cerrando el navegador.' },
            { icon: '📑', bg: 'rgba(52,211,153,0.15)', title: 'Navegación por Partes', desc: 'Salta directamente a cualquier capítulo con un solo clic. El libro se divide inteligentemente en partes.' },
            { icon: '🗂️', bg: 'rgba(251,191,36,0.15)', title: '34 Géneros Literarios', desc: 'Organiza tu biblioteca con categorías personalizables: Filosofía, Ciencia Ficción, Historia, Romance y más.' },
            { icon: '📲', bg: 'rgba(167,139,250,0.15)', title: 'Instalable como App', desc: 'Funciona como app nativa gracias a la tecnología PWA. Instálala en tu computadora o teléfono con un clic.' },
          ].map((f, i) => (
            <div key={i} className="feature-card reveal">
              <div className="feature-icon" style={{ background: f.bg }}>{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="how" id="how">
        <div className="section-header reveal">
          <div className="section-eyebrow">Pasos</div>
          <h2 className="section-title">Tan simple como 1, 2, 3</h2>
          <p className="section-sub">Empieza a escuchar tus obras favoritas o contribuye a la comunidad.</p>
        </div>
        <div className="steps">
          {[
            { title: 'Explora o Sube tu Libro', desc: 'Revisa nuestra biblioteca para ver si alguien ya subió el libro que buscas. Si no está, súbelo tú mismo (máx 10 MB) para alimentar a la comunidad.' },
            { title: 'Crea una cuenta para guardar progreso', desc: 'Al registrarte, la app sincroniza exactamente en qué segundo dejaste tu lectura para que continúes sin importar el dispositivo.' },
            { title: '¿Libro muy pesado? ¡Solicítalo!', desc: 'Para libros grandes e intensos que superen los 10 MB, usa el botón de "Solicitar", y nuestro equipo se encargará de procesarlos.' },
          ].map((s, i) => (
            <div key={i} className="step reveal">
              <div className="step-num">{i + 1}</div>
              <div>
                <h3>{s.title}</h3>
                <p>{s.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* VOICES */}
      <section className="voices" id="voices">
        <div className="section-header reveal">
          <div className="section-eyebrow">Voces disponibles</div>
          <h2 className="section-title">Narrado por voces que amará tu oído</h2>
          <p className="section-sub">100% neurales impulsadas por la IA de Microsoft. Sin sonido robótico.</p>
        </div>
        <div className="voices-grid reveal">
          {[
            { flag: '🇪🇸', name: 'Elvira', country: 'España · Mujer' },
            { flag: '🇪🇸', name: 'Álvaro', country: 'España · Hombre' },
            { flag: '🇲🇽', name: 'Dalia', country: 'México · Mujer' },
            { flag: '🇲🇽', name: 'Jorge', country: 'México · Hombre' },
            { flag: '🇦🇷', name: 'Elena', country: 'Argentina · Mujer' },
            { flag: '🇦🇷', name: 'Tomás', country: 'Argentina · Hombre' },
            { flag: '🇨🇴', name: 'Salome', country: 'Colombia · Mujer' },
            { flag: '🇻🇪', name: 'Paola', country: 'Venezuela · Mujer' },
            { flag: '🇺🇸', name: 'Aria', country: 'USA · Mujer' },
            { flag: '🇺🇸', name: 'Guy', country: 'USA · Hombre' },
            { flag: '🇧🇷', name: 'Francisca', country: 'Brasil · Mujer' },
            { flag: '🇫🇷', name: 'Denise', country: 'Francia · Mujer' },
          ].map((v, i) => (
            <div key={i} className="voice-chip">
              <span style={{ fontSize: '1.2rem' }}>{v.flag}</span>
              <div><span className="voice-name">{v.name}</span><span className="voice-country">{v.country}</span></div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="cta-section">
        <div className="cta-card reveal">
          <h2>Tu próximo audiolibro te está<br /><span className="gradient-text">esperando</span></h2>
          <p>Entra a la biblioteca, elige tu próximo título y deja que la IA te lea mientras conduces, haces ejercicio o te relajas.</p>
          <button className="btn-primary" onClick={goToApp}>
            ▶ Entrar a LibrisAudio
          </button>
        </div>
      </section>

      {/* FLOATING BUTTON */}
      <a href="mailto:admin@librisaudio.com?subject=Solicitud de Libro Nuevo" className="landing-floating-btn" aria-label="Solicitar Libro">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
        <div className="landing-floating-tooltip">¿Falta un libro? ¡Solicítalo!</div>
      </a>

      {/* FOOTER */}
      <footer className="l-footer">
        <span className="l-footer-logo">📚 LibrisAudio</span>
        <p>Hecho con ❤️ · Potenciado por Microsoft Edge TTS</p>
        <p style={{ fontSize: '0.75rem' }}>© 2025 LibrisAudio. Todos los derechos reservados.</p>
      </footer>
    </div>
  );
}
