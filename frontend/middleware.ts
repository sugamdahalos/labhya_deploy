import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Protected routes that require authentication
  const protectedRoutes = ["/dashboard", "/host", "/session"]

  // Check if the current path is protected
  const isProtectedRoute = protectedRoutes.some((route) => pathname.startsWith(route))

  if (isProtectedRoute) {
    // Check for user session in localStorage (this is a simplified check)
    // In a real app, you'd validate a JWT token or session cookie
    const response = NextResponse.next()

    // Add a header to indicate this is a protected route
    response.headers.set("x-protected-route", "true")

    return response
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/dashboard/:path*", "/host/:path*", "/session/:path*"],
}
