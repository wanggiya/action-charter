export type Coordinate=[number,number];
export type Geometry={type:string;coordinates:unknown};
export type MapFeature={id:number;geometry:Geometry;properties:Record<string,string|null>};
const levels:Record<string,number>={Point:0,MultiPoint:1,LineString:1,MultiLineString:2,Polygon:2,MultiPolygon:3};
export function geometryFeatures(value:unknown):MapFeature[]{
 if(!value||typeof value!=='object')return [];
 const data=value as Record<string,unknown>;
 if(data.status!=='available'||!['EPSG:4326','OGC:CRS84'].includes(String(data.crs)))return [];
 if(data.kind==='wgs84_points'&&Array.isArray(data.points))return data.points.slice(0,32).flatMap((p):MapFeature[]=>Array.isArray(p)&&p.length===3&&p.every(Number.isFinite)&&Math.abs(p[0])<=180&&Math.abs(p[1])<=90?[{id:p[2],geometry:{type:'Point',coordinates:p.slice(0,2)},properties:{}}]:[]);
 if(data.kind!=='wgs84_geometry'||!Array.isArray(data.features)||JSON.stringify(data.features).length>128000)return [];
 let count=0;
 const valid=(v:unknown,depth:number):boolean=>Array.isArray(v)&&v.length>0&&(depth===0?v.length===2&&v.every(Number.isFinite)&&Math.abs(v[0])<=180&&Math.abs(v[1])<=90&&++count<=2048:depth<=3&&v.every(child=>valid(child,depth-1)));
 return data.features.slice(0,32).flatMap((raw):MapFeature[]=>{
  if(!raw||typeof raw!=='object')return [];
  const feature=raw as MapFeature,g=feature.geometry;
  if(!Number.isInteger(feature.id)||!g||!(g.type in levels)||!valid(g.coordinates,levels[g.type]))return [];
  const properties=Object.fromEntries(Object.entries(feature.properties??{}).slice(0,12).map(([key,v])=>[key.slice(0,80),v==null?null:String(v).slice(0,160)]));
  return [{id:feature.id,geometry:g,properties}];
 });
}
export function geometryCoordinates(value:unknown):Coordinate[]{
 if(!Array.isArray(value)||!value.length)return [];
 return typeof value[0]==='number'?[value as Coordinate]:value.flatMap(geometryCoordinates);
}
export function geometryPath(geometry:Geometry,project:(p:Coordinate)=>Coordinate):string {
 const line=(coords:unknown,close=false)=>{const points=(coords as Coordinate[]).map(project);return points.map(([x,y],i)=>`${i?'L':'M'}${x} ${y}`).join(' ')+(close?' Z':'');};
 if(geometry.type==='LineString')return line(geometry.coordinates);
 if(geometry.type==='MultiLineString')return (geometry.coordinates as unknown[]).map(c=>line(c)).join(' ');
 if(geometry.type==='Polygon')return (geometry.coordinates as unknown[]).map(c=>line(c,true)).join(' ');
 if(geometry.type==='MultiPolygon')return (geometry.coordinates as unknown[][]).flatMap(p=>p.map(c=>line(c,true))).join(' ');
 return '';
}
