// Security utilities for input sanitization and XSS prevention
// Addresses CVE-2025-55182 by preventing malicious payloads

import DOMPurify from "isomorphic-dompurify"

/**
 * Sanitize HTML content to prevent XSS attacks
 */
export function sanitizeHtml(dirty: string): string {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ["b", "i", "em", "strong", "a", "p", "br"],
    ALLOWED_ATTR: ["href", "target", "rel"],
  })
}

/**
 * Sanitize user input for database queries
 * Escapes special characters that could be used in SQL injection
 */
export function sanitizeInput(input: string): string {
  if (typeof input !== "string") return ""

  return input
    .replace(/[<>]/g, "") // Remove angle brackets
    .replace(/javascript:/gi, "") // Remove javascript: protocol
    .replace(/on\w+=/gi, "") // Remove event handlers
    .trim()
}

/**
 * Validate and sanitize numeric input
 */
export function sanitizeNumber(value: unknown): number {
  const num = Number(value)
  if (Number.isNaN(num) || !Number.isFinite(num)) return 0
  return num
}

/**
 * Validate email format
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Sanitize object properties recursively
 * Used to clean data before sending to server components
 */
export function sanitizeObject<T extends Record<string, unknown>>(obj: T): T {
  const result = {} as T

  for (const key in obj) {
    const value = obj[key]

    if (typeof value === "string") {
      result[key] = sanitizeInput(value) as T[typeof key]
    } else if (typeof value === "number") {
      result[key] = sanitizeNumber(value) as T[typeof key]
    } else if (typeof value === "object" && value !== null && !Array.isArray(value)) {
      result[key] = sanitizeObject(value as Record<string, unknown>) as T[typeof key]
    } else if (Array.isArray(value)) {
      result[key] = value.map((item) =>
        typeof item === "object" && item !== null
          ? sanitizeObject(item as Record<string, unknown>)
          : typeof item === "string"
            ? sanitizeInput(item)
            : item,
      ) as T[typeof key]
    } else {
      result[key] = value
    }
  }

  return result
}

/**
 * Validate UUID format
 */
export function isValidUUID(uuid: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
  return uuidRegex.test(uuid)
}

/**
 * Rate limiting helper for server actions
 * Prevents brute force attacks
 */
const rateLimitMap = new Map<string, { count: number; resetTime: number }>()

export function checkRateLimit(identifier: string, maxRequests = 10, windowMs = 60000): boolean {
  const now = Date.now()
  const record = rateLimitMap.get(identifier)

  if (!record || now > record.resetTime) {
    rateLimitMap.set(identifier, { count: 1, resetTime: now + windowMs })
    return true
  }

  if (record.count >= maxRequests) {
    return false
  }

  record.count++
  return true
}

/**
 * CSRF token generation
 */
export function generateCSRFToken(): string {
  const array = new Uint8Array(32)
  crypto.getRandomValues(array)
  return Array.from(array, (byte) => byte.toString(16).padStart(2, "0")).join("")
}
