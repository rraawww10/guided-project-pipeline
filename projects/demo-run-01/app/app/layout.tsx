export const metadata = {
  title: "Shortlist Scorer",
  description: "Rank a small seed of candidates by simple, explainable rules",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: 'sans-serif', padding: 16 }}>{children}</body>
    </html>
  )
}
