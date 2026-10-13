from settings import WORKSPACE, ARCHIVE_DIR
"""Apply the frozen all84 classifier to the untouched 30-point final test."""
import hashlib,json,time
from pathlib import Path
import numpy as np
import torch
from PIL import Image,ImageOps
from transformers import CLIPModel,CLIPProcessor
ROOT=WORKSPACE
DATA=ROOT/'annotation30'
OUT=ROOT/'evaluation30'

def main():
    OUT.mkdir(exist_ok=True)
    target=OUT/'predictions_before_labels.json'
    if target.exists():raise SystemExit('Frozen predictions already exist; refusing to replace them.')
    sample=json.loads((DATA/'sample.json').read_text());weights=ROOT/'classifier_trial/classifier_all84.npz'
    model_hash=hashlib.sha256(weights.read_bytes()).hexdigest();classifier=np.load(weights)
    assert classifier['classes'].tolist()==[0,1]
    device='mps' if torch.backends.mps.is_available() else 'cpu';torch.set_num_threads(4)
    local=ROOT/'models/clip-vit-base-patch32'
    encoder=CLIPModel.from_pretrained(local,use_safetensors=True,local_files_only=True).to(device).eval()
    processor=CLIPProcessor.from_pretrained(local,local_files_only=True,use_fast=False)
    paths=[DATA/im['url'].lstrip('/') for p in sample['points'] for im in p['images']];batches=[];start=time.perf_counter()
    with torch.inference_mode():
        for b in range(0,len(paths),16):
            images=[]
            for path in paths[b:b+16]:
                with Image.open(path) as im:images.append(ImageOps.pad(im.convert('RGB'),(224,224),method=Image.Resampling.LANCZOS,color=(127,127,127)))
            f=encoder.get_image_features(**processor(images=images,return_tensors='pt').to(device));f=f/f.norm(dim=-1,keepdim=True);batches.append(f.cpu().numpy())
            print('Predicted features',min(b+16,len(paths)),'/120',flush=True)
    features=np.concatenate(batches);scores=(features@classifier['coef'].T+classifier['intercept']).reshape(30,4);predictions=[]
    for n,p in enumerate(sample['points']):
        values={im['angle']:float(scores[n,i]) for i,im in enumerate(p['images'])};delta=values[0]+values[180]-values[90]-values[270]
        predictions.append({'id':p['id'],'point_id':p['point_id'],'road_level':p['road_level'],'predicted':[0,180] if delta>=0 else [90,270],'scores':values,'pair_margin':abs(delta)})
    payload={'sample_id':sample['sample_id'],'classifier_sha256':model_hash,'classifier_file':str(weights),'training_points':84,'device':device,'predictions':predictions,'seconds':time.perf_counter()-start,'labels_read':False}
    target.write_text(json.dumps(payload,ensure_ascii=False,indent=2));np.save(OUT/'image_features.npy',features)
    print('Saved 30 frozen predictions from unchanged all84 classifier; no labels read.',flush=True)

if __name__=='__main__':main()
