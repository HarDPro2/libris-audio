import { emblemBase64 } from './AuthorSignatureAssets';

/**
 * @name AuthorSignature
 * @description Universal, adaptive Developer Signature component.
 * It is completely self-contained and injects its own CSS to avoid dependencies.
 *
 * It defaults to a sleek dark-glass style but uses 'currentColor' hooks
 * to easily adapt to any project's theme.
 */
export default function AuthorSignature({ 
  className = "", 
  adaptive = false, 
  glowColor1 = "hsl(187, 80%, 45%)", // Cyan
  glowColor2 = "hsl(263, 70%, 58%)"  // Purple
}) {
  const containerStyle = adaptive 
    ? "backdrop-blur-xl border border-current/10 bg-current/5" 
    : "backdrop-blur-xl border border-[rgba(34,211,238,0.1)] bg-[rgba(15,23,42,0.4)]";

  const textColor = adaptive ? "text-current" : "text-[hsl(215,16%,47%)]"; // muted-foreground equivalent
  const titleColor = adaptive ? "text-current opacity-90" : "text-[#f8fafc]";

  return (
    <div className={`w-full max-w-2xl mx-auto mt-12 mb-8 px-4 ${className}`} style={adaptive ? { color: 'inherit' } : {}}>
      <div 
        className={`rounded-xl p-10 text-center shadow-2xl overflow-hidden relative ${containerStyle}`}
        style={adaptive ? { borderTopColor: 'inherit' } : { borderTopColor: 'rgba(34,211,238,0.2)' }}
      >
        {/* Glow overlay effect independent of Tailwind */}
        <div 
          className="absolute -top-24 -left-24 w-96 h-96 rounded-full mix-blend-screen opacity-10 pointer-events-none"
          style={{ background: `radial-gradient(circle, ${glowColor1} 0%, transparent 70%)` }}
        />

        {/* Top label */}
        <p className={`text-xs uppercase tracking-[0.3em] mb-8 font-mono opacity-80 ${textColor}`}>
          La calidad de este ecosistema está garantizada por su creador
        </p>

        {/* Emblem */}
        <div className="flex justify-center mb-8 relative">
          <div className="relative">
            <div
              className="absolute inset-0 rounded-full blur-2xl opacity-45"
              style={{ background: `linear-gradient(135deg, ${glowColor1}, ${glowColor2})` }}
            />
            <img
              src={emblemBase64}
              alt="Author Emblem"
              width={120}
              height={120}
              loading="lazy"
              className="relative z-10 drop-shadow-[0_0_15px_rgba(255,255,255,0.1)] hover:scale-105 transition-transform duration-500"
              style={{ animation: 'float 6s ease-in-out infinite' }}
            />
          </div>
        </div>

        {/* Author name */}
        <div className="mb-4">
          <span className={`text-sm font-mono tracking-widest opacity-80 ${textColor}`}>Desarrollador Independiente: </span>
          <span 
            className="text-lg font-black tracking-wide bg-clip-text text-transparent"
            style={{ backgroundImage: `linear-gradient(90deg, ${glowColor1}, ${glowColor2})` }}
          >
            HarD P.
          </span>
        </div>

        <p className={`text-sm opacity-90 mb-1 font-medium ${titleColor}`}>Código con propósito · Soluciones digitales</p>
        <p className={`text-xs opacity-60 font-mono ${textColor}`}>Ingeniería independiente · Diseño con propósito</p>
        
        <style dangerouslySetInnerHTML={{__html: `
          @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
          }
        `}} />
      </div>
    </div>
  );
}
