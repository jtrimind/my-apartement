import pandas as pd
import numpy as np
import re
import os

def clean_text(x):
    if pd.isna(x): return ""
    s = str(x).replace(" ", "")
    s = re.sub(r'아파트$', '', s)
    s = re.sub(r'\(.*\)', '', s) # Remove anything in parentheses
    return s

def extract_jibun(addr):
    if pd.isna(addr): return None, None
    # match patterns like ' 73-1 ' or ' 73 ' or ' 산1-2 '
    # just extract the first number pattern we find after a space
    m = re.search(r'\s([산]?\d+)(?:-(\d+))?', addr)
    if m:
        main_no = m.group(1).replace('산', '')
        sub_no = m.group(2) if m.group(2) else '0'
        return main_no, sub_no
    return None, None

print("Loading apt_basic.csv...")
apt_basic = pd.read_csv('apt_basic.csv', dtype={'bjdCode': str})

print("Loading 역세권_공동주택_실거래정보.csv...")
try:
    subway_df = pd.read_csv('역세권_공동주택_실거래정보.csv', encoding='utf-8', dtype={'SIGUNGU_CD': str, 'EMDL_CD': str})
except UnicodeDecodeError:
    subway_df = pd.read_csv('역세권_공동주택_실거래정보.csv', encoding='cp949', dtype={'SIGUNGU_CD': str, 'EMDL_CD': str})

subway_df['SIGUNGU_CD'] = subway_df['SIGUNGU_CD'].str.zfill(5)
subway_df['EMDL_CD'] = subway_df['EMDL_CD'].str.zfill(5)
subway_df['bjdCode'] = subway_df['SIGUNGU_CD'] + subway_df['EMDL_CD']

# Prepare subway data
subway_agg = subway_df.dropna(subset=['HSMP_NM', 'NRB_SWST_NM', 'NRB_SWST_DIST']).copy()
subway_agg['clean_name'] = subway_agg['HSMP_NM'].apply(clean_text)
# Jibun mapping
subway_agg['HMNO'] = subway_agg['HMNO'].astype(str).str.replace(r'\.0$', '', regex=True)
subway_agg['VCNO'] = subway_agg['VCNO'].astype(str).str.replace(r'\.0$', '', regex=True)

# Min dist by name
idx_min_dist_name = subway_agg.groupby(['bjdCode', 'clean_name'])['NRB_SWST_DIST'].idxmin()
subway_by_name = subway_agg.loc[idx_min_dist_name, ['bjdCode', 'clean_name', 'NRB_SWST_NM', 'NRB_SWST_DIST']]

# Min dist by jibun
idx_min_dist_jibun = subway_agg.groupby(['bjdCode', 'HMNO', 'VCNO'])['NRB_SWST_DIST'].idxmin()
subway_by_jibun = subway_agg.loc[idx_min_dist_jibun, ['bjdCode', 'HMNO', 'VCNO', 'NRB_SWST_NM', 'NRB_SWST_DIST']]

# Prepare apt_basic
apt_basic['clean_name'] = apt_basic['kaptName'].apply(clean_text)
apt_basic[['HMNO', 'VCNO']] = apt_basic['kaptAddr'].apply(lambda x: pd.Series(extract_jibun(x)))

# Merge twice: first by jibun, then by name for remaining
mapped_jibun = pd.merge(apt_basic, subway_by_jibun, on=['bjdCode', 'HMNO', 'VCNO'], how='inner')
mapped_jibun['match_type'] = 'jibun'

remaining_apt = apt_basic[~apt_basic['kaptCode'].isin(mapped_jibun['kaptCode'])]
mapped_name = pd.merge(remaining_apt, subway_by_name, on=['bjdCode', 'clean_name'], how='inner')
mapped_name['match_type'] = 'name'

mapped = pd.concat([mapped_jibun, mapped_name], ignore_index=True)

print(f"Total apartments in apt_basic: {len(apt_basic)}")
print(f"Successfully mapped: {len(mapped)} complexes ({len(mapped_jibun)} by jibun, {len(mapped_name)} by name)")

output_cols = ['kaptCode', 'NRB_SWST_NM', 'NRB_SWST_DIST']
final_mapped = mapped[output_cols].rename(columns={
    'NRB_SWST_NM': 'subwayStation',
    'NRB_SWST_DIST': 'subwayDist'
})

# Some duplicate kaptCodes might exist due to bugs in source data, so drop duplicates
final_mapped = final_mapped.drop_duplicates(subset=['kaptCode'])

# Check for existing override file to append cumulatively
override_file_path = 'apt_subway_override.csv'
if os.path.exists(override_file_path):
    print(f"Found existing {override_file_path}. Loading to keep previous data...")
    try:
        existing_override = pd.read_csv(override_file_path)
        # Identify new records that are not in the existing file
        new_records = final_mapped[~final_mapped['kaptCode'].isin(existing_override['kaptCode'])]
        
        if len(new_records) > 0:
            print(f"Adding {len(new_records)} new complexes to the existing dataset.")
            final_mapped = pd.concat([existing_override, new_records], ignore_index=True)
        else:
            print("No new complexes found to add. Dataset is up to date.")
            final_mapped = existing_override
    except Exception as e:
        print(f"Error reading existing file: {e}. Overwriting instead.")

final_mapped.to_csv(override_file_path, index=False, encoding='utf-8')
print(f"Saved {override_file_path} (Total records: {len(final_mapped)})")
print(final_mapped.head())
