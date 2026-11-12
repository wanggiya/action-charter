"""Loopback-only API transport; never replay a failed/uncertain submission."""
import re
from urllib.parse import urlsplit
import httpx

class ChatError(ValueError):
    def __init__(self,message,*,uncertain=False):
        super().__init__(message);self.uncertain=uncertain

class ChatClient:
    def __init__(self,url='http://127.0.0.1:8765'):
        parsed=urlsplit(url)
        if (parsed.scheme!='http' or parsed.hostname not in {'127.0.0.1','localhost','::1'}
            or parsed.username or parsed.password or parsed.path not in {'','/'} or parsed.query or parsed.fragment):
            raise ChatError('Use a loopback HTTP API address, for example http://127.0.0.1:8765')
        try:
            if not parsed.port or not 1<=parsed.port<=65535:raise ValueError()
        except ValueError:raise ChatError('Specify a valid local API port') from None
        self.url=url.rstrip('/')

    def post(self,endpoint,payload):return self.request('POST',endpoint,payload)

    def get(self,endpoint):return self.request('GET',endpoint,None)

    def request(self,method,endpoint,payload):
        try:
            with httpx.Client(base_url=self.url,trust_env=False,follow_redirects=False,timeout=httpx.Timeout(190,connect=3)) as client:
                with client.stream(method,endpoint,json=payload) as response:
                    body=bytearray()
                    for chunk in response.iter_bytes():
                        body.extend(chunk)
                        if len(body)>4*1024**2:raise ChatError('API response exceeds 4 MiB; inspect saved chat state before retrying')
                    import json
                    try:value=json.loads(body)
                    except ValueError:raise ChatError('API returned an invalid response; inspect saved chat state before retrying') from None
                    if not response.is_success:
                        message=value.get('error','Request rejected') if isinstance(value,dict) else 'Request rejected'
                        raise ChatError(str(message)[:1200],uncertain=response.status_code>=500)
                    if not isinstance(value,dict):raise ChatError('Unexpected API response structure')
                    return value
        except httpx.HTTPError:
            raise ChatError('Local API connection failed or timed out. Start the existing launcher, verify --api-url, and check the saved chat/submission before resending. Nothing was automatically retried.',uncertain=True) from None

    def conversation(self,action,identity):
        if not re.fullmatch('[a-f0-9]{32}',identity):raise ChatError('Chat identity must be 32 lowercase hexadecimal characters')
        return self.post('/api/v1/planner/conversation',{'action':action,'conversation_id':identity})

    def send(self,identity,message,*,expected_revision=None,skills=None,history=None,submission_id):
        try:state=self.conversation('read',identity)
        except ChatError as error:
            error.uncertain=False  # No submission has been sent.
            raise
        revision=state['revision'] if expected_revision is None else expected_revision
        if revision!=state['revision']:raise ChatError('Chat changed since the expected revision; read it before sending. Nothing submitted.')
        selected=state.get('selected_skill_ids',[]) if skills is None else skills
        turn={'action':'turn','conversation_id':identity,'expected_revision':revision,'message':message,
              'allowed_skill_ids':selected,'use_history':history if history is not None else (state.get('context_usage') or {}).get('history_enabled',True)}
        # No current_plan override: continue exactly this chat's server-side proposal.
        return self.post('/api/v1/planner/submit',{'action':'submit','conversation_id':identity,
            'submission_id':submission_id,'inspect_on_send':False,'turn':turn})

    def receipt(self,identity,submission):
        if not re.fullmatch('[a-f0-9]{32}',identity) or not re.fullmatch('[a-f0-9]{32}',submission):raise ChatError('Invalid chat/submission identity')
        return self.post('/api/v1/planner/submit',{'action':'read','conversation_id':identity,'submission_id':submission})
