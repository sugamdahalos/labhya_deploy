"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { toast } from "@/hooks/use-toast"
import {
  Play,
  Pause,
  Square,
  RotateCcw,
  Settings,
  Monitor,
  Cpu,
  HardDrive,
  Thermometer,
  Activity,
  Download,
  Upload,
  Terminal,
  FileText,
  Camera,
  Maximize,
  Volume2,
  VolumeX,
  Loader2,
} from "lucide-react"
import { useAuth } from "@/components/auth/auth-context"
import { apiClient } from "@/lib/api"

export default function SessionPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string
  const { user } = useAuth()
  const [session, setSession] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [audioEnabled, setAudioEnabled] = useState(true)
  const [currentTime, setCurrentTime] = useState(new Date())
  const [endSessionOpen, setEndSessionOpen] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    const fetchSession = async () => {
      if (!user || !sessionId) return
      
      try {
        setLoading(true)
        const sessionData = await apiClient.getSession(sessionId)
        setSession(sessionData)
      } catch (err: any) {
        setError(err.message || 'Failed to fetch session')
      } finally {
        setLoading(false)
      }
    }

    fetchSession()
  }, [user, sessionId])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p>Loading session...</p>
        </div>
      </div>
    )
  }

  if (error || !session) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">Error: {error || 'Session not found'}</p>
          <Button onClick={() => window.history.back()}>Go Back</Button>
        </div>
      </div>
    )
  }

  const getElapsedTime = () => {
    if (!session.start_time) return 0
    const start = new Date(session.start_time)
    const elapsed = Math.floor(((currentTime.getTime() - start.getTime()) / 1000 / 3600) * 10) / 10
    return Math.max(0, elapsed)
  }

  const getRemainingTime = () => {
    if (!session.duration_hours) return 0
    const elapsed = getElapsedTime()
    return Math.max(0, session.duration_hours - elapsed)
  }

  const handleEndSession = async () => {
    if (!session) return

    setIsProcessing(true)
    try {
      const result = await apiClient.endSession(session.id)
      
      toast({
        title: "Session Ended",
        description: `Session ended successfully. Total cost: $${result.total_cost}`,
        variant: "default"
      })

      // Refresh session data
      const updatedSession = await apiClient.getSession(sessionId)
      setSession(updatedSession)
      setEndSessionOpen(false)

      // Redirect to dashboard after a delay
      setTimeout(() => {
        router.push("/dashboard")
      }, 3000)
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to end session. Please try again.",
        variant: "destructive"
      })
    } finally {
      setIsProcessing(false)
    }
  }

  const handleCancelSession = async () => {
    if (!session) return

    setIsProcessing(true)
    try {
      await apiClient.cancelSession(session.id)
      
      toast({
        title: "Session Cancelled",
        description: "Session has been cancelled successfully.",
        variant: "default"
      })

      // Refresh session data
      const updatedSession = await apiClient.getSession(sessionId)
      setSession(updatedSession)

      // Redirect to dashboard
      setTimeout(() => {
        router.push("/dashboard")
      }, 2000)
    } catch (error: any) {
      toast({
        title: "Error", 
        description: error.message || "Failed to cancel session. Please try again.",
        variant: "destructive"
      })
    } finally {
      setIsProcessing(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500/10 text-green-500 border-green-500/20'
      case 'paused':
        return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
      case 'completed':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
      case 'terminated':
        return 'bg-red-500/10 text-red-500 border-red-500/20'
      default:
        return 'bg-gray-500/10 text-gray-500 border-gray-500/20'
    }
  }

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-2xl font-bold mb-2">Session: {session.id}</h1>
            <p className="text-muted-foreground">
              {session.gpu?.gpu_name || 'GPU Session'} • Started {new Date(session.start_time).toLocaleString()}
            </p>
          </div>
          <Badge className={getStatusColor(session.status)}>
            {session.status.charAt(0).toUpperCase() + session.status.slice(1)}
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Session View */}
        <div className="lg:col-span-2 space-y-6">
          {/* Remote Desktop */}
          <Card className="gradient-card rtx-border">
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle className="flex items-center gap-2">
                  <Monitor className="h-5 w-5" />
                  Remote Desktop
                </CardTitle>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setAudioEnabled(!audioEnabled)}
                    className="rtx-border"
                  >
                    {audioEnabled ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsFullscreen(!isFullscreen)}
                    className="rtx-border"
                  >
                    <Maximize className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="aspect-video bg-black rounded-lg flex items-center justify-center border-2 border-dashed border-muted-foreground/20">
                <div className="text-center">
                  <Monitor className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-lg font-semibold mb-2">Remote Desktop View</p>
                  <p className="text-muted-foreground mb-4">
                    Connection Status: {session.connection_status || 'Disconnected'}
                  </p>
                  {session.status === 'active' && (
                    <Button className="gradient-rtx gradient-rtx-hover">
                      <Play className="h-4 w-4 mr-2" />
                      Connect to Desktop
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Session Controls */}
          <Card className="gradient-card rtx-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Session Controls
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-3 flex-wrap">
                {session.status === 'ACTIVE' && (
                  <>
                    <Dialog open={endSessionOpen} onOpenChange={setEndSessionOpen}>
                      <DialogTrigger asChild>
                        <Button variant="outline" className="rtx-border">
                          <Square className="h-4 w-4 mr-2" />
                          End Session
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>End Session</DialogTitle>
                          <DialogDescription>
                            Are you sure you want to end this session? This will process the final payment and terminate all connections.
                          </DialogDescription>
                        </DialogHeader>
                        <div className="bg-yellow-500/10 p-4 rounded-lg border border-yellow-500/20">
                          <p className="text-sm text-yellow-600 dark:text-yellow-400">
                            <strong>Current Session Cost:</strong> ${(getElapsedTime() * (session.gpu?.gpu_price || 0)).toFixed(2)}<br/>
                            <strong>Elapsed Time:</strong> {getElapsedTime().toFixed(1)} hours
                          </p>
                        </div>
                        <DialogFooter>
                          <Button variant="outline" onClick={() => setEndSessionOpen(false)}>
                            Cancel
                          </Button>
                          <Button 
                            onClick={handleEndSession}
                            disabled={isProcessing}
                            variant="destructive"
                          >
                            {isProcessing ? (
                              <>
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                Ending...
                              </>
                            ) : (
                              <>
                                <Square className="h-4 w-4 mr-2" />
                                End Session
                              </>
                            )}
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                    
                    <Button 
                      variant="destructive" 
                      onClick={handleCancelSession}
                      disabled={isProcessing}
                    >
                      {isProcessing ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Cancelling...
                        </>
                      ) : (
                        <>
                          <Square className="h-4 w-4 mr-2" />
                          Cancel Session
                        </>
                      )}
                    </Button>
                  </>
                )}
                
                {session.status === 'COMPLETED' && (
                  <div className="text-center w-full py-4">
                    <p className="text-muted-foreground">Session has ended</p>
                    <Button 
                      onClick={() => router.push("/dashboard")}
                      className="mt-2"
                    >
                      Return to Dashboard
                    </Button>
                  </div>
                )}
                
                {session.status === 'CANCELLED' && (
                  <div className="text-center w-full py-4">
                    <p className="text-muted-foreground">Session was cancelled</p>
                    <Button 
                      onClick={() => router.push("/dashboard")}
                      className="mt-2"
                    >
                      Return to Dashboard
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Session Logs */}
          <Card className="gradient-card rtx-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Terminal className="h-5 w-5" />
                Session Logs
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-black/80 rounded-lg p-4 font-mono text-sm max-h-64 overflow-y-auto">
                <div className="space-y-1">
                  <div className="text-green-400">
                    [{new Date(session.start_time).toLocaleTimeString()}] INFO: Session initialized successfully
                  </div>
                  <div className="text-blue-400">
                    [{new Date(session.start_time).toLocaleTimeString()}] INFO: GPU allocated: {session.gpu?.gpu_name}
                  </div>
                  <div className="text-green-400">
                    [{new Date().toLocaleTimeString()}] INFO: Session status: {session.status}
                  </div>
                  {session.connection_error && (
                    <div className="text-red-400">
                      [{new Date().toLocaleTimeString()}] ERROR: {session.connection_error}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Session Info */}
          <Card className="gradient-card rtx-border">
            <CardHeader>
              <CardTitle>Session Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">GPU</span>
                  <span className="text-sm font-medium">{session.gpu?.gpu_name || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Host</span>
                  <span className="text-sm font-medium">{session.gpu?.host?.user?.first_name || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Duration</span>
                  <span className="text-sm font-medium">{session.duration_hours}h</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Elapsed</span>
                  <span className="text-sm font-medium">{getElapsedTime().toFixed(1)}h</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Remaining</span>
                  <span className="text-sm font-medium">{getRemainingTime().toFixed(1)}h</span>
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Rate</span>
                  <span className="text-sm font-medium">${session.gpu?.gpu_price_per_hour || 0}/hour</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Total Cost</span>
                  <span className="text-sm font-medium">
                    ${(getElapsedTime() * (session.gpu?.gpu_price_per_hour || 0)).toFixed(2)}
                  </span>
                </div>
              </div>

              <Separator />

              <Progress value={(getElapsedTime() / session.duration_hours) * 100} className="w-full" />
            </CardContent>
          </Card>

          {/* GPU Specs */}
          {session.gpu && (
            <Card className="gradient-card rtx-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cpu className="h-5 w-5" />
                  GPU Specifications
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Model</span>
                  <span className="text-sm font-medium">{session.gpu.gpu_model}</span>
                </div>
                {session.gpu.gpu_memory && (
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Memory</span>
                    <span className="text-sm font-medium">{session.gpu.gpu_memory}</span>
                  </div>
                )}
                {session.gpu.cuda_cores && (
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">CUDA Cores</span>
                    <span className="text-sm font-medium">{session.gpu.cuda_cores}</span>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
