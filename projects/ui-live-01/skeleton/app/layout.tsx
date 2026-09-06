export const metadata = {
  title: "Rule-Based Budget Allocator",
  description: "UI project: classify transactions and summarize by category",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <main style={{ padding: 16, fontFamily: 'sans-serif' }}>{children}</main>
      </body>
    </html>
  )
}
