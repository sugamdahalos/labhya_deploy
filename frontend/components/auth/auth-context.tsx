"use client"

import type React from "react"
import { createContext, useContext, useState, useEffect } from "react"
import { apiClient } from "@/lib/api"

interface User {
  id: string
  name: string
  email: string
  role: "renter" | "host"
  avatar?: string
}

interface AuthContextType {
  user: User | null
  login: (email: string, password: string) => Promise<boolean>
  register: (name: string, email: string, password: string, role: "renter" | "host") => Promise<boolean>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check for existing session on mount
    const savedUser = localStorage.getItem("labhya_user")
    const token = localStorage.getItem("labhya_token")
    
    if (savedUser && token) {
      try {
        setUser(JSON.parse(savedUser))
      } catch (error) {
        console.error("Error parsing saved user:", error)
        localStorage.removeItem("labhya_user")
        localStorage.removeItem("labhya_token")
        localStorage.removeItem("labhya_refresh_token")
      }
    }
    setIsLoading(false)
  }, [])

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const response = await apiClient.login(email, password)
      console.log('Login response:', response)
      
      if (response.access) {
        // Use the response data to determine role and user info
        const role = response.user_type || (response.host_id ? "host" : "renter")
        const userId = response.renter_id || response.host_id || response.user_id
        
        const authUser: User = {
          id: userId ? userId.toString() : `user_${response.user_id || Date.now()}`,
          name: response.first_name || email.split("@")[0],
          email: response.email || email,
          role: role as "renter" | "host",
          avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${email}`,
        }

        setUser(authUser)
        localStorage.setItem("labhya_user", JSON.stringify(authUser))
        localStorage.setItem("labhya_token", response.access)
        localStorage.setItem("labhya_refresh_token", response.refresh)
        
        return true
      }
      return false
    } catch (error) {
      console.error("Login error:", error)
      return false
    }
  }

  const register = async (name: string, email: string, password: string, role: "renter" | "host"): Promise<boolean> => {
    try {
      const response = role === "renter" 
        ? await apiClient.registerRenter(name, email, password)
        : await apiClient.registerHost(name, email, password)

      if (response.access) {
        const userId = response.renter_id || response.host_id
        
        const authUser: User = {
          id: userId,
          name,
          email,
          role,
          avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${email}`,
        }

        setUser(authUser)
        localStorage.setItem("labhya_user", JSON.stringify(authUser))
        localStorage.setItem("labhya_token", response.access)
        localStorage.setItem("labhya_refresh_token", response.refresh)
        
        return true
      }
      return false
    } catch (error) {
      console.error("Registration error:", error)
      return false
    }
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem("labhya_user")
    localStorage.removeItem("labhya_token")
    localStorage.removeItem("labhya_refresh_token")
  }

  return <AuthContext.Provider value={{ user, login, register, logout, isLoading }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
