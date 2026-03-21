import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function AuthPage() {
  const { signIn, signUp } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    if (tab === 'login') {
      const { error } = await signIn(email, password);
      if (error) { setError(error); setLoading(false); return; }
      navigate('/library');
    } else {
      const { error } = await signUp(email, password);
      if (error) { setError(error); setLoading(false); return; }
      setSuccess(true);
    }
    setLoading(false);
  };

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'linear-gradient(135deg, #05050f 0%, #0d0d2f 100%)',
      fontFamily: "'Inter', system-ui, sans-serif",
      position: 'relative', overflow: 'hidden',
    }}>
      {/* Orbs */}
      <div style={{ position:'fixed', inset:0, pointerEvents:'none', zIndex:0 }}>
        <div style={{ position:'absolute', width:600, height:600, borderRadius:'50%', background:'#8B5CF6', filter:'blur(140px)', opacity:0.12, top:-100, left:-100 }} />
        <div style={{ position:'absolute', width:400, height:400, borderRadius:'50%', background:'#06B6D4', filter:'blur(140px)', opacity:0.1, bottom:-50, right:-50 }} />
      </div>

      <div style={{
        position:'relative', zIndex:1, width:'100%', maxWidth:440,
        margin:'2rem', padding:'2.5rem',
        background:'rgba(255,255,255,0.04)',
        border:'1px solid rgba(255,255,255,0.09)',
        borderRadius:24, backdropFilter:'blur(20px)',
        boxShadow:'0 32px 80px rgba(0,0,0,0.5)',
      }}>
        {/* Logo */}
        <div style={{ textAlign:'center', marginBottom:'2rem' }}>
          <div style={{ fontSize:'2rem', marginBottom:'0.5rem' }}>📚</div>
          <h1 style={{ fontSize:'1.5rem', fontWeight:800, background:'linear-gradient(135deg,#A78BFA,#06B6D4)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent', margin:0 }}>
            LibrisAudio
          </h1>
          <p style={{ color:'#94A3B8', fontSize:'0.85rem', marginTop:'0.25rem' }}>Tu biblioteca de audiolibros con IA</p>
        </div>

        {/* Tabs */}
        <div style={{ display:'flex', background:'rgba(255,255,255,0.05)', borderRadius:12, padding:4, marginBottom:'1.75rem' }}>
          {(['login','register'] as const).map(t => (
            <button key={t} onClick={() => { setTab(t); setError(null); setSuccess(false); }} style={{
              flex:1, padding:'0.6rem', borderRadius:9, border:'none', cursor:'pointer', fontWeight:600, fontSize:'0.88rem', transition:'all 0.2s',
              background: tab === t ? 'linear-gradient(135deg,#8B5CF6,#6D28D9)' : 'transparent',
              color: tab === t ? '#fff' : '#94A3B8',
              boxShadow: tab === t ? '0 4px 12px rgba(139,92,246,0.4)' : 'none',
            }}>
              {t === 'login' ? 'Iniciar sesión' : 'Registrarse'}
            </button>
          ))}
        </div>

        {success ? (
          <div style={{ textAlign:'center', padding:'1.5rem', background:'rgba(52,211,153,0.1)', border:'1px solid rgba(52,211,153,0.3)', borderRadius:12 }}>
            <div style={{ fontSize:'2rem', marginBottom:'0.5rem' }}>✉️</div>
            <p style={{ color:'#34D399', fontWeight:600, marginBottom:'0.5rem' }}>¡Revisa tu correo!</p>
            <p style={{ color:'#94A3B8', fontSize:'0.85rem' }}>Te enviamos un enlace de confirmación. Después de confirmar, podrás iniciar sesión.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ display:'flex', flexDirection:'column', gap:'1rem' }}>
            <div>
              <label style={{ color:'#94A3B8', fontSize:'0.8rem', fontWeight:600, display:'block', marginBottom:'0.4rem' }}>Correo electrónico</label>
              <input
                type="email" value={email} onChange={e => setEmail(e.target.value)} required
                placeholder="tu@correo.com"
                style={{
                  width:'100%', padding:'0.75rem 1rem', background:'rgba(255,255,255,0.06)',
                  border:'1px solid rgba(255,255,255,0.1)', borderRadius:10, color:'#F8FAFC',
                  fontSize:'0.95rem', outline:'none', boxSizing:'border-box',
                }}
              />
            </div>
            <div>
              <label style={{ color:'#94A3B8', fontSize:'0.8rem', fontWeight:600, display:'block', marginBottom:'0.4rem' }}>Contraseña</label>
              <input
                type="password" value={password} onChange={e => setPassword(e.target.value)} required
                placeholder="••••••••"
                style={{
                  width:'100%', padding:'0.75rem 1rem', background:'rgba(255,255,255,0.06)',
                  border:'1px solid rgba(255,255,255,0.1)', borderRadius:10, color:'#F8FAFC',
                  fontSize:'0.95rem', outline:'none', boxSizing:'border-box',
                }}
              />
            </div>

            {error && (
              <div style={{ background:'rgba(239,68,68,0.1)', border:'1px solid rgba(239,68,68,0.3)', borderRadius:8, padding:'0.75rem 1rem', color:'#FCA5A5', fontSize:'0.85rem' }}>
                {error}
              </div>
            )}

            <button type="submit" disabled={loading} style={{
              background:'linear-gradient(135deg,#8B5CF6,#6D28D9)',
              color:'#fff', border:'none', padding:'0.85rem',
              borderRadius:12, fontWeight:700, fontSize:'1rem', cursor:'pointer',
              boxShadow:'0 0 30px rgba(139,92,246,0.4)',
              opacity: loading ? 0.7 : 1,
              transition:'opacity 0.2s, transform 0.2s',
            }}>
              {loading ? 'Procesando...' : tab === 'login' ? '→ Entrar a mi biblioteca' : '→ Crear mi cuenta'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
