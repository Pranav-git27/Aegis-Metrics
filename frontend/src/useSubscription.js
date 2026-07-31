import { useCallback, useEffect, useRef, useState } from 'react'
import { supabase } from './supabaseClient.js'

export default function useSubscription(table, options = {}) {
  const {
    orderBy = { column: 'detected_at', ascending: false },
    filter = null,
  } = options

  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const mountedRef = useRef(true)

  const fetchInitial = useCallback(async () => {
    try {
      let query = supabase
        .from(table)
        .select('*')
        .order(orderBy.column, { ascending: orderBy.ascending })

      if (filter) {
        query = query.eq(filter.column, filter.value)
      }

      const { data: initial, error: fetchErr } = await query
      if (!mountedRef.current) return

      if (fetchErr) {
        setError(fetchErr)
      } else {
        setData(initial || [])
        setError(null)
      }
    } catch (err) {
      if (mountedRef.current) setError(err)
    } finally {
      if (mountedRef.current) setLoading(false)
    }
  }, [table, orderBy.column, orderBy.ascending, filter?.column, filter?.value])

  useEffect(() => {
    mountedRef.current = true
    setLoading(true)

    fetchInitial()

    const channel = supabase
      .channel(`${table}-realtime`)
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table },
        (payload) => {
          if (!mountedRef.current) return
          setData((prev) => {
            const { eventType, new: newRecord, old: oldRecord } = payload
            if (eventType === 'INSERT') {
              return [newRecord, ...prev]
            }
            if (eventType === 'UPDATE') {
              return prev.map((r) => (r.id === newRecord.id ? newRecord : r))
            }
            if (eventType === 'DELETE') {
              return prev.filter((r) => r.id !== oldRecord.id)
            }
            return prev
          })
        },
      )
      .subscribe()

    return () => {
      mountedRef.current = false
      supabase.removeChannel(channel)
    }
  }, [table, fetchInitial])

  return { data, loading, error }
}
