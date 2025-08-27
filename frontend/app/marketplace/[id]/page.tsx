"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { useAuth } from "@/components/auth/auth-context"
import { apiClient } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Calendar } from "@/components/ui/calendar"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { toast } from "@/hooks/use-toast"
import { ArrowLeft, Star, MapPin, Zap, Shield, Wifi, User, MessageSquare, ThumbsUp, Loader2 } from "lucide-react"
import Link from "next/link"

// Mock data for GPU details
const gpuDetails = {
  id: 1,
  name: "RTX 4090",
  model: "NVIDIA GeForce RTX 4090",
  location: "New York, USA",
  price: 2.5,
  specs: {
    vram: "24GB",
    cuda: "16,384",
    boost: "2.52 GHz",
    memory: "GDDR6X",
    bandwidth: "1008 GB/s",
    architecture: "Ada Lovelace",
    process: "4nm TSMC",
  },
  rating: 4.9,
  reviews: 127,
  available: true,
  host: {
    name: "TechHost Pro",
    rating: 4.8,
    totalGPUs: 15,
    joinedDate: "2022",
  },
  features: ["Ray Tracing", "DLSS 3", "AV1 Encode", "PCIe 4.0", "CUDA 11.8"],
  images: ["/rtx-4090-graphics-card-front-view.png", "/rtx-4090-graphics-card-side-view.png", "/rtx-4090-graphics-card-setup.png"],
  description:
    "High-performance RTX 4090 perfect for AI training, 3D rendering, and gaming. Hosted in a professional data center with 24/7 monitoring and support.",
  connectivity: {
    internet: "1 Gbps",
    latency: "< 5ms",
    uptime: "99.9%",
  },
}

const reviews = [
  {
    id: 1,
    user: "Alex Chen",
    rating: 5,
    date: "2024-01-15",
    comment: "Excellent performance for AI training. Setup was seamless and support was responsive.",
    helpful: 12,
    verified: true,
  },
  {
    id: 2,
    user: "Sarah Johnson",
    rating: 5,
    date: "2024-01-10",
    comment: "Perfect for rendering my 3D animations. Great value for the performance.",
    helpful: 8,
    verified: true,
  },
  {
    id: 3,
    user: "Mike Rodriguez",
    rating: 4,
    date: "2024-01-05",
    comment: "Good GPU, minor connectivity issues initially but host resolved quickly.",
    helpful: 5,
    verified: true,
  },
]

export default function GPUDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const { user } = useAuth()
  const [selectedImage, setSelectedImage] = useState(0)
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date())
  const [duration, setDuration] = useState("4")
  const [rentalType, setRentalType] = useState("hourly")
  const [bookingOpen, setBookingOpen] = useState(false)
  const [isBooking, setIsBooking] = useState(false)
  const [gpuData, setGpuData] = useState(gpuDetails) // Will be replaced with API call

  const handleBookGPU = async () => {
    if (!user) {
      toast({
        title: "Authentication Required",
        description: "Please log in to rent a GPU.",
        variant: "destructive"
      })
      router.push("/login")
      return
    }

    if (user.role !== "renter") {
      toast({
        title: "Access Denied",
        description: "Only renters can book GPUs.",
        variant: "destructive"
      })
      return
    }

    setIsBooking(true)
    try {
      const sessionData = {
        gpu: params.id,
        renter: user.id,
        duration: parseInt(duration),
        start_time: selectedDate?.toISOString(),
        description: "GPU rental session"
      }

      const session = await apiClient.createSession(sessionData)
      
      toast({
        title: "GPU Booked Successfully!",
        description: `Your GPU rental session has been created. Session ID: ${session.id}`,
        variant: "default"
      })

      // Redirect to session page
      router.push(`/session/${session.id}`)
    } catch (error: any) {
      toast({
        title: "Booking Failed",
        description: error.message || "Failed to book GPU. Please try again.",
        variant: "destructive"
      })
    } finally {
      setIsBooking(false)
      setBookingOpen(false)
    }
  }

  const calculateTotal = () => {
    const hours = Number.parseInt(duration)
    const rate =
      rentalType === "hourly"
        ? gpuDetails.price
        : rentalType === "daily"
          ? gpuDetails.price * 24 * 0.9
          : gpuDetails.price * 24 * 30 * 0.8
    return (hours * rate).toFixed(2)
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-border bg-card/50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Link href="/marketplace">
              <Button variant="ghost" size="sm" className="rtx-border">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Marketplace
              </Button>
            </Link>
            <div className="flex items-center gap-2">
              <Badge variant={gpuDetails.available ? "default" : "secondary"} className="gradient-rtx">
                {gpuDetails.available ? "Available" : "Busy"}
              </Badge>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Image Gallery */}
            <Card className="gradient-card rtx-border">
              <CardContent className="p-6">
                <div className="space-y-4">
                  <img
                    src={gpuDetails.images[selectedImage] || "/placeholder.svg"}
                    alt={gpuDetails.name}
                    className="w-full h-80 object-cover rounded-lg"
                  />
                  <div className="flex gap-2 overflow-x-auto">
                    {gpuDetails.images.map((image, index) => (
                      <button
                        key={index}
                        onClick={() => setSelectedImage(index)}
                        className={`flex-shrink-0 w-20 h-20 rounded border-2 overflow-hidden ${
                          selectedImage === index ? "border-primary" : "border-border"
                        }`}
                      >
                        <img src={image || "/placeholder.svg"} alt="" className="w-full h-full object-cover" />
                      </button>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* GPU Info */}
            <Card className="gradient-card rtx-border">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-2xl">{gpuDetails.name}</CardTitle>
                    <CardDescription className="text-lg">{gpuDetails.model}</CardDescription>
                    <div className="flex items-center mt-2 text-sm text-muted-foreground">
                      <MapPin className="h-4 w-4 mr-1" />
                      {gpuDetails.location}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold text-primary">${gpuDetails.price}/hr</div>
                    <div className="flex items-center mt-1">
                      <Star className="h-4 w-4 text-yellow-400 mr-1" />
                      <span className="font-semibold">{gpuDetails.rating}</span>
                      <span className="text-muted-foreground ml-1">({gpuDetails.reviews} reviews)</span>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-6">{gpuDetails.description}</p>

                <Tabs defaultValue="specs" className="w-full">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="specs">Specifications</TabsTrigger>
                    <TabsTrigger value="features">Features</TabsTrigger>
                    <TabsTrigger value="connectivity">Connectivity</TabsTrigger>
                  </TabsList>

                  <TabsContent value="specs" className="mt-6">
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      {Object.entries(gpuDetails.specs).map(([key, value]) => (
                        <div key={key} className="text-center p-4 bg-muted/20 rounded-lg">
                          <div className="font-semibold capitalize">{key.replace(/([A-Z])/g, " $1")}</div>
                          <div className="text-sm text-muted-foreground mt-1">{value}</div>
                        </div>
                      ))}
                    </div>
                  </TabsContent>

                  <TabsContent value="features" className="mt-6">
                    <div className="flex flex-wrap gap-2">
                      {gpuDetails.features.map((feature, index) => (
                        <Badge key={index} variant="outline" className="text-sm py-2 px-3">
                          {feature}
                        </Badge>
                      ))}
                    </div>
                  </TabsContent>

                  <TabsContent value="connectivity" className="mt-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="text-center p-4 bg-muted/20 rounded-lg">
                        <Wifi className="h-6 w-6 mx-auto mb-2 text-primary" />
                        <div className="font-semibold">{gpuDetails.connectivity.internet}</div>
                        <div className="text-sm text-muted-foreground">Internet Speed</div>
                      </div>
                      <div className="text-center p-4 bg-muted/20 rounded-lg">
                        <Zap className="h-6 w-6 mx-auto mb-2 text-secondary" />
                        <div className="font-semibold">{gpuDetails.connectivity.latency}</div>
                        <div className="text-sm text-muted-foreground">Latency</div>
                      </div>
                      <div className="text-center p-4 bg-muted/20 rounded-lg">
                        <Shield className="h-6 w-6 mx-auto mb-2 text-accent" />
                        <div className="font-semibold">{gpuDetails.connectivity.uptime}</div>
                        <div className="text-sm text-muted-foreground">Uptime</div>
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>

            {/* Reviews */}
            <Card className="gradient-card rtx-border">
              <CardHeader>
                <CardTitle>Reviews ({reviews.length})</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {reviews.map((review) => (
                  <div key={review.id} className="space-y-3">
                    <div className="flex justify-between items-start">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gradient-to-r from-primary to-secondary rounded-full flex items-center justify-center">
                          <User className="h-5 w-5 text-primary-foreground" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">{review.user}</span>
                            {review.verified && (
                              <Badge variant="outline" className="text-xs">
                                Verified
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-1">
                            {[...Array(5)].map((_, i) => (
                              <Star
                                key={i}
                                className={`h-4 w-4 ${
                                  i < review.rating ? "text-yellow-400 fill-current" : "text-muted-foreground"
                                }`}
                              />
                            ))}
                            <span className="text-sm text-muted-foreground ml-2">{review.date}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <p className="text-muted-foreground">{review.comment}</p>
                    <div className="flex items-center gap-4 text-sm">
                      <Button variant="ghost" size="sm" className="h-8 px-2">
                        <ThumbsUp className="h-3 w-3 mr-1" />
                        Helpful ({review.helpful})
                      </Button>
                    </div>
                    <Separator />
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Booking Sidebar */}
          <div className="space-y-6">
            {/* Host Info */}
            <Card className="gradient-card rtx-border glow-blue">
              <CardHeader>
                <CardTitle className="text-lg">Hosted by {gpuDetails.host.name}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Star className="h-4 w-4 text-yellow-400 mr-1" />
                    <span className="font-semibold">{gpuDetails.host.rating}</span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {gpuDetails.host.totalGPUs} GPUs • Since {gpuDetails.host.joinedDate}
                  </div>
                </div>
                <Button variant="outline" className="w-full rtx-border bg-transparent">
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Contact Host
                </Button>
              </CardContent>
            </Card>

            {/* Booking Form */}
            <Card className="gradient-card rtx-border glow-green">
              <CardHeader>
                <CardTitle className="text-lg">Book This GPU</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Rental Type</Label>
                  <Select value={rentalType} onValueChange={setRentalType}>
                    <SelectTrigger className="rtx-border">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="hourly">Hourly</SelectItem>
                      <SelectItem value="daily">Daily (10% off)</SelectItem>
                      <SelectItem value="monthly">Monthly (20% off)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>
                    Duration ({rentalType === "hourly" ? "hours" : rentalType === "daily" ? "days" : "months"})
                  </Label>
                  <Input
                    type="number"
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                    min="1"
                    className="rtx-border"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Start Date</Label>
                  <Calendar
                    mode="single"
                    selected={selectedDate}
                    onSelect={setSelectedDate}
                    className="rounded-md border rtx-border"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Special Requirements (Optional)</Label>
                  <Textarea placeholder="Any specific setup or configuration needs..." className="rtx-border" />
                </div>

                <Separator />

                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Rate</span>
                    <span>${gpuDetails.price}/hour</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Duration</span>
                    <span>
                      {duration} {rentalType === "hourly" ? "hours" : rentalType === "daily" ? "days" : "months"}
                    </span>
                  </div>
                  <div className="flex justify-between font-semibold text-lg">
                    <span>Total</span>
                    <span className="text-primary">${calculateTotal()}</span>
                  </div>
                </div>

                <Dialog open={bookingOpen} onOpenChange={setBookingOpen}>
                  <DialogTrigger asChild>
                    <Button className="w-full gradient-rtx gradient-rtx-hover glow-green">
                      <Zap className="h-4 w-4 mr-2" />
                      Book Now
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Confirm GPU Rental</DialogTitle>
                      <DialogDescription>
                        Review your booking details before confirming the rental.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div className="bg-muted/50 p-4 rounded-lg">
                        <h4 className="font-semibold mb-2">{gpuDetails.name}</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span>Duration:</span>
                            <span>{duration} hours</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Rate:</span>
                            <span>${gpuDetails.price}/hour</span>
                          </div>
                          <div className="flex justify-between font-semibold">
                            <span>Total:</span>
                            <span>${calculateTotal()}</span>
                          </div>
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Your session will begin immediately after booking confirmation.
                      </p>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setBookingOpen(false)}>
                        Cancel
                      </Button>
                      <Button 
                        onClick={handleBookGPU}
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
                            <Zap className="h-4 w-4 mr-2" />
                            Confirm Booking
                          </>
                        )}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>

                <div className="text-xs text-muted-foreground text-center">
                  You won't be charged until your booking is confirmed
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
