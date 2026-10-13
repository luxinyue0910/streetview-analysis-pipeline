from settings import WORKSPACE, ARCHIVE_DIR
"""Predict fresh points without reading their human labels or changing the baseline."""
import json
import time
import hashlib
from pathlib import Path
import torch
from PIL import Image, ImageOps
from transformers import CLIPModel, CLIPProcessor
from evaluate_clip import MODEL, SIDE, ALONG

ROOT=WORKSPACE
DATA=ROOT/'annotation100'
OUT=ROOT/'evaluation100'

def main():
    OUT.mkdir(exist_ok=True)
    sample=json.loads((DATA/'sample.json').read_text())
    device='mps' if torch.backends.mps.is_available() else 'cpu'
    torch.set_num_threads(4)
    # The original run cached converted safetensors in a separate revision.
    # Combine cached assets locally so HF does not query conversion metadata.
    cached=Path.home()/'.cache/huggingface/hub/models--openai--clip-vit-base-patch32/snapshots'
    local=ROOT/'models/clip-vit-base-patch32';local.mkdir(parents=True,exist_ok=True)
    for snapshot in sorted(cached.iterdir()):
        for asset in snapshot.iterdir():
            dest=local/asset.name
            if not dest.exists():dest.symlink_to(asset.resolve())
    model=CLIPModel.from_pretrained(local,use_safetensors=True,local_files_only=True).to(device).eval()
    processor=CLIPProcessor.from_pretrained(local,local_files_only=True,use_fast=False)
    text_inputs=processor(text=SIDE+ALONG,return_tensors='pt',padding=True).to(device)
    records=[(p,im) for p in sample['points'] for im in p['images']];scores=[]
    start=time.perf_counter()
    with torch.inference_mode():
        text=model.get_text_features(**text_inputs);text=text/text.norm(dim=-1,keepdim=True)
        for b in range(0,len(records),16):
            imgs=[]
            for p,im in records[b:b+16]:
                with Image.open(DATA/im['url'].lstrip('/')) as image:
                    imgs.append(ImageOps.pad(image.convert('RGB'),(224,224),method=Image.Resampling.LANCZOS,color=(127,127,127)))
            feat=model.get_image_features(**processor(images=imgs,return_tensors='pt').to(device));feat=feat/feat.norm(dim=-1,keepdim=True)
            sim=feat@text.T;scores.extend((sim[:,:len(SIDE)].mean(1)-sim[:,len(SIDE):].mean(1)).cpu().tolist())
            print(f'Predicted {min(b+16,len(records))}/400 images',flush=True)
    elapsed=time.perf_counter()-start
    predictions=[]
    for n,p in enumerate(sample['points']):
        values={im['angle']:scores[4*n+i] for i,im in enumerate(p['images'])}
        delta=values[0]+values[180]-values[90]-values[270]
        predictions.append({'id':p['id'],'point_id':p['point_id'],'road_level':p['road_level'],'predicted':[0,180] if delta>=0 else [90,270],'scores':values,'pair_margin':abs(delta)})
    payload={'sample_id':sample['sample_id'],'model':MODEL,'method_sha256':hashlib.sha256((ROOT/'evaluation/method.json').read_bytes()).hexdigest(),'device':device,'seconds':elapsed,'predictions':predictions}
    (OUT/'predictions_before_labels.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
    print(f'Saved 100 predictions independently of labels in {elapsed:.2f}s on {device}.',flush=True)

if __name__=='__main__':main()
