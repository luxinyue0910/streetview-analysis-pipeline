from settings import WORKSPACE, ARCHIVE_DIR
"""Compare frozen zero-shot predictions with certain and uncertain human selections."""
import base64
import csv
import html
import io
import json
from collections import defaultdict
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = WORKSPACE
OUT = ROOT / 'evaluation30'

def main():
    sample=json.loads((ROOT/'annotation30/sample.json').read_text())
    labels=json.loads((ROOT/'annotation30/labels.json').read_text())
    frozen=json.loads((OUT/'predictions_before_labels.json').read_text())
    assert frozen['sample_id']==sample['sample_id']
    lookup={p['id']:p for p in frozen['predictions']}
    records=[]
    for index,p in enumerate(sample['points']):
        l=labels[p['id']];assert l['status'] in ['confirmed','needs_review'] and len(set(l['selected']))==2
        pred=lookup[p['id']];truth=sorted(l['selected'])
        records.append({**p,'sample_number':index+1,'status':l['status'],'human':truth,'predicted':pred['predicted'],
                        'agree':truth==pred['predicted'],'note':l.get('note',''),'pair_margin':pred['pair_margin'],'scores':pred['scores']})
    def stats(group):
        return {'n':len(group),'agree':sum(p['agree'] for p in group),'disagree':sum(not p['agree'] for p in group),
                'agreement_rate':sum(p['agree'] for p in group)/len(group) if group else None}
    summary={'overall':stats(records),'certain':stats([p for p in records if p['status']=='confirmed']),
             'uncertain':stats([p for p in records if p['status']=='needs_review']),
             'by_level':{str(l):{'overall':stats([p for p in records if p['road_level']==l]),
                               'certain':stats([p for p in records if p['road_level']==l and p['status']=='confirmed']),
                               'uncertain':stats([p for p in records if p['road_level']==l and p['status']=='needs_review'])} for l in [1,2,3,4]},
             'note':'Exact pair agreement, ignoring side_a/b order. Uncertain disagreements are not definitive model errors. Predictions frozen before labeling; no retraining or prompt tuning.'}
    (OUT/'comparison_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    (OUT/'comparison_records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
    with (OUT/'comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['sample_number','point_id','road_level','human_certainty','human_pair','model_pair','agree','pair_margin','note'])
        for p in records:w.writerow([p['sample_number'],p['point_id'],p['road_level'],'certain' if p['status']=='confirmed' else 'uncertain','/'.join(map(str,p['human'])),'/'.join(map(str,p['predicted'])),p['agree'],p['pair_margin'],p['note']])
    sections=[]
    ordered=sorted(records,key=lambda p:(p['agree'],p['status']!='confirmed',p['pair_margin']))
    for p in ordered:
        certain=p['status']=='confirmed';group='确定组' if certain else '勉强组';tag='一致' if p['agree'] else ('模型选错（以确定标注为准）' if certain else '不一致，人工也不确定')
        cards=[]
        for im in p['images']:
            a=im['angle']
            with Image.open(ROOT/'annotation30'/im['url'].lstrip('/')) as img:
                img=img.convert('RGB');img.thumbnail((600,300));buf=io.BytesIO();img.save(buf,format='JPEG',quality=85)
            tags=[]
            if a in p['human']:tags.append('人工保留')
            if a in p['predicted']:tags.append('模型保留')
            cards.append(f'<div><b>{a}° · {" / ".join(tags) or "均不选"}</b><img src="data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}" alt="{a}度街景"></div>')
        sections.append(f'<section data-group="{"certain" if certain else "uncertain"}" data-agree="{str(p["agree"]).lower()}" id="point-{p["sample_number"]}"><h2>#{p["sample_number"]} · {group} · {tag}</h2><p>{p["point_id"]} · {p["road_level"]}级 ｜ 人工 {p["human"]} ｜ 模型 {p["predicted"]} ｜ 分差 {p["pair_margin"]:.4f}</p><div class="cards">{"".join(cards)}</div><p>{html.escape(p["note"])}</p></section>')
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>30点位独立验证对比</title><style>body{font:14px -apple-system,sans-serif;background:#f5f6f2;color:#24352f;margin:26px}h1{font-size:24px}h2{font-size:17px}.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.cards img{width:100%;display:block;margin-top:8px}section{background:white;padding:18px;margin:20px 0;border-left:5px solid #6b9077;border-radius:9px}section[data-agree=false]{border-color:#b66348}section[data-group=uncertain]{border-color:#bd9f55}button{padding:10px 14px;cursor:pointer;margin:5px}table{border-collapse:collapse;background:white}th,td{text-align:left;padding:12px 22px;border-bottom:1px solid #ddd}@media(max-width:700px){.cards{grid-template-columns:repeat(2,1fr)}}</style><h1>30个新点位：固定模型独立验证</h1><table><tr><th>组别</th><th>一致 / 总数</th><th>一致率</th><th>不一致</th></tr><tr><td>确定组</td><td>24 / 25</td><td>96.0%</td><td>1</td></tr><tr><td>勉强组</td><td>2 / 5</td><td>40.0%</td><td>3</td></tr><tr><td>全部</td><td>26 / 30</td><td>86.7%</td><td>4</td></tr></table><p>确定组以人工标注作为参考答案。勉强组的不一致不直接算模型错误。使用此前84个确定点位训练的新分类器；本批30个点位未参与训练，预测在人工标注前已保存，未改模型或规则。两张均匹配才计一致，不区分 side_a/b 顺序。</p><button onclick="filter('certain',false)">确定组的1个错误</button><button onclick="filter('uncertain',false)">勉强组的3个不一致</button><button onclick="filter(null,false)">全部4个不一致</button><button onclick="filter(null,null)">显示全部30组</button><script>function filter(group,agree){document.querySelectorAll('section').forEach(s=>s.hidden=(group!==null&&s.dataset.group!==group)||(agree!==null&&s.dataset.agree!==String(agree)))}</script>'''+''.join(sections)+'</html>'
    # Render counts from computed labels, never from historical hard-coded text.
    import re
    table_rows = []
    for title, key in [('确定组', 'certain'), ('勉强组', 'uncertain'), ('全部', 'overall')]:
        value = summary[key]
        rate = 'n.a.' if value['agreement_rate'] is None else f"{value['agreement_rate']:.1%}"
        table_rows.append(f"<tr><td>{title}</td><td>{value['agree']} / {value['n']}</td><td>{rate}</td><td>{value['disagree']}</td></tr>")
    table = '<table><tr><th>组别</th><th>一致 / 总数</th><th>一致率</th><th>不一致</th></tr>' + ''.join(table_rows) + '</table>'
    page = re.sub(r'<table>.*?</table>', lambda _: table, page, count=1, flags=re.S)
    page = re.sub(r'确定组的\d+个错误', f"确定组的{summary['certain']['disagree']}个错误", page)
    page = re.sub(r'勉强组的\d+个不一致', f"勉强组的{summary['uncertain']['disagree']}个不一致", page)
    page = re.sub(r'全部\d+个不一致', f"全部{summary['overall']['disagree']}个不一致", page)
    (OUT/'review.html').write_text(page)
    (ROOT/'evaluation/validation30_review.html').write_text(page)
    for status,name in [('confirmed','certain_errors'),('needs_review','uncertain_disagreements')]:
        group=[p for p in records if p['status']==status and not p['agree']]
        canvas=Image.new('RGB',(1440,245*len(group)),'white');d=ImageDraw.Draw(canvas)
        for row,p in enumerate(group):
            d.text((8,row*245+4),f"#{p['sample_number']} {p['point_id']} level {p['road_level']} HUMAN {p['human']} MODEL {p['predicted']} margin {p['pair_margin']:.4f}",fill='black')
            for col,im in enumerate(p['images']):
                a=im['angle'];img=Image.open(ROOT/'annotation30'/im['url'].lstrip('/')).convert('RGB');img.thumbnail((350,190));canvas.paste(img,(360*col,row*245+42))
                d.text((360*col+5,row*245+23),f"{a}deg human={'YES' if a in p['human'] else '-'} model={'YES' if a in p['predicted'] else '-'}",fill='black')
        canvas.save(OUT/(name+'.jpg'),quality=95)
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
