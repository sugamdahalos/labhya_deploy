"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Zap, Search, LayoutDashboard, Server, Settings, Menu, LogOut, Bell, User } from "lucide-react"
import { useAuth } from "@/components/auth/auth-context"

// Role-based navigation
const getRoleBasedNavigation = (userRole: string | undefined) => {
  const baseNav = [
    { name: "Marketplace", href: "/marketplace", icon: Search },
  ]
  
  if (userRole === "renter") {
    return [
      ...baseNav,
      { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    ]
  } else if (userRole === "host") {
    return [
      ...baseNav,
      { name: "Host Panel", href: "/host", icon: Server },
    ]
  }
  
  return baseNav
}

export function Navigation() {
  const pathname = usePathname()
  const router = useRouter()
  const [isOpen, setIsOpen] = useState(false)
  const { user, logout, isLoading } = useAuth()
  
  const navigation = getRoleBasedNavigation(user?.role)

  const isActive = (href: string) => pathname.startsWith(href)

  const handleLogout = () => {
    logout()
    router.push("/")
    setIsOpen(false)
  }

  return (
    <nav className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-r from-primary to-secondary rounded-lg flex items-center justify-center glow-green">
              <Zap className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="font-bold text-xl bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
              Labhya
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-6">
            {user &&
              navigation.map((item) => {
                const Icon = item.icon
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all duration-200 ${
                      isActive(item.href)
                        ? "bg-primary/10 text-primary glow-green"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {item.name}
                  </Link>
                )
              })}
          </div>

          {/* User Menu */}
          <div className="hidden md:flex items-center gap-4">
            {user ? (
              <>
                <Button variant="ghost" size="sm" className="relative">
                  <Bell className="h-4 w-4" />
                  <Badge className="absolute -top-1 -right-1 h-5 w-5 p-0 text-xs gradient-rtx">3</Badge>
                </Button>

                <div className="flex items-center gap-3">
                  <Avatar className="h-8 w-8 ring-2 ring-primary/20">
                    <AvatarImage src={user.avatar || "/placeholder.svg"} />
                    <AvatarFallback className="bg-gradient-to-r from-primary to-secondary text-primary-foreground text-sm">
                      {user.name.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div className="text-sm">
                    <div className="font-semibold">{user.name}</div>
                    <div className="text-xs text-muted-foreground capitalize">{user.role}</div>
                  </div>
                </div>

                <Button variant="ghost" size="sm" onClick={handleLogout}>
                  <LogOut className="h-4 w-4" />
                </Button>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <Link href="/login">
                  <Button variant="ghost" size="sm">
                    Sign In
                  </Button>
                </Link>
                <Link href="/register">
                  <Button size="sm" className="gradient-rtx gradient-rtx-hover glow-green">
                    Get Started
                  </Button>
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Menu */}
          <Sheet open={isOpen} onOpenChange={setIsOpen}>
            <SheetTrigger asChild className="md:hidden">
              <Button variant="ghost" size="sm">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="gradient-card rtx-border">
              <div className="flex flex-col h-full">
                {user ? (
                  <>
                    <div className="flex items-center gap-3 mb-8">
                      <Avatar className="h-10 w-10 ring-2 ring-primary/20">
                        <AvatarImage src={user.avatar || "/placeholder.svg"} />
                        <AvatarFallback className="bg-gradient-to-r from-primary to-secondary text-primary-foreground">
                          {user.name.charAt(0).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <div className="font-semibold">{user.name}</div>
                        <div className="text-sm text-muted-foreground capitalize">{user.role}</div>
                      </div>
                    </div>

                    <div className="space-y-2 flex-1">
                      {navigation.map((item) => {
                        const Icon = item.icon
                        return (
                          <Link
                            key={item.name}
                            href={item.href}
                            onClick={() => setIsOpen(false)}
                            className={`flex items-center gap-3 px-3 py-3 rounded-lg transition-all duration-200 ${
                              isActive(item.href)
                                ? "bg-primary/10 text-primary glow-green"
                                : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                            }`}
                          >
                            <Icon className="h-5 w-5" />
                            {item.name}
                          </Link>
                        )
                      })}
                    </div>

                    <div className="space-y-2 pt-4 border-t border-border">
                      <Button variant="ghost" className="w-full justify-start">
                        <Settings className="h-4 w-4 mr-3" />
                        Settings
                      </Button>
                      <Button variant="ghost" className="w-full justify-start" onClick={handleLogout}>
                        <LogOut className="h-4 w-4 mr-3" />
                        Sign Out
                      </Button>
                    </div>
                  </>
                ) : (
                  <div className="space-y-4">
                    <div className="text-center mb-8">
                      <h3 className="font-semibold text-lg mb-2">Welcome to Labhya</h3>
                      <p className="text-sm text-muted-foreground">Sign in to access GPU rentals</p>
                    </div>

                    <Link href="/login" onClick={() => setIsOpen(false)}>
                      <Button variant="outline" className="w-full rtx-border bg-transparent">
                        <User className="h-4 w-4 mr-2" />
                        Sign In
                      </Button>
                    </Link>

                    <Link href="/register" onClick={() => setIsOpen(false)}>
                      <Button className="w-full gradient-rtx gradient-rtx-hover glow-green">Get Started</Button>
                    </Link>
                  </div>
                )}
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </nav>
  )
}
