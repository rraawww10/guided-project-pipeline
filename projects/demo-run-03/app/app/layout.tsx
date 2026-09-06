export const metadata = {
  title: 'Stockroom Reorder Advisor'
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body style={{ fontFamily: 'sans-serif', padding: 20 }}>
        <nav style={{ marginBottom: 16 }}>
          <a href="/" style={{ marginRight: 12 }}>SKUs</a>
          <a href="/suggestions" style={{ marginRight: 12 }}>Suggestions</a>
          <a href="/purchase-orders" style={{ marginRight: 12 }}>PO History</a>
        </nav>
        {children}
      </body>
    </html>
  )
}
