"""Synthetic spatial display measurements, not an LLM or competitor benchmark."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('/tmp/actioncharter-spatial-view-measurements.json'))
    args=parser.parse_args()
    import geopandas as gpd
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin
    from geoagent_harness.interface_api.inspection_policy import bounded_read
    cases=[]
    with TemporaryDirectory(prefix='actioncharter-spatial-measurements-') as directory:
        root=Path(directory);(root/'data/input').mkdir(parents=True)
        for count in (100,1000,10000):
            path=f'data/input/points_{count}.gpkg'
            gpd.GeoDataFrame({'id':range(count)},geometry=gpd.points_from_xy(np.linspace(0,1,count),np.linspace(1,2,count)),crs='EPSG:4326').to_file(root/path,layer='points',driver='GPKG')
            digest=bounded_read(root,action='snapshot',path=path)['source_sha256']
            started=monotonic();value=bounded_read(root,action='spatial_view',path=path,source_sha256=digest,view_options={'mode':'vector'})
            assert value['spatial_preview']['total_features']==count
            cases.append({'kind':'vector','source_features':count,'source_bytes':(root/path).stat().st_size,'display_features':len(value['spatial_preview']['features']),'response_bytes':len(json.dumps(value).encode()),'wall_seconds':round(monotonic()-started,4),**value['resource_usage']})
        for size in (256,1024,2048):
            path=f'data/input/raster_{size}.tif'
            with rasterio.open(root/path,'w',driver='GTiff',width=size,height=size,count=1,dtype='uint8',crs='EPSG:4326',transform=from_origin(0,1,1/size,1/size),compress='deflate') as dataset:
                dataset.write(np.broadcast_to(np.arange(size,dtype='uint8'),(1,size,size)))
            digest=bounded_read(root,action='snapshot',path=path)['source_sha256']
            started=monotonic();value=bounded_read(root,action='spatial_view',path=path,source_sha256=digest,view_options={'mode':'raster','render':'ramp'})
            assert max(value['width'],value['height'])<=256
            cases.append({'kind':'raster','source_width':size,'source_height':size,'source_bytes':(root/path).stat().st_size,'preview_width':value['width'],'preview_height':value['height'],'response_bytes':len(json.dumps(value).encode()),'wall_seconds':round(monotonic()-started,4),**value['resource_usage']})
    report={'status':'passed','cases':cases,'synthetic_only':True,'live_service_calls':0,'model_calls':0,'scope':'Single sequential bounded preview reads; peak RSS is Linux worker process memory, not whole-platform memory. No scalability or model-speed comparison.'}
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
