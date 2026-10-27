import {z} from 'zod';
import {plannerResultSchema} from './interface-api';
import {analyticalSessionSchema} from './analytical-session';
import {conversationSchema} from './planner-conversation';
import {runSchema} from './workflow-tools';
export const historyEntrySchema=z.object({id:z.string(),kind:z.string(),revision:z.number().nullable(),summary:z.string(),recorded_at:z.string().optional()}).passthrough();
export const historyRecordSchema=z.object({entry:historyEntrySchema,planner_result:plannerResultSchema.nullable(),analytical_session:analyticalSessionSchema.nullable(),view:z.record(z.unknown()).nullable(),run:runSchema.nullable(),execution_performed:z.literal(false),approval_performed:z.literal(false)});
export type HistoryRecord=z.infer<typeof historyRecordSchema>;
export async function chatHistory(id:string,action:'list'|'read'|'continue'='list',entryId?:string,revision?:number){
 const response=await fetch('/api/v1/chat/history',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,conversation_id:id,entry_id:entryId,expected_revision:revision})});
 const value=await response.json();if(!response.ok)throw new Error(response.status===404?'Restart the updated launcher and refresh to use workflow history. No work was rerun.':value.error??'Chat history unavailable');return value;
}
export const historyConversation=(v:unknown)=>conversationSchema.parse(v);
