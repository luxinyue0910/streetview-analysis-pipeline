from settings import WORKSPACE, ARCHIVE_DIR
"""Fixed-prompt zero-shot baseline; no training or prompt tuning on the 50 labels."""
import base64
import csv
import html
import io
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageOps
from transformers import CLIPModel, CLIPProcessor

ROOT = WORKSPACE
OUT = ROOT / 'evaluation'
MODEL = 'openai/clip-vit-base-patch32'
SIDE = [
    'A street view looking sideways across the road at the buildings and sidewalk on one side of the street.',
    'A side-facing street photograph looking directly at roadside trees, vegetation, walls or storefronts.',
    'A view perpendicular to the street, with the roadside facade or vegetation in front of the camera.',
    'A street-level photograph facing the side of a road, with the road crossing horizontally in the foreground.',
]
ALONG = [
    'A street view looking forward or backward along a road that extends into the distance.',
    'A road-facing street photograph with the road ahead and buildings or trees lining both sides.',
    'A view along the street, with road lanes converging toward a vanishing point in the distance.',
    'A street-level photograph facing down a road, with the roadway stretching away from the camera.',
]

def main():
    OUT.mkdir(exist_ok=True)
    sample = json.loads((ROOT / 'annotation/sample.json').read_text())
    labels = json.loads((ROOT / 'annotation/labels.json').read_text())
    assert all(labels[p['id']]['status'] == 'confirmed' for p in sample['points'])
    # Fix text descriptions and preprocessing before computing predictions.
    method = {'model': MODEL, 'side_prompts': SIDE, 'along_prompts': ALONG,
              'preprocess': 'Fit entire RGB image within a 224x224 square using gray letterboxing; no horizontal crop.',
              'selection': 'Mean cosine similarity to side prompts minus mean similarity to along prompts; select opposite pair with highest sum.',
              'training': 'None; labels used only after predictions for evaluation.'}
    (OUT / 'method.json').write_text(json.dumps(method, indent=2))
    print('Loading CLIP weights...', flush=True)
    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    torch.set_num_threads(4)
    model = CLIPModel.from_pretrained(MODEL, use_safetensors=True).to(device).eval()
    processor = CLIPProcessor.from_pretrained(MODEL)
    text_inputs = processor(text=SIDE + ALONG, return_tensors='pt', padding=True).to(device)
    with torch.inference_mode():
        text = model.get_text_features(**text_inputs)
        text = text / text.norm(dim=-1, keepdim=True)
    records = [(p, im) for p in sample['points'] for im in p['images']]
    features, scores = [], []
    start = time.perf_counter()
    with torch.inference_mode():
        for begin in range(0, len(records), 16):
            imgs = []
            for p, im in records[begin:begin+16]:
                with Image.open(ROOT / 'annotation' / im['url'].lstrip('/')) as original:
                    imgs.append(ImageOps.pad(original.convert('RGB'), (224,224), method=Image.Resampling.LANCZOS, color=(127,127,127)))
            inputs = processor(images=imgs, return_tensors='pt').to(device)
            feat = model.get_image_features(**inputs)
            feat = feat / feat.norm(dim=-1, keepdim=True)
            sims = feat @ text.T
            scores.extend((sims[:, :len(SIDE)].mean(dim=1) - sims[:, len(SIDE):].mean(dim=1)).cpu().tolist())
            features.append(feat.cpu().numpy())
            print(f'Processed {min(begin+16,len(records))}/{len(records)} on {device}', flush=True)
    if device == 'mps': torch.mps.synchronize()
    elapsed = time.perf_counter() - start
    np.save(OUT / 'image_features.npy', np.concatenate(features))
    predictions=[]
    for n,p in enumerate(sample['points']):
        values={im['angle']:scores[n*4+i] for i,im in enumerate(p['images'])}
        pair0=values[0]+values[180];pair90=values[90]+values[270]
        predicted=[0,180] if pair0>=pair90 else [90,270]
        top2=sorted(sorted(values,key=values.get,reverse=True)[:2])
        # Human annotation is only accessed after model selection.
        label=labels[p['id']];truth=sorted(label['selected'])
        predictions.append({**p,'truth':truth,'predicted':predicted,'correct':truth==predicted,
                            'top2':top2,'top2_correct':truth==top2,'scores':values,
                            'pair_margin':abs(pair0-pair90),'note':label.get('note','')})
    correct=sum(p['correct'] for p in predictions);n=len(predictions)
    # Wilson interval is descriptive only: balanced road-stratum sample, not population-weighted.
    z=1.96;ph=correct/n;den=1+z*z/n;mid=(ph+z*z/(2*n))/den
    half=z*math.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/den
    summary={'points':n,'pair_correct':correct,'pair_accuracy':correct/n,
             'pair_accuracy_wilson95':[mid-half,mid+half],
             'unconstrained_top2_correct':sum(p['top2_correct'] for p in predictions),
             'per_image_accuracy':sum(len(set(p['truth'])&set(p['predicted'])) for p in predictions)*2/(n*4),
             'by_road_level':{str(level):{'n':len(g),'correct':sum(p['correct'] for p in g)} for level in [1,2,3,4] if (g:=[p for p in predictions if p['road_level']==level])},
             'noted_points':{'n':sum(bool(p['note']) for p in predictions),'errors':sum(bool(p['note']) and not p['correct'] for p in predictions)},
             'default_0_180_correct':sum(p['truth']==[0,180] for p in predictions),
             'device':device,'inference_seconds_including_image_decode':elapsed,
             'images_per_second':200/elapsed,'versions':{'torch':torch.__version__},
             'limitation':'Small road-stratified sample; zero-shot diagnostic baseline, not a validated full-dataset accuracy estimate.'}
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    (OUT/'predictions.json').write_text(json.dumps(predictions,ensure_ascii=False,indent=2))
    with (OUT/'comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['point_id','road_level','human_pair','model_pair','correct','pair_margin','score_0','score_90','score_180','score_270','note'])
        for p in predictions:w.writerow([p['point_id'],p['road_level'],'/'.join(map(str,p['truth'])),'/'.join(map(str,p['predicted'])),p['correct'],p['pair_margin'],*[p['scores'][a] for a in [0,90,180,270]],p['note']])
    build_review(predictions,summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)

def build_review(predictions,summary):
    sections=[]
    for p in sorted(predictions,key=lambda p:(p['correct'],p['pair_margin'])):
        cards=[]
        for im in p['images']:
            with Image.open(ROOT/'annotation'/im['url'].lstrip('/')) as image:
                image=image.convert('RGB');image.thumbnail((600,300));buf=io.BytesIO();image.save(buf,format='JPEG',quality=85)
            src=base64.b64encode(buf.getvalue()).decode()
            a=im['angle'];tags=[]
            if a in p['truth']:tags.append('人工保留')
            if a in p['predicted']:tags.append('模型保留')
            cards.append(f'<div class="card"><div>{a}° · {" / ".join(tags) or "均不选"}</div><img src="data:image/jpeg;base64,{src}" alt="{a}度街景"><small>侧向分数 {p["scores"][a]:.4f}</small></div>')
        mark='正确' if p['correct'] else '选错'
        sections.append(f'<section class="{"correct" if p["correct"] else "wrong"}"><h2>{mark} · {p["point_id"]} · {p["road_level"]}级</h2><p>人工：{p["truth"]} ｜ 模型：{p["predicted"]} ｜ 两对分差：{p["pair_margin"]:.4f} ｜ 备注：{html.escape(p["note"]) or "无"}</p><div class="cards">{"".join(cards)}</div></section>')
    page=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>街景模型与人工标注对比</title><style>body{{font:14px -apple-system,sans-serif;background:#f5f6f2;color:#24352f;margin:28px}}h1{{font-size:24px}}h2{{font-size:17px}}section{{background:white;padding:18px;margin:20px 0;border-radius:10px;border-left:5px solid #679075}}section.wrong{{border-left-color:#b95b47}}.cards{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}}.card img{{width:100%;display:block;margin:8px 0}}small{{color:#64746a}}button{{padding:10px 16px;margin-right:8px;cursor:pointer}}@media(max-width:700px){{.cards{{grid-template-columns:repeat(2,1fr)}}}}</style><h1>CLIP 本地零样本试验</h1><p>整组选对 {summary['pair_correct']} / 50（{summary['pair_accuracy']:.0%}）。先显示选错点位，再显示正确点位；同类按两对分差从小到大排列。分差是模型排序信号，不是正确概率。</p><button onclick="document.querySelectorAll('section.correct').forEach(s=>s.hidden=true)">只看选错</button><button onclick="document.querySelectorAll('section').forEach(s=>s.hidden=false)">显示全部 50 组</button>{''.join(sections)}</html>'''
    (OUT/'review.html').write_text(page)

if __name__=='__main__':main()
