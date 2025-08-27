import { Button } from "@/components/ui/button"
import Link from "next/link"

export default function HomePage() {
  return (
    <div className="min-h-screen relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-black via-primary/20 to-secondary/30" />
      <div className="absolute inset-0 bg-gradient-to-tr from-accent/10 via-transparent to-primary/20" />

      <div className="relative flex items-center justify-center min-h-screen">
        <div className="text-center space-y-12 px-4">
          <div className="space-y-6">
            <h1 className="text-7xl md:text-8xl font-bold bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent glow-text">
              Labhya
            </h1>
            <p className="text-2xl md:text-3xl text-white/90 font-medium">GPU Rental Platform</p>
            <p className="text-lg text-white/70 max-w-2xl mx-auto">
              Rent high-performance RTX GPUs or become a host and earn money from your hardware
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
            <Link href="/register?type=renter">
              <Button
                size="lg"
                className="gradient-rtx gradient-rtx-hover glow-green text-xl px-12 py-6 h-auto font-semibold min-w-[200px]"
              >
                Rent GPU
              </Button>
            </Link>

            <Link href="/register?type=host">
              <Button
                size="lg"
                variant="outline"
                className="rtx-border glow-blue text-xl px-12 py-6 h-auto bg-transparent text-white border-2 border-secondary hover:bg-secondary/20 font-semibold min-w-[200px]"
              >
                Become a Host
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
