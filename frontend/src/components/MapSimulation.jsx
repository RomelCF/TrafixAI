import { useState, useRef, useEffect } from 'react'

const ZONAS_CENTRO = [
  { key: 'Centro histórico', label: 'Centro Histórico' },
  { key: 'San Blas',         label: 'San Blas' },
  { key: 'San Pedro',        label: 'San Pedro' },
  { key: 'Eje Av. El Sol',   label: 'Av. El Sol' },
]

const ZONAS_ANGOSTURA = [
  { key: 'Calle 1',   label: 'Calle 1 (Evit.)' },
  { key: 'Calle 2',   label: 'Calle 2' },
  { key: 'Calle 3-4', label: 'Calles 3-4' },
  { key: 'Calle 5-6', label: 'Calles 5-6' },
  { key: 'Zona Norte',label: 'Zona Norte' },
]

function estilosNivel(nivel) {
  switch (nivel) {
    case 'Crítico':       return 'bg-[#fca5a5]/10 border-[#fca5a5]/30 text-[#fca5a5]'
    case 'Congestionado': return 'bg-[#fbbf24]/15 border-[#fbbf24]/30 text-[#fbbf24]'
    case 'Moderado':      return 'bg-[#fbbf24]/10 border-[#fbbf24]/20 text-[#fbbf24]'
    default:              return 'bg-[#22d3ee]/10 border-[#22d3ee]/30 text-[#22d3ee]'
  }
}

export default function SimulacionMapa({ metrics, streamUrl, localidad = 'centro_historico' }) {
  const [imgError, setImgError]       = useState(false)
  const [fullscreen, setFullscreen]   = useState(false)
  const imgRef = useRef(null)

  useEffect(() => {
    setImgError(false)
  }, [streamUrl, localidad])

  useEffect(() => {
    if (metrics) setImgError(false)
  }, [metrics])

  const isCentro  = localidad === 'centro_historico'
  const zonasDef  = isCentro ? ZONAS_CENTRO : ZONAS_ANGOSTURA
  const zonasData = metrics?.zonas ?? {}

  const horaSimulada = metrics?.hora_simulada ?? '—:—'
  const cong = metrics?.globales?.congestion_global ?? 0
  const tendenciaPositiva = cong <= 55
  const tendencia = tendenciaPositiva ? '-8% Proyectado (15m)' : '+3% Proyectado (15m)'

  const nombreLocalidad = isCentro ? 'Centro Histórico' : 'Sector Angostura'

  return (
    <div className={`md:col-span-6 flex flex-col gap-[12px] order-1 md:order-2 ${fullscreen ? 'fixed inset-0 z-[150] p-4 bg-[#0a0818]' : ''}`}>
      <div className="glass-panel rounded-xl overflow-hidden flex-1 flex flex-col relative border border-[#adc6ff]/20 min-h-[400px] md:min-h-[600px] lg:min-h-[800px]">

        <div className="p-4 border-b border-[#374151] flex justify-between items-center bg-[#120e2a] shrink-0">
          <h3 className="font-[Hanken_Grotesk] text-[11px] font-bold uppercase tracking-wider flex items-center gap-2 text-[#e8e0f5]">
            <span className="material-symbols-outlined text-[18px]">videocam</span>
            Simulación en tiempo real — {nombreLocalidad}
          </h3>

          <div className="flex items-center gap-4">
            
            <span className="hidden sm:flex text-[10px] font-[Hanken_Grotesk] font-bold text-[#c4b5fd] items-center gap-2 uppercase tracking-wider">
              <span className={`w-2 h-2 rounded-full ${imgError ? 'bg-[#fca5a5]' : 'bg-[#22d3ee] ai-pulse'}`} />
              {imgError ? 'SIN SEÑAL' : 'VIVO'}
            </span>

            <span className="text-[10px] font-[JetBrains_Mono] text-[#c4b5fd]/60">
              🕐 {horaSimulada}
            </span>

            <button
              onClick={() => setFullscreen(f => !f)}
              className="p-1 hover:bg-[#2d2847] rounded text-[#c4b5fd] transition-colors cursor-pointer"
              title={fullscreen ? 'Salir de pantalla completa' : 'Pantalla completa'}
            >
              <span className="material-symbols-outlined text-[20px]">
                {fullscreen ? 'fullscreen_exit' : 'fullscreen'}
              </span>
            </button>
          </div>
        </div>

        <div className="relative flex-1 bg-[#060e20] overflow-hidden flex items-center justify-center">
          {!imgError ? (
            <img
              key={localidad}
              ref={imgRef}
              src={streamUrl}
              alt={`Simulación Pygame — ${nombreLocalidad}`}
              className="absolute inset-0 w-full h-full object-contain"
              onError={() => setImgError(true)}
              onLoad={()  => setImgError(false)}
            />
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-4">
              <span className="material-symbols-outlined text-[48px] text-[#374151]">videocam_off</span>
              <p className="text-[#8b90a0] text-[12px] font-[Hanken_Grotesk] font-bold uppercase tracking-wider">
                Backend no disponible
              </p>
              <p className="text-[#374151] text-[10px] font-[JetBrains_Mono]">
                Inicia: cd backend → uvicorn main:app
              </p>
            </div>
          )}
        </div>

        <div className="p-4 md:p-0 md:absolute md:bottom-6 md:left-6 md:right-6 z-20 flex flex-wrap items-center justify-between gap-4 pointer-events-none">

          <div className={`glass-panel px-4 py-2 rounded-lg border-l-4 pointer-events-auto shrink-0 flex flex-col justify-center ${tendenciaPositiva ? 'border-[#22d3ee]' : 'border-[#fca5a5]'}`}>
            <p className="text-[8px] font-[Hanken_Grotesk] font-bold text-[#c4b5fd]/60 tracking-widest mb-1 uppercase">
              Tendencia Actual
            </p>
            <p className={`flex items-center gap-2 font-bold text-[11px] font-[JetBrains_Mono] ${tendenciaPositiva ? 'text-[#22d3ee]' : 'text-[#fca5a5]'}`}>
              <span className="material-symbols-outlined text-[14px]">
                {tendenciaPositiva ? 'trending_down' : 'trending_up'}
              </span>
              {tendencia}
            </p>
          </div>

          {!imgError && (
            <div className="flex flex-wrap items-center justify-center gap-2 pointer-events-auto">
              {zonasDef.map(({ key, label }) => {
                const data  = zonasData?.[key]
                const nivel = data?.nivel ?? '—'
                const congVal = data ? `${Number(data.congestion ?? 0).toFixed(0)}%` : '...'
                const displayText = (nivel === 'Crítico' ? 'CRÍTICO'
                                   : nivel === 'Fluido'  ? 'FLUIDO'
                                   : congVal)
                return (
                  <div
                    key={key}
                    className={`border px-3 py-1.5 text-center rounded-xl backdrop-blur-md transition-all duration-300 min-w-[95px] flex flex-col items-center justify-center ${estilosNivel(nivel)}`}
                  >
                    <span className="text-[8px] font-bold block mb-0.5 font-[Hanken_Grotesk] uppercase tracking-wider text-white/70">
                      {label}
                    </span>
                    <span className="text-[13px] font-[JetBrains_Mono] font-bold text-white">
                      {displayText}
                    </span>
                    {data && (
                      <div className="text-[7px] text-white/50 font-[Hanken_Grotesk] mt-0.5">
                        {data.vehiculos} veh · {data.detenidos} det
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}

          {metrics && (
            <div className="glass-panel px-4 py-2 rounded-lg pointer-events-auto shrink-0 flex flex-col justify-center">
              <p className="text-[8px] font-[Hanken_Grotesk] font-bold text-[#c4b5fd]/60 tracking-widest mb-1 uppercase">
                Congestión Global
              </p>
              <p className={`text-[16px] font-bold font-[JetBrains_Mono] ${cong > 60 ? 'text-[#fca5a5]' : cong > 35 ? 'text-[#fbbf24]' : 'text-[#22d3ee]'}`}>
                {cong.toFixed(1)}%
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
