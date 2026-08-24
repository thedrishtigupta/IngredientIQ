import csv, hashlib, json, glob, os
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; RAW=ROOT/'data'/'raw'; OUT=ROOT/'data'/'processed'; OUT.mkdir(parents=True,exist_ok=True)
files=sorted(glob.glob(str(RAW/'reviews_*.csv')))
cols=['author_id','rating','is_recommended','helpfulness','total_feedback_count','total_neg_feedback_count','total_pos_feedback_count','submission_time','review_text','review_title','skin_tone','eye_color','skin_type','hair_color','product_id','product_name','brand_name','price_usd']
outcols=['review_id']+cols+['has_review_text','has_review_title','source_file']
seen=set(); summary={}; raw=clean=dup=0; counts={}; missing_text=missing_title=missing_rec=0; rating_counts={}; date_min=date_max=None
with open(OUT/'reviews_clean.csv','w',newline='',encoding='utf8') as fo:
 w=csv.DictWriter(fo,fieldnames=outcols); w.writeheader()
 for fp in files:
  name=os.path.basename(fp); counts[name]=0
  for df in pd.read_csv(fp,usecols=cols,chunksize=50000,low_memory=False):
   raw+=len(df); counts[name]+=len(df)
   # clean only fields where normalization is safe and useful
   for c in ['author_id','product_id','product_name','brand_name','review_title','skin_tone','eye_color','skin_type','hair_color']:
    df[c]=df[c].astype('string').str.strip()
   df['review_text']=df['review_text'].astype('string').str.strip()
   df['submission_time']=pd.to_datetime(df['submission_time'],errors='coerce')
   for c in ['rating','is_recommended','helpfulness','total_feedback_count','total_neg_feedback_count','total_pos_feedback_count','price_usd']:
    df[c]=pd.to_numeric(df[c],errors='coerce')
   for row in df.itertuples(index=False,name=None):
    d=dict(zip(cols,row)); pid='' if pd.isna(d['product_id']) else str(d['product_id']); aid='' if pd.isna(d['author_id']) else str(d['author_id'])
    if not pid: continue
    date='' if pd.isna(d['submission_time']) else pd.Timestamp(d['submission_time']).strftime('%Y-%m-%d')
    text='' if pd.isna(d['review_text']) else str(d['review_text']); title='' if pd.isna(d['review_title']) else str(d['review_title'])
    rating='' if pd.isna(d['rating']) else str(int(d['rating']))
    ident='|'.join((aid,pid,date,text or title,rating)); h=hashlib.sha256(ident.encode()).hexdigest()
    if h in seen: dup+=1; continue
    seen.add(h); clean+=1
    has_text=bool(text); has_title=bool(title)
    missing_text += not has_text; missing_title += not has_title; missing_rec += pd.isna(d['is_recommended'])
    if not pd.isna(d['rating']): rating_counts[int(d['rating'])]=rating_counts.get(int(d['rating']),0)+1
    if date:
     date_min=date if date_min is None or date<date_min else date; date_max=date if date_max is None or date>date_max else date
    out={'review_id':h,**d,'submission_time':date,'has_review_text':has_text,'has_review_title':has_title,'source_file':name}
    for k,v in list(out.items()):
     if pd.isna(v): out[k]=''
     elif isinstance(v,(pd.Timestamp,)): out[k]=v.strftime('%Y-%m-%d')
    w.writerow(out)
    s=summary.get(pid)
    if s is None: s=summary[pid]=[0,0.0,0,0,0.0,0,0,0,0,date,date]
    s[0]+=1
    if not pd.isna(d['rating']): s[1]+=float(d['rating']); s[2]+=1
    if not pd.isna(d['is_recommended']): s[3]+=1; s[4]+=float(d['is_recommended'])
    if not pd.isna(d['helpfulness']): s[5]+=float(d['helpfulness']); s[6]+=1
    s[7]+=int(has_text); s[8]+=int(has_title)
    if date and (not s[9] or date<s[9]): s[9]=date
    if date and (not s[10] or date>s[10]): s[10]=date

p=pd.read_csv(RAW/'product_info.csv',usecols=['product_id','reviews','rating','loves_count'],low_memory=False); p.product_id=p.product_id.astype('string').str.strip(); cat=set(p.product_id.dropna()); orphans=sorted(set(summary)-cat)
rows=[]
for pid,s in summary.items():
 rows.append([pid,s[0],s[1]/s[2] if s[2] else '',int(s[4]),s[3],s[4]/s[3] if s[3] else '',s[5]/s[6] if s[6] else '',s[6],s[7],s[8],s[9],s[10]])
s=pd.DataFrame(rows,columns=['product_id','review_count','avg_review_rating','recommendation_count','recommendation_denominator','recommendation_rate','avg_helpfulness','helpfulness_count','review_text_count','review_title_count','earliest_review','latest_review'])
s=s.merge(p.rename(columns={'reviews':'catalog_review_count','rating':'catalog_rating','loves_count':'catalog_loves_count'}),on='product_id',how='left'); s['review_count_gap_vs_catalog']=s.review_count-s.catalog_review_count;s.to_csv(OUT/'product_review_summary.csv',index=False)
report={'raw_source_files':counts,'raw_review_rows':raw,'clean_review_rows':clean,'duplicate_rows_removed':dup,'unique_products_in_reviews':len(summary),'products_in_catalog':len(p),'review_products_missing_from_catalog':len(orphans),'orphan_product_ids':orphans[:100],'missing_review_text':missing_text,'missing_review_title':missing_title,'missing_recommendation_flag':missing_rec,'rating_counts':dict(sorted(rating_counts.items())),'review_date_min':date_min,'review_date_max':date_max,'summary_products':len(s),'summary_products_with_recommendation_rate':int(s.recommendation_rate.astype(str).ne('').sum()),'summary_products_with_text':int((s.review_text_count>0).sum())}
(OUT/'review_pipeline_quality_report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))
