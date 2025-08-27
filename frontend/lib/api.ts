// API configuration and client
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api'

class ApiError extends Error {
  details?: any
  
  constructor(message: string, details?: any) {
    super(message)
    this.name = 'ApiError'
    this.details = details
  }
}

class ApiClient {
  private baseURL: string
  
  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL
  }

  private async request(endpoint: string, options: RequestInit = {}): Promise<any> {
    const url = `${this.baseURL}${endpoint}`
    
    // Get token from localStorage
    const token = typeof window !== 'undefined' ? localStorage.getItem('labhya_token') : null
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    }

    try {
      console.log('API Request:', { url, method: config.method || 'GET', headers: config.headers })
      const response = await fetch(url, config)
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('API Error Response:', { status: response.status, statusText: response.statusText, body: errorText })
        
        let errorData
        try {
          errorData = JSON.parse(errorText)
        } catch {
          errorData = { message: errorText || 'Unknown error' }
        }
        
        throw new ApiError(errorData.message || `HTTP ${response.status}`, errorData)
      }

      const data = await response.json()
      console.log('API Success Response:', data)
      return data
    } catch (error) {
      console.error('API Request Error:', error)
      if (error instanceof ApiError) {
        throw error
      }
      throw new ApiError('Network error or server unavailable')
    }
  }

  // Authentication
  async login(email: string, password: string) {
    return this.request('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  }

  async registerRenter(name: string, email: string, password: string) {
    return this.request('/auth/register/renter/', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    })
  }

  async registerHost(name: string, email: string, password: string) {
    return this.request('/auth/register/host/', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    })
  }

  async refreshToken(refreshToken: string) {
    return this.request('/auth/refresh/', {
      method: 'POST',
      body: JSON.stringify({ refresh: refreshToken }),
    })
  }

  // Renters
  async getRenterProfile(id: string) {
    return this.request(`/renters/${id}/`)
  }

  async getRenterWallet(id: string) {
    return this.request(`/renters/${id}/wallet/`)
  }

  async addMoney(renterId: string, amount: number, description?: string) {
    return this.request(`/renters/${renterId}/add_money/`, {
      method: 'POST',
      body: JSON.stringify({ amount, description }),
    })
  }

  async getRenterSessions(id: string) {
    return this.request(`/renters/${id}/sessions/`)
  }

  // Hosts
  async getHostProfile(id: string) {
    return this.request(`/hosts/${id}/`)
  }

  async getHostWallet(id: string) {
    return this.request(`/hosts/${id}/wallet/`)
  }

  async withdrawMoney(hostId: string, amount: number, description?: string) {
    return this.request(`/hosts/${hostId}/withdraw_money/`, {
      method: 'POST',
      body: JSON.stringify({ amount, description }),
    })
  }

  async getHostGPUs(id: string) {
    return this.request(`/hosts/${id}/gpus/`)
  }

  async getHostSessions(id: string) {
    return this.request(`/hosts/${id}/sessions/`)
  }

  async getCurrentHost() {
    return this.request('/hosts/current/')
  }

  async registerAsHost() {
    return this.request('/hosts/register/', {
      method: 'POST',
    })
  }

  // GPUs
  async getAvailableGPUs() {
    return this.request('/gpus/available/')
  }

  async getGPU(id: string) {
    return this.request(`/gpus/${id}/`)
  }

  async createGPU(data: any) {
    return this.request('/gpus/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateGPU(id: string, data: any) {
    return this.request(`/gpus/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  }

  // Sessions
  async createSession(data: any) {
    return this.request('/sessions/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getSession(id: string) {
    return this.request(`/sessions/${id}/`)
  }

  async updateSession(id: string, data: any) {
    return this.request(`/sessions/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  }

  async startSession(id: string) {
    return this.request(`/sessions/${id}/start/`, {
      method: 'POST',
    })
  }

  async stopSession(id: string) {
    return this.request(`/sessions/${id}/stop/`, {
      method: 'POST',
    })
  }

  async endSession(id: string) {
    return this.request(`/sessions/${id}/end_session/`, {
      method: 'POST',
    })
  }

  async cancelSession(id: string) {
    return this.request(`/sessions/${id}/cancel_session/`, {
      method: 'POST',
    })
  }

  async extendSession(id: string, hours: number) {
    return this.request(`/sessions/${id}/extend/`, {
      method: 'POST',
      body: JSON.stringify({ hours }),
    })
  }

  // Dashboard
  async getDashboardStats() {
    return this.request('/dashboard/stats/')
  }

  // Tunnels
  async getTunnelStatus() {
    return this.request('/tunnels/manage/')
  }

  // GPU Management
  async toggleGpuAvailability(gpuId: string) {
    return this.request(`/gpus/${gpuId}/toggle_availability/`, {
      method: 'POST',
    })
  }

  async updateGpuPricing(gpuId: string, pricePerHour: number) {
    return this.request(`/gpus/${gpuId}/`, {
      method: 'PATCH',
      body: JSON.stringify({ gpu_price: pricePerHour }),
    })
  }
}

export const apiClient = new ApiClient()
export type { ApiError }
