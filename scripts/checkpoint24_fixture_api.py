"""Private temporary browser API. Only model completion is replaced; no live services."""
import argparse
import json
import os
from pathlib import Path
from shutil import copytree
from http.server import ThreadingHTTPServer
from geoagent_harness.interface_api import conversation, server
from geoagent_harness.model.schemas import ModelResult

parser=argparse.ArgumentParser()
parser.add_argument('--root',required=True)
args=parser.parse_args()
root=Path(args.root).resolve()
repo=Path(__file__).resolve().parents[1]
for directory in ['context','agents']:
    copytree(repo/directory,root/directory)
(root/'data/input').mkdir(parents=True)
for name in ['sample_orders.csv','sample_regions.csv','sample_points.geojson']:
    (root/'data/input'/name).write_bytes((repo/'data/input'/name).read_bytes())
(root/'data/output').mkdir()
plan=json.loads((repo/'examples/checkpoint24/regional_csv_plan.json').read_text())
class FixtureModel:
    def complete(self,request):
        return ModelResult(model='temporary deterministic browser fixture',content=json.dumps({'message':'Review regional totals; no operation has run.', 'plan':plan}))
conversation.SharedModelClient=lambda settings:FixtureModel()
os.chdir(root)
http=ThreadingHTTPServer(('127.0.0.1',0),server._handler(root))
print(json.dumps({'port':http.server_port,'root':str(root)}),flush=True)
http.serve_forever()
