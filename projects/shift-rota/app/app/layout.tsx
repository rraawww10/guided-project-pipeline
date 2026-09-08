export const metadata = {
  title: "Escalation Simulator",
  description: "On-call escalation as a small state machine"
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: 'sans-serif', margin: 20 }}>
        <nav style={{ marginBottom: 16 }}>
          <a href="/" style={{ marginRight: 12 }}>Sim</a>
          <a href="/script">Script</a>
        </nav>
        {children}
      </body>
    </html>
  )
}
