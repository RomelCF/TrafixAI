const NOMBRES_MOSTRAR = {
  'Centro histórico': 'Centro Hist.',
  'San Pedro': 'San Pedro',
  'San Blas': 'San Blas',
  'Eje Av. El Sol': 'Av. El Sol',
  'Zona Este': 'Zona Este',
  'Calle 1': 'Calle 1 (Evit.)',
  'Calle 2': 'Calle 2',
  'Calle 3-4': 'Calles 3-4',
  'Calle 5-6': 'Calles 5-6',
  'Zona Norte': 'Zona Norte',
}

function estiloNivel(nivel) {
  switch (nivel) {
    case 'Crítico':      return 'bg-[#ffb4ab]/10 text-[#ffb4ab] border border-[#ffb4ab]/20'
    case 'Congestionado': return 'bg-[#ffb95f]/10 text-[#ffb95f] border border-[#ffb95f]/20'
    case 'Moderado':     return 'bg-[#ffb95f]/10 text-[#ffb95f] border border-[#ffb95f]/20'
    default:             return 'bg-[#4edea3]/10 text-[#4edea3] border border-[#4edea3]/20'
  }
}

function colorCongestion(nivel) {
  if (nivel === 'Crítico') return 'text-[#ffb4ab]'
  if (nivel === 'Congestionado' || nivel === 'Moderado') return 'text-[#ffb95f]'
  return 'text-[#4edea3]'
}

function colorLos(los) {
  if (los === 'F' || los === 'E') return 'text-[#ffb4ab]'
  if (los === 'D') return 'text-[#ffb95f]'
  return 'text-[#4edea3]'
}

function EsqueletoTabla({ rows = 4, cols = 3 }) {
  return (
    <div className="p-3 space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 animate-pulse">
          {Array.from({ length: cols }).map((_, j) => (
            <div key={j} className="h-3 bg-[#414755]/40 rounded flex-1" />
          ))}
        </div>
      ))}
    </div>
  )
}

export default function ColumnaIzquierda({ metrics, loading, localidad = 'centro_historico' }) {
  const zonas = metrics?.zonas || {}
  const intersecciones = metrics?.intersecciones || []
  const fleet = metrics?.fleet || {}

  const isAngostura = localidad === 'sector_angostura'

  const fleetBars = isAngostura
    
    ? [
        { label: 'Autos',          pct: fleet.detalle?.['Autos']          ?? 0, color: 'bg-[#adc6ff]' },
        { label: 'Pick-ups',       pct: fleet.detalle?.['Pick-ups']       ?? 0, color: 'bg-[#93c4ff]' },
        { label: 'Buses',          pct: fleet.detalle?.['Buses']          ?? 0, color: 'bg-[#4edea3]' },
        { label: 'Transp. Urbano', pct: fleet.detalle?.['Transp. Urbano'] ?? 0, color: 'bg-[#50d7c0]' },
        { label: 'C. Ligero',      pct: fleet.detalle?.['C. Ligero']      ?? 0, color: 'bg-[#ffb95f]' },
        { label: 'C. Mediano',     pct: fleet.detalle?.['C. Mediano']     ?? 0, color: 'bg-[#ff9e42]' },
        { label: 'C. Pesado',      pct: fleet.detalle?.['C. Pesado']      ?? 0, color: 'bg-[#ff7b3f]' },
        { label: 'Articulado',     pct: fleet.detalle?.['Articulado']     ?? 0, color: 'bg-[#ff5533]' },
      ]
    
    : [
        { label: 'Particulares',       pct: fleet.particulares      ?? 65, color: 'bg-[#adc6ff]' },
        { label: 'Transporte Público', pct: fleet.transporte_publico ?? 25, color: 'bg-[#4edea3]' },
        { label: 'Motos',              pct: fleet.motos             ?? 0,  color: 'bg-[#ffb95f]' },
        { label: 'Taxis/Combis',       pct: fleet.transporte_publico ?? 10, color: 'bg-[#ffb95f]/70' },
      ]

  const listadoZonas = isAngostura
    ? ['Calle 1', 'Calle 2', 'Calle 3-4', 'Calle 5-6', 'Zona Norte']
    : ['Centro histórico', 'San Pedro', 'San Blas', 'Eje Av. El Sol', 'Zona Este']

  const zonaRows = listadoZonas.map(nombre => ({
    nombre,
    data: zonas[nombre] || null
  }))

  return (
    <div className="md:col-span-3 flex flex-col gap-[12px] order-2 md:order-1">

      <div className="glass-panel rounded-xl flex flex-col min-h-[250px]">
        <div className="p-3 border-b border-[#414755] bg-[#222a3d]/30 flex items-center justify-between">
          <h3 className="font-[Hanken_Grotesk] text-[11px] font-bold flex items-center gap-2 text-[#dae2fd] uppercase tracking-wider">
            <span className="material-symbols-outlined text-[18px]">fact_check</span>
            Diagnóstico por Zona
          </h3>
          {metrics && (
            <span className="w-1.5 h-1.5 rounded-full bg-[#4edea3] ai-pulse" />
          )}
        </div>
        <div className="flex-1 overflow-y-auto">
          {loading || !metrics ? (
            <EsqueletoTabla rows={5} cols={3} />
          ) : (
            <table className="w-full text-left font-[JetBrains_Mono] text-[11px]">
              <thead className="bg-[#222a3d]/20 sticky top-0">
                <tr className="border-b border-[#414755]">
                  <th className="p-3 font-medium">Zona</th>
                  <th className="p-3 font-medium">Nivel</th>
                  <th className="p-3 font-medium">Cong.</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#414755]/10">
                {zonaRows.map(({ nombre, data }) => (
                  <tr key={nombre} className="hover:bg-[#222a3d]/30 transition-colors">
                    <td className="p-3 font-bold text-[10px]">{NOMBRES_MOSTRAR[nombre] || nombre}</td>
                    <td className="p-3">
                      {data ? (
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${estiloNivel(data.nivel)}`}>
                          {data.nivel === 'Congestionado' ? 'Congest.' : data.nivel}
                        </span>
                      ) : (
                        <span className="text-[#414755]">—</span>
                      )}
                    </td>
                    <td className={`p-3 font-bold ${data ? colorCongestion(data.nivel) : 'text-[#414755]'}`}>
                      {data ? `${data.congestion.toFixed(0)}%` : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <div className="glass-panel rounded-xl flex flex-col min-h-[200px]">
        <div className="p-3 border-b border-[#414755] bg-[#222a3d]/30">
          <h3 className="font-[Hanken_Grotesk] text-[11px] font-bold flex items-center gap-2 text-[#dae2fd] uppercase tracking-wider">
            <span className="material-symbols-outlined text-[18px]">traffic</span>
            Monitoreo Intersecciones
          </h3>
        </div>
        <div className="flex-1 overflow-y-auto">
          {loading || !metrics ? (
            <EsqueletoTabla rows={3} cols={3} />
          ) : (
            <table className="w-full text-left font-[JetBrains_Mono] text-[11px]">
              <thead className="bg-[#222a3d]/20 sticky top-0">
                <tr className="border-b border-[#414755]">
                  <th className="p-3 font-medium">Intersección</th>
                  <th className="p-3 font-medium">Espera</th>
                  <th className="p-3 font-medium">LOS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#414755]/10">
                {intersecciones.length > 0 ? intersecciones.map((int, i) => (
                  <tr key={i} className="hover:bg-[#222a3d]/30 transition-colors">
                    <td className="p-3 font-bold text-[10px]">{int.nombre}</td>
                    <td className="p-3">{int.espera}</td>
                    <td className={`p-3 font-bold ${colorLos(int.los)}`}>{int.los}</td>
                  </tr>
                )) : (
                  <tr><td colSpan={3} className="p-3 text-[#414755] text-center">Cargando datos...</td></tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <div className="glass-panel rounded-xl p-4 flex flex-col">
        <h3 className="font-[Hanken_Grotesk] text-[11px] font-bold flex items-center gap-2 mb-4 text-[#dae2fd] uppercase tracking-wider">
          <span className="material-symbols-outlined text-[18px]">directions_car</span>
          Composición Flota
        </h3>
        {loading || !metrics ? (
          <div className="space-y-4 animate-pulse">
            {[1,2,3].map(i => <div key={i} className="h-5 bg-[#414755]/30 rounded" />)}
          </div>
        ) : (
          <div className="space-y-4">
            {fleetBars.map(f => (
              <div key={f.label} className="space-y-1">
                <div className="flex justify-between font-[JetBrains_Mono] text-[10px]">
                  <span>{f.label}</span>
                  <span>{f.pct.toFixed(0)}%</span>
                </div>
                <div className="h-1.5 bg-[#414755] rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all duration-700 ${f.color}`} style={{ width: `${Math.min(f.pct, 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  )
}
