"use client"

import { useState } from "react"
import { useAuth } from "@/components/auth/auth-context"
import { useRenterDashboard } from "@/hooks/use-api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { toast } from "@/hooks/use-toast"
import { apiClient } from "@/lib/api"
import { Loader2, Activity, DollarSign, Clock, Play, Square, Plus, Receipt } from "lucide-react"
import { formatCurrency, toNumber } from "@/lib/utils"

export default function RenterDashboard() {
  const { user } = useAuth()
  const { sessions, wallet, loading, error, addMoney } = useRenterDashboard()
  const [addFundsOpen, setAddFundsOpen] = useState(false)
  const [amount, setAmount] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)

  const handleAddFunds = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      toast({
        title: "Invalid Amount",
        description: "Please enter a valid amount to add.",
        variant: "destructive"
      })
      return
    }

    setIsProcessing(true)
    try {
      await addMoney(parseFloat(amount), "Manual deposit")
      toast({
        title: "Funds Added",
        description: `Successfully added $${amount} to your wallet.`,
        variant: "default"
      })
      setAmount("")
      setAddFundsOpen(false)
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to add funds. Please try again.",
        variant: "destructive"
      })
    } finally {
      setIsProcessing(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading dashboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">Error: {error}</p>
          <Button onClick={() => window.location.reload()}>Retry</Button>
        </div>
      </div>
    )
  }

  const activeSessions = sessions.filter((s: any) => s.status === 'ACTIVE')
  const completedSessions = sessions.filter((s: any) => s.status === 'COMPLETED')
  const totalSpent = completedSessions.reduce((sum: number, s: any) => {
    return sum + toNumber(s.total_cost)
  }, 0)

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
          Welcome back, {user?.name}!
        </h1>
        <p className="text-muted-foreground mt-2">Manage your GPU rentals and monitor performance</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card className="gradient-card rtx-border glow-green">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Active Rentals</p>
                <p className="text-2xl font-bold">{activeSessions.length}</p>
              </div>
              <Activity className="h-8 w-8 text-primary" />
            </div>
          </CardContent>
        </Card>

        <Card className="gradient-card rtx-border glow-blue">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Wallet Balance</p>
                <p className="text-2xl font-bold">${formatCurrency(wallet?.balance)}</p>
              </div>
              <DollarSign className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="gradient-card rtx-border glow-purple">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Sessions</p>
                <p className="text-2xl font-bold">{sessions.length}</p>
              </div>
              <Clock className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="gradient-card rtx-border glow-orange">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Spent</p>
                <p className="text-2xl font-bold">${totalSpent.toFixed(2)}</p>
              </div>
              <DollarSign className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="active" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="active">Active Rentals</TabsTrigger>
          <TabsTrigger value="history">Rental History</TabsTrigger>
          <TabsTrigger value="wallet">Wallet</TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="space-y-6">
          {activeSessions.length === 0 ? (
            <Card className="gradient-card rtx-border">
              <CardContent className="p-8 text-center">
                <Activity className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">No Active Rentals</h3>
                <p className="text-muted-foreground mb-4">Start renting a GPU to see your active sessions here</p>
                <Button asChild className="gradient-rtx gradient-rtx-hover glow-green">
                  <a href="/marketplace">Browse GPUs</a>
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {activeSessions.map((session: any) => (
                <Card key={session.id} className="gradient-card rtx-border glow-green">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{session.gpu.gpu_name}</CardTitle>
                      <Badge variant="default" className="bg-green-500/10 text-green-500 border-green-500/20">
                        {session.status}
                      </Badge>
                    </div>
                    <CardDescription>{session.gpu.gpu_model}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Duration</span>
                      <span className="font-medium">{session.duration_hours}h</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Cost</span>
                      <span className="font-medium">${formatCurrency(session.total_cost)}</span>
                    </div>
                    {session.ssh_port && (
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">SSH Port</span>
                        <span className="font-medium">{session.ssh_port}</span>
                      </div>
                    )}
                    <div className="flex gap-2 pt-2">
                      <Button size="sm" className="flex-1">
                        <Play className="h-4 w-4 mr-2" />
                        Connect
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1"
                        onClick={async () => {
                          try {
                            setIsProcessing(true)
                            await apiClient.stopSession(session.id)
                            toast({ title: 'Stopped', description: 'Session stopped', variant: 'default' })
                            // refresh dashboard to reflect changes
                            window.location.reload()
                          } catch (err: any) {
                            toast({ title: 'Error', description: err?.message || 'Failed to stop session', variant: 'destructive' })
                          } finally {
                            setIsProcessing(false)
                          }
                        }}
                      >
                        <Square className="h-4 w-4 mr-2" />
                        Stop
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="history" className="space-y-6">
          <Card className="gradient-card rtx-border">
            <CardHeader>
              <CardTitle>Rental History</CardTitle>
              <CardDescription>Your past GPU rental sessions</CardDescription>
            </CardHeader>
            <CardContent>
              {completedSessions.length === 0 ? (
                <div className="text-center py-8">
                  <Clock className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground">No rental history yet</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {completedSessions.map((session: any) => (
                    <div key={session.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <h4 className="font-medium">{session.gpu.gpu_name}</h4>
                        <p className="text-sm text-muted-foreground">
                          {session.duration_hours}h • {new Date(session.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">${formatCurrency(session.total_cost)}</p>
                        <Badge variant="secondary">{session.status}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="wallet" className="space-y-6">
          <Card className="gradient-card rtx-border glow-blue">
            <CardHeader>
              <CardTitle>Wallet Balance</CardTitle>
              <CardDescription>Manage your funds for GPU rentals</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center mb-6">
                <p className="text-3xl font-bold">${formatCurrency(wallet?.balance)}</p>
                <p className="text-muted-foreground">Available Balance</p>
              </div>
              <div className="flex gap-4">
                <Dialog open={addFundsOpen} onOpenChange={setAddFundsOpen}>
                  <DialogTrigger asChild>
                    <Button className="flex-1 gradient-rtx gradient-rtx-hover glow-green">
                      <Plus className="h-4 w-4 mr-2" />
                      Add Funds
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Add Funds to Wallet</DialogTitle>
                      <DialogDescription>
                        Enter the amount you want to add to your wallet for GPU rentals.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="amount">Amount ($)</Label>
                        <Input
                          id="amount"
                          type="number"
                          placeholder="Enter amount"
                          value={amount}
                          onChange={(e) => setAmount(e.target.value)}
                          min="1"
                          step="0.01"
                        />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setAddFundsOpen(false)}>
                        Cancel
                      </Button>
                      <Button 
                        onClick={handleAddFunds}
                        disabled={isProcessing}
                        className="gradient-rtx gradient-rtx-hover"
                      >
                        {isProcessing ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Processing...
                          </>
                        ) : (
                          "Add Funds"
                        )}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
                <Button variant="outline" className="flex-1 rtx-border">
                  <Receipt className="h-4 w-4 mr-2" />
                  View Transactions
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
