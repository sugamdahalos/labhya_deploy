"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Play, Pause, Clock, DollarSign, Monitor, AlertTriangle } from "lucide-react"

interface SessionManagerProps {
  sessions: Array<{
    id: string
    gpuName: string
    status: "running" | "paused" | "stopped"
    startTime: string
    duration: number
    remaining: number
    price: number
    usage: {
      gpu: number
      memory: number
      temperature: number
    }
  }>
}

export function SessionManager({ sessions }: SessionManagerProps) {
  const [selectedSession, setSelectedSession] = useState<string | null>(null)
  const [showExtendDialog, setShowExtendDialog] = useState(false)
  const [extendHours, setExtendHours] = useState("2")

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return "bg-green-500"
      case "paused":
        return "bg-yellow-500"
      case "stopped":
        return "bg-red-500"
      default:
        return "bg-gray-500"
    }
  }

  const handleSessionAction = (sessionId: string, action: "pause" | "resume" | "stop") => {
    console.log(`[v0] Session ${sessionId} action: ${action}`)
    // Handle session control logic here
  }

  const handleExtendSession = (sessionId: string, hours: number) => {
    console.log(`[v0] Extending session ${sessionId} by ${hours} hours`)
    setShowExtendDialog(false)
    // Handle session extension logic here
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Active Sessions</h2>
        <Badge variant="outline" className="gradient-rtx">
          {sessions.filter((s) => s.status === "running").length} Running
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sessions.map((session) => (
          <Card key={session.id} className="gradient-card rtx-border hover:glow-green transition-all duration-300">
            <CardHeader className="pb-3">
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg">{session.gpuName}</CardTitle>
                  <CardDescription className="text-sm">Session {session.id.slice(-8)}</CardDescription>
                </div>
                <Badge variant="outline" className={`${getStatusColor(session.status)} text-white`}>
                  {session.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Time and Cost Info */}
              <div className="grid grid-cols-2 gap-4 text-center">
                <div className="p-2 bg-muted/20 rounded">
                  <Clock className="h-4 w-4 mx-auto mb-1 text-primary" />
                  <div className="font-semibold text-sm">{session.remaining.toFixed(1)}h</div>
                  <div className="text-xs text-muted-foreground">Remaining</div>
                </div>
                <div className="p-2 bg-muted/20 rounded">
                  <DollarSign className="h-4 w-4 mx-auto mb-1 text-secondary" />
                  <div className="font-semibold text-sm">${session.price}/hr</div>
                  <div className="text-xs text-muted-foreground">Rate</div>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Progress</span>
                  <span>{(((session.duration - session.remaining) / session.duration) * 100).toFixed(0)}%</span>
                </div>
                <Progress value={((session.duration - session.remaining) / session.duration) * 100} className="h-2" />
              </div>

              {/* Performance Indicators */}
              <div className="space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <span>GPU Usage</span>
                  <span className="font-semibold">{session.usage.gpu}%</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span>Temperature</span>
                  <span
                    className={`font-semibold ${session.usage.temperature > 75 ? "text-red-400" : "text-green-400"}`}
                  >
                    {session.usage.temperature}°C
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 pt-2">
                {session.status === "running" ? (
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1 rtx-border bg-transparent"
                    onClick={() => handleSessionAction(session.id, "pause")}
                  >
                    <Pause className="h-3 w-3 mr-1" />
                    Pause
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    className="flex-1 gradient-rtx gradient-rtx-hover"
                    onClick={() => handleSessionAction(session.id, "resume")}
                  >
                    <Play className="h-3 w-3 mr-1" />
                    Resume
                  </Button>
                )}

                <Button
                  size="sm"
                  variant="outline"
                  className="rtx-border bg-transparent"
                  onClick={() => window.open(`/session/${session.id}`, "_blank")}
                >
                  <Monitor className="h-3 w-3" />
                </Button>

                <Dialog open={showExtendDialog} onOpenChange={setShowExtendDialog}>
                  <DialogTrigger asChild>
                    <Button
                      size="sm"
                      variant="outline"
                      className="rtx-border bg-transparent"
                      onClick={() => setSelectedSession(session.id)}
                    >
                      <Clock className="h-3 w-3" />
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="gradient-card rtx-border">
                    <DialogHeader>
                      <DialogTitle>Extend Session</DialogTitle>
                      <DialogDescription>Add more time to your GPU rental session</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <Label>Additional Hours</Label>
                        <Select value={extendHours} onValueChange={setExtendHours}>
                          <SelectTrigger className="rtx-border">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="1">1 hour</SelectItem>
                            <SelectItem value="2">2 hours</SelectItem>
                            <SelectItem value="4">4 hours</SelectItem>
                            <SelectItem value="8">8 hours</SelectItem>
                            <SelectItem value="12">12 hours</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-muted/20 rounded">
                        <span>Additional Cost</span>
                        <span className="font-semibold text-primary">
                          ${(Number(extendHours) * session.price).toFixed(2)}
                        </span>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          className="flex-1 rtx-border bg-transparent"
                          onClick={() => setShowExtendDialog(false)}
                        >
                          Cancel
                        </Button>
                        <Button
                          className="flex-1 gradient-rtx gradient-rtx-hover"
                          onClick={() => handleExtendSession(selectedSession!, Number(extendHours))}
                        >
                          Extend Session
                        </Button>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>

              {/* Warnings */}
              {session.remaining < 0.5 && (
                <div className="flex items-center gap-2 p-2 bg-yellow-500/20 rounded text-yellow-400 text-sm">
                  <AlertTriangle className="h-4 w-4" />
                  <span>Session ending soon</span>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {sessions.length === 0 && (
        <Card className="gradient-card rtx-border text-center py-12">
          <CardContent>
            <Monitor className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold mb-2">No Active Sessions</h3>
            <p className="text-muted-foreground mb-4">Start a GPU rental to see your sessions here</p>
            <Button className="gradient-rtx gradient-rtx-hover glow-green">Browse GPUs</Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
