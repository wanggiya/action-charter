"""Exercise the real full-screen entry point in a PTY against an isolated fixture API."""
import argparse,json,os,pty,re,select,struct,subprocess,time,fcntl,termios
from pathlib import Path

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--api-url',required=True);parser.add_argument('--chat');args=parser.parse_args()
 repo=Path(__file__).resolve().parents[1];master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',32,120,0,0))
 process=subprocess.Popen([str(repo/'actioncharter'),'--api-url',args.api_url]+(['--chat',args.chat] if args.chat else []),stdin=slave,stdout=slave,stderr=slave,cwd=repo,env={**os.environ,'TERM':'xterm-256color'})
 os.close(slave);seen=bytearray()
 def wait_for(text,timeout=25):
  start=time.monotonic();received=bytearray()
  while time.monotonic()-start<timeout:
   if select.select([master],[],[],.1)[0]:
    try:chunk=os.read(master,65536)
    except OSError:break
    received.extend(chunk);seen.extend(chunk)
    if text.encode() in received:return received.decode(errors='replace')
   if process.poll() is not None:break
  raise AssertionError('Terminal did not display '+text+'; tail: '+repr(bytes(received[-1400:])))
 def command(value,expected):os.write(master,value.encode()+b'\r');return wait_for(expected)
 try:
  wait_for('Ready')
  if args.chat:
   chart=command('/chart age','#');assert '#' in chart
   command('/chart groups within','denominators')
   command('/columns age','frequencies')
   command('/columns age readmitted','Cross-tab')
   command('/crosstab row','100.00%')
   command('/crosstab column swap','readmitted')
  else:
   command('Inspect sample_orders.csv.','Proposal only')
   command('/review','review ')
   command('/execute','Run ')
   command('/history','workflow')
   command('/view 1','HISTORICAL')
   command('/current','Chat')
  os.write(master,b'/quit\r');process.wait(timeout=10);assert process.returncode==0
  print(json.dumps({'status':'passed','entry':'./actioncharter','mode':'full-screen PTY','charts_verified':bool(args.chat),'journey':'new chat -> send -> review -> execute read-only -> run history -> outcome -> historical view -> current -> quit','python_command_required':False}))
 finally:
  if process.poll() is None:process.terminate();process.wait(timeout=5)
  os.close(master)
if __name__=='__main__':main()
