import { useState, useEffect } from 'react'
import './index.css'
import { useSimulacion, obtenerUrlStream } from './hooks/useSimulation'
import Cabecera from './components/Header'
import SeccionKPI from './components/KPISection'
import ColumnaIzquierda from './components/LeftColumn'
import SimulacionMapa from './components/MapSimulation'
import ColumnaDerecha from './components/RightColumn'
import SeccionAnalisis from './components/AnalyticsSection'
import PiePagina from './components/Footer'

export default function Aplicacion() {
  const [localidad, setLocalidad] = useState('centro_historico')

  const { metrics, history, error, loading, enviarControl } = useSimulacion(localidad)

  const streamUrl = obtenerUrlStream(localidad)

  const benchmarkFase = metrics?.comparativa?.benchmark_fase ?? 0
  const [showBenchmarkModal, setShowBenchmarkModal] = useState(false)
  const [ultimoBenchmarkFase, setUltimoBenchmarkFase] = useState(0)

  useEffect(() => {
    if (benchmarkFase === 3 && ultimoBenchmarkFase !== 3) {
      setShowBenchmarkModal(true)
      setUltimoBenchmarkFase(3)
    } else if (benchmarkFase !== 3 && ultimoBenchmarkFase === 3) {
      setUltimoBenchmarkFase(benchmarkFase)
    }
  }, [benchmarkFase, ultimoBenchmarkFase])

  return (
    <div className="min-h-screen bg-[#0a0818] text-[#e8e0f5] overflow-x-hidden">

      {error && (
        <div className="fixed top-0 left-0 right-0 z-[200] bg-[#fca5a5]/10 border-b border-[#fca5a5]/30 px-6 py-2 text-center">
          <p className="text-[#fca5a5] text-[11px] font-[Hanken_Grotesk] font-bold uppercase tracking-wider flex items-center justify-center gap-2">
            <span className="material-symbols-outlined text-[14px]">wifi_off</span>
            {error} — Inicia el backend con <code className="bg-[#fca5a5]/10 px-2 py-0.5 rounded font-[JetBrains_Mono]">cd backend &amp;&amp; uvicorn main:app</code>
          </p>
        </div>
      )}

      <Cabecera
        metrics={metrics}
        enviarControl={enviarControl}
        hasError={!!error}
        localidad={localidad}
        setLocalidad={setLocalidad}
      />

      {showBenchmarkModal && (
        <div className="fixed inset-0 z-[300] flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-[#120e2a] border border-[#22d3ee]/30 rounded-xl p-6 max-w-md w-full shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-[#22d3ee] to-[#0891b2]" />

            <button
              onClick={() => setShowBenchmarkModal(false)}
              className="absolute top-4 right-4 text-[#c4b5fd] hover:text-[#e8e0f5] transition-colors"
            >
              <span className="material-symbols-outlined text-[20px]">close</span>
            </button>

            <div className="flex flex-col items-center text-center mt-2">
              <div className="w-12 h-12 rounded-full bg-[#22d3ee]/10 flex items-center justify-center text-[#22d3ee] mb-4">
                <span className="material-symbols-outlined text-[28px] animate-bounce">emoji_events</span>
              </div>

              <h3 className="font-[Hanken_Grotesk] text-[16px] font-bold text-[#e8e0f5] mb-2 uppercase tracking-wide">
                ¡Benchmark Finalizado!
              </h3>

              <p className="font-[Hanken_Grotesk] text-[12px] text-[#c4b5fd]/90 mb-6 leading-relaxed">
                La evaluación comparativa automática ha terminado con éxito. La simulación ha sido pausada y ya puedes descargar el reporte detallado con las métricas de tráfico.
              </p>

              <div className="flex flex-col sm:flex-row gap-3 w-full justify-center">
                <a
                  href={`http://localhost:8000/api/export?localidad=${localidad}`}
                  download={`reporte_trafico_${localidad}.xlsx`}
                  onClick={() => setShowBenchmarkModal(false)}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-[#0891b2] hover:bg-[#0891b2]/90 text-[#0e7490] rounded font-[Hanken_Grotesk] text-[11px] font-bold uppercase tracking-wider transition-all"
                >
                  <span className="material-symbols-outlined text-[18px]">download</span>
                  <span>Exportar Reporte (CSV)</span>
                </a>

                <button
                  onClick={() => setShowBenchmarkModal(false)}
                  className="flex-1 px-4 py-2.5 bg-[#2d2847] hover:bg-[#3d3660] border border-[#374151] text-[#c4b5fd] rounded font-[Hanken_Grotesk] text-[11px] font-bold uppercase tracking-wider transition-all"
                >
                  Entendido
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <main className={`p-[16px] flex flex-col gap-[16px] max-w-[1600px] mx-auto w-full ${error ? 'mt-10' : ''}`}>
        <SeccionKPI metrics={metrics} loading={loading} localidad={localidad} />

        <div className="grid grid-cols-1 md:grid-cols-12 gap-[12px]">
          <ColumnaIzquierda metrics={metrics} loading={loading} localidad={localidad} />
          <SimulacionMapa metrics={metrics} streamUrl={streamUrl} localidad={localidad} />
          <ColumnaDerecha metrics={metrics} loading={loading} enviarControl={enviarControl} localidad={localidad} />
        </div>

        <SeccionAnalisis history={history} metrics={metrics} />
      </main>

      <PiePagina />
    </div>
  )
}
