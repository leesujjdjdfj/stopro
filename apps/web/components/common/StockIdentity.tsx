type StockLike = {
  name?: string | null;
  ticker?: string | null;
  displayTicker?: string | null;
  market?: string | null;
  exchange?: string | null;
};

export function StockIdentity({
  stock,
  className = "",
  nameClassName = "text-sm font-black text-text",
  metaClassName = "mt-0.5 text-xs font-bold text-subText"
}: {
  stock: StockLike;
  className?: string;
  nameClassName?: string;
  metaClassName?: string;
}) {
  const code = stock.displayTicker || stock.ticker || "";
  const market = stock.market || stock.exchange || "";
  const rawName = stock.name?.trim();
  const hasDistinctName = rawName && rawName.toUpperCase() !== code.toUpperCase();
  const primary = hasDistinctName ? rawName : code;
  const meta = [code, market].filter(Boolean).join(" · ");

  return (
    <div className={`min-w-0 ${className}`}>
      <p className={`truncate ${nameClassName}`}>{primary || "종목명 확인 중"}</p>
      {hasDistinctName && meta ? <p className={`truncate ${metaClassName}`}>{meta}</p> : null}
    </div>
  );
}
