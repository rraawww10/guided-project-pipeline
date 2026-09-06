export const metadata = {
  title: "FairShare",
  description: "Expense Settlement Calculator",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <main style={{ padding: 16, fontFamily: 'system-ui, sans-serif' }}>{children}</main>
      </body>
    </html>
  );
}
