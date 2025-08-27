"use client"

import { useState } from "react"
import { useAuth } from "@/components/auth/auth-context"
import { useHostDashboard } from "@/hooks/use-api"
import { apiClient } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { toast } from "@/hooks/use-toast"
import { 
  Loader2, 
  Server, 
  DollarSign, 
  Users, 
  TrendingUp, 
  Plus, 
  Edit, 
  Activity,
  ArrowDownToLine,
  Receipt
} from "lucide-react"
import { formatCurrency, toNumber } from "@/lib/utils"

export default function HostDashboard() {
  const { user } = useAuth()
  const { gpus, sessions, wallet, loading, error, withdrawMoney } = useHostDashboard()
  const [withdrawOpen, setWithdrawOpen] = useState(false)
  const [withdrawAmount, setWithdrawAmount] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [agentSetupOpen, setAgentSetupOpen] = useState(false)
  const [editGpuOpen, setEditGpuOpen] = useState(false)
  const [selectedGpu, setSelectedGpu] = useState<any>(null)
  const [editPrice, setEditPrice] = useState("")

  const handleWithdraw = async () => {
    if (!withdrawAmount || parseFloat(withdrawAmount) <= 0) {
      toast({
        title: "Invalid Amount",
        description: "Please enter a valid amount to withdraw.",
        variant: "destructive"
      })
      return
    }

    const walletBalance = toNumber(wallet?.balance) || 0
    if (parseFloat(withdrawAmount) > walletBalance) {
      toast({
        title: "Insufficient Balance",
        description: "You don't have enough balance to withdraw this amount.",
        variant: "destructive"
      })
      return
    }

    setIsProcessing(true)
    try {
      await withdrawMoney(parseFloat(withdrawAmount), "Withdrawal request")
      toast({
        title: "Withdrawal Successful",
        description: `Successfully withdrew $${withdrawAmount} from your wallet.`,
        variant: "default"
      })
      setWithdrawAmount("")
      setWithdrawOpen(false)
    } catch (error: any) {
      toast({
        title: "Withdrawal Failed",
        description: error.message || "Failed to process withdrawal. Please try again.",
        variant: "destructive"
      })
    } finally {
      setIsProcessing(false)
    }
  }

  const handleDownloadAgent = () => {
    // For now, we'll provide instructions to download from GitHub or backend
    setAgentSetupOpen(true)
  }

  const handleAgentDownload = () => {
    // Create download URL for the agent from backend
    const agentDownloadUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api'}/agent/download/`
    
    // Create a temporary link and trigger download
    const link = document.createElement('a')
    link.href = agentDownloadUrl
    link.download = 'labhya-gpu-agent.zip'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    toast({
      title: "Agent Download Started",
      description: "Download started. Extract the files and run start_agent.py to register your GPUs.",
      variant: "default"
    })
    
    // Close the dialog
    setAgentSetupOpen(false)
  }

  const handleToggleAvailability = async (gpuId: string, currentAvailability: boolean) => {
    try {
      setIsProcessing(true)
      await apiClient.toggleGpuAvailability(gpuId)
      
      toast({
        title: "Success",
        description: `GPU ${currentAvailability ? 'disabled' : 'enabled'} successfully`,
      })
      // Trigger a refresh of the data
      window.location.reload()
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to toggle GPU availability. Please try again.",
        variant: "destructive"
      })
    } finally {
      setIsProcessing(false)
    }
  }

  const handleEditGpu = (gpu: any) => {
    setSelectedGpu(gpu)
    setEditPrice(gpu.gpu_price?.toString() || "1.0")
    setEditGpuOpen(true)
  }

  const handleSaveEdit = async () => {
    if (!selectedGpu) return
    
    try {
      setIsProcessing(true)
      await apiClient.updateGpuPricing(selectedGpu.id, parseFloat(editPrice) || 1.0)
      
      toast({
        title: "Success",
        description: "GPU price updated successfully",
      })
      setEditGpuOpen(false)
      window.location.reload()
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update GPU price. Please try again.",
        variant: "destructive"
      })
    } finally {
      setIsProcessing(false)
    }
  }

  const handleMonitorGpu = (gpu: any) => {
    toast({
      title: "Monitor GPU",
      description: `Monitoring for ${gpu.gpu_name} will be available when sessions are active.`,
    })
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading host dashboard...</p>
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

  const activeRentals = sessions.filter((s: any) => s.status === 'ACTIVE')
  const totalEarnings = sessions
    .filter((s: any) => s.status === 'COMPLETED')
    .reduce((sum: number, s: any) => {
      return sum + toNumber(s.total_cost)
    }, 0)

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
          Host Dashboard
        </h1>
        <p className="text-muted-foreground mt-2">Manage your GPU rentals and earnings</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card className="gradient-card rtx-border glow-green">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total GPUs</p>
                <p className="text-2xl font-bold">{gpus.length}</p>
              </div>
              <Server className="h-8 w-8 text-primary" />
            </div>
          </CardContent>
        </Card>

        <Card className="gradient-card rtx-border glow-blue">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Active Rentals</p>
                <p className="text-2xl font-bold">{activeRentals.length}</p>
              </div>
              <Users className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="gradient-card rtx-border glow-purple">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Earnings</p>
                <p className="text-2xl font-bold">${totalEarnings.toFixed(2)}</p>
              </div>
              <TrendingUp className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="gradient-card rtx-border glow-orange">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Wallet Balance</p>
                <p className="text-2xl font-bold">${formatCurrency(wallet?.balance)}</p>
              </div>
              <DollarSign className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="gpus" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="gpus">My GPUs</TabsTrigger>
          <TabsTrigger value="rentals">Active Rentals</TabsTrigger>
          <TabsTrigger value="earnings">Earnings</TabsTrigger>
          <TabsTrigger value="wallet">Wallet</TabsTrigger>
        </TabsList>

        <TabsContent value="gpus" className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold">My GPUs</h2>
            <Dialog open={agentSetupOpen} onOpenChange={setAgentSetupOpen}>
              <DialogTrigger asChild>
                <Button className="gradient-rtx gradient-rtx-hover glow-green">
                  <Plus className="h-4 w-4 mr-2" />
                  Add GPU
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Setup GPU Agent</DialogTitle>
                  <DialogDescription>
                    To add GPUs, you need to install the Labhya GPU Agent on your system.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="bg-muted/50 p-4 rounded-lg">
                    <h4 className="font-semibold mb-2">Agent Requirements:</h4>
                    <ul className="text-sm space-y-1 list-disc list-inside">
                      <li>Windows 10/11 with WSL2 enabled</li>
                      <li>Ubuntu 22.04 LTS in WSL2</li>
                      <li>Docker Desktop with WSL2 backend</li>
                      <li>NVIDIA GPU with compatible drivers</li>
                      <li>Python 3.8+</li>
                    </ul>
                  </div>
                  <div className="bg-blue-500/10 p-4 rounded-lg border border-blue-500/20">
                    <h4 className="font-semibold mb-2 text-blue-600">Setup Instructions:</h4>
                    <ol className="text-sm space-y-2 list-decimal list-inside">
                      <li>Download the agent from the repository</li>
                      <li>Extract files and run <code className="bg-muted px-1 rounded">start_agent.py</code></li>
                      <li>Configure with your host account credentials</li>
                      <li>Agent will auto-detect and register your GPUs</li>
                      <li>GPUs will appear in this dashboard once registered</li>
                    </ol>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    <strong>Note:</strong> The agent runs continuously to manage GPU rentals and tunneling.
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setAgentSetupOpen(false)}>
                    Close
                  </Button>
                  <Button 
                    onClick={handleAgentDownload}
                    className="gradient-rtx gradient-rtx-hover"
                  >
                    Download Agent
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {gpus.length === 0 ? (
            <Card className="gradient-card rtx-border">
              <CardContent className="p-8 text-center">
                <Server className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">No GPUs Listed</h3>
                <p className="text-muted-foreground mb-4">Install the GPU agent to automatically detect and register your GPUs</p>
                <Button 
                  className="gradient-rtx gradient-rtx-hover glow-green"
                  onClick={() => setAgentSetupOpen(true)}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Setup GPU Agent
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {gpus.map((gpu: any) => (
                <Card key={gpu.id} className="gradient-card rtx-border glow-green">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{gpu.gpu_name}</CardTitle>
                      <div className="flex items-center space-x-2">
                        <Switch 
                          checked={gpu.gpu_availability} 
                          onCheckedChange={() => handleToggleAvailability(gpu.id, gpu.gpu_availability)}
                          disabled={isProcessing}
                          id={`gpu-${gpu.id}`}
                        />
                        <Label htmlFor={`gpu-${gpu.id}`} className="text-sm">
                          {gpu.gpu_availability ? 'Available' : 'Offline'}
                        </Label>
                      </div>
                    </div>
                    <CardDescription>{gpu.gpu_model}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Price per hour</span>
                      <span className="font-medium">${gpu.gpu_price_per_hour?.toFixed(2) || '0.00'}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Status</span>
                      <Badge 
                        variant={gpu.gpu_availability ? "default" : "secondary"}
                        className={gpu.gpu_availability ? "bg-green-500/10 text-green-500 border-green-500/20" : ""}
                      >
                        {gpu.gpu_availability ? 'Available' : 'Offline'}
                      </Badge>
                    </div>
                    <div className="flex gap-2 pt-2">
                      <Button 
                        size="sm" 
                        variant="outline" 
                        className="flex-1"
                        onClick={() => handleEditGpu(gpu)}
                        disabled={isProcessing}
                      >
                        <Edit className="h-4 w-4 mr-2" />
                        Edit
                      </Button>
                      <Button 
                        size="sm" 
                        variant="outline" 
                        className="flex-1"
                        onClick={() => handleMonitorGpu(gpu)}
                      >
                        <Activity className="h-4 w-4 mr-2" />
                        Monitor
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="rentals" className="space-y-6">
          <Card className="gradient-card rtx-border">
            <CardHeader>
              <CardTitle>Active Rentals</CardTitle>
              <CardDescription>Currently running GPU rentals</CardDescription>
            </CardHeader>
            <CardContent>
              {activeRentals.length === 0 ? (
                <div className="text-center py-8">
                  <Users className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground">No active rentals</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {activeRentals.map((session: any) => (
                    <div key={session.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <h4 className="font-medium">{session.gpu.gpu_name}</h4>
                        <p className="text-sm text-muted-foreground">
                          Renter: {session.renter} • Duration: {session.duration_hours}h
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">${formatCurrency(session.total_cost)}</p>
                        <Badge className="bg-green-500/10 text-green-500 border-green-500/20">
                          {session.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="earnings" className="space-y-6">
          <Card className="gradient-card rtx-border">
            <CardHeader>
              <CardTitle>Earnings Overview</CardTitle>
              <CardDescription>Your rental earnings history</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center mb-6">
                <p className="text-3xl font-bold">${totalEarnings.toFixed(2)}</p>
                <p className="text-muted-foreground">Total Earnings</p>
              </div>
              <div className="space-y-4">
                {sessions.filter((s: any) => s.status === 'COMPLETED').map((session: any) => (
                  <div key={session.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <h4 className="font-medium">{session.gpu.gpu_name}</h4>
                      <p className="text-sm text-muted-foreground">
                        {new Date(session.created_at).toLocaleDateString()} • {session.duration_hours}h
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">+${formatCurrency(session.total_cost)}</p>
                      <Badge variant="secondary">Completed</Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="wallet" className="space-y-6">
          <Card className="gradient-card rtx-border glow-blue">
            <CardHeader>
              <CardTitle>Wallet Balance</CardTitle>
              <CardDescription>Manage your earnings and withdrawals</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center mb-6">
                <p className="text-3xl font-bold">${formatCurrency(wallet?.balance)}</p>
                <p className="text-muted-foreground">Available Balance</p>
              </div>
              <div className="flex gap-4">
                <Dialog open={withdrawOpen} onOpenChange={setWithdrawOpen}>
                  <DialogTrigger asChild>
                    <Button className="flex-1 gradient-rtx gradient-rtx-hover glow-green">
                      <ArrowDownToLine className="h-4 w-4 mr-2" />
                      Withdraw Funds
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Withdraw Funds</DialogTitle>
                      <DialogDescription>
                        Enter the amount you want to withdraw from your earnings.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="withdrawAmount">Amount ($)</Label>
                        <Input
                          id="withdrawAmount"
                          type="number"
                          placeholder="Enter amount"
                          value={withdrawAmount}
                          onChange={(e) => setWithdrawAmount(e.target.value)}
                          min="1"
                          step="0.01"
                          max={formatCurrency(wallet?.balance)}
                        />
                        <p className="text-sm text-muted-foreground mt-1">
                          Available balance: ${formatCurrency(wallet?.balance)}
                        </p>
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setWithdrawOpen(false)}>
                        Cancel
                      </Button>
                      <Button 
                        onClick={handleWithdraw}
                        disabled={isProcessing}
                        className="gradient-rtx gradient-rtx-hover"
                      >
                        {isProcessing ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Processing...
                          </>
                        ) : (
                          "Withdraw"
                        )}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>

                {/* Edit GPU Dialog */}
                <Dialog open={editGpuOpen} onOpenChange={setEditGpuOpen}>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Edit GPU Price</DialogTitle>
                      <DialogDescription>
                        Update the hourly rental price for {selectedGpu?.gpu_name}
                      </DialogDescription>
                    </DialogHeader>
                    <div className="py-4">
                      <Label htmlFor="price">Price per Hour ($)</Label>
                      <Input
                        id="price"
                        type="number"
                        step="0.01"
                        min="0.01"
                        value={editPrice}
                        onChange={(e) => setEditPrice(e.target.value)}
                        className="mt-2"
                      />
                    </div>
                    <DialogFooter>
                      <Button 
                        variant="outline" 
                        onClick={() => setEditGpuOpen(false)}
                        disabled={isProcessing}
                      >
                        Cancel
                      </Button>
                      <Button 
                        onClick={handleSaveEdit}
                        disabled={isProcessing}
                      >
                        {isProcessing ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Saving...
                          </>
                        ) : (
                          "Save Changes"
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
