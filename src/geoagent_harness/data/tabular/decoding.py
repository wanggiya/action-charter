"""Sectioned codebook decoding preserves source columns and encounter grain."""
import pandas as pd
from geoagent_harness.contracts.paths import TabularError

def decode(frame,args,book):
    if len(args.columns)!=len(set(args.columns)):raise TabularError('Decode fields must be unique')
    output=frame.copy();coverage={}
    for name in args.columns:
        if name not in frame or name not in book['sections']:raise TabularError('Decode field must exist in both source and supplied codebook')
        target=name+'_label'
        if target in frame.columns:raise TabularError('Decoded label column already exists')
        mapping=book['sections'][name]
        found=frame[name].isin(mapping)
        unmatched=int((~found).sum())
        if unmatched and args.unknown_policy=='error':raise TabularError('Codebook has unmatched source codes; review coverage or explicitly preserve unknown codes')
        output[target]=frame[name].map(mapping).astype('string')
        coverage[name]={'label_column':target,'matched_rows':int(found.sum()),'unmatched_rows':unmatched,'source_codes_preserved':True}
    return output,coverage

def verify(original,output,args,book):
    """Reconcile each serialized label against its supplied mapping and all original values."""
    if len(original)!=len(output) or list(output.columns)!=[*original.columns,*[c+'_label' for c in args.columns]]:return False
    for name in original.columns:
        if not original[name].fillna('').equals(output[name].fillna('')):return False
    for name in args.columns:
        mapping=book['sections'].get(name,{})
        for value,label in zip(original[name],output[name+'_label']):
            expected=None if pd.isna(value) else mapping.get(str(value))
            if expected is None:
                if not pd.isna(label) or args.unknown_policy=='error':return False
            elif pd.isna(label) or str(label)!=expected:return False
    return True
