export const metadata = {
  title: 'Mastermind',
  description: 'Seeded Mastermind with deterministic hint and replay',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: 'sans-serif', margin: 20 }}>{children}</body>
    </html>
  )
}
