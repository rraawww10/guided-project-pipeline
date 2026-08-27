import type { ReactNode } from 'react'

import './globals.css'

export const metadata = {
  title: 'Recipe Box',
  description: 'A recipe library you can browse, search and re-scale, running from a JSON file on disk.',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
