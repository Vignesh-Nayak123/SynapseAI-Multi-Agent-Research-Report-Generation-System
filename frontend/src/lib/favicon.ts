const LIGHT_SVG = '%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 100 100%27%3E%3Cdefs%3E%3ClinearGradient id=%27bg%27 x1=%270%27 y1=%270%27 x2=%27100%27 y2=%27100%27%3E%3Cstop offset=%270%25%27 stop-color=%27%236366f1%27/%3E%3Cstop offset=%27100%25%27 stop-color=%27%23818cf8%27/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width=%27100%27 height=%27100%27 rx=%2722%27 fill=%27url(%23bg)%27/%3E%3Cpath d=%27M35 28C35 25.8 36.8 24 39 24h16l16 16v32c0 2.2-1.8 4-4 4H39c-2.2 0-4-1.8-4-4V28z%27 fill=%27%23fff%27 opacity=%270.95%27/%3E%3Cpath d=%27M55 24v12c0 2.2 1.8 4 4 4h12%27 fill=%27none%27 stroke=%27%23fff%27 stroke-width=%272%27 opacity=%270.5%27/%3E%3Cpath d=%27M41 47h18M41 55h18M41 63h12%27 stroke=%27%234f46e5%27 stroke-width=%273%27 stroke-linecap=%27round%27 opacity=%270.5%27/%3E%3C/svg%3E'

const DARK_SVG = '%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 100 100%27%3E%3Crect width=%27100%27 height=%27100%27 rx=%2722%27 fill=%27%231c1b1a%27/%3E%3Cpath d=%27M35 28C35 25.8 36.8 24 39 24h16l16 16v32c0 2.2-1.8 4-4 4H39c-2.2 0-4-1.8-4-4V28z%27 fill=%27%23e8e6e1%27 opacity=%27.95%27/%3E%3Cpath d=%27M55 24v12c0 2.2 1.8 4 4 4h12%27 fill=%27none%27 stroke=%27%23e8e6e1%27 stroke-width=%272%27 opacity=%27.6%27/%3E%3Cpath d=%27M41 47h18M41 55h18M41 63h12%27 stroke=%27%23a5b4fc%27 stroke-width=%273%27 stroke-linecap=%27round%27 opacity=%27.8%27/%3E%3C/svg%3E'

const LIGHT_APPLE_SVG = '%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 180 180%27%3E%3Cdefs%3E%3ClinearGradient id=%27bg%27 x1=%270%27 y1=%270%27 x2=%27180%27 y2=%27180%27%3E%3Cstop offset=%270%25%27 stop-color=%27%236366f1%27/%3E%3Cstop offset=%27100%25%27 stop-color=%27%23818cf8%27/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width=%27180%27 height=%27180%27 rx=%2740%27 fill=%27url(%23bg)%27/%3E%3Cpath d=%27M68 48C68 44.7 70.7 42 74 42h42l28 28v60c0 3.3-2.7 6-6 6H74c-3.3 0-6-2.7-6-6V48z%27 fill=%27%23fff%27 opacity=%270.95%27/%3E%3Cpath d=%27M116 42v22c0 3.3 2.7 6 6 6h22%27 fill=%27none%27 stroke=%27%23fff%27 stroke-width=%273%27 opacity=%270.5%27/%3E%3Cpath d=%27M78 84h34M78 100h34M78 116h22%27 stroke=%27%234f46e5%27 stroke-width=%275%27 stroke-linecap=%27round%27 opacity=%270.5%27/%3E%3C/svg%3E'

const DARK_APPLE_SVG = '%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 180 180%27%3E%3Crect width=%27180%27 height=%27180%27 rx=%2740%27 fill=%27%231c1b1a%27/%3E%3Cpath d=%27M68 48C68 44.7 70.7 42 74 42h42l28 28v60c0 3.3-2.7 6-6 6H74c-3.3 0-6-2.7-6-6V48z%27 fill=%27%23e8e6e1%27 opacity=%27.95%27/%3E%3Cpath d=%27M116 42v22c0 3.3 2.7 6 6 6h22%27 fill=%27none%27 stroke=%27%23e8e6e1%27 stroke-width=%273%27 opacity=%27.6%27/%3E%3Cpath d=%27M78 84h34M78 100h34M78 116h22%27 stroke=%27%23a5b4fc%27 stroke-width=%275%27 stroke-linecap=%27round%27 opacity=%27.8%27/%3E%3C/svg%3E'

const LIGHT_THEME_COLOR = '#faf9f7'
const DARK_THEME_COLOR = '#0c0b0a'

export function setFavicon(theme: 'light' | 'dark') {
  if (typeof document === 'undefined') return
  const href = `data:image/svg+xml,${theme === 'light' ? LIGHT_SVG : DARK_SVG}`

  // Remove existing favicon links to avoid conflicts with HTML media-query variants
  document.querySelectorAll('link[rel="icon"]').forEach(el => el.remove())

  // Add a single favicon link matching the current theme
  const link = document.createElement('link')
  link.rel = 'icon'
  link.type = 'image/svg+xml'
  link.href = href
  document.head.appendChild(link)

  // Update apple-touch-icon for iOS home screen
  const appleHref = `data:image/svg+xml,${theme === 'light' ? LIGHT_APPLE_SVG : DARK_APPLE_SVG}`
  const existingApple = document.querySelector('link[rel="apple-touch-icon"]')
  if (existingApple) {
    existingApple.setAttribute('href', appleHref)
  }

  // Also update theme-color meta tags
  const color = theme === 'light' ? LIGHT_THEME_COLOR : DARK_THEME_COLOR
  document.querySelectorAll('meta[name="theme-color"]').forEach(el => el.setAttribute('content', color))
}
