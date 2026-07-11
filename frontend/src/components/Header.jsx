import { useEffect, useState } from 'react'

export default function Cabecera({ metrics, enviarControl, hasError, localidad = 'centro_historico', setLocalidad }) {
  const [clock, setClock] = useState('')

  useEffect(() => {
    const marcarSegundo = () => {
      const now = new Date()
      setClock(`${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}`)
    }
    marcarSegundo()
    const id = setInterval(marcarSegundo, 1000)
    return () => clearInterval(id)
  }, [])

  const iaActiva = metrics?.ia_activa ?? true
  const pausado  = metrics?.pausado  ?? false
  const horaSimulada = metrics?.hora_simulada ?? '—:—'

  return (
    <header className={`sticky top-0 z-[100] flex flex-col md:flex-row justify-between items-center px-[24px] py-3 w-full bg-[#0a0818] border-b border-[#374151] shadow-md gap-4 ${hasError ? 'mt-10' : ''}`}>

      <div className="flex items-center gap-6 w-full md:w-auto">
        <h1 className="text-[18px] md:text-[24px] font-bold text-[#e8e0f5] tracking-tight truncate leading-tight font-[Hanken_Grotesk]">
          TrafixAI
        </h1>
        <div className="hidden sm:flex items-center gap-6 border-l border-[#374151] pl-6">
          <span className="font-[JetBrains_Mono] text-[12px] text-[#c4b5fd] flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px]">schedule</span>
            {clock}
          </span>
          {metrics && (
            <span className="font-[JetBrains_Mono] text-[11px] text-[#c4b5fd]/70 flex items-center gap-1">
              <span className="material-symbols-outlined text-[13px]">sim_card</span>
              {horaSimulada}h sim.
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 flex-wrap justify-center md:justify-end w-full md:w-auto">

        <div className="relative flex items-center">
          <select
            id="locality-select"
            value={localidad}
            onChange={(e) => setLocalidad?.(e.target.value)}
            className="appearance-none bg-[#2d2847] border border-[#374151] text-[#c4b5fd] pl-3 pr-8 py-1.5 rounded text-[10px] font-[Hanken_Grotesk] uppercase tracking-wider font-bold focus:outline-none focus:border-[#c4b5fd]/50 transition-all cursor-pointer"
          >
            <option value="centro_historico" className="bg-[#120e2a] text-[#c4b5fd]">Centro Histórico</option>
            <option value="sector_angostura" className="bg-[#120e2a] text-[#c4b5fd]">Sector Angostura</option>
          </select>
          <div className="pointer-events-none absolute right-2 flex items-center text-[#c4b5fd]">
            <span className="material-symbols-outlined text-[14px]">expand_more</span>
          </div>
        </div>

        <button
          id="ai-toggle-btn"
          onClick={() => !metrics?.comparativa?.benchmark_activo && enviarControl('toggle_ai')}
          disabled={metrics?.comparativa?.benchmark_activo}
          title={
            metrics?.comparativa?.benchmark_activo
              ? `Benchmark en curso (Fase ${metrics.comparativa.benchmark_fase}/2) — La IA se controla automaticamente`
              : iaActiva ? 'Haz clic para desactivar la IA' : 'Haz clic para activar la IA'
          }
          className={`flex items-center gap-2 px-3 py-1.5 rounded border transition-all ${
            metrics?.comparativa?.benchmark_activo
              ? 'opacity-60 cursor-not-allowed bg-[#fbbf24]/10 border-[#fbbf24]/30 text-[#fbbf24]'
              : iaActiva
                ? 'bg-[#22d3ee]/10 border-[#22d3ee]/40 text-[#22d3ee]'
                : 'bg-[#2d2847] border-[#374151] text-[#c4b5fd]'
          }`}
        >
          <span className={`material-symbols-outlined text-[18px] ${iaActiva && !metrics?.comparativa?.benchmark_activo ? 'ai-pulse' : ''}`}>
            {metrics?.comparativa?.benchmark_activo ? 'lock' : 'auto_awesome'}
          </span>
          <span className="text-[10px] font-[Hanken_Grotesk] uppercase tracking-wider font-bold">
            {metrics?.comparativa?.benchmark_activo
              ? `Benchmark F${metrics.comparativa.benchmark_fase}/2`
              : iaActiva ? 'IA Activa' : 'IA Inactiva'}
          </span>
          {!metrics?.comparativa?.benchmark_activo && (
            <div className="w-8 h-4 bg-[#22d3ee]/30 rounded-full relative">
              <div className={`absolute top-0.5 w-3 h-3 rounded-full shadow-sm transition-all duration-300 ${
                iaActiva ? 'right-0.5 bg-[#22d3ee]' : 'left-0.5 bg-[#9ca3af]'
              }`} />
            </div>
          )}
        </button>

        <button
          className={`flex items-center gap-1 px-2.5 py-1.5 rounded hover:bg-[#2d2847] transition-colors ${
            pausado ? 'text-[#22d3ee] border border-[#22d3ee]/30' : 'text-[#c4b5fd]'
          }`}
          onClick={() => enviarControl(pausado ? 'resume' : 'pause')}
          title={pausado ? 'Reanudar simulación' : 'Pausar simulación'}
        >
          <span className="material-symbols-outlined text-[18px]">{pausado ? 'play_arrow' : 'pause'}</span>
          <span className="hidden sm:inline text-[11px] font-[Hanken_Grotesk] uppercase tracking-wider font-bold">
            {pausado ? 'Reanudar' : 'Pausar'}
          </span>
        </button>

        <button
          className="flex items-center gap-1 px-2.5 py-1.5 rounded hover:bg-[#2d2847] transition-colors text-[#c4b5fd]"
          onClick={() => enviarControl('restart')}
          title="Reiniciar simulación"
        >
          <span className="material-symbols-outlined text-[18px]">refresh</span>
          <span className="hidden sm:inline text-[11px] font-[Hanken_Grotesk] uppercase tracking-wider font-bold">Reiniciar</span>
        </button>

        <button
          className="flex items-center gap-1 px-2.5 py-1.5 rounded hover:bg-[#2d2847] transition-colors text-[#c4b5fd]"
          onClick={() => enviarControl('fast_forward')}
          title="Avanzar 1 hora simulada"
        >
          <span className="material-symbols-outlined text-[18px]">fast_forward</span>
          <span className="hidden sm:inline text-[11px] font-[Hanken_Grotesk] uppercase tracking-wider font-bold">Adelantar 1h</span>
        </button>

        {metrics?.comparativa?.benchmark_activo ? (
          /* ── Benchmark corriendo → botón CANCELAR ── */
          <button
            className="flex items-center gap-1 px-2.5 py-1.5 rounded transition-all border bg-[#fca5a5]/10 border-[#fca5a5]/40 text-[#fca5a5] hover:bg-[#fca5a5]/20]"
            onClick={() => enviarControl('cancel_benchmark')}
            title="Detener el benchmark y volver al modo normal"
          >
            <span className="material-symbols-outlined text-[18px]">cancel</span>
            <span className="hidden sm:inline text-[11px] font-[Hanken_Grotesk] uppercase tracking-wider font-bold">
              Cancelar F{metrics.comparativa.benchmark_fase}/2
            </span>
          </button>
        ) : (
          /* ── Benchmark inactivo → botón INICIAR ── */
          <button
            className="flex items-center gap-1 px-2.5 py-1.5 rounded transition-all border hover:bg-[#2d2847] text-[#c4b5fd] border-transparent"
            onClick={() => enviarControl('benchmark')}
            title="Iniciar prueba comparativa automática: 1000 pasos Sin IA vs 1000 pasos Con IA"
          >
            <span className="material-symbols-outlined text-[18px]">assessment</span>
            <span className="hidden sm:inline text-[11px] font-[Hanken_Grotesk] uppercase tracking-wider font-bold">
              {metrics?.comparativa?.benchmark_fase === 3 ? 'Repetir Benchmark' : 'Benchmark'}
            </span>
          </button>
        )}

        <a
          href={`http://localhost:8000/api/export?localidad=${localidad}`}
          download={`reporte_trafico_${localidad}.xlsx`}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-[#0891b2] text-[#0e7490] hover:bg-[#0891b2]/90 rounded font-[Hanken_Grotesk] text-[11px] uppercase tracking-wider font-bold transition-all"
        >
          <span className="material-symbols-outlined text-[18px]">download</span>
          <span>Exportar Excel</span>
        </a>

        <div className={`flex items-center gap-2 px-4 py-1.5 rounded font-[Hanken_Grotesk] text-[11px] uppercase tracking-wider font-bold ${
          metrics
            ? 'bg-[#22d3ee]/10 border border-[#22d3ee]/30 text-[#22d3ee]'
            : 'bg-[#fca5a5]/10 border border-[#fca5a5]/30 text-[#fca5a5]'
        }`}>

          <span className={`w-2 h-2 rounded-full ${metrics ? 'bg-[#22d3ee] ai-pulse' : 'bg-[#fca5a5]'}`} />
          {metrics ? `${metrics.globales?.vehiculos_activos ?? 0} veh` : 'Sin conexión'}
        </div>
      </div>
    </header>
  )
}
