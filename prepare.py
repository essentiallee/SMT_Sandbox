"""Prepare the user's real source records. No slider-dependent values are computed here.
Run with python3 prepare.py. Original is a symlink to the user's untouched source folder.
Census geocoder response is cached in work/geocode-response.csv; no runtime network.
"""
from pathlib import Path
import csv, json, hashlib, shutil
import pandas as pd
import geopandas as gpd

ROOT=Path(__file__).resolve().parent
ORIGINAL=ROOT/'data/Original'
OUT=ROOT/'data/Processed'
EXPORT=Path('/Users/jaehyunlee/Desktop/GSAPP/02. 2026_FALL/04. Simulation/02. Data/sandbox_data/Processed')
OUT.mkdir(parents=True,exist_ok=True)
EXPORT.mkdir(parents=True,exist_ok=True)
audit={}
def report(step, count, **extra):
    audit[step]={'rows':int(count),**extra}
    print(step, json.dumps(audit[step]))

# 1. Read original transaction records as strings; retain the source's signed amounts.
source=next(ORIGINAL.glob('Prime*/Assistance_PrimeTransactions*.csv'))
df=pd.read_csv(source,dtype=str).fillna('')
report('1_original_transactions',len(df),sha256=hashlib.sha256(source.read_bytes()).hexdigest())
assert not df.assistance_transaction_unique_key.duplicated().any(), 'Duplicate transaction keys require review.'

# 2. Filter fiscal years, listing 45.024, NYC recipient counties, and named recipient IDs.
counties={'36005','36047','36061','36081','36085'}
reasons=[]
for _,r in df.iterrows():
    why=[]
    if r.action_date_fiscal_year not in ['2022','2023','2024','2025']: why.append('outside fiscal years')
    if r.cfda_number!='45.024': why.append('not listing 45.024')
    if r.prime_award_transaction_recipient_county_fips_code not in counties: why.append('recipient county outside NYC')
    if not r.recipient_uei or r.recipient_name=='MULTIPLE RECIPIENTS': why.append('no named recipient ID')
    reasons.append('; '.join(why))
df['exclusion_reason']=reasons
df[df.exclusion_reason!=''].to_csv(OUT/'excluded_transactions.csv',index=False)
d=df[df.exclusion_reason==''].copy()
d['cents']=d.federal_action_obligation.map(lambda x:int(round(float(x)*100)))
d['fy']=d.action_date_fiscal_year.astype(int)
report('2_eligible_transactions',len(d),excluded=len(df)-len(d),organizations=d.recipient_uei.nunique())
d.to_csv(OUT/'eligible_transactions.csv',index=False)

# 3. Fix each organization's address at its first observed transaction; retain every signed organization-year total.
org=d.sort_values(['action_date','assistance_transaction_unique_key']).drop_duplicates('recipient_uei').copy()
org=org.sort_values('recipient_uei').reset_index(drop=True)
annual=d.groupby(['recipient_uei','fy']).cents.sum().unstack(fill_value=0).reindex(columns=[2022,2023,2024,2025],fill_value=0)
annual.to_csv(OUT/'observed_organization_year_cents.csv')
budgets=[int(d.loc[d.fy==y,'cents'].sum()) for y in range(2022,2026)]
report('3_observed_organizations',len(org),budgets_cents=budgets,negative_organization_years=int((annual<0).sum().sum()))

# 4. Read NYC tract-to-NTA geography and dissolve the actual polygons by NTA code.
tract=gpd.read_file(ORIGINAL/'zoning related/dcp_ct2020_wi.shp/dcp_ct2020_wi.shp')
report('4_source_tracts',len(tract),missing_nta=int(tract.nta2020.isna().sum()))
tract[['geoid','nta2020','ntaname','boroname']].to_csv(OUT/'tract_to_nta.csv',index=False)
projected=tract.to_crs(2263)
nta=projected[['nta2020','ntaname','geometry']].dissolve(by='nta2020',aggfunc='first').sort_index()
report('4_neighborhoods',len(nta))

# 5. Join real Census-geocoded points to original tract polygons in the same projected CRS.
cache=ROOT/'work/geocode-response.csv'
if not cache.exists(): cache=OUT/'census_geocoder_response.csv'
if not cache.exists(): raise FileNotFoundError('Restore the cached Census geocoder response before preparing the data.')
geo={}
for row in csv.reader(cache.open()):
    if len(row)>5 and row[2]=='Match':
        try: geo[row[0]]=[float(x) for x in row[5].split(',')]
        except ValueError: pass
points=[]
for i,r in org.iterrows():
    if r.recipient_uei in geo:
        x,y=geo[r.recipient_uei];points.append({'id':r.recipient_uei,'longitude':x,'latitude':y})
pointdf=pd.DataFrame(points)
pts=gpd.GeoDataFrame(pointdf,geometry=gpd.points_from_xy(pointdf.longitude,pointdf.latitude),crs=4326).to_crs(2263)
joined=gpd.sjoin(pts,projected[['nta2020','geometry']],how='left',predicate='intersects')
# Ambiguous boundaries remain unmapped rather than selecting an arbitrary polygon.
mapping={}
for ident,group in joined.groupby('id'):
    codes=group.nta2020.dropna().unique()
    if len(codes)==1: mapping[ident]=codes[0]
org['nta2020']=org.recipient_uei.map(mapping).fillna('UNMAPPED')
org['geocode_status']=org.recipient_uei.map(lambda v:'matched to NTA' if v in mapping else ('point outside/ambiguous NTA' if v in geo else 'Census address unmatched'))
org[['recipient_uei','recipient_name','recipient_address_line_1','recipient_city_name','recipient_zip_code','nta2020','geocode_status']].to_csv(OUT/'organization_locations.csv',index=False)
unmatched=org[org.nta2020=='UNMAPPED']
unmatched.to_csv(OUT/'unmapped_organizations.csv',index=False)
report('5_locations',len(org),census_matched=len(geo),nta_matched=len(mapping),unmapped=len(unmatched),unmapped_names=unmatched.recipient_name.tolist())
if cache.resolve() != (OUT/'census_geocoder_response.csv').resolve():
    shutil.copyfile(cache,OUT/'census_geocoder_response.csv')

# 6. Keep adopted zoning records with actual effective dates inside federal FY2022–25.
z=gpd.read_file(ORIGINAL/'zoning related/zoning.gdb',layer='nyzma')
report('6_original_amendments',len(z))
mask=(z.STATUS=='Adopted')&(z.EFFECTIVE>='2021-10-01')&(z.EFFECTIVE<'2025-10-01')
zs=z[mask].copy().to_crs(2263)
z.drop(columns='geometry').assign(included=mask).to_csv(OUT/'amendment_filter_audit.csv',index=False)
report('6_fiscal_year_amendments',len(zs),excluded=len(z)-len(zs))
zs.drop(columns='geometry').to_csv(OUT/'adopted_amendments.csv',index=False)

# 7. Simplify display geometry in feet only; spatial joins used the unsimplified boundaries.
xmin,ymin,xmax,ymax=nta.total_bounds
span=max(xmax-xmin,ymax-ymin)
def xy(x,y): return [round((x-xmin)/span*900+50,2),round((ymax-y)/span*900+50,2)]
def svgpath(geom):
    if geom.is_empty:return ''
    if geom.geom_type=='Polygon': polys=[geom]
    elif geom.geom_type=='MultiPolygon':polys=list(geom.geoms)
    else:return ''
    bits=[]
    for poly in polys:
        for ring in [poly.exterior,*poly.interiors]:
            coords=[xy(x,y) for x,y,*_ in ring.coords]
            bits.append('M'+'L'.join(f'{x},{y}' for x,y in coords)+'Z')
    return ''.join(bits)
borough={'BX':'Bronx','BK':'Brooklyn','MN':'Manhattan','QN':'Queens','SI':'Staten Island'}
neighborhoods=[]
for code,r in nta.iterrows():
    pt=r.geometry.representative_point()
    neighborhoods.append({'id':code,'name':r.ntaname,'borough':borough.get(code[:2],''),'path':svgpath(r.geometry.simplify(35,preserve_topology=True)),'label':xy(pt.x,pt.y)})
organizations=[]
for _,r in org.iterrows():
    organizations.append({'id':r.recipient_uei,'name':r.recipient_name,'nta':r.nta2020,'first':int(r.fy),'observed':[int(annual.loc[r.recipient_uei,y]) for y in range(2022,2026)]})
amendments=[]
for _,r in zs.sort_values('EFFECTIVE').iterrows():
    date=r.EFFECTIVE.strftime('%Y-%m-%d')
    amendments.append({'name':str(r.PROJECT_NAME).strip(),'id':str(r.ULURPNO),'date':date,'fy':int(r.EFFECTIVE.year+(r.EFFECTIVE.month>=10)),'path':svgpath(r.geometry.simplify(20,preserve_topology=True))})
data={'years':[2022,2023,2024,2025],'budgets':budgets,'neighborhoods':neighborhoods,'organizations':organizations,'amendments':amendments,'audit':audit,'metadata':{'sourceTransactions':len(df),'eligibleTransactions':len(d),'unmapped':len(unmatched),'geocoder':'US Census Public_AR_Current, downloaded 2026-10-08','geometry':'2020 NTA geography from supplied DCP 26b tract file; display simplification 35 feet','addressPolicy':'First recorded address per UEI; held fixed across years','font':'Space Mono / SIL Open Font License'}}
(OUT/'sandbox.json').write_text(json.dumps(data,separators=(',',':'),ensure_ascii=False))
(OUT/'audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
for f in OUT.iterdir():
    if f.is_file():shutil.copyfile(f,EXPORT/f.name)
report('7_exported_files',len(list(OUT.iterdir())),embedded_json_bytes=(OUT/'sandbox.json').stat().st_size)
print('Real observed amounts and hypothetical allocations remain separate. No missing addresses were guessed.')
