"use client"

import { RegisterForm } from "@/components/auth/register-form"
import { useSearchParams } from "next/navigation"

export default function RegisterPage() {
  const searchParams = useSearchParams()
  const userType = searchParams.get("type") as "renter" | "host" | null

  return <RegisterForm defaultUserType={userType} />
}
