"use client"

import { useState } from "react"
import { useAuth } from "@/components/auth/auth-context"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { toast } from "@/hooks/use-toast"
import { Search, Filter, MapPin, Star, Cpu, HardDrive, Gauge, Zap, Clock, SlidersHorizontal, Loader2, Copy, CheckCircle } from "lucide-react"
import { useAvailableGPUs } from "@/hooks/use-api"
import { apiClient } from "@/lib/api"

export default function Marketplace() {
  const { user } = useAuth()
  const { gpus, loading, error } = useAvailableGPUs()
  const [searchTerm, setSearchTerm] = useState("")
  const [sortBy, setSortBy] = useState("price")
  const [priceRange, setPriceRange] = useState([0, 10])
  const [rentDialogOpen, setRentDialogOpen] = useState(false)
  const [selectedGpu, setSelectedGpu] = useState<any>(null)
  const [rentDuration, setRentDuration] = useState("1")
  const [isBooking, setIsBooking] = useState(false)
  const [sessionDetails, setSessionDetails] = useState<any>(null)
  const [connectionDialogOpen, setConnectionDialogOpen] = useState(false)

  const handleRentNow = (gpu: any) => {
    if (!user || user.role !== 'renter') {
      toast({
        title: "Access Denied",
        description: "You must be logged in as a renter to book GPUs.",
        variant: "destructive"
      })
      return
    }
    setSelectedGpu(gpu)
    setRentDialogOpen(true)
  }

  const handleBookGpu = async () => {
    if (!selectedGpu || !user) return

    try {
      setIsBooking(true)
      
      const now = new Date()
      const endTime = new Date(now.getTime() + (parseInt(rentDuration) * 60 * 60 * 1000))
      
      const sessionData = {
        gpu: selectedGpu.id,
        start_time: now.toISOString(),
        ssh_username: 'ubuntu',
        ssh_port: 22
      }

      const response = await apiClient.createSession(sessionData)
      
      if (response.tunnel_info || response.connection_status === 'CONNECTED') {
        setSessionDetails(response)
        setRentDialogOpen(false)
        setConnectionDialogOpen(true)
        
        toast({
          title: "GPU Booked Successfully!",
          description: `Your ${selectedGpu.gpu_name} session is being prepared. Connection details are ready.`,
        })
      } else {
        toast({
          title: "Booking Successful",
          description: `Your ${selectedGpu.gpu_name} session is being set up. Connection details will be available shortly.`,
        })
        setRentDialogOpen(false)
      }
    } catch (error: any) {
      console.error('Booking error:', error)
      toast({
        title: "Booking Failed",
        description: error.message || "Failed to book GPU. Please try again.",
        variant: "destructive"
      })
    } finally {
      setIsBooking(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast({
      title: "Copied!",
      description: "Connection details copied to clipboard.",
    })
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p>Loading available GPUs...</p>
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

  // Filter GPUs based on search and filters
  const filteredGPUs = gpus.filter((gpu: any) => {
    const matchesSearch = gpu.gpu_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         gpu.gpu_model.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesPrice = gpu.gpu_price >= priceRange[0] && gpu.gpu_price <= priceRange[1]
    return matchesSearch && matchesPrice && gpu.gpu_availability
  })

  // Sort GPUs
  const sortedGPUs = [...filteredGPUs].sort((a: any, b: any) => {
    switch (sortBy) {
      case "price":
        return a.gpu_price - b.gpu_price
      case "name":
        return a.gpu_name.localeCompare(b.gpu_name)
      default:
        return 0
    }
  })

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">GPU Marketplace</h1>
        <p className="text-muted-foreground">Discover and rent high-performance GPUs for your projects</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Filters Sidebar */}
        <div className="lg:col-span-1">
          <Card className="gradient-card rtx-border sticky top-4">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <SlidersHorizontal className="h-5 w-5" />
                Filters
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Search */}
              <div className="space-y-2">
                <Label htmlFor="search">Search GPUs</Label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="search"
                    placeholder="Search by name or model"
                    className="pl-10 rtx-border"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
              </div>

              {/* Price Range */}
              <div className="space-y-2">
                <Label>Price Range (per hour)</Label>
                <div className="px-3">
                  <Slider
                    value={priceRange}
                    onValueChange={setPriceRange}
                    max={10}
                    min={0}
                    step={0.1}
                    className="w-full"
                  />
                  <div className="flex justify-between text-sm text-muted-foreground mt-1">
                    <span>${priceRange[0]}</span>
                    <span>${priceRange[1]}</span>
                  </div>
                </div>
              </div>

              {/* Sort */}
              <div className="space-y-2">
                <Label>Sort By</Label>
                <Select value={sortBy} onValueChange={setSortBy}>
                  <SelectTrigger className="rtx-border">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="price">Price: Low to High</SelectItem>
                    <SelectItem value="name">Name: A to Z</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button 
                variant="outline" 
                className="w-full rtx-border"
                onClick={() => {
                  setSearchTerm("")
                  setPriceRange([0, 10])
                  setSortBy("price")
                }}
              >
                Clear Filters
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* GPU Grid */}
        <div className="lg:col-span-3">
          <div className="flex justify-between items-center mb-6">
            <p className="text-muted-foreground">
              {sortedGPUs.length} GPU{sortedGPUs.length !== 1 ? 's' : ''} available
            </p>
          </div>

          {sortedGPUs.length === 0 ? (
            <Card className="gradient-card rtx-border">
              <CardContent className="p-8 text-center">
                <Search className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">No GPUs Found</h3>
                <p className="text-muted-foreground">Try adjusting your filters or search terms</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {sortedGPUs.map((gpu: any) => (
                <Card key={gpu.id} className="gradient-card rtx-border glow-green hover:glow-blue transition-all duration-300">
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-lg">{gpu.gpu_name}</CardTitle>
                        <CardDescription>{gpu.gpu_model}</CardDescription>
                      </div>
                      <Badge className="bg-green-500/10 text-green-500 border-green-500/20">
                        Available
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="text-center p-4 bg-muted/20 rounded-lg">
                      <div className="text-2xl font-bold text-primary">
                        ${gpu.gpu_price.toFixed(2)}
                      </div>
                      <div className="text-sm text-muted-foreground">per hour</div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Host</span>
                        <span className="text-sm font-medium">{gpu.host_name}</span>
                      </div>
                      {gpu.gpu_memory && (
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">Memory</span>
                          <span className="text-sm font-medium">{gpu.gpu_memory}</span>
                        </div>
                      )}
                      {gpu.cuda_cores && (
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">CUDA Cores</span>
                          <span className="text-sm font-medium">{gpu.cuda_cores}</span>
                        </div>
                      )}
                    </div>

                    <Separator />

                    <Button 
                      className="w-full gradient-rtx gradient-rtx-hover glow-green"
                      onClick={() => handleRentNow(gpu)}
                    >
                      <Clock className="h-4 w-4 mr-2" />
                      Rent Now
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Rental Confirmation Dialog */}
      <Dialog open={rentDialogOpen} onOpenChange={setRentDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Book GPU: {selectedGpu?.gpu_name}</DialogTitle>
            <DialogDescription>
              Configure your rental session details
            </DialogDescription>
          </DialogHeader>
          
          {selectedGpu && (
            <div className="space-y-4">
              <div className="p-4 bg-muted/20 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium">{selectedGpu.gpu_name}</span>
                  <Badge className="bg-green-500/10 text-green-500 border-green-500/20">
                    Available
                  </Badge>
                </div>
                <div className="text-sm text-muted-foreground">
                  Host: {selectedGpu.host_name} • {selectedGpu.gpu_memory}GB Memory
                </div>
              </div>
              
              <div>
                <Label htmlFor="duration">Rental Duration (hours)</Label>
                <Select value={rentDuration} onValueChange={setRentDuration}>
                  <SelectTrigger className="mt-2">
                    <SelectValue placeholder="Select duration" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1 hour</SelectItem>
                    <SelectItem value="2">2 hours</SelectItem>
                    <SelectItem value="4">4 hours</SelectItem>
                    <SelectItem value="8">8 hours</SelectItem>
                    <SelectItem value="12">12 hours</SelectItem>
                    <SelectItem value="24">24 hours</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="font-medium">Total Cost:</span>
                  <span className="text-lg font-bold text-primary">
                    ${((selectedGpu.gpu_price || 0) * (parseInt(rentDuration) || 1)).toFixed(2)}
                  </span>
                </div>
                <div className="text-sm text-muted-foreground mt-1">
                  ${selectedGpu.gpu_price}/hour × {rentDuration} hour{parseInt(rentDuration) > 1 ? 's' : ''}
                </div>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setRentDialogOpen(false)}
              disabled={isBooking}
            >
              Cancel
            </Button>
            <Button 
              onClick={handleBookGpu}
              disabled={isBooking}
              className="gradient-rtx gradient-rtx-hover"
            >
              {isBooking ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Booking...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Confirm Booking
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* SSH Connection Details Dialog */}
      <Dialog open={connectionDialogOpen} onOpenChange={setConnectionDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>GPU Session Ready!</DialogTitle>
            <DialogDescription>
              Your GPU session has been established. Use these connection details to access your remote GPU.
            </DialogDescription>
          </DialogHeader>
          
          {sessionDetails && (
            <div className="space-y-4">
              <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="font-medium text-green-700">Session Active</span>
                </div>
                <div className="text-sm text-muted-foreground">
                  Session ID: {sessionDetails.id}
                </div>
              </div>
              
              {sessionDetails.tunnel_info && (
                <div className="space-y-3">
                  <h4 className="font-medium">SSH Connection Details:</h4>
                  
                  <div className="p-3 bg-muted/50 rounded-lg font-mono text-sm">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium">Connection String:</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(sessionDetails.tunnel_info.connection_string)}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                    <code className="block bg-black/20 p-2 rounded">
                      {sessionDetails.tunnel_info.connection_string}
                    </code>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-muted/30 rounded-lg">
                      <div className="text-sm text-muted-foreground mb-1">Host:</div>
                      <div className="font-mono">localhost</div>
                    </div>
                    <div className="p-3 bg-muted/30 rounded-lg">
                      <div className="text-sm text-muted-foreground mb-1">Port:</div>
                      <div className="font-mono">{sessionDetails.tunnel_info.tunnel_port}</div>
                    </div>
                  </div>
                  
                  <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                    <div className="text-sm font-medium mb-1">Quick Start:</div>
                    <ol className="text-sm text-muted-foreground space-y-1">
                      <li>1. Copy the SSH connection string above</li>
                      <li>2. Open your terminal/SSH client</li>
                      <li>3. Paste and run the command</li>
                      <li>4. Access GPU with <code className="bg-black/20 px-1 rounded">nvidia-smi</code></li>
                    </ol>
                  </div>
                </div>
              )}
            </div>
          )}
          
          <DialogFooter>
            <Button 
              variant="outline"
              onClick={() => setConnectionDialogOpen(false)}
            >
              Close
            </Button>
            <Button 
              onClick={() => window.location.href = '/dashboard'}
              className="gradient-rtx gradient-rtx-hover"
            >
              Go to Dashboard
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
