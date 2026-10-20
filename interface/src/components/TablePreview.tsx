type Props = { value: unknown; columns?: string[] };
export function TablePreview({ value, columns: preferred }: Props) {
  if (!value || typeof value !== "object") return null;
  const data=value as Record<string,unknown>;
  if (!Array.isArray(data.columns) || !Array.isArray(data.preview)) return null;
  const available=data.columns.filter((c):c is string=>typeof c==="string");
  const columns=preferred?preferred.filter(column=>available.includes(column)):available;
  const rows=data.preview.filter((r):r is Record<string,unknown>=>!!r && typeof r==="object");
  return <div className="table-result-preview"><p>Bounded preview · {rows.length} of {String(data.row_count ?? "?")} rows</p><div tabIndex={0} role="region" aria-label="Table result preview"><table><thead><tr>{columns.map(c=><th key={c}>{c}</th>)}</tr></thead><tbody>{rows.map((row,i)=><tr key={i}>{columns.map(c=><td key={c}>{row[c] == null ? <span aria-label="Missing value">—</span> : String(row[c])}</td>)}</tr>)}</tbody></table></div></div>;
}
