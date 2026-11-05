import { useRef, useState } from "react";
import type {WorkspaceState} from './state';

export function useResultsLocalState(shared: WorkspaceState) {
  
  const observedWritePolicy=useRef<string|null>(null);
  const executionScopeRef=useRef<{sha:string|undefined;edited:boolean;chat:string|null}>({sha:undefined,edited:false,chat:null});
  const executionStartRef=useRef(false);
  const workflowNoticeRef = useRef<HTMLParagraphElement>(null);
  const [authorizationFocus, setAuthorizationFocus] = useState(false);
  const [workflowApprover, setWorkflowApprover] = useState("operator");
  const [workflowReason, setWorkflowReason] = useState("");
  const approvalRequestRef = useRef<HTMLElement>(null);
  return {observedWritePolicy, executionScopeRef, executionStartRef, workflowNoticeRef, authorizationFocus, setAuthorizationFocus, workflowApprover, setWorkflowApprover, workflowReason, setWorkflowReason, approvalRequestRef};
}
