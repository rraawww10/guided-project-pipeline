/**
 * The 404 body for `/accounts/[name]`. `notFound()` throws, so the page that
 * called it renders nothing further and this boundary answers instead: HTTP
 * 404, one `account-missing` element, and no title, total, sidebar or rows.
 */
export default function AccountNotFound() {
  return (
    <main className="page">
      <h1>Ledger</h1>
      <p data-testid="account-missing">Account not found</p>
    </main>
  )
}
