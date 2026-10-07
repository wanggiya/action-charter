"""Drag coordinate and DOM-preview lifecycle checks exercise the real frontend helpers."""
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_graph_drag_preview_coordinates_wires_and_cancel_restore():
    if not shutil.which('node') or not (ROOT / 'interface/node_modules/vite').exists():
        pytest.skip('Installed frontend dependencies required for drag integration')
    script = r'''
import {transformWithEsbuild} from 'vite';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const raw = await readFile('src/lib/graph-drag-preview.ts','utf8');
const {code} = await transformWithEsbuild(raw,'drag.ts',{loader:'ts',target:'es2022'});
const drag = await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
const origin={x:100,y:200};
assert.deepEqual(drag.canonicalDragPosition(origin,{x:20,y:40},.5,true),{x:140,y:280});
const vertical = drag.canonicalDragPosition(origin,{x:25,y:72},1,false);
assert.deepEqual(vertical,{x:200,y:220});
assert.deepEqual(drag.displayDragPosition(origin,{x:120,y:35},vertical,false),{x:145,y:107});
assert.deepEqual(drag.canonicalDragPosition(origin,{x:-9999,y:9999},1,true),{x:0,y:4000});
const horizontal = drag.bezierGeometry({x:10,y:20},{x:110,y:60},true);
assert.equal(horizontal.path,'M 10 20 C 60 20, 60 60, 110 60');
assert.equal(horizontal.labelX,60);
assert.equal(drag.bezierGeometry({x:10,y:20},{x:110,y:60},false).path,'M 10 20 C 10 40, 110 40, 110 60');
const attributes = (initial) => ({values:{...initial},getAttribute(key){return this.values[key]??null},setAttribute(key,value){this.values[key]=value}});
const path=attributes({d:'original path'}),label=attributes({x:'1',y:'2'});
const classes=new Set();
const node={style:{transform:''},classList:{add(name){classes.add(name)},remove(name){classes.delete(name)}}};
const preview=drag.createNodeDragPreview(node,origin,[{path,label,geometry:(point)=>drag.bezierGeometry(point,{x:300,y:400},true)}]);
assert(classes.has('is-dragging'));
preview.move({x:130,y:240});
assert.equal(node.style.transform,'translate3d(30px, 40px, 0)');
assert(path.values.d.startsWith('M 130 240'));
assert.equal(label.values.x,'215');
// Preview mutates presentation only, leaving canonical positions unchanged.
assert.deepEqual(origin,{x:100,y:200});
preview.finish(true);
assert.equal(node.style.transform,'');
assert.equal(path.values.d,'original path');
assert.equal(label.values.x,'1');
assert.equal(label.values.y,'2');
assert(!classes.has('is-dragging'));
console.log('Drag preview invariants passed');
'''
    result = subprocess.run(['node','--input-type=module','-e',script],cwd=ROOT/'interface',capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    assert 'invariants passed' in result.stdout
