import { useEffect, useRef, useState } from "react";
type Props = { value: object; disabled: boolean; onValue: (value: unknown) => void; onValidity: (valid: boolean) => void };
export function StructuredArgument({ value, disabled, onValue, onValidity }: Props) {
  const encoded = JSON.stringify(value, null, 2);
  const [text, setText] = useState(encoded);
  const [error, setError] = useState("");
  const validity = useRef(onValidity);
  validity.current = onValidity;
  // An unmounted editor discards its unapplied text; do not leave a stale blocker.
  useEffect(() => () => validity.current(true), []);
  useEffect(() => { setText(encoded); setError(""); }, [encoded]);
  const apply = () => {
    try {
      const parsed: unknown = JSON.parse(text);
      if (typeof parsed !== "object" || parsed === null) throw new Error("Use an object or array");
      onValue(parsed); onValidity(true);
    } catch {
      setError("Use valid JSON. This draft has not been applied; fix it before validation.");
    }
  };
  return <><textarea aria-label="Structured operation parameter" rows={4} value={text} maxLength={12000} disabled={disabled} onChange={event => { setText(event.target.value); setError(""); onValidity(false); }} onBlur={apply}/>{error && <small role="alert">{error}</small>}</>;
}
