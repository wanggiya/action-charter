import { useState, type ReactNode } from "react";
import { CircleAlert } from "lucide-react";

type Props = { executionButton: ReactNode; initialApprover: string; initialReason: string; busy: boolean; authorized: boolean; available: boolean; onDraft: (approver: string, reason: string) => void; onAuthorize: (approver: string, reason: string) => void };
export function WorkflowAuthorizationForm({ executionButton, initialApprover, initialReason, busy, authorized, available, onDraft, onAuthorize }: Props) {
  const [approver, setApprover] = useState(initialApprover);
  const [reason, setReason] = useState(initialReason);
  return <form className="workflow-authorization-form" onSubmit={(event) => { event.preventDefault(); if (busy || authorized || !available || !approver.trim() || !reason.trim()) return; onDraft(approver, reason); onAuthorize(approver.trim(), reason.trim()); }}>
    <p>Authorize these exact operations for 30 minutes. Execution starts only when you click Execute.</p>
    <label>Approver<input value={approver} maxLength={200} disabled={busy || authorized} onChange={(event) => setApprover(event.target.value)} onBlur={() => onDraft(approver, reason)}/></label>
    <label>Reason<textarea rows={3} placeholder="Why do you authorize these exact operations?" value={reason} maxLength={2000} disabled={busy || authorized} onChange={(event) => setReason(event.target.value)} onBlur={() => onDraft(approver, reason)}/></label>
    <div className="workflow-decision-actions"><button type="submit" className="context-intent-toggle authorize-button" disabled={busy || authorized || !available || !approver.trim() || !reason.trim()}><CircleAlert size={16}/>{authorized ? "Authorized" : busy ? "Authorizing…" : "Authorize"}</button>{executionButton}</div>
  </form>;
}
