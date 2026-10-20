import { type SVGAttributes } from 'react'

interface Props extends SVGAttributes<SVGSVGElement> {
  size?: number
}

export function BrandIcon({ size = 24, className, ...props }: Props) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      {...props}
    >
      <defs>
        <linearGradient id="brand-bg" x1="0" y1="0" x2="100" y2="100">
          <stop offset="0%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#818cf8" />
        </linearGradient>
      </defs>
      {/* App icon rounded square background */}
      <rect width="100" height="100" rx="22" fill="url(#brand-bg)" />
      {/* Document body */}
      <path
        d="M35 28C35 25.8 36.8 24 39 24h16l16 16v32c0 2.2-1.8 4-4 4H39c-2.2 0-4-1.8-4-4V28z"
        fill="#fff"
        opacity="0.95"
      />
      {/* Fold corner */}
      <path
        d="M55 24v12c0 2.2 1.8 4 4 4h12"
        fill="none"
        stroke="#fff"
        strokeWidth="2"
        opacity="0.5"
      />
      {/* Text lines */}
      <path
        d="M41 47h18M41 55h18M41 63h12"
        stroke="#4f46e5"
        strokeWidth="3"
        strokeLinecap="round"
        opacity="0.5"
      />
    </svg>
  )
}

export function BrandMark({ size = 24, className, ...props }: Props) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      {...props}
    >
      <defs>
        <linearGradient id="brand-mark-bg" x1="0" y1="0" x2="100" y2="100">
          <stop offset="0%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#818cf8" />
        </linearGradient>
      </defs>
      {/* Circular background */}
      <circle cx="50" cy="50" r="48" fill="url(#brand-mark-bg)" />
      {/* Document icon */}
      <path
        d="M33 28C33 25.8 34.8 24 37 24h14l16 16v32c0 2.2-1.8 4-4 4H37c-2.2 0-4-1.8-4-4V28z"
        fill="#fff"
        opacity="0.95"
      />
      <path
        d="M51 24v12c0 2.2 1.8 4 4 4h12"
        fill="none"
        stroke="#fff"
        strokeWidth="2"
        opacity="0.5"
      />
      <path
        d="M39 47h16M39 55h16M39 63h10"
        stroke="#4f46e5"
        strokeWidth="3"
        strokeLinecap="round"
        opacity="0.5"
      />
    </svg>
  )
}
