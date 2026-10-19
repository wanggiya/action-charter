import type { ReusableRecipe, SuccessfulMethod } from "./workflow-tools";

export function recipeKeywords(recipe:ReusableRecipe):string[]{
  const skills=recipe.steps.map(step=>step.skill),words=new Set<string>();
  for(const skill of skills){
    if(skill.includes('csv')||skill.startsWith('ext_'))words.add('csv');
    if(skill.startsWith('inspect_'))words.add('inspection');
    if(skill.includes('vector')){words.add('vector');words.add('geospatial');}
    if(skill.includes('raster')){words.add('raster');words.add('geospatial');}
    if(skill.includes('postgis'))words.add('postgis');
    if(['select_csv_columns','filter_csv_rows','handle_csv_missing'].includes(skill))words.add('cleaning');
    if(skill==='aggregate_csv')words.add('aggregation');
    if(skill==='calculate_csv_columns')words.add('calculation');
    if(skill==='join_csv')words.add('join');
    if(skill.startsWith('export_'))words.add('export');
  }
  return [...words].sort();
}
export function successfulSummary(record:SuccessfulMethod):string {
  const ids=record.operations.map(operation=>operation.skill_id);
  if(ids.every(id=>id==='inspect_csv'))return 'Inspect CSV structure';
  if(ids.every(id=>id==='inspect_vector'))return 'Inspect vector geometry and CRS';
  if(ids.includes('aggregate_csv'))return 'Group and aggregate rows';
  if(ids.includes('join_csv'))return 'Join datasets';
  if(ids.includes('select_csv_columns')&&ids.includes('handle_csv_missing'))return 'Select columns and handle missing values';
  if(ids.includes('filter_csv_rows'))return 'Filter table rows';
  return record.name.length>100?record.name.slice(0,97)+'…':record.name;
}
