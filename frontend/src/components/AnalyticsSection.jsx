import { useState, useMemo } from 'react'

function GraficoLinea({ data, dataKey, color, label, unit, avg }) {
  const points = data.slice(-60)
  const values = points.map(p => p[dataKey] ?? 0)
  const min = Math.min(...values, 0)
  const max = Math.max(...values, 0.1)
  const range = max - min || 1

  const svgPoints = values.map((v, i) => {
    const x = (i / Math.max(values.length - 1, 1)) * 100
    const y = 95 - ((v - min) / range) * 85
    return `${x},${y}`
  }).join(' ')

  const areaPoints = values.length > 0
    ? `0,100 ${svgPoints} 100,100`
    : '0,100 100,100'

  const current = values[values.length - 1] ?? 0

  return (
    <div className="glass-panel rounded-xl p-5 flex flex-col h-[290px]">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-[Hanken_Grotesk] text-[14px] font-bold uppercase tracking-wider text-[#e8e0f5] flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px]" style={{ color }}>{label.icon}</span>
          {label.text}
        </h3>
        <span className="font-[JetBrains_Mono] text-[14px] font-bold" style={{ color }}>
          {current.toFixed(label.decimals ?? 1)} {unit}
        </span>
      </div>
      <div className="flex-1 relative bg-[#131b2e]/50 rounded-lg border border-[#374151]/10 overflow-hidden p-3 pb-8">
        {values.length > 1 ? (
          <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 100">
            <polygon
              points={areaPoints}
              fill={color}
              fillOpacity="0.08"
            />
            <polyline
              points={svgPoints}
              fill="none"
              stroke={color}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            {values.length > 0 && (() => {
              const lx = ((values.length - 1) / Math.max(values.length - 1, 1)) * 100
              const ly = 95 - ((values[values.length - 1] - min) / range) * 85
              return <circle cx={lx} cy={ly} r="2.5" fill={color} />
            })()}
          </svg>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-[#374151] text-[10px] font-[Hanken_Grotesk]">
            Acumulando datos...
          </div>
        )}
        <div className="absolute bottom-1.5 left-3 right-3 flex justify-between text-[10px] font-[JetBrains_Mono] text-[#c4b5fd]/70 font-semibold">
          <span>-60s</span><span>-45s</span><span>-30s</span><span>-15s</span><span>ahora</span>
        </div>
      </div>
    </div>
  )
}

function GraficoBarras({ data, dataKey, color, label, unit }) {
  const points = data.slice(-20)
  const values = points.map(p => p[dataKey] ?? 0)
  const max = Math.max(...values, 1)
  const current = values[values.length - 1] ?? 0

  return (
    <div className="glass-panel rounded-xl p-5 flex flex-col h-[290px]">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-[Hanken_Grotesk] text-[14px] font-bold uppercase tracking-wider text-[#e8e0f5] flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px]" style={{ color }}>{label.icon}</span>
          {label.text}
        </h3>
        <span className="font-[JetBrains_Mono] text-[14px] font-bold" style={{ color }}>
          {current.toFixed(0)} {unit}
        </span>
      </div>
      <div className="flex-1 relative bg-[#131b2e]/50 rounded-lg border border-[#374151]/10 overflow-hidden p-3 pb-8">
        {values.length > 0 ? (
          <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 100">
            {values.map((v, i) => {
              const barW = 100 / values.length * 0.7
              const x = (i / values.length) * 100 + (100 / values.length * 0.15)
              const h = (v / max) * 85
              return (
                <rect
                  key={i}
                  x={x} y={100 - h} width={barW} height={h}
                  fill={color} fillOpacity={0.5 + (i / values.length) * 0.5}
                  rx="1"
                />
              )
            })}
          </svg>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-[#374151] text-[10px] font-[Hanken_Grotesk]">
            Acumulando datos...
          </div>
        )}
        <div className="absolute bottom-1.5 left-3 right-3 flex justify-between text-[10px] font-[JetBrains_Mono] text-[#c4b5fd]/70 font-semibold">
          <span>-20s</span><span>-15s</span><span>-10s</span><span>-5s</span><span>ahora</span>
        </div>
      </div>
    </div>
  )
}

export default function SeccionAnalisis({ history, metrics }) {
  const [period, setPeriod] = useState('daily')

  const displayHistory = useMemo(() => {
    if (history && history.length > 0) return history
    return Array.from({ length: 10 }, (_, i) => ({
      timestamp: Date.now() / 1000 - (10 - i),
      velocidad: 1.2 + Math.random() * 0.8,
      congestion: 40 + Math.random() * 20,
      flujo: 3.5 + Math.random() * 2,
      vehiculos: 70 + Math.floor(Math.random() * 30),
    }))
  }, [history])

  const ml = metrics?.ml_stats || { disponible: false }

  return (
    <section className="mt-4 pb-12">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 gap-4">
        <h2 className="font-[Hanken_Grotesk] text-[24px] font-semibold leading-8 text-[#e8e0f5] flex items-center gap-3">
          <span className="material-symbols-outlined text-[#c4b5fd]">analytics</span>
          Analítica Técnica de Tráfico
        </h2>
        <div className="flex gap-2 w-full sm:w-auto">
          {['weekly', 'daily'].map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`flex-1 sm:flex-none px-3 py-1.5 rounded-lg border text-[10px] font-[Hanken_Grotesk] font-bold uppercase tracking-wider transition-colors ${
                period === p
                  ? 'bg-[#c4b5fd]/10 border-[#c4b5fd]/30 text-[#c4b5fd]'
                  : 'bg-[#222a3d] border-[#374151] text-[#c4b5fd] hover:text-[#e8e0f5]'
              }`}
            >
              {p === 'daily' ? 'Diario (Actual)' : 'Semanal'}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-[12px] mb-4">
        <GraficoLinea
          data={displayHistory}
          dataKey="velocidad"
          color="#22d3ee"
          label={{ text: 'Velocidad vs Tiempo (km/h)', icon: 'speed', decimals: 2 }}
          unit="km/h"
        />
        <GraficoLinea
          data={displayHistory}
          dataKey="flujo"
          color="#c4b5fd"
          label={{ text: 'Flujo vs Tiempo (veh/min)', icon: 'moving', decimals: 1 }}
          unit="veh/min"
        />
        <GraficoLinea
          data={displayHistory}
          dataKey="congestion"
          color="#fca5a5"
          label={{ text: 'Congestión vs Tiempo (%)', icon: 'emergency_share', decimals: 1 }}
          unit="%"
        />
        <GraficoBarras
          data={displayHistory}
          dataKey="vehiculos"
          color="#fbbf24"
          label={{ text: 'Vehículos Activos vs Tiempo', icon: 'grid_view' }}
          unit="veh"
        />
      </div>

      <div className="glass-panel rounded-xl p-5 border border-[#374151]/20 mb-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4 border-b border-[#374151]/20 pb-3">
          <div>
            <h3 className="font-[Hanken_Grotesk] text-[16px] font-bold text-[#e8e0f5] flex items-center gap-2">
              <span className="material-symbols-outlined text-[#c4b5fd]">bar_chart</span>
              Comparativa de Escenarios (Escenario 1: Tiempo Fijo vs Escenario 2: Adaptativo IA)
            </h3>
            <p className="text-[11px] text-[#c4b5fd]/70 font-semibold mt-1">
              Evaluación y contraste de métricas de rendimiento vial con y sin control inteligente de tráfico
            </p>
          </div>
          {metrics?.comparativa?.benchmark_activo ? (
            <div className="flex flex-col items-end gap-1 w-full sm:w-auto shrink-0">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#fbbf24]">
                Benchmark en curso: {metrics.comparativa.benchmark_fase === 1 ? 'Tiempo Fijo (1/2)' : 'IA Adaptativa (2/2)'} ({Math.round(100 * (metrics.comparativa.benchmark_frames_fase - metrics.comparativa.benchmark_frames_restantes) / metrics.comparativa.benchmark_frames_fase)}%)
              </span>
              <div className="flex items-center gap-3">
                <span className="text-[9px] text-[#c4b5fd]/80 font-mono font-semibold">
                  E1: {metrics.comparativa.sin_ia?.frames || 0}/{metrics.comparativa.benchmark_frames_fase || 1000} | E2: {metrics.comparativa.con_ia?.frames || 0}/{metrics.comparativa.benchmark_frames_fase || 1000}
                </span>
                <div className="w-24 h-2 bg-[#374151]/40 rounded-full overflow-hidden shrink-0">
                  <div className="h-full bg-[#fbbf24] rounded-full transition-all duration-300" style={{ width: `${Math.round(100 * (metrics.comparativa.benchmark_frames_fase - metrics.comparativa.benchmark_frames_restantes) / metrics.comparativa.benchmark_frames_fase)}%` }} />
                </div>
              </div>
            </div>
          ) : metrics?.comparativa?.benchmark_fase === 3 ? (
            <span className="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#22d3ee]/10 border border-[#22d3ee]/20 text-[#22d3ee]">
              🏆 Benchmark Completado
            </span>
          ) : (
            <span className="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#c4b5fd]/10 border border-[#c4b5fd]/20 text-[#c4b5fd]">
              Modo Monitoreo
            </span>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-[JetBrains_Mono] text-[12px] min-w-[500px]">
            <thead className="bg-[#222a3d]/20">
              <tr className="border-b border-[#374151]/40">
                <th className="p-3 text-[#c4b5fd] font-bold uppercase text-[10px]">Métrica</th>
                <th className="p-3 text-[#c4b5fd] font-bold uppercase text-[10px]">
                  <div>Escenario 1 (Tiempo Fijo / Sin IA)</div>
                  {metrics?.comparativa?.benchmark_activo || metrics?.comparativa?.benchmark_fase === 3 ? (
                    <div className="text-[9px] font-normal lowercase text-[#c4b5fd]/60 mt-0.5 font-mono">
                      {metrics?.comparativa?.sin_ia?.frames || 0} / {metrics?.comparativa?.benchmark_frames_fase || 1000} pasos
                    </div>
                  ) : null}
                </th>
                <th className="p-3 text-[#c4b5fd] font-bold uppercase text-[10px]">
                  <div>Escenario 2 (Adaptativo / Con IA)</div>
                  {metrics?.comparativa?.benchmark_activo || metrics?.comparativa?.benchmark_fase === 3 ? (
                    <div className="text-[9px] font-normal lowercase text-[#c4b5fd]/60 mt-0.5 font-mono">
                      {metrics?.comparativa?.con_ia?.frames || 0} / {metrics?.comparativa?.benchmark_frames_fase || 1000} pasos
                    </div>
                  ) : null}
                </th>
                <th className="p-3 text-[#c4b5fd] font-bold uppercase text-[10px]">Mejora %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#374151]/10">
              {(() => {
                const sin = metrics?.comparativa?.sin_ia || {}
                const con = metrics?.comparativa?.con_ia || {}
                const hasSinData = (sin.frames || 0) > 0
                const hasConData = (con.frames || 0) > 0

                const formatVal = (val, hasData, suffix = '') => {
                  if (!hasData || val === undefined || val === null) return '—'
                  return `${val}${suffix}`
                }
                
                const calcMejora = (valSin, valCon, lowerBetter = true) => {
                  if (!hasSinData || !hasConData || valSin === undefined || valCon === undefined) {
                    return { text: 'N/A', positive: null }
                  }
                  if (valSin === 0) return { text: '+0.0%', positive: true }
                  let pct
                  if (lowerBetter) {
                    pct = 100 * (valSin - valCon) / valSin
                  } else {
                    pct = 100 * (valCon - valSin) / valSin
                  }
                  const positive = pct >= 0
                  return {
                    text: `${positive ? '+' : ''}${pct.toFixed(1)}%`,
                    positive
                  }
                }

                const compRows = [
                  { name: 'Congestión Promedio', sin: formatVal(sin.congestiva, hasSinData, '%'), con: formatVal(con.congestiva, hasConData, '%'), ...calcMejora(sin.congestiva, con.congestiva, true) },
                  { name: 'Velocidad Promedio', sin: formatVal(sin.velocidad, hasSinData, ' px/f'), con: formatVal(con.velocidad, hasConData, ' px/f'), ...calcMejora(sin.velocidad, con.velocidad, false) },
                  { name: 'Vehículos Detenidos (Prom)', sin: formatVal(sin.detenidos, hasSinData), con: formatVal(con.detenidos, hasConData), ...calcMejora(sin.detenidos, con.detenidos, true) },
                  { name: 'Espera Promedio por Veh.', sin: formatVal(sin.espera, hasSinData, ' s'), con: formatVal(con.espera, hasConData, ' s'), ...calcMejora(sin.espera, con.espera, true) },
                  { name: 'Flujo Vehicular (Completados)', sin: formatVal(sin.flujo, hasSinData, ' /min'), con: formatVal(con.flujo, hasConData, ' /min'), ...calcMejora(sin.flujo, con.flujo, false) },
                  { name: 'Efectividad Semáforos', sin: formatVal(sin.efectividad, hasSinData, '%'), con: formatVal(con.efectividad, hasConData, '%'), ...calcMejora(sin.efectividad, con.efectividad, false) },
                  { name: 'Vehículos Desviados por IA', sin: formatVal(sin.desviados, hasSinData), con: formatVal(con.desviados, hasConData), text: hasConData ? `${con.desviados ?? 0} total` : 'N/A', positive: hasConData ? true : null },
                ]

                return compRows.map((row, i) => (
                  <tr key={i} className="hover:bg-[#222a3d]/20 transition-colors">
                    <td className="p-3 font-semibold text-[#e8e0f5]/90">{row.name}</td>
                    <td className="p-3 text-[#c4b5fd]">{row.sin}</td>
                    <td className="p-3 text-[#e8e0f5] font-medium">{row.con}</td>
                    <td className={`p-3 font-bold ${
                      row.positive === null ? 'text-[#c4b5fd]' : row.positive ? 'text-[#22d3ee]' : 'text-[#fca5a5]'
                    }`}>
                      {row.text}
                    </td>
                  </tr>
                ))
              })()}
            </tbody>
          </table>
        </div>
      </div>

      <div className="glass-panel rounded-xl p-5 border border-[#374151]/20">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4 border-b border-[#374151]/20 pb-3">
          <div>
            <h3 className="font-[Hanken_Grotesk] text-[16px] font-bold text-[#e8e0f5] flex items-center gap-2">
              <span className="material-symbols-outlined text-[#c4b5fd] animate-pulse">memory</span>
              Capa de Aprendizaje Automático Avanzado (Machine Learning)
            </h3>
            <p className="text-[11px] text-[#c4b5fd]/70 font-semibold mt-1">
              PyTorch DQN (Aprendizaje por Refuerzo) + Scikit-learn Random Forest
            </p>
          </div>
          <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-1.5 ${
            ml.disponible 
              ? 'bg-[#22d3ee]/10 border border-[#22d3ee]/20 text-[#22d3ee]' 
              : 'bg-[#fbbf24]/10 border border-[#fbbf24]/20 text-[#fbbf24]'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${ml.disponible ? 'bg-[#22d3ee] animate-ping' : 'bg-[#fbbf24]'}`} />
            {ml.disponible ? 'ML Activo (Modelo Pre-entrenado)' : 'Fallback a Reglas Heurísticas'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          <div className="bg-[#131b2e]/30 rounded-lg p-4 border border-[#374151]/10">
            <h4 className="text-[12px] font-bold text-[#c4b5fd] uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px]">psychology</span>
              Agente de Aprendizaje por Refuerzo (PyTorch DQN)
            </h4>
            
            <div className="flex flex-col gap-4">
              <div>
                <div className="flex justify-between text-[11px] font-semibold text-[#c4b5fd] mb-1.5">
                  <span>Ratio de Explotación (Conocimiento adquirido)</span>
                  <span className="font-[JetBrains_Mono] text-[#22d3ee] font-bold">
                    {ml.disponible ? `${((1 - ml.epsilon) * 100).toFixed(1)}%` : '0.0%'}
                  </span>
                </div>
                <div className="h-2 bg-[#374151]/40 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-[#c4b5fd] to-[#22d3ee] rounded-full transition-all duration-500" 
                    style={{ width: ml.disponible ? `${(1 - ml.epsilon) * 100}%` : '0%' }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-[11px] font-semibold text-[#c4b5fd] mb-1.5">
                  <span>Exploración del Entorno (Epsilon)</span>
                  <span className="font-[JetBrains_Mono] text-[#fbbf24] font-bold">
                    {ml.disponible ? ml.epsilon.toFixed(3) : '1.000'}
                  </span>
                </div>
                <div className="h-2 bg-[#374151]/40 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-[#fbbf24] rounded-full transition-all duration-500" 
                    style={{ width: ml.disponible ? `${ml.epsilon * 100}%` : '100%' }}
                  />
                </div>
              </div>

              <div className="flex justify-between items-center text-[11px] bg-[#1a233d]/50 p-2.5 rounded border border-[#374151]/10">
                <span className="text-[#c4b5fd] font-semibold">Memoria de Experiencias (Replay Buffer)</span>
                <span className="font-[JetBrains_Mono] text-[#e8e0f5] font-bold">
                  {ml.disponible ? `${ml.buffer_size} / 5000 transiciones` : '0 / 5000'}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-[#131b2e]/30 rounded-lg p-4 border border-[#374151]/10">
            <h4 className="text-[12px] font-bold text-[#c4b5fd] uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px]">pattern</span>
              Probabilidades de Estado de Tráfico (Random Forest)
            </h4>

            <div className="flex flex-col gap-2">
              {[
                { name: 'Fluido', prob: ml.prediction_probs?.[0] ?? 0.25, color: '#22d3ee', bg: 'bg-[#22d3ee]' },
                { name: 'Moderado', prob: ml.prediction_probs?.[1] ?? 0.25, color: '#fbbf24', bg: 'bg-[#fbbf24]' },
                { name: 'Congestionado', prob: ml.prediction_probs?.[2] ?? 0.25, color: '#fca5a5', bg: 'bg-[#fca5a5]' },
                { name: 'Crítico', prob: ml.prediction_probs?.[3] ?? 0.25, color: '#ff8a80', bg: 'bg-[#ff8a80]' }
              ].map((cls, i) => (
                <div key={i}>
                  <div className="flex justify-between text-[10px] font-bold text-[#c4b5fd] mb-1">
                    <span>{cls.name}</span>
                    <span className="font-[JetBrains_Mono] font-semibold" style={{ color: cls.color }}>
                      {(cls.prob * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-1.5 bg-[#374151]/30 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full transition-all duration-500 ${cls.bg}`} 
                      style={{ width: `${cls.prob * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
