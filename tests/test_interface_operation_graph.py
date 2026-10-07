"""Exercise real frontend dependency edits, including deletion and cycle guards."""
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_frontend_operation_edits_preserve_dependencies_and_reject_cycles():
    if not shutil.which('node') or not (ROOT / 'interface/node_modules/vite').exists():
        pytest.skip('Installed frontend dependencies required for operation-graph integration')
    code = r'''
import {transformWithEsbuild} from 'vite';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const source = await readFile('src/lib/operation-graph.ts', 'utf8');
const transformed = await transformWithEsbuild(source, 'operation-graph.ts', {loader:'ts', target:'es2022'});
const graph = await import('data:text/javascript;base64,' + Buffer.from(transformed.code).toString('base64'));
const original = {plan:{steps:[{step_id:'step_1'},{step_id:'step_2'},{step_id:'step_3'}]}};
assert.deepEqual(graph.operationDependencies(original.plan.steps), {step_1:[],step_2:['step_1'],step_3:['step_2']});
assert.equal(graph.canConnectOperations(original.plan.steps,'step_2','step_1'),false);
assert.equal(graph.canConnectOperations(original.plan.steps,'step_1','step_2'),false);
assert.equal(graph.canConnectOperations(original.plan.steps,'step_1','step_99'),false);
assert.equal(graph.canConnectOperations(original.plan.steps,'step_1','step_1'),false);
const disconnected = graph.disconnectOperations(original,'step_2','step_3');
assert.deepEqual(disconnected.plan.steps[2].depends_on,[]);
assert.equal(graph.canConnectOperations(disconnected.plan.steps,'step_1','step_3'),true);
const connected = graph.connectOperations(disconnected,'step_1','step_3');
assert.deepEqual(connected.plan.steps[2].depends_on,['step_1']);
assert.throws(() => graph.connectOperations(connected,'step_3','step_1'), /cycle/);
const renamed = graph.deleteOperation(connected,'step_2');
assert.deepEqual(renamed.plan.steps.map(s=>s.step_id),['step_1','step_2']);
assert.deepEqual(renamed.plan.steps[1].depends_on,['step_1']);
const lostParent = graph.deleteOperation(original,'step_2');
assert.deepEqual(lostParent.plan.steps[1].depends_on,[]);
assert.equal(original.plan.steps[2].depends_on,undefined);
assert.throws(() => graph.deleteOperation({plan:{steps:[{step_id:'step_1'}]}},'step_1'), /at least one/);
const four = {plan:{steps:[{step_id:'step_1'},{step_id:'step_2'},{step_id:'step_3'},{step_id:'step_4'}]}};
assert.deepEqual(graph.pinConnections(four.plan.steps,'step_2','in'),[{from:'step_1',to:'step_2'}]);
assert.deepEqual(graph.breakPinConnections(four,'step_2','in').plan.steps[1].depends_on,[]);
assert.deepEqual(graph.breakPinConnections(four,'step_2','out').plan.steps[2].depends_on,[]);
const movedInput = graph.movePinConnections(four,'step_2','step_4','in');
assert.deepEqual(movedInput.plan.steps[1].depends_on,[]);
assert.deepEqual(movedInput.plan.steps[3].depends_on,['step_3','step_1']);
const movedOutput = graph.movePinConnections(four,'step_2','step_1','out');
assert.deepEqual(movedOutput.plan.steps[2].depends_on,['step_1']);
assert.equal(four.plan.steps[2].depends_on,undefined);
const fanout = {plan:{steps:[{step_id:'step_1',depends_on:[]},{step_id:'step_2',depends_on:['step_1']},{step_id:'step_3',depends_on:['step_1']}]}};
const unchanged = JSON.stringify(fanout);
assert.throws(() => graph.movePinConnections(fanout,'step_1','step_3','out'), /cycle/);
assert.equal(JSON.stringify(fanout),unchanged);
console.log('Frontend dependency edit invariants passed');
'''
    completed = subprocess.run(['node', '--input-type=module', '-e', code], cwd=ROOT / 'interface', capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr
    assert 'invariants passed' in completed.stdout
