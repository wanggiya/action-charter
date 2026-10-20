import {useWritePolicy} from '../lib/write-policy';
export function WriteToolsStatus(){
 const {policy,error}=useWritePolicy();
 return <details className="write-tools-status"><summary>Write tools: {policy?.active?(policy.enabled?'enabled':'disabled'):'status unavailable'}</summary><p>{policy?.enabled?'Exact authorization is still required for write operations.':'Open Settings → Allow write operations. Read-only inspection remains available.'}</p>{policy?.locked&&<p>Administratively locked read-only.</p>}{error&&<p>{error}</p>}<small>Availability changes invalidate pending authorization. No overwrite permission is granted.</small></details>;
}
