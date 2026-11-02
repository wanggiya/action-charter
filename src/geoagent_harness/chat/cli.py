"""Readable shared chats and analytical results through the running interface API."""
import json,uuid
from typing import Literal
import typer
from .client import ChatClient,ChatError
from .views import clean,table,render_chat,render_view,saved_view,interactive_view

def register(app):
    chat=typer.Typer(help='Continue frontend chats and inspect their saved results. Start the normal launcher first.',no_args_is_help=True)
    app.add_typer(chat,name='chat')

    @chat.callback()
    def configure(ctx:typer.Context,api_url:str=typer.Option('http://127.0.0.1:8765','--api-url',envvar='ACTIONCHARTER_API_URL')):
        try:ctx.obj=ChatClient(api_url)
        except ChatError as error:raise typer.BadParameter(str(error)) from None

    def call(fn):
        try:return fn()
        except (ChatError,KeyError,TypeError) as error:
            from geoagent_harness.context_pack.redaction import redact_text
            typer.echo('Error: '+clean(redact_text(str(error)),1500),err=True)
            raise typer.Exit(2)

    def emit(value,text,as_json):typer.echo(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False) if as_json else text())

    @chat.command('diagnostics')
    def diagnostics(ctx:typer.Context,chat_id:str,as_json:bool=typer.Option(False,'--json')):
        """Read bounded content-free usage records, including failed requests."""
        value=call(lambda:ctx.obj.post('/api/v1/planner/diagnostics',{'conversation_id':chat_id}))
        emit(value,lambda:table(['Kind','Status','Phase','Error','Seconds'],[[r['kind'],r['status'],r.get('phase','submission'),r.get('error_code') or '',(r.get('resources') or {}).get('elapsed_seconds','unknown')] for r in value['records']])+'\nRAM is sampled API process RSS; unknown tokens remain unknown. No retry or execution.',as_json)

    @chat.command('report')
    def report(ctx:typer.Context,run_id:str,kind:Literal['analytical','technical','json']=typer.Option('technical','--kind')):
        """Read saved workflow handoff; no source scan, execution or model call."""
        value=call(lambda:ctx.obj.post('/api/v1/workflow/runs',{'action':'report','run_id':run_id}))
        if kind=='json':typer.echo(json.dumps(value,indent=2))
        else:typer.echo(value['handoff'][kind+'_markdown'])

    @chat.command('list')
    def inventory(ctx:typer.Context,as_json:bool=typer.Option(False,'--json')):
        value=call(lambda:ctx.obj.conversation('list','0'*32))
        emit(value,lambda:table(['Chat ID','Revision','Summary'],[[s['conversation_id'],s['revision'],s['summary']] for s in value['conversations']])+'\nLatest 20 saved chats; reads do not run the model.',as_json)

    @chat.command('show')
    def show(ctx:typer.Context,chat_id:str=typer.Argument(),as_json:bool=typer.Option(False,'--json')):
        value=call(lambda:ctx.obj.conversation('read',chat_id));emit(value,lambda:render_chat(value),as_json)

    @chat.command('mode')
    def mode(ctx:typer.Context,chat_id:str,mode:Literal['single','three']):
        state=call(lambda:ctx.obj.conversation('read',chat_id))
        value=call(lambda:ctx.obj.post('/api/v1/planner/conversation',{'action':'configure_agent_mode','conversation_id':chat_id,'expected_revision':state['revision'],'agent_mode':mode}))
        typer.echo('Next planning mode: '+value['agent_mode']+'; no execution or authorization.')

    @chat.command('send')
    def send(ctx:typer.Context,message:str=typer.Argument(),chat_id:str|None=typer.Option(None,'--chat'),
             expected_revision:int|None=typer.Option(None,'--expected-revision',min=0),
             skills:list[str]|None=typer.Option(None,'--skill'),automatic_skills:bool=typer.Option(False,'--automatic-skills'),
             history:bool|None=typer.Option(None,'--history/--no-history'),as_json:bool=typer.Option(False,'--json')):
        """Send a planning/exploration message; omit --chat for a new shared chat. Never authorizes or dispatches a workflow."""
        if not message.strip() or len(message)>8000:raise typer.BadParameter('Use a nonempty message up to 8,000 characters')
        if automatic_skills and skills:raise typer.BadParameter('Choose --skill or --automatic-skills')
        identity=chat_id or uuid.uuid4().hex;submission=uuid.uuid4().hex
        # Print recovery IDs before dispatch, including when the response is lost.
        typer.echo(f'Chat: {identity}\nSubmission: {submission}\nRecovery: chat receipt {identity} {submission}',err=True)
        value=call(lambda:ctx.obj.send(identity,message,expected_revision=expected_revision,skills=[] if automatic_skills else skills or None,history=history,submission_id=submission))
        emit(value,lambda:render_chat(value['conversation'])+'\n\n'+clean(value['submission']['finding'],1000),as_json)

    @chat.command('receipt')
    def receipt(ctx:typer.Context,chat_id:str=typer.Argument(),submission_id:str=typer.Argument(),as_json:bool=typer.Option(False,'--json')):
        """Read submission status only; never resend or execute."""
        value=call(lambda:ctx.obj.receipt(chat_id,submission_id))
        emit(value,lambda:clean(value['submission']['status'])+' · '+clean(value['submission']['finding'],1000),as_json)

    @chat.command('result')
    def result(ctx:typer.Context,chat_id:str=typer.Argument(),view:Literal['overview','columns','table','chart','groups','checks','report']=typer.Option('overview','--view'),
               source:str|None=typer.Option(None,'--source'),field:str|None=typer.Option(None,'--field'),offset:int=typer.Option(0,'--offset',min=0),
               limit:int=typer.Option(20,'--limit',min=1,max=100),as_json:bool=typer.Option(False,'--json')):
        """View saved comprehensive analysis, without scans/model calls. --field selects a column or chart distribution."""
        value=call(lambda:interactive_view(ctx.obj,ctx.obj.conversation('read',chat_id),view,source=source,field=field,offset=offset,limit=limit))
        emit(value,lambda:render_view(value),as_json)

    @chat.command('explore')
    def explore(ctx:typer.Context,chat_id:str=typer.Argument(),group_by:str|None=typer.Option(None,'--group-by'),split_by:str|None=typer.Option(None,'--split-by'),
                columns:list[str]|None=typer.Option(None,'--column'),view:Literal['groups','table']=typer.Option('groups','--view'),source:str|None=typer.Option(None,'--source'),
                offset:int=typer.Option(0,'--offset',min=0),as_json:bool=typer.Option(False,'--json')):
        """Explicit hash-verified full-file read for selected fields/groups; no LLM or workflow execution. Saved selection is shared with frontend."""
        selected=columns or ([group_by]+([split_by] if split_by else []) if group_by else [])
        if not selected or len(selected)>2 or len(set(selected))!=len(selected):raise typer.BadParameter('Choose one/two distinct --column fields, or --group-by and optional --split-by')
        if columns and (group_by or split_by):raise typer.BadParameter('Choose --column or --group-by/--split-by')
        def calculate():
            state=ctx.obj.conversation('read',chat_id);check=saved_view(state,'checks',source=source)
            ctx.obj.post('/api/v1/analysis/view',{'action':'calculate','conversation_id':chat_id,'expected_revision':state['revision'],
                'source_sha256':check['source_sha256'],'profile_sha256':check['artifact']['sha256'],'view':view,'columns':selected,'offset':offset})
            return interactive_view(ctx.obj,state,view,source=source)
        value=call(calculate);emit(value,lambda:render_view(value),as_json)

    @chat.command('history')
    def history(ctx:typer.Context,chat_id:str=typer.Argument(),entry_id:str|None=typer.Option(None,'--entry'),as_json:bool=typer.Option(False,'--json')):
        """List this chat's recorded versions and runs; --entry opens one without changing the current draft."""
        value=call(lambda:ctx.obj.post('/api/v1/chat/history',{'action':'read' if entry_id else 'list','conversation_id':chat_id,'entry_id':entry_id}))
        from .workspace import Workspace
        emit(value,lambda:Workspace(ctx.obj,chat_id).render_history(value) if entry_id else table(['ID','Kind','Revision','Summary'],[[e['id'],e['kind'],e['revision'],e['summary']] for e in value['entries']])+'\n'+value['finding'],as_json)
