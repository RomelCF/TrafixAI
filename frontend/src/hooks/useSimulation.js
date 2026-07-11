import { useState, useEffect, useCallback, useRef } from 'react'

const API = ''
const POLL_MS = 2000

export function useSimulacion(localidad = 'centro_historico') {
  const [metrics, setMetrics] = useState(null)
  const [history, setHistory] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const historyRef = useRef([])

  useEffect(() => {
    let active = true

    const obtenerMetricas = async () => {
      try {
        const res = await fetch(`${API}/api/metrics?localidad=${localidad}`)
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        if (active) {
          setMetrics(data)
          setError(null)
          setLoading(false)
        }
      } catch (err) {
        if (active) setError('No se puede conectar con el backend (puerto 8000)')
      }
    }

    setLoading(true)
    obtenerMetricas()
    const id = setInterval(obtenerMetricas, POLL_MS)
    return () => { active = false; clearInterval(id) }
  }, [localidad])

  useEffect(() => {
    let active = true
    const obtenerHistorial = async () => {
      try {
        const res = await fetch(`${API}/api/history?localidad=${localidad}`)
        if (!res.ok) return
        const data = await res.json()
        if (active) setHistory(data)
      } catch (_) {}
    }
    setHistory([])
    obtenerHistorial()
    const id = setInterval(obtenerHistorial, 3000)
    return () => { active = false; clearInterval(id) }
  }, [localidad])

  const enviarControl = useCallback(async (accion) => {
    try {
      await fetch(`${API}/api/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: accion, localidad }),
      })
      
      const res = await fetch(`${API}/api/metrics?localidad=${localidad}`)
      if (res.ok) {
        const data = await res.json()
        setMetrics(data)
      }
    } catch (err) {
      console.error('Error de control:', err)
    }
  }, [localidad])

  return { metrics, history, error, loading, enviarControl }
}

export function obtenerUrlStream(localidad = 'centro_historico') {
  return `http://localhost:8000/api/stream?localidad=${localidad}`
}

export const URL_TRANSMISION = `http://localhost:8000/api/stream?localidad=centro_historico`

export function useKpis(localidad = 'centro_historico') {
  const [kpis, setKpis] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let active = true
    const obtenerKpis = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/kpis?localidad=${localidad}`)
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        if (active) {
          setKpis(data)
          setError(null)
          setLoading(false)
        }
      } catch (err) {
        if (active) {
          setError(err.message)
        }
      }
    }
    setLoading(true)
    obtenerKpis()
    const id = setInterval(obtenerKpis, 2000)
    return () => { active = false; clearInterval(id) }
  }, [localidad])

  return { kpis, loading, error }
}

