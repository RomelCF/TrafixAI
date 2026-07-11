import { useState } from 'react'

const ESTILOS_ETIQUETAS = {
  'IA: Ingreso reducido':   'bg-[#ffb4ab]/20 text-[#ffb4ab]',
  'IA: Ingreso normalizado':'bg-[#4edea3]/20 text-[#4edea3]',
  'IA: Desvio activo':      'bg-[#ffb95f]/20 text-[#ffb95f]',
  'IA: Desvio cancelado':   'bg-[#4edea3]/20 text-[#4edea3]',
  'IA: Activada':           'bg-[#4edea3]/20 text-[#4edea3]',
  'IA: Desactivada':        'bg-[#ffb4ab]/20 text-[#ffb4ab]',
  'IA: Semáforo':           'bg-[#adc6ff]/20 text-[#adc6ff]',
  'IA: Benchmark':          'bg-[#2d3449] text-[#c1c6d7]',
  'default':                'bg-[#2d3449] text-[#c1c6d7]',
}

function obtenerEstiloEtiqueta(texto) {
  for (const [clave, estilo] of Object.entries(ESTILOS_ETIQUETAS)) {
    if (texto.startsWith(clave)) return estilo
  }
  return ESTILOS_ETIQUETAS.default
}

function obtenerEtiqueta(texto) {
  if (texto.includes('Ingreso reducido') || texto.includes('Desvio activo')) return 'Acceso'
  if (texto.includes('Ingreso normalizado') || texto.includes('Desvio cancelado')) return 'Ruta'
  if (texto.includes('Semáforo') || texto.includes('semáforos') || texto.includes('verde')) return 'Semáforo'
  if (texto.includes('Activada') || texto.includes('Desactivada') || texto.includes('reiniciada')) return 'Sistema'
  if (texto.includes('desviados')) return 'Ruta'
  return 'Sistema'
}

function obtenerHoraActual() {
  const ahora = new Date()
  return `${String(ahora.getHours()).padStart(2,'0')}:${String(ahora.getMinutes()).padStart(2,'0')}`
}

export default function ColumnaDerecha({ metrics, loading, enviarControl, localidad = 'centro_historico' }) {
  const logAcciones = metrics?.log_acciones || []
  const recomendaciones = metrics?.recomendaciones || []
  const impacto = metrics?.impacto_predictivo || []
  const iaActiva = metrics?.ia_activa ?? true
  const pausado = metrics?.pausado ?? false
  const [showRecs, setShowRecs] = useState(false)

  const isCentro = localidad === 'centro_historico'
  const mainRec = recomendaciones[0] || (isCentro 
    ? 'Sistema estable: monitoreando red vial de Cusco.' 
    : 'Sector Angostura estable: monitoreando red vial.')

  const recParts = mainRec.split(/(\bCentro histórico\b|\bSan Pedro\b|\bSan Blas\b|\bEje Av\. El Sol\b|\bZona Este\b|\bCalle 1\b|\bCalle 2\b|\bCalle 3\-4\b|\bCalle 5\-6\b|\bZona Norte\b)/gi)

  return (
    <div className="md:col-span-3 flex flex-col gap-[12px] order-3">

      <div className="glass-panel rounded-xl p-4 border-l-4 border-[#adc6ff]">
        <h3 className="font-[Hanken_Grotesk] text-[11px] font-bold uppercase tracking-wider flex items-center gap-2 text-[#dae2fd] mb-3">
          <span className="material-symbols-outlined text-[18px]">chat_bubble</span>
          Módulo IA <span className="text-[#adc6ff]/60 ml-1 normal-case">v3</span>
        </h3>
        <div className="font-[JetBrains_Mono] text-[11px] leading-relaxed text-[#dae2fd]/80 min-h-[48px]">
          {loading ? (
            <div className="space-y-2 animate-pulse">
              <div className="h-3 bg-[#414755]/40 rounded w-full" />
              <div className="h-3 bg-[#414755]/40 rounded w-4/5" />
            </div>
          ) : (
            <p>
              {recParts.map((part, i) => {
                const isZone = /Centro histórico|San Pedro|San Blas|Eje Av\. El Sol|Zona Este|Calle 1|Calle 2|Calle 3-4|Calle 5-6|Zona Norte/i.test(part)
                return isZone
                  ? <span key={i} className="text-[#ffb95f] font-bold">{part}</span>
                  : <span key={i}>{part}</span>
              })}
            </p>
          )}
        </div>

        <div className="mt-4">
          <button
            className={`w-full py-1.5 rounded text-[9px] font-[Hanken_Grotesk] font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-1 border ${
              showRecs
                ? 'bg-[#adc6ff]/15 border-[#adc6ff]/40 text-[#adc6ff]'
                : 'bg-[#2d3449] border-[#414755] text-[#c1c6d7] hover:bg-[#adc6ff]/10 hover:border-[#adc6ff]/30 hover:text-[#adc6ff]'
            }`}
            onClick={() => setShowRecs(v => !v)}
          >
            <span className="material-symbols-outlined text-[13px]">
              {showRecs ? 'expand_less' : 'expand_more'}
            </span>
            {showRecs ? 'CERRAR' : 'EXPLICAR'}
          </button>

          {showRecs && (
            <div className="mt-3 space-y-2 border-t border-[#414755]/40 pt-3 max-h-[280px] overflow-y-auto">
              {recomendaciones.length > 0 ? (
                recomendaciones.map((rec, i) => (
                  <div
                    key={i}
                    className="flex gap-3 items-start p-2.5 rounded-lg bg-[#131b2e]/60 border border-[#414755]/20 hover:border-[#adc6ff]/20 transition-colors"
                  >
                    <span className="shrink-0 w-5 h-5 rounded-full bg-[#adc6ff]/15 text-[#adc6ff] text-[9px] font-bold font-[JetBrains_Mono] flex items-center justify-center mt-0.5">
                      {i + 1}
                    </span>
                    <p className="text-[10px] font-[JetBrains_Mono] text-[#dae2fd]/80 leading-relaxed">{rec}</p>
                  </div>
                ))
              ) : (
                <p className="text-[#414755] text-[10px] font-[Hanken_Grotesk] text-center py-2">
                  Sin recomendaciones activas
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="glass-panel rounded-xl p-4 flex flex-col flex-1 min-h-[300px] overflow-hidden">
        <h3 className="font-[Hanken_Grotesk] text-[11px] font-bold uppercase tracking-wider flex items-center gap-2 mb-4 text-[#dae2fd]">
          <span className="material-symbols-outlined text-[18px]">list_alt</span>
          Log de Acciones
        </h3>
        <div className="space-y-4 font-[JetBrains_Mono] text-[10px] overflow-y-auto flex-1 pr-1">
          {loading ? (
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex gap-3 animate-pulse">
                <div className="h-3 w-10 bg-[#414755]/40 rounded" />
                <div className="flex-1 space-y-1">
                  <div className="h-3 w-16 bg-[#414755]/40 rounded" />
                  <div className="h-3 bg-[#414755]/30 rounded" />
                </div>
              </div>
            ))
          ) : logAcciones.length > 0 ? (
            logAcciones.map((entry, i) => {
              const tag = obtenerEtiqueta(entry)
              const tagStyle = obtenerEstiloEtiqueta(entry)
              return (
                <div key={i} className="flex gap-3 items-start">
                  <span className="opacity-40 shrink-0 mt-0.5">{obtenerHoraActual()}</span>
                  <div className="flex-1">
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold mb-1 inline-block uppercase ${tagStyle}`}>
                      {tag}
                    </span>
                    <p className="text-[#dae2fd]/70 leading-tight">{entry.replace(/^IA:\s*/, '')}</p>
                  </div>
                </div>
              )
            })
          ) : (
            <p className="text-[#414755] text-center text-[10px] pt-4">Sin acciones registradas</p>
          )}
        </div>
      </div>

      <div className="glass-panel rounded-xl p-4">
        <h3 className="font-[Hanken_Grotesk] text-[11px] font-bold uppercase tracking-wider flex items-center gap-2 mb-4 text-[#dae2fd]">
          <span className="material-symbols-outlined text-[18px]">troubleshoot</span>
          Impacto Predictivo
        </h3>
        <div className="space-y-2">
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-8 bg-[#2d3449]/30 rounded animate-pulse" />
            ))
          ) : impacto.length > 0 ? (
            impacto.slice(0, 4).map((item, i) => (
              <div key={i} className="flex justify-between items-center text-[10px] p-2 bg-[#2d3449]/30 rounded border border-[#414755]/10">
                <span className="text-[#c1c6d7] truncate max-w-[140px]">
                  {item.zona?.replace('Centro histórico', 'Centro Hist.').replace('Eje Av. El Sol', 'Av. El Sol')}: {item.accion}
                </span>
                <span className="font-bold font-[JetBrains_Mono] text-[#4edea3] ml-2 shrink-0">{item.mejora_vel}</span>
              </div>
            ))
          ) : (
            <>
              <div className="flex justify-between items-center text-[10px] p-2 bg-[#2d3449]/30 rounded border border-[#414755]/10">
                <span className="text-[#c1c6d7]">Red estable</span>
                <span className="font-bold font-[JetBrains_Mono] text-[#4edea3]">Sin acción</span>
              </div>
            </>
          )}
        </div>
      </div>

    </div>
  )
}
