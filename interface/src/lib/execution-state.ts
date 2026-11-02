/** Presentation only: backend preparation remains authoritative. */
export function executionBlockReason(s:{graph:string;busy:boolean;editing:boolean;draft:boolean;saved:boolean;edited:boolean;needsApproval:boolean;authorized:boolean;available:boolean}):string{
 if(s.graph==='chat-history')return 'Historical view is read-only. Return to the current workflow or continue it as a new draft.';
 if(s.graph==='analytical-session')return 'Recorded analytical evidence. Use its Outcome views; open an executable proposal to run operations.';
 if(s.busy)return 'A task is in progress. Wait for it to finish or inspect its execution status.';
 if(s.editing||s.draft||s.edited)return 'Validate and save the workflow edits before execution.';
 if(!s.saved)return 'No saved executable proposal. Generate or open this conversation’s plan.';
 if(s.needsApproval&&!s.available)return 'Review write availability and authorize the exact workflow before execution.';
 if(s.needsApproval&&!s.authorized)return 'Authorize this exact workflow before execution.';
 return '';
}
