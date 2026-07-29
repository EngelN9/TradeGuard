const checks = [
  ["環境", "research"],
  ["服務狀態", "Bootstrap"],
  ["最高允許環境", "shadow"],
  ["Connected adapters", "尚未實作"],
] as const;

export default function Home() {
  return (
    <main>
      <header>
        <p className="eyebrow">TRADEGUARD</p>
        <span className="environment">RESEARCH / NOT TRADABLE</span>
      </header>

      <section className="hero">
        <p className="kicker">安全優先的策略研究基線</p>
        <h1>先驗證證據，再談策略。</h1>
        <p className="lede">
          目前是可重現開發環境的 Bootstrap。沒有正式交易、提款、轉帳或投資建議功能。
        </p>
      </section>

      <section aria-labelledby="status-heading" className="status-panel">
        <div>
          <p className="kicker">SYSTEM STATUS</p>
          <h2 id="status-heading">明確標示每個安全邊界</h2>
        </div>
        <dl>
          {checks.map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      </section>

      <footer>
        模擬與歷史結果不代表未來報酬。Prompt 1 僅提供離線服務骨架。
      </footer>
    </main>
  );
}
