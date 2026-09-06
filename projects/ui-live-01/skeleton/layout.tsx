export const metadata = {
  title: "Rule-Based Budget Allocator",
  description: "UI live project",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
