import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Utility function to safely format currency values
export function formatCurrency(value: string | number | null | undefined, defaultValue: string = '0.00'): string {
  if (value === null || value === undefined) {
    return defaultValue
  }
  
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  
  if (isNaN(numValue)) {
    return defaultValue
  }
  
  return numValue.toFixed(2)
}

// Utility function to safely convert to number
export function toNumber(value: string | number | null | undefined, defaultValue: number = 0): number {
  if (value === null || value === undefined) {
    return defaultValue
  }
  
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  
  if (isNaN(numValue)) {
    return defaultValue
  }
  
  return numValue
}
