"""Synthetic discovery measurements; not a model or competitor benchmark."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('/tmp/actioncharter-discovery-measurements.json'))
    parser.add_argument('--spatial',action='store_true',help='Measure TIFF metadata/hash workers on 16/64 MiB temporary rasters')
    args=parser.parse_args()
    from geoagent_harness.interface_api.inspection_policy import bounded_read
    report={'scope':'temporary_synthetic_tiff_only' if args.spatial else 'temporary_synthetic_csv_only','model_calls':0,'live_service_calls':0,'cases':[]}
    with TemporaryDirectory(prefix='actioncharter-csv-measure-') as directory:
        root=Path(directory);(root/'data/input').mkdir(parents=True)
        for mib in (16,64):
            if args.spatial:
                import numpy as np
                import rasterio
                from rasterio.transform import from_origin
                from rasterio.windows import Window
                path=root/'data/input/terrain.tif';size=2048 if mib==16 else 4096
                with rasterio.open(path,'w',driver='GTiff',width=size,height=size,count=1,dtype='float32',crs='EPSG:4326',transform=from_origin(1,4,.001,.001)) as target:
                    for row in range(0,size,64):target.write(np.zeros((1,64,size),dtype='float32'),window=Window(0,row,size,64))
                with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
                started=monotonic();events=[]
                source=bounded_read(root,action='spatial_probe',path='data/input/terrain.tif')
                result=bounded_read(root,action='spatial_discover',path=source['path'],source_identity=source['source_identity'],on_metadata=lambda value:events.append({'seconds':round(monotonic()-started,4),'phase':value['discovery']['phase']}))
                assert result['width']==size and result['height']==size
                assert result['source_manifest']=={'data/input/terrain.tif':digest}
                oracle=hashlib.sha256(json.dumps({'data/input/terrain.tif':digest},sort_keys=True).encode()).hexdigest()
                assert result['source_sha256']==oracle and events[0]['phase']=='verifying'
                report['cases'].append({'bytes':path.stat().st_size,'width':size,'height':size,'seconds':round(monotonic()-started,4),
                    'metadata_events':events,'resource_usage':result['resource_usage'],'hash_and_dimensions_match':True})
                continue
            path=root/'data/input/orders.csv'
            row=b'001,'+b'x'*1000+b'\n'
            rows=(mib*1024**2)//len(row)
            with path.open('wb') as output:
                output.write(b'id,note\n')
                for _ in range(rows):output.write(row)
            with path.open('rb') as source:oracle=hashlib.file_digest(source,'sha256').hexdigest()
            started=monotonic();events=[]
            source=bounded_read(root,action='csv_probe',path='data/input/orders.csv')
            result=bounded_read(root,action='csv_discover',path=source['path'],source_identity=source['source_identity'],on_metadata=lambda value:events.append({'seconds':round(monotonic()-started,4),'phase':value['discovery']['phase']}))
            assert result['row_count']==rows and result['source_sha256']==oracle
            assert events and events[0]['phase']=='verifying'
            report['cases'].append({'bytes':path.stat().st_size,'rows':rows,'seconds':round(monotonic()-started,4),'metadata_events':events,
                'resource_usage':result['resource_usage'],'hash_and_count_match':True})
    report['status']='passed'
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
