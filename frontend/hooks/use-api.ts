import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'
import { useAuth } from '@/components/auth/auth-context'

// Types matching our Django backend models
export interface GPU {
  id: string
  gpu_name: string
  gpu_model: string
  gpu_availability: boolean
  gpu_price_per_hour: number
  host: {
    id: string
    user: {
      first_name: string
      email: string
    }
  }
}

export interface Session {
  id: string
  renter: string
  gpu: GPU
  status: 'PENDING' | 'ACTIVE' | 'COMPLETED' | 'CANCELLED'
  start_time: string | null
  end_time: string | null
  duration_hours: number
  total_cost: string | number  // Can come as string or number from API
  ssh_port: number | null
  created_at: string
  updated_at: string
  connection_status: string
  connection_error: string | null
}

export interface Wallet {
  id: string
  balance: string | number  // Can come as string or number from API
  currency: string
  created_at: string
  updated_at: string
}

// Hook for available GPUs (marketplace)
export function useAvailableGPUs() {
  const [gpus, setGpus] = useState<GPU[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchGPUs = async () => {
      try {
        setLoading(true)
        const data = await apiClient.getAvailableGPUs()
        setGpus(data)
        setError(null)
      } catch (err: any) {
        setError(err.message || 'Failed to fetch GPUs')
        setGpus([])
      } finally {
        setLoading(false)
      }
    }

    fetchGPUs()
  }, [])

  return { gpus, loading, error }
}

// Hook for renter dashboard data
export function useRenterDashboard() {
  const { user } = useAuth()
  const [sessions, setSessions] = useState<Session[]>([])
  const [wallet, setWallet] = useState<Wallet | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!user || user.role !== 'renter') {
      setLoading(false)
      return
    }

    const fetchRenterData = async () => {
      try {
        setLoading(true)
        
        // Fetch sessions and wallet data from our Django backend
        const [sessionsData, walletData] = await Promise.all([
          apiClient.getRenterSessions(user.id),
          apiClient.getRenterWallet(user.id)
        ])
        
        setSessions(sessionsData)
        setWallet(walletData)
        setError(null)
      } catch (err: any) {
        setError(err.message || 'Failed to fetch renter data')
      } finally {
        setLoading(false)
      }
    }

    fetchRenterData()
  }, [user])

  const addMoney = async (amount: number, description?: string) => {
    if (!user) throw new Error('User not authenticated')
    
    try {
      const result = await apiClient.addMoney(user.id, amount, description)
      // Refresh wallet data
      const walletData = await apiClient.getRenterWallet(user.id)
      setWallet(walletData)
      return result
    } catch (err: any) {
      throw new Error(err.message || 'Failed to add money')
    }
  }

  return { sessions, wallet, loading, error, addMoney }
}

// Hook for host dashboard data
export function useHostDashboard() {
  const { user } = useAuth()
  const [gpus, setGpus] = useState<GPU[]>([])
  const [sessions, setSessions] = useState<Session[]>([])
  const [wallet, setWallet] = useState<Wallet | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!user || user.role !== 'host') {
      setLoading(false)
      return
    }

    const fetchHostData = async () => {
      try {
        setLoading(true)
        
        // Fetch GPUs, sessions, and wallet data from our Django backend
        const [gpusData, sessionsData, walletData] = await Promise.all([
          apiClient.getHostGPUs(user.id),
          apiClient.getHostSessions(user.id),
          apiClient.getHostWallet(user.id)
        ])
        
        setGpus(gpusData)
        setSessions(sessionsData)
        setWallet(walletData)
        setError(null)
      } catch (err: any) {
        setError(err.message || 'Failed to fetch host data')
      } finally {
        setLoading(false)
      }
    }

    fetchHostData()
  }, [user])

  const withdrawMoney = async (amount: number, description?: string) => {
    if (!user) throw new Error('User not authenticated')
    
    try {
      const result = await apiClient.withdrawMoney(user.id, amount, description)
      // Refresh wallet data
      const walletData = await apiClient.getHostWallet(user.id)
      setWallet(walletData)
      return result
    } catch (err: any) {
      throw new Error(err.message || 'Failed to withdraw money')
    }
  }

  return { gpus, sessions, wallet, loading, error, withdrawMoney }
}
