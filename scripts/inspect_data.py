"""Index archive members and match a center-point XLS without unpacking full archives."""
import argparse
import csv
import json
import re
import zipfile
from collections import Counter, defaultdict
from decimal import Decimal
import xlrd
from settings import WORKSPACE, ARCHIVE_DIR

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--centers',required=True,help='Private XLS containing point_id_, road_level, longitude_, latitude_')
    args=parser.parse_args()
    sheet=xlrd.open_workbook(args.centers).sheet_by_index(0)
    headers=sheet.row_values(0)
    col={name:headers.index(name) for name in ['point_id_','road_level','longitude_','latitude_']}
    def coord(x,y):return Decimal(str(x)).normalize(),Decimal(str(y)).normalize()
    centers={}
    for i in range(1,sheet.nrows):
        pid=str(sheet.cell_value(i,col['point_id_']));key=coord(*pid.split('_'))
        numeric=coord(sheet.cell_value(i,col['longitude_']),sheet.cell_value(i,col['latitude_']))
        if key!=numeric:raise ValueError(f'Coordinate mismatch in center row {i+1}')
        level=int(sheet.cell_value(i,col['road_level']))
        if key in centers:raise ValueError(f'Duplicate coordinate in center row {i+1}')
        centers[key]=level
    inventory={};manifest=[];matched=set();summaries=[]
    for archive in sorted(ARCHIVE_DIR.glob('*.zip')):
        level=next((v for k,v in {'一级':1,'二级':2,'三级':3,'四级':4}.items() if k in archive.name),None)
        if level is None:continue
        groups=defaultdict(list)
        with zipfile.ZipFile(archive) as z:
            for member in z.infolist():
                if member.is_dir() or member.filename.startswith('__MACOSX/'):continue
                filename=member.filename.rsplit('/',1)[-1]
                if not filename.lower().endswith(('.png','.jpg','.jpeg')):continue
                m=re.fullmatch(r'([\d.]+)_([\d.]+)_(0|90|180|270)_([\d.-]+)\.(?:png|jpg|jpeg)',filename,re.I)
                if not m:raise ValueError('Unrecognized image filename')
                x,y,a,pitch=m.groups();groups[x+'_'+y].append({'angle':int(a),'filename':filename,'bytes':member.file_size})
        keep=0;images=0;kept_images=0
        for pid,files in groups.items():
            if sorted(f['angle'] for f in files)!=[0,90,180,270]:raise ValueError('Incomplete or duplicate directional group')
            key=coord(*pid.split('_'));retain=key in centers
            if retain:
                if centers[key]!=level:raise ValueError('Road level mismatch')
                matched.add(key);keep+=1;kept_images+=len(files)
            images+=len(files);manifest.append([archive.name,pid,level,'keep' if retain else 'exclude',len(files)])
        inventory[archive.name]={'points':dict(groups),'bad_names':[]}
        summaries.append({'archive':archive.name,'points':len(groups),'keep_points':keep,'images':images,'keep_images':kept_images})
    out=WORKSPACE/'inspection';out.mkdir(parents=True,exist_ok=True)
    (out/'all_archives_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False))
    with (out/'center_point_filter_manifest.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['archive','point_id','road_level','decision','image_count']);w.writerows(manifest)
    report={'center_points':len(centers),'matched_centers':len(matched),'missing_centers':len(set(centers)-matched),'archives':summaries}
    (out/'center_match_summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
