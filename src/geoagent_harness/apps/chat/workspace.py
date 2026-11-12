"""Persistent terminal workspace, with standard-library full-screen and plain modes."""
import argparse,json,os,queue,shlex,sys,textwrap,threading,time,uuid
from geoagent_harness.apps.chat.client import ChatClient, ChatError
from geoagent_harness.apps.chat.views import clean, render_chat, render_view, saved_view, interactive_view, table, grouped_chart

HELP='''Type a message to continue this chat. Read-only exploration may calculate; proposals never execute automatically.
/new                 Start a separate chat
/chats               List chats; /open NUMBER or CHAT_ID opens one
/refresh             Reload current chat and list after frontend work
/mode [single|three] Set agent mode for subsequent planning; never execute
/report [RUN_ID]     Read the recorded coordinated report
/diagnostics         Read saved request usage and failures
/workflow            Show the current workflow and parameters
/result [VIEW] [FIELD]  overview, columns, table, chart, groups, report, checks
/chart FIELD         Show saved field distributions as terminal bars
/chart groups [total|within]  Chart saved grouped percentages
/charts              Chart command guide
/groups FIELD [SPLIT] Explicit complete-file grouped calculation, no model call
/columns FIELD SPLIT  Two-field cross-tab (same calculation as /groups)
/statistics [RUN_ID] Read recorded descriptive statistics, matrices and regression
/guidance [RUN_ID]   Read recorded candidate statistical fields and cautions
/analysis-report [RUN_ID] Read the same source-linked statistical report
/crosstab count|row|column|total [swap] Display saved two-field groups
/tablefields FIELD [FIELD]  Load selected source columns
/review              Inspect exact current operations, inputs and effects
/writes [on|off]      Explicit write availability; does not authorize execution
/authorize NAME REASON  Authorize the exact reviewed write workflow, no execution
/execute             Explicitly start the current reviewed workflow
/run [RUN_ID]        Read recorded progress/outcomes; /cancel stops a run
/history             List this chat's workflow, analysis, view and execution records
/view NUMBER         Open a historical record without replacing current work
/continue NUMBER     Restore a workflow/analysis as a new draft revision, no approval reuse
/current             Return to current chat after viewing history
/receipt ID          Check an uncertain submission; never resend automatically
/quit                Exit; /help shows this guide
Full-screen: F2 chats · F3 history · F4 outcome · F5 chart · PgUp/PgDn scroll · Ctrl+D exit.'''


def workflow_text(plan):
    if not plan:return 'No workflow proposal in this chat. Analytical exploration has its own recorded outcome.'
    lines=[plan['plan']['summary']]
    for s in plan['plan']['steps']:
        lines += [f"{s['step_id']} → {s['skill']} · after {', '.join(s.get('depends_on') or []) or 'workflow start'}",clean(json.dumps(s['arguments'],ensure_ascii=False),2000)]
    return '\n'.join(lines)+'\nProposal only. Use the existing governed execution interface to run it.'


class Workspace:
    def __init__(self,client,identity=None):
        self.client=client;self.identity=identity or uuid.uuid4().hex;self.state=None;self.chats=[];self.entries=[];self.historical=None;self.pending_receipt=None;self.review=None;self.authorization=None;self.last_run=None;self.uncertain_execution=None
    def refresh(self):
        self.review=None;self.authorization=None
        self.state=self.client.conversation('read',self.identity);self.chats=self.client.conversation('list','0'*32)['conversations'];self.historical=None
        return render_chat(self.state)
    def history(self):return self.client.post('/api/v1/chat/history',{'action':'list','conversation_id':self.identity})
    def history_item(self,index,action='read'):
        if not self.entries:self.entries=self.history()['entries']
        try:item=self.entries[int(index)-1]
        except (ValueError,IndexError):raise ChatError('Choose a history number from /history') from None
        if int(index)<1:raise ChatError('History numbers start at 1')
        return self.client.post('/api/v1/chat/history',{'action':action,'conversation_id':self.identity,'entry_id':item['id'],**({'expected_revision':self.state['revision']} if action=='continue' else {})})
    def render_history(self,item):
        entry=item['entry'];lines=[f"HISTORICAL · {entry['kind']} · revision {entry.get('revision')} · {entry.get('summary','')}",'Current draft is unchanged. /current returns; /continue NUMBER restores a new draft.']
        if item.get('run'):
            r=item['run'];lines += [f"Run {r['run_id']} · {r['status']}",table(['Step','Operation','Status'],[[s['step_id'],s['skill_id'],s['status']] for s in r['steps']])]
            for s in r['steps']:
                if s.get('outcome'):lines += [s['step_id']+' recorded output:',clean(json.dumps(s['outcome'],ensure_ascii=False),5000)]
        elif item.get('view'):
            v=item['view'];lines += [' / '.join(v['columns']),f"{v['matching_rows']:,} matching rows"]
            rows=v['groups'] if v['view']=='groups' else v['table']['preview'];headers=list(rows[0]) if rows else []
            lines += [table(headers,[[r.get(c) for c in headers] for r in rows[:30]]) if rows else 'No matching rows.', 'Display limited to 30 saved rows; chat history read --json exposes the bounded full record.']
        elif item.get('analytical_session') and entry['kind']=='analysis':
            fake={'conversation_id':self.identity,'revision':entry['revision'],'analytical_session':item['analytical_session']}
            try:lines += [render_view(saved_view(fake))]
            except ChatError:lines += [item['analytical_session']['message']]
        else:lines += [workflow_text(item.get('planner_result'))]
        return '\n'.join(lines)
    def execute(self,line):
        line=line.strip()
        if not line:return ''
        if not self.state:self.refresh()
        if line.split()[0]=='/guidance':
            self.operation('/run',line.split()[1:])
            advice=[(s.get('outcome') or {}).get('field_guidance') for s in self.last_run.get('steps',[])]
            advice=[g for g in advice if g]
            if not advice:raise ChatError('No field guidance in this saved run. A new inspection can record it; no scan was started.')
            lines=[]
            for g in advice:
                lines += [f"Recorded field guidance: {clean(g['source'],960)} · {g['matching_rows']} inspected records",'Advisory candidates; choose the objective and confirm field meanings before statistics.']
                lines += [clean(kind.title()+': '+', '.join(names),2000) for kind,names in g['candidates'].items()]
                lines += [clean(f['name']+': '+'; '.join(f['cautions']),2000) for f in g['fields'] if f['cautions']]
            return '\n'.join(lines)
        if line.split()[0] in {'/statistics','/analysis-report'}:
            self.operation('/run',line.split()[1:])
            reports=[((s.get('outcome') or {}).get('table_analysis') or {}).get('statistics') for s in self.last_run.get('steps',[])]
            reports=[r['report_markdown'] for r in reports if r]
            if not reports:raise ChatError('No statistical analysis is recorded. Ask Planner to include the methods and execute the read-only workflow.')
            return '\n\n'.join('\n'.join(clean(line,64000) for line in r[:64000].split('\n'))+('\n[Terminal report display truncated at 64,000 characters; download the recorded report in Outcome → Statistics.]' if len(r)>64000 else '') for r in reports)
        if self.uncertain_execution and (not line.startswith('/') or line.split()[0] in {'/new','/open','/continue'}):raise ChatError('Execution response is unconfirmed. Inspect /history and /run RUN_ID before sending or switching chats.')
        if self.pending_receipt and (not line.startswith('/') or line.split()[0] in {'/new','/open','/continue'}):raise ChatError('Last submission is unconfirmed. Use /receipt then /refresh before sending or switching chats.')
        if not line.startswith('/'):
            if self.historical:raise ChatError('Historical view is read-only. Use /current to continue current work, or /continue NUMBER to restore a version.')
            if len(line)>8000:raise ChatError('Message exceeds 8,000 characters')
            submission=uuid.uuid4().hex;self.pending_receipt=submission
            try:value=self.client.send(self.identity,line,expected_revision=self.state['revision'],submission_id=submission)
            except ChatError as error:
                if not error.uncertain:self.pending_receipt=None
                raise
            self.state=value['conversation'];self.review=None;self.authorization=None;self.last_run=None;self.pending_receipt=None;self.chats=self.client.conversation('list','0'*32)['conversations']
            output=self.state['messages'][-1]['content']+'\n\n'+value['submission']['finding']
            if (self.state.get('context_usage') or {}).get('model_request',{}).get('stage')=='analytical_exploration':
                try:output+='\n\n'+render_view(saved_view(self.state))
                except ChatError:output+='\nPartial observations saved. /history or /refresh shows available evidence.'
            elif self.state.get('planner_result'):output+='\n\n'+workflow_text(self.state['planner_result'])
            return output
        parts=shlex.split(line);command=parts[0];args=parts[1:]
        if command=='/help':return HELP
        if command=='/quit':return '__QUIT__'
        if command in {'/refresh','/current'}:return self.refresh()
        if command=='/new':self.identity=uuid.uuid4().hex;self.entries=[];return self.refresh()+'\nNew chat. Type a request.'
        if command=='/chats':
            self.chats=self.client.conversation('list','0'*32)['conversations']
            return table(['#','Chat','Summary'],[[i+1,s['conversation_id'],s['summary']] for i,s in enumerate(self.chats)])
        if command=='/open':
            if len(args)!=1:raise ChatError('Use /open NUMBER or CHAT_ID')
            identity=args[0]
            if identity.isdigit():
                index=int(identity)-1
                if not 0<=index<len(self.chats):raise ChatError('Choose a chat number from /chats')
                identity=self.chats[index]['conversation_id']
            state=self.client.conversation('read',identity);self.identity=identity;self.state=state;self.historical=None;self.entries=[]
            return render_chat(state)
        if command in {'/review','/writes','/authorize','/execute','/run','/cancel'}:return self.operation(command,args)
        if command=='/mode':
            if self.historical:raise ChatError('Historical view is read-only; /current first')
            if not args:return 'Agent mode: '+str(self.state.get('agent_mode') or 'legacy; choose single or three')
            if len(args)!=1 or args[0] not in {'single','three'}:raise ChatError('Use /mode single or /mode three')
            self.state=self.client.post('/api/v1/planner/conversation',{'action':'configure_agent_mode','conversation_id':self.identity,'expected_revision':self.state['revision'],'agent_mode':args[0]});self.review=None;self.authorization=None
            return 'Next planning mode: '+args[0]+'. Existing runs keep their recorded mode; nothing executed.'
        report_run=self.historical.get('run') if self.historical else self.last_run
        if command=='/report' and (args or report_run):
            identity=args[0] if args else (report_run or {}).get('run_id')
            if not identity:raise ChatError('Use /report RUN_ID')
            report=self.client.post('/api/v1/workflow/runs',{'action':'report','run_id':identity})
            if report.get('handoff'):
                doc=report['handoff']
                return '\n'.join(clean(line,64000) for line in (doc['analytical_markdown']+'\n'+doc['technical_markdown']).splitlines())
            return json.dumps(report,indent=2,ensure_ascii=False)
        if command=='/diagnostics':
            value=self.client.post('/api/v1/planner/diagnostics',{'conversation_id':self.identity})
            return table(['Kind','Status','Role / phase','Error','Seconds'],[[r['kind'],r['status'],r.get('role','')+' / '+r.get('phase','submission'),r.get('error_code') or '',(r.get('resources') or {}).get('elapsed_seconds','unknown')] for r in value['records']])+'\nSampled API process RAM is shared; model/worker/GPU memory and missing tokens are unknown. Nothing retried or executed.'
        if command=='/workflow':return workflow_text((self.historical or self.state).get('planner_result'))
        if command=='/history':
            history=self.history();self.entries=history['entries']
            return table(['#','Kind','Revision','Summary'],[[i+1,e['kind'],e['revision'],e['summary']] for i,e in enumerate(self.entries)])+'\n'+history['finding']
        if command in {'/view','/continue'}:
            if len(args)!=1:raise ChatError('Use '+command+' NUMBER from /history')
            value=self.history_item(args[0],'continue' if command=='/continue' else 'read')
            if command=='/continue':self.state=value['conversation'];self.historical=None;self.review=None;self.authorization=None;self.last_run=None;return 'Restored as a new draft; no approval or execution reused.\n'+render_chat(self.state)
            self.historical=value;return self.render_history(value)
        if command=='/receipt':
            identity=args[0] if args else self.pending_receipt
            if not identity:raise ChatError('Use /receipt SUBMISSION_ID')
            value=self.client.receipt(self.identity,identity)
            if value['submission']['status'] not in {'processing','starting'}:self.pending_receipt=None
            return value['submission']['status']+' · '+value['submission']['finding']
        if command=='/charts':return 'Terminal charts: /chart age, /chart time_in_hospital, /chart groups total, /chart groups within. Use /groups age readmitted to calculate a new grouping first. Charts read saved evidence only.'
        if command=='/chart' and args and args[0]=='groups':
            if self.historical:
                archived=self.historical.get('view')
                if archived and archived['view']=='groups':
                    value={'chat_id':self.identity,'revision':self.historical['entry']['revision'],'analysis_revision':None,'source':archived['source'],'source_rows':archived['source_rows'],'source_sha256':archived['source_sha256'],'matching_rows':archived['matching_rows'],'rows':archived['groups'],'group_by':archived['group_by'],'total_rows':len(archived['groups'])}
                else:value=saved_view({'conversation_id':self.identity,'revision':self.historical['entry']['revision'],'analytical_session':self.historical.get('analytical_session')},'groups',limit=100)
            else:value=interactive_view(self.client,self.state,'groups',limit=100)
            return render_view(grouped_chart(value,args[1] if len(args)>1 else 'total'))
        if command=='/crosstab':
            if len(args)>2 or (len(args)==2 and args[1]!='swap'):raise ChatError('Use /crosstab count|row|column|total [swap]')
            measure=args[0] if args else 'count';swap=len(args)==2
            if self.historical:
                from geoagent_harness.apps.chat.views import cross_tab
                archived=self.historical.get('view')
                state={'conversation_id':self.identity,'revision':self.historical['entry']['revision'],'analytical_session':self.historical.get('analytical_session')}
                value=saved_view(state,'groups',cross_measure=measure,cross_swap=swap)
                if archived and archived['view']=='groups':value['cross_tab']=cross_tab(archived['groups'],archived['group_by'],archived['matching_rows'],measure=measure,swap=swap)
            else:value=interactive_view(self.client,self.state,'groups',cross_measure=measure,cross_swap=swap)
            if not value.get('cross_tab'):raise ChatError('Use /groups FIELD SPLIT to calculate a two-field grouping first.')
            return render_view(value)
        if command in {'/result','/overview','/columns','/table','/chart','/groups','/checks','/report'}:
            if command=='/groups' and args:return self.calculate('groups',args)
            if command=='/columns' and len(args)==2:return self.calculate('groups',args)
            view=args[0] if command=='/result' and args else 'overview' if command=='/result' else command[1:]
            field=args[1] if command=='/result' and len(args)>1 else args[0] if command in {'/columns','/chart'} and args else None
            if self.last_run and not self.historical and view=='overview' and (self.state.get('context_usage') or {}).get('model_request',{}).get('stage')!='analytical_exploration':return self.run_text(self.last_run)
            if self.historical:
                if not self.historical.get('analytical_session'):raise ChatError('This item has no analytical profile; /view shows its recorded output')
                state={'conversation_id':self.identity,'revision':self.historical['entry']['revision'],'analytical_session':self.historical['analytical_session']}
                return 'HISTORICAL · no calculation\n'+render_view(saved_view(state,view,field=field))
            return render_view(interactive_view(self.client,self.state,view,field=field))
        if command=='/tablefields':return self.calculate('table',args)
        raise ChatError('Unknown command. /help lists available actions.')
    def prepare(self):
        if self.historical:raise ChatError('Historical view is read-only. /current or /continue first.')
        current=self.client.conversation('read',self.identity)
        if current['revision']!=self.state['revision']:raise ChatError('Chat changed; /refresh before reviewing/executing')
        plan=current.get('planner_result')
        if not plan:raise ChatError('No workflow proposal. Analytical exploration already has its own result.')
        stored=self.client.post('/api/v1/plans/save-generated',{'action':'save_generated_plan','task_id':None,'confirmed_plan_sha256':plan['plan_sha256'],'allowed_skill_ids':plan['allowed_skill_ids'],'planner_result':{k:plan[k] for k in ['agent_id','model','original_request','context_references','plan','warnings']}})
        review=self.client.post('/api/v1/workflow/prepare',{'action':'prepare_workflow','conversation_id':self.identity,'plan_filename':stored['plan_filename'],'confirmed_plan_sha256':stored['plan_sha256']})
        if self.review and self.review['review_sha256']!=review['review_sha256']:self.authorization=None
        self.review=review
        return review
    def operation(self,command,args):
        if self.historical:raise ChatError('Historical view is read-only; /current before changing policy or executing')
        if command=='/writes':
            state=self.client.get('/api/v1/write-policy')
            if args:
                if len(args)!=1 or args[0] not in {'on','off'}:raise ChatError('Use /writes on or /writes off')
                state=self.client.post('/api/v1/write-policy',{'enabled':args[0]=='on','session_id':state['session_id'],'revision':state['revision']});self.authorization=None;self.review=None
            return 'Write availability: '+('ON' if state.get('enabled') else 'OFF')+' · this grants no workflow authorization.'
        if self.uncertain_execution and command not in {'/run','/cancel'}:raise ChatError('Execution response is unconfirmed; inspect /history and /run RUN_ID before another action')
        if command in {'/run','/cancel'}:
            identity=args[0] if args else (self.last_run or {}).get('run_id')
            run=None
            if not identity and command=='/run':
                proposal=self.state.get('planner_result') or {}
                if proposal.get('plan_sha256'):
                    run=self.client.post('/api/v1/workflow/runs',{'action':'latest','conversation_id':self.identity,'confirmed_plan_sha256':proposal['plan_sha256']}).get('record')
                    if run and (run.get('conversation_id')!=self.identity or run.get('plan_sha256')!=proposal['plan_sha256']):
                        raise ChatError('Recovered run does not match this conversation and plan')
                    identity=(run or {}).get('run_id')
            if not identity:raise ChatError('Use /run RUN_ID from /history or /execute')
            if run is None:run=self.client.post('/api/v1/workflow/runs',{'action':'read','run_id':identity})
            if run.get('conversation_id')!=self.identity:raise ChatError('Run does not belong to this chat')
            if command=='/cancel':run=self.client.post('/api/v1/workflow/runs',{'action':'cancel','run_id':identity})
            if self.uncertain_execution:
                from datetime import datetime
                if run['plan_sha256']!=self.uncertain_execution[0] or datetime.fromisoformat(run['started_at']).timestamp()<self.uncertain_execution[1]-.5:raise ChatError('Inspect the recent matching run for the unconfirmed dispatch')
                self.uncertain_execution=None
            self.last_run=run
            return self.run_text(run)
        review=self.prepare()
        if command=='/review':return 'Exact review '+review['review_sha256']+'\n'+table(['Step','Operation','Authorization'],[[s['step_id'],s['skill'],s['requires_approval']] for s in review['steps']])+'\n'+workflow_text(self.state.get('planner_result'))
        if command=='/authorize':
            if not review['approval_required_step_ids']:return 'Read-only workflow: no authorization record needed. /execute starts this exact workflow.'
            if len(args)<2:raise ChatError('Use /authorize YOUR_NAME REASON after inspecting /review')
            self.authorization=self.client.post('/api/v1/workflow/authorize',{'action':'authorize_workflow','conversation_id':review.get('conversation_id'),'plan_filename':review['plan_filename'],'confirmed_plan_sha256':review['plan_sha256'],'confirmed_review_sha256':review['review_sha256'],'approve_required_steps':True,'approver':args[0],'reason':' '.join(args[1:])})
            return 'Authorization recorded for the exact review. Nothing executed. /execute starts it; backend expiry and write policy still apply.'
        if review['approval_required_step_ids'] and (not self.authorization or self.authorization['review_sha256']!=review['review_sha256']):raise ChatError('Write workflow requires Allow writes and exact authorization. Inspect /review, use /writes on and /authorize NAME REASON, then /execute.')
        if self.client.conversation('read',self.identity)['revision']!=self.state['revision']:raise ChatError('Chat changed before dispatch; /refresh first')
        workflow={'action':'execute_workflow','conversation_id':review.get('conversation_id'),'plan_filename':review['plan_filename'],'confirmed_plan_sha256':review['plan_sha256'],'confirmed_review_sha256':review['review_sha256'],'confirm_execution':True}
        if self.authorization:workflow.update({k:self.authorization[k] for k in ['plan_approval_filename','recipe_approval_filename']})
        self.uncertain_execution=(review['plan_sha256'],time.time())
        try:run=self.client.post('/api/v1/workflow/runs',{'action':'start','conversation_id':self.identity,'review_outcome':True,'workflow':workflow})
        except ChatError as error:
            if not error.uncertain:self.uncertain_execution=None;self.authorization=None
            raise
        self.last_run=run;self.authorization=None;self.uncertain_execution=None
        return self.run_text(run)+'\n/run refreshes this recorded attempt; it does not restart it.'
    @staticmethod
    def run_text(run):
        lines=[f"Run {run['run_id']} · {run['status']}",table(['Step','Operation','Status'],[[s['step_id'],s['skill_id'],s['status']] for s in run['steps']])]
        for step in run['steps']:
            if step.get('outcome'):
                outcome=step['outcome'];lines += [step['step_id']+' recorded outcome:']
                if isinstance(outcome,dict) and isinstance(outcome.get('columns'),list) and isinstance(outcome.get('preview'),list):
                    columns=outcome['columns'][:16];lines += [f"{outcome.get('row_count','?')} source rows · bounded preview",table(columns,[[row.get(c) for c in columns] for row in outcome['preview'][:20]])]
                else:lines += [clean(json.dumps(outcome,ensure_ascii=False),6000)]
        if run.get('finding'):lines += [run['finding']]
        return '\n'.join(lines)
    def calculate(self,view,columns):
        if self.historical:raise ChatError('Historical results are read-only; /current first')
        if not 1<=len(columns)<=2:raise ChatError('Choose one or two fields')
        check=saved_view(self.state,'checks')
        self.client.post('/api/v1/analysis/view',{'action':'calculate','conversation_id':self.identity,'expected_revision':self.state['revision'],'source_sha256':check['source_sha256'],'profile_sha256':check['artifact']['sha256'],'view':view,'columns':columns})
        return render_view(interactive_view(self.client,self.state,view))


def terminal_text(value):return '\n'.join(clean(line,10000) for line in str(value).splitlines())


def plain(workspace):
    print('ActionCharter terminal workspace · /help for commands')
    try:print(terminal_text(workspace.refresh()))
    except ChatError as e:print(str(e))
    while True:
        try:line=input('actioncharter> ')
        except (EOFError,KeyboardInterrupt):break
        try:
            result=workspace.execute(line)
            if result=='__QUIT__':break
            print(terminal_text(result))
        except (ChatError,ValueError,KeyError) as e:print('Error: '+clean(str(e),1500))


def fullscreen(workspace):
    import curses
    def run(screen):
        curses.curs_set(1);screen.timeout(100)
        results=queue.Queue();busy=False;output=HELP;draft='';scroll=0;cursor=0
        def task(line):
            try:results.put(workspace.refresh() if line is None else workspace.execute(line))
            except Exception as e:results.put('Error: '+clean(str(e),1500))
        def dispatch(line):
            threading.Thread(target=task,args=(line,),daemon=True).start()
        busy=True;dispatch(None)
        while True:
            try:
                value=results.get_nowait();busy=False
                if value=='__QUIT__':return
                output=value;scroll=0
            except queue.Empty:pass
            h,w=screen.getmaxyx();screen.erase()
            def put(y,x,value,attr=0):
                if 0<=y<h and 0<=x<w:
                    try:screen.addnstr(y,x,clean(value,10000),max(0,w-x-1),attr)
                    except curses.error:pass
            if h<12 or w<65:
                put(0,0,'Resize terminal to at least 65 × 12, or use --plain. Ctrl+D exits.')
            else:
                side=min(30,w//4);status='Working '+ '|/-\\'[int(time.monotonic()*5)%4] if busy else 'Ready'
                put(0,0,'ActionCharter · '+status+' · '+workspace.client.url,curses.A_BOLD)
                put(1,0,('HISTORICAL · ' if workspace.historical else '')+'Chat '+workspace.identity+' · rev '+str((workspace.state or {}).get('revision',0)))
                put(3,0,'CHATS · /open number',curses.A_BOLD)
                for i,c in enumerate(workspace.chats[:h-8]):put(4+i,0,str(i+1)+'. '+clean(c['summary'],side-5),curses.A_REVERSE if c['conversation_id']==workspace.identity else 0)
                for y in range(3,h-4):put(y,side,'│')
                lines=[part for line in output.splitlines() for part in (textwrap.wrap(line,max(12,w-side-4),replace_whitespace=False) or [''])]
                height=h-8;maximum=max(0,len(lines)-height);scroll=min(scroll,maximum);start=maximum-scroll
                for i,line in enumerate(lines[start:start+height]):put(3+i,side+2,line)
                put(h-4,0,'F2 chats · F3 history · F4 outcome · F5 chart · PgUp/PgDn scroll · /help · Ctrl+D quit')
                if workspace.pending_receipt:put(h-3,0,'Submission '+workspace.pending_receipt+' · /receipt checks status; never resend automatically')
                visible=max(1,w-4);begin=max(0,cursor-visible+1);put(h-2,0,'> '+draft[begin:begin+visible])
                try:screen.move(h-2,min(w-2,2+cursor-begin))
                except curses.error:pass
            screen.refresh()
            try:key=screen.get_wch()
            except curses.error:continue
            if key=='\x04':return
            if key=='\x03':draft='';cursor=0;continue
            if key==curses.KEY_PPAGE:scroll+=max(1,h//2);continue
            if key==curses.KEY_NPAGE:scroll=max(0,scroll-max(1,h//2));continue
            if key in {curses.KEY_F2,curses.KEY_F3,curses.KEY_F4,curses.KEY_F5} and not busy:
                dispatch({curses.KEY_F2:'/chats',curses.KEY_F3:'/history',curses.KEY_F4:'/result',curses.KEY_F5:'/chart'}[key]);busy=True;continue
            if key in {'\n','\r',curses.KEY_ENTER}:
                if not busy and draft.strip():dispatch(draft);busy=True;draft='';cursor=0
            elif key in {curses.KEY_BACKSPACE,'\x7f','\b'}:
                if cursor:draft=draft[:cursor-1]+draft[cursor:];cursor-=1
            elif key==curses.KEY_DC:draft=draft[:cursor]+draft[cursor+1:]
            elif key==curses.KEY_LEFT:cursor=max(0,cursor-1)
            elif key==curses.KEY_RIGHT:cursor=min(len(draft),cursor+1)
            elif key==curses.KEY_HOME:cursor=0
            elif key==curses.KEY_END:cursor=len(draft)
            elif isinstance(key,str) and key.isprintable() and len(draft)<8000:draft=draft[:cursor]+key+draft[cursor:];cursor+=1
    try:curses.wrapper(run)
    except curses.error as error:raise ChatError('This terminal cannot initialize full-screen mode; use --plain') from error


def main():
    parser=argparse.ArgumentParser(description='Persistent ActionCharter terminal workspace sharing the frontend API.')
    parser.add_argument('--api-url',default=os.environ.get('ACTIONCHARTER_API_URL','http://127.0.0.1:8765'))
    parser.add_argument('--chat');parser.add_argument('--plain',action='store_true',help='Scrolling prompt mode for limited terminals/pipes')
    args=parser.parse_args()
    try:
        workspace=Workspace(ChatClient(args.api_url),args.chat)
        if args.plain or not sys.stdin.isatty() or not sys.stdout.isatty():plain(workspace)
        else:fullscreen(workspace)
        if workspace.pending_receipt:print('Unconfirmed submission:',workspace.identity,workspace.pending_receipt,'— check /receipt before resending.')
        if workspace.uncertain_execution:print('Unconfirmed execution for chat',workspace.identity,'— inspect /history and the recent /run before retrying.')
    except (ValueError,ImportError) as e:parser.exit(2,'Error: '+clean(str(e),1500)+'\nUse --plain if this terminal cannot run full-screen mode.\n')

if __name__=='__main__':main()
