import { useKpis } from '../hooks/useSimulation'

function EsqueletoKPI() {
  return (
    <div className="glass-panel p-4 rounded-xl min-h-[90px] animate-pulse">
      <div className="h-2 bg-[#374151]/50 rounded w-20 mb-3" />
      <div className="h-7 bg-[#374151]/50 rounded w-16 mb-2" />
      <div className="h-1 bg-[#374151]/30 rounded-full w-full" />
    </div>
  )
}

function TarjetaKPI({ label, value, unit, valueColor = 'text-[#dae2fd]', unitColor, suffix,
                   badgeIcon, badgeText, badgeColor, icon, sub, subIcon, bar, type,
                   subText, losLetter, losColor }) {
  if (type === 'los') {
    return (
      <div className="glass-panel p-4 rounded-xl flex items-center justify-between min-h-[90px]">
        <div>
          <span className="font-[Hanken_Grotesk] text-[9px] text-[#c4b5fd] uppercase tracking-wider font-bold">{label}</span>
          <p className="text-[11px] text-[#e8e0f5]/70 mt-1">{subText}</p>
        </div>
        <div className={`w-10 h-10 rounded-full border-2 flex items-center justify-center font-bold text-lg ${losColor}`}>
          {losLetter}
        </div>
      </div>
    )
  }
  return (
    <div className="glass-panel p-4 rounded-xl flex flex-col justify-between min-h-[90px]">
      <span className="font-[Hanken_Grotesk] text-[9px] text-[#c4b5fd] uppercase tracking-wider font-bold">{label}</span>
      <div className="flex items-baseline gap-2 mt-1">
        <span className={`font-[JetBrains_Mono] text-[20px] sm:text-[24px] font-bold leading-none ${valueColor}`}>{value}</span>
        {unit  && <span className={`font-[JetBrains_Mono] text-[11px] sm:text-[12px] font-medium ${unitColor || valueColor}`}>{unit}</span>}
        {suffix && <span className="font-[JetBrains_Mono] text-[11px] sm:text-[12px] opacity-60">{suffix}</span>}
        {badgeText && (
          <span className={`text-[10px] font-[JetBrains_Mono] flex items-center ${badgeColor || ''}`}>
            {badgeIcon && <span className="material-symbols-outlined text-[12px]">{badgeIcon}</span>}
            {badgeText}
          </span>
        )}
        {icon && <span className={`material-symbols-outlined text-[20px] ml-auto ${icon.color}`}>{icon.name}</span>}
      </div>
      {sub && (
        <p className={`text-[9px] flex items-center gap-1 mt-1 font-[Hanken_Grotesk] font-bold ${sub.color}`}>
          {subIcon && <span className="material-symbols-outlined text-[10px]">{subIcon}</span>}
          {sub.text}
        </p>
      )}
      {bar && (
        <div className="h-1 bg-[#374151] w-full mt-2 rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all duration-700 ${bar.color}`} style={{ width: `${Math.min(bar.value, 100)}%` }} />
        </div>
      )}
    </div>
  )
}

export default function SeccionKPI({ metrics, loading, localidad }) {
  const { kpis, loading: kpisLoading } = useKpis(localidad)

  if (loading || !metrics) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-[12px]">
        {Array.from({ length: 10 }).map((_, i) => <EsqueletoKPI key={i} />)}
      </div>
    )
  }

  const g = metrics.globales

  const obtenerColorEstado = (estado) => {
    if (estado === 'Crítico') return 'text-[#fca5a5]'
    if (estado === 'Alerta') return 'text-[#fbbf24]'
    return 'text-[#22d3ee]'
  }

  const obtenerBgColorEstado = (estado) => {
    if (estado === 'Crítico') return 'bg-[#fca5a5]'
    if (estado === 'Alerta') return 'bg-[#fbbf24]'
    return 'bg-[#22d3ee]'
  }

  const kpisList = [
    {
      label: 'Congestión Global',
      value: `${(kpis ? kpis.congestion_global.valor : g.congestion_global).toFixed(1)}%`,
      valueColor: obtenerColorEstado(kpis ? kpis.congestion_global.estado : (g.congestion_global > 60 ? 'Crítico' : g.congestion_global > 35 ? 'Alerta' : 'Normal')),
      bar: { 
        value: kpis ? kpis.congestion_global.valor : g.congestion_global, 
        color: obtenerBgColorEstado(kpis ? kpis.congestion_global.estado : (g.congestion_global > 60 ? 'Crítico' : g.congestion_global > 35 ? 'Alerta' : 'Normal')) 
      },
      sub: kpis ? { text: `Umbral Alerta: >${kpis.congestion_global.umbrales.alerta}%`, color: 'text-[#c4b5fd]/70' } : null
    },
    {
      label: 'Velocidad Prom.',
      value: (kpis ? kpis.velocidad_promedio.valor : g.velocidad_promedio * 12.0).toFixed(1),
      unit: 'km/h',
      valueColor: obtenerColorEstado(kpis ? kpis.velocidad_promedio.estado : 'Normal'),
      sub: { 
        text: kpis ? `Umbral Alerta: <${kpis.velocidad_promedio.umbrales.alerta} km/h` : `Actual: ${g.velocidad_promedio.toFixed(2)}`, 
        color: 'text-[#c4b5fd]/70' 
      },
    },
    {
      label: 'Vehículos Activos',
      value: `${g.vehiculos_activos}`,
      suffix: `/${g.vehiculos_max}`,
      bar: { value: (g.vehiculos_activos / g.vehiculos_max) * 100, color: 'bg-[#c4b5fd]' },
    },
    {
      label: 'Detenidos',
      value: `${g.detenidos}`,
      valueColor: g.detenidos > 20 ? 'text-[#fca5a5]' : 'text-[#22d3ee]',
      badgeText: g.detenidos > 0 ? `${Math.round(g.detenidos / Math.max(g.vehiculos_activos, 1) * 100)}%` : '0%',
      badgeColor: g.detenidos > 20 ? 'text-[#fca5a5]' : 'text-[#22d3ee]',
      bar: { value: (g.detenidos / Math.max(g.vehiculos_activos, 1)) * 100, color: g.detenidos > 20 ? 'bg-[#fca5a5]/50' : 'bg-[#22d3ee]/50' },
    },
    {
      label: 'Espera Prom.',
      value: (kpis ? kpis.tiempo_espera_promedio.valor : g.espera_promedio * 60.0).toFixed(1),
      unit: 's',
      valueColor: obtenerColorEstado(kpis ? kpis.tiempo_espera_promedio.estado : 'Normal'),
      sub: { 
        text: kpis ? `Umbral Alerta: >${kpis.tiempo_espera_promedio.umbrales.alerta}s` : 'Tiempo en detención', 
        color: 'text-[#c4b5fd]/70' 
      },
    },
    {
      label: 'Efect. Semáforos',
      value: `${(kpis ? kpis.efectividad_semaforos.valor : g.efectividad_semaforos).toFixed(0)}%`,
      valueColor: obtenerColorEstado(kpis ? kpis.efectividad_semaforos.estado : 'Normal'),
      icon: { name: 'verified', color: obtenerColorEstado(kpis ? kpis.efectividad_semaforos.estado : 'Normal') },
      bar: { 
        value: kpis ? kpis.efectividad_semaforos.valor : g.efectividad_semaforos, 
        color: obtenerBgColorEstado(kpis ? kpis.efectividad_semaforos.estado : 'Normal') 
      },
      sub: kpis ? { text: `Umbral Alerta: <${kpis.efectividad_semaforos.umbrales.alerta}%`, color: 'text-[#c4b5fd]/70' } : null
    },
    {
      label: 'Throughput',
      value: (kpis ? kpis.throughput.valor : 0.0).toFixed(1),
      unit: 'veh/min',
      valueColor: obtenerColorEstado(kpis ? kpis.throughput.estado : 'Normal'),
      sub: { 
        text: kpis ? `Umbral Alerta: <${kpis.throughput.umbrales.alerta} v/m` : 'Flujo completado', 
        color: 'text-[#c4b5fd]/70' 
      },
    },
    {
      type: 'los',
      label: 'Nivel Servicio (LOS)',
      subText: kpis ? `Estado: ${kpis.nivel_servicio.estado}` : g.los_label,
      losLetter: kpis ? kpis.nivel_servicio.valor : g.los,
      losColor: kpis 
        ? (kpis.nivel_servicio.estado === 'Crítico' ? 'border-[#fca5a5] text-[#fca5a5]' : kpis.nivel_servicio.estado === 'Alerta' ? 'border-[#fbbf24] text-[#fbbf24]' : 'border-[#22d3ee] text-[#22d3ee]')
        : (['A','B'].includes(g.los) ? 'border-[#22d3ee] text-[#22d3ee]' : g.los === 'C' ? 'border-[#c4b5fd] text-[#c4b5fd]' : g.los === 'D' ? 'border-[#fbbf24] text-[#fbbf24]' : 'border-[#fca5a5] text-[#fca5a5]'),
    },
    {
      label: 'Emisiones CO₂',
      value: (kpis ? kpis.emisiones_co2_estimadas.valor : g.emisiones_co2).toFixed(1),
      unit: 'kg/h',
      valueColor: obtenerColorEstado(kpis ? kpis.emisiones_co2_estimadas.estado : (g.emisiones_co2 > 100 ? 'Crítico' : 'Alerta')),
      bar: { 
        value: Math.min((kpis ? kpis.emisiones_co2_estimadas.valor : g.emisiones_co2) / 20.0 * 100, 100), 
        color: obtenerBgColorEstado(kpis ? kpis.emisiones_co2_estimadas.estado : 'Normal') 
      },
      sub: kpis ? { text: `Umbral Alerta: >${kpis.emisiones_co2_estimadas.umbrales.alerta} kg/h`, color: 'text-[#c4b5fd]/70' } : null
    },
    {
      label: 'Accidentes',
      value: `${g.accidentes}`,
      valueColor: 'text-[#22d3ee]',
      icon: { name: 'check_circle', color: 'text-[#22d3ee]' },
      sub: { text: 'Sin reportes', color: 'text-[#22d3ee]/70' },
    },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-[12px]">
      {kpisList.map((kpi, i) => <TarjetaKPI key={i} {...kpi} />)}
    </div>
  )
}

