import {z} from 'zod';
import {runs} from './workflow-tools';
export type SpatialOptions={mode:'vector'|'raster'|'pixel';layer?:string;bands?:number[];render?:'gray'|'ramp'|'rgb'|'classes';stretch?:'minmax'|'percentile';row?:number;column?:number};
export type SpatialScope={run_id:string;plan_sha256:string;conversation_id:string;step_id:string};
const common={run_id:z.string(),plan_sha256:z.string(),conversation_id:z.string(),step_id:z.string(),source:z.string(),source_sha256:z.string(),verified_at_read:z.literal(true),execution_performed:z.literal(false),approval_performed:z.literal(false)};
const raster={source_width:z.number().int().positive(),source_height:z.number().int().positive(),band_count:z.number().int().max(16),crs:z.string().nullable(),bounds:z.array(z.number().finite()).length(4),transform:z.array(z.number().finite()).length(6),bands:z.array(z.number().int()).max(3)};
const schema=z.discriminatedUnion('kind',[
 z.object({...common,kind:z.literal('vector'),layers:z.array(z.string()).max(8),layer:z.string(),source_crs:z.string().nullable(),display_crs:z.string().nullable(),reprojected:z.boolean(),spatial_preview:z.record(z.unknown()),scope:z.literal('bounded_geometry_sample')}),
 z.object({...common,...raster,kind:z.literal('raster'),width:z.number().int().min(1).max(256),height:z.number().int().min(1).max(256),image:z.string().max(480000).regex(/^data:image\/png;base64,[A-Za-z0-9+/=]+$/),render:z.enum(['gray','ramp','rgb','classes']),stretch:z.enum(['minmax','percentile']),ranges:z.array(z.object({band:z.number(),minimum:z.number().finite().nullable(),maximum:z.number().finite().nullable()})).max(3),legend:z.array(z.object({value:z.number().finite(),color:z.string().regex(/^#[0-9a-f]{6}$/)})).max(32),valid_preview_pixels:z.number(),nodata_preview_pixels:z.number(),scope:z.literal('nearest_resampled_preview'),statistics_scope:z.literal('preview_pixels_only')}),
 z.object({...common,...raster,kind:z.literal('pixel'),row:z.number().int(),column:z.number().int(),x:z.number().finite(),y:z.number().finite(),values:z.array(z.number().finite().nullable()).max(3),scope:z.literal('exact_source_pixel')})
]);
export type SpatialResult=z.infer<typeof schema>;
export async function loadSpatial(scope:SpatialScope,spatial:SpatialOptions):Promise<SpatialResult>{
 const value=schema.parse(await runs({action:'spatial_view',run_id:scope.run_id,confirmed_plan_sha256:scope.plan_sha256,conversation_id:scope.conversation_id,step_id:scope.step_id,spatial}));
 if(Object.entries(scope).some(([key,expected])=>value[key as keyof typeof scope]!==expected))throw new Error('Spatial response does not match this recorded result.');
 if(value.kind!==spatial.mode)throw new Error('Spatial view response type mismatch.');
 return value;
}
