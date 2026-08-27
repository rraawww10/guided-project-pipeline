const items = ["alpha", "beta", "gamma"]

export default function Page() {
  return (
    <main>
      <h1>Runner Check</h1>
      <ul>
        {/* >>> CUT cut-ui-items */}
        {items.map((it) => (
          <li key={it} data-testid="item">{it}</li>
        ))}
        {/* <<< CUT cut-ui-items */}
      </ul>
    </main>
  )
}
