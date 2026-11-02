"""Independent CSV/Decimal reference for supplied diabetes files; no platform adapters."""
from collections import Counter
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import statistics

FIELDS=['encounter_id','patient_nbr','age','gender','race','time_in_hospital','readmitted','admission_type_id','discharge_disposition_id','admission_source_id','weight','payer_code','medical_specialty']
CODES=['admission_type_id','discharge_disposition_id','admission_source_id']

def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk:=stream.read(1024*1024):digest.update(chunk)
    return digest.hexdigest()

def read_book(path):
    sections={};current=None
    with Path(path).open(newline='',encoding='utf-8-sig') as stream:
        for row in csv.reader(stream):
            if not row or not any(v.strip() for v in row):current=None;continue
            if len(row)!=2:raise ValueError('Reference expects two-column codebook sections')
            key,value=[v.strip() for v in row]
            if current is None:
                if value.lower()!='description' or key in sections:raise ValueError('Invalid codebook section')
                current=key;sections[current]={}
            else:
                if key in sections[current] or not key or not value:raise ValueError('Invalid/duplicate mapping code')
                sections[current][key]=value
    return sections

def summarize(path,book):
    encounters=Counter();patients=Counter();rows=Counter();missing=Counter();empty=Counter();groups=Counter();age_gender=Counter();admissions=Counter();readmitted=Counter();gender=Counter();time=[];coverage={k:Counter() for k in CODES}
    with Path(path).open(newline='',encoding='utf-8-sig') as stream:
        reader=csv.DictReader(stream);columns=reader.fieldnames
        if not columns or set(FIELDS)-set(columns):raise ValueError('Dataset is missing expected diabetes fields')
        for row in reader:
            if None in row or any(v is None for v in row.values()):raise ValueError('Ragged source')
            encounters[row['encounter_id']]+=1;patients[row['patient_nbr']]+=1
            rows[hashlib.sha256(json.dumps([row[c] for c in columns],separators=(',',':')).encode()).hexdigest()]+=1
            groups[row['age'],row['readmitted']]+=1;age_gender[row['age'],row['gender']]+=1;admissions[row['admission_source_id'],row['readmitted']]+=1
            readmitted[row['readmitted']]+=1;gender[row['gender']]+=1;time.append(Decimal(row['time_in_hospital']))
            for key,value in row.items():
                if value=='?':missing[key]+=1
                if value=='':empty[key]+=1
            for key in CODES:coverage[key]['matched_rows' if row[key] in book[key] else 'unmatched_rows']+=1
    def pairs(counts,keys):return [{**dict(zip(keys,k)),'row_count':n} for k,n in sorted(counts.items())]
    total=sum(encounters.values())
    return {'rows':total,'columns':len(columns),'distinct_encounters':len(encounters),'distinct_patients':len(patients),
        'repeated_patients':sum(v>1 for v in patients.values()),'once_only_patients':sum(v==1 for v in patients.values()),
        'excess_patient_occurrences':sum(v-1 for v in patients.values()),'duplicate_encounters':sum(v-1 for v in encounters.values()),'duplicate_entire_rows':sum(v-1 for v in rows.values()),
        'question_mark_counts':dict(sorted(missing.items())),'empty_counts':dict(sorted(empty.items())),
        'readmitted':dict(sorted(readmitted.items())),'gender':dict(sorted(gender.items())),
        'time_in_hospital':{'count':len(time),'sum':str(sum(time)),'mean':str(sum(time)/len(time)),'minimum':str(min(time)),'maximum':str(max(time)),'median':str(statistics.median(time))},
        'codebook_coverage':{k:{'matched_rows':v['matched_rows'],'unmatched_rows':v['unmatched_rows']} for k,v in coverage.items()},
        'age_readmitted':pairs(groups,['age','readmitted']),'age_gender':pairs(age_gender,['age','gender']),'admission_source_readmitted':pairs(admissions,['admission_source_id','readmitted'])},rows

def reference(csv_path,codebook_path,full_path=None):
    book=read_book(codebook_path);sample,sample_rows=summarize(csv_path,book)
    result={'source':{'filename':Path(csv_path).name,'sha256':sha(csv_path),'bytes':Path(csv_path).stat().st_size},'codebook':{'filename':Path(codebook_path).name,'sha256':sha(codebook_path),'sections':{k:len(v) for k,v in book.items()}},'sample':sample,'authority_granted':False}
    if full_path:
        full,full_rows=summarize(full_path,book)
        with Path(csv_path).open(newline='',encoding='utf-8-sig') as left,Path(full_path).open(newline='',encoding='utf-8-sig') as right:
            a=csv.DictReader(left);b=csv.DictReader(right);prefix=all(next(b,None)==row for row in a)
        result.update(full_source={'filename':Path(full_path).name,'sha256':sha(full_path),'bytes':Path(full_path).stat().st_size,'summary':full},
            sample_provenance={'all_sample_rows_found_with_multiplicity':not bool(sample_rows-full_rows),'is_first_n_rows':prefix,'random_or_representative_sample_proven':False})
    return result

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--csv',type=Path,default=Path('data/input/test/diabetic_sample_5000.csv'));parser.add_argument('--codebook',type=Path,default=Path('data/input/test/IDS_mapping.csv'));parser.add_argument('--full',type=Path,default=Path('data/input/test/diabetic_data.csv'));parser.add_argument('--report',type=Path)
    args=parser.parse_args();value=reference(args.csv,args.codebook,args.full)
    encoded=json.dumps(value,indent=2)
    if args.report:
        with args.report.open('x') as stream:stream.write(encoded+'\n')
    else:print(encoded)
