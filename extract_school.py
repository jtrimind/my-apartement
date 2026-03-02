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
    m = re.search(r'\s([산]?\d+)(?:-(\d+))?', addr)
    if m:
        main_no = m.group(1).replace('산', '')
        sub_no = m.group(2) if m.group(2) else '0'
        return main_no, sub_no
    return None, None

print("Loading apt_basic.csv...")
apt_basic = pd.read_csv('apt_basic.csv', dtype={'bjdCode': str})

print("Loading 초등학교_도보통학권_아파트_정보.csv...")
school_df = pd.read_csv('초등학교_도보통학권_아파트_정보.csv', encoding='utf-8')

# Prepare school data
school_agg = school_df.dropna(subset=['apt_nm', 'schul_nm', 'schul_dstnc', 'pnu']).copy()
school_agg['clean_name'] = school_agg['apt_nm'].apply(clean_text)

# Extract bjdCode, HMNO(본번), VCNO(부번) from 19-digit pnu
# PNU Format: Sido(2) + Sigungu(3) + Eupmyeondong(3) + Ri(2) + LandType(1) + MainNo(4) + SubNo(4)
# bjdCode = Sido(2) + Sigungu(3) + Eupmyeondong(3) + Ri(2) (First 10 digits)
school_agg['pnu_str'] = school_agg['pnu'].astype(str).str.zfill(19)
school_agg['bjdCode'] = school_agg['pnu_str'].str[:10]
school_agg['HMNO'] = school_agg['pnu_str'].str[11:15].astype(int).astype(str) # Remove leading zeros
school_agg['VCNO'] = school_agg['pnu_str'].str[15:19].astype(int).astype(str)

# Min dist by name
idx_min_dist_name = school_agg.groupby(['bjdCode', 'clean_name'])['schul_dstnc'].idxmin()
school_by_name = school_agg.loc[idx_min_dist_name, ['bjdCode', 'clean_name', 'schul_nm', 'schul_dstnc']]

# Min dist by jibun
idx_min_dist_jibun = school_agg.groupby(['bjdCode', 'HMNO', 'VCNO'])['schul_dstnc'].idxmin()
school_by_jibun = school_agg.loc[idx_min_dist_jibun, ['bjdCode', 'HMNO', 'VCNO', 'schul_nm', 'schul_dstnc']]

# Prepare apt_basic
apt_basic['clean_name'] = apt_basic['kaptName'].apply(clean_text)
apt_basic[['HMNO', 'VCNO']] = apt_basic['kaptAddr'].apply(lambda x: pd.Series(extract_jibun(x)))

# Merge twice: first by jibun, then by name for remaining
mapped_jibun = pd.merge(apt_basic, school_by_jibun, on=['bjdCode', 'HMNO', 'VCNO'], how='inner')
mapped_jibun['match_type'] = 'jibun'

remaining_apt = apt_basic[~apt_basic['kaptCode'].isin(mapped_jibun['kaptCode'])]
mapped_name = pd.merge(remaining_apt, school_by_name, on=['bjdCode', 'clean_name'], how='inner')
mapped_name['match_type'] = 'name'

mapped = pd.concat([mapped_jibun, mapped_name], ignore_index=True)

print(f"Total apartments in apt_basic: {len(apt_basic)}")
print(f"Successfully mapped: {len(mapped)} complexes ({len(mapped_jibun)} by jibun, {len(mapped_name)} by name)")

output_cols = ['kaptCode', 'schul_nm', 'schul_dstnc']
final_mapped = mapped[output_cols]

# Drop duplicates
final_mapped = final_mapped.drop_duplicates(subset=['kaptCode'])

output_file_path = 'apt_school_mapped.csv'
final_mapped.to_csv(output_file_path, index=False, encoding='utf-8')
print(f"Saved {output_file_path} (Total records: {len(final_mapped)})")
print(final_mapped.head())
