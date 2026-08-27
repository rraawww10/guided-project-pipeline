import type { ReactNode } from 'react'

import './globals.css'

export const metadata = {
  title: 'Tip Split',
  description: 'A shelf of saved restaurant bills, re-split across any number of people.',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
