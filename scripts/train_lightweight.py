from settings import WORKSPACE, ARCHIVE_DIR
"""Frozen CLIP image features + fixed L2 logistic classifier; grouped OOF evaluation."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import numpy as np
import torch
from PIL import Image, ImageOps
from transformers import CLIPModel, CLIPProcessor
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
import sklearn

ROOT=WORKSPACE
DATA=ROOT/'annotation100'
OUT=ROOT/'classifier_trial'

def main():
    OUT.mkdir(exist_ok=True)
    sample=json.loads((DATA/'sample.json').read_text())
    labels=json.loads((DATA/'labels.json').read_text())
    points=[p for p in sample['points'] if labels[p['id']]['status']=='confirmed']
    assert len(points)==84
    baseline={p['id']:p for p in json.loads((ROOT/'evaluation100/predictions_before_labels.json').read_text())['predictions']}
    recipe={'training_points':84,'excluded_uncertain_points':16,'encoder':'openai/clip-vit-base-patch32',
            'classifier':'L2 logistic regression on frozen normalized image embeddings, C=1, no feature scaling',
            'preprocess':'Same 224-square gray letterbox as zero-shot baseline',
            'validation':'5-fold StratifiedGroupKFold on points; exact duplicate image groups joined; seed=20261013',
            'selection':'Sum classifier decision scores per opposite pair; higher pair selected',
            'hyperparameter_search':False,'sklearn_version':sklearn.__version__}
    (OUT/'method.json').write_text(json.dumps(recipe,indent=2))
    # Merge point groups if they share any byte-identical image.
    parent=list(range(len(points)))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    seen={};digests=[]
    for i,p in enumerate(points):
        point_hashes=[]
        for im in p['images']:
            h=hashlib.sha256((DATA/im['url'].lstrip('/')).read_bytes()).hexdigest();point_hashes.append(h)
            if h in seen:parent[find(i)]=find(seen[h])
            seen[h]=i
        digests.append(point_hashes)
    groups=np.array([find(i) for i in range(len(points))])
    y_pair=np.array([int(sorted(labels[p['id']]['selected'])==[0,180]) for p in points])
    if (OUT/'image_features.npy').exists():
        metadata=json.loads((OUT/'feature_points.json').read_text())
        assert metadata==[p['id'] for p in points]
        features=np.load(OUT/'image_features.npy')
    else:
        device='mps' if torch.backends.mps.is_available() else 'cpu';torch.set_num_threads(4)
        local=ROOT/'models/clip-vit-base-patch32'
        encoder=CLIPModel.from_pretrained(local,use_safetensors=True,local_files_only=True).to(device).eval()
        processor=CLIPProcessor.from_pretrained(local,local_files_only=True,use_fast=False)
        paths=[DATA/im['url'].lstrip('/') for p in points for im in p['images']];batches=[]
        with torch.inference_mode():
            for start in range(0,len(paths),16):
                images=[]
                for path in paths[start:start+16]:
                    with Image.open(path) as image:images.append(ImageOps.pad(image.convert('RGB'),(224,224),method=Image.Resampling.LANCZOS,color=(127,127,127)))
                f=encoder.get_image_features(**processor(images=images,return_tensors='pt').to(device));f=f/f.norm(dim=-1,keepdim=True);batches.append(f.cpu().numpy())
                print('Features',min(start+16,len(paths)),'/',len(paths),flush=True)
        features=np.concatenate(batches)
        np.save(OUT/'image_features.npy',features);(OUT/'feature_points.json').write_text(json.dumps([p['id'] for p in points]))
    assert features.shape==(336,512)
    truth=np.array([int(im['angle'] in labels[p['id']]['selected']) for p in points for im in p['images']])
    def classifier():return LogisticRegression(C=1.0,solver='lbfgs',max_iter=1000,random_state=20261013)
    folds=StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=20261013)
    results={};fold_summary=[];fold_members=[]
    for fold,(train,val) in enumerate(folds.split(np.zeros((84,1)),y_pair,groups),1):
        assert not set(groups[train])&set(groups[val])
        assert not {h for i in train for h in digests[i]}&{h for i in val for h in digests[i]}
        train_imgs=np.array([i*4+j for i in train for j in range(4)])
        val_imgs=np.array([i*4+j for i in val for j in range(4)])
        model=classifier();model.fit(features[train_imgs],truth[train_imgs]);scores=model.decision_function(features[val_imgs]).reshape(-1,4)
        for row,i in enumerate(val):
            p=points[i];delta=float(scores[row,0]+scores[row,2]-scores[row,1]-scores[row,3]);pred=[0,180] if delta>=0 else [90,270]
            human=sorted(labels[p['id']]['selected']);base=baseline[p['id']]['predicted']
            results[int(i)]={'id':p['id'],'point_id':p['point_id'],'road_level':p['road_level'],'fold':fold,'human':human,
                             'baseline':base,'classifier':pred,'baseline_correct':base==human,'classifier_correct':pred==human,
                             'classifier_margin':abs(delta),'group':int(groups[i])}
        fold_summary.append({'fold':fold,'training_points':len(train),'validation_points':len(val),
                             'baseline_correct':sum(results[int(i)]['baseline_correct'] for i in val),
                             'classifier_correct':sum(results[int(i)]['classifier_correct'] for i in val)})
        fold_members.append({'fold':fold,'train':[points[i]['id'] for i in train],'validation':[points[i]['id'] for i in val]})
    assert len(results)==84
    records=[results[i] for i in range(84)]
    better=[p for p in records if p['classifier_correct'] and not p['baseline_correct']]
    worse=[p for p in records if p['baseline_correct'] and not p['classifier_correct']]
    summary={'points':84,'distinct_duplicate_groups':len(set(groups)),'baseline_correct':sum(p['baseline_correct'] for p in records),
             'classifier_oof_correct':sum(p['classifier_correct'] for p in records),'baseline_accuracy':sum(p['baseline_correct'] for p in records)/84,
             'classifier_oof_accuracy':sum(p['classifier_correct'] for p in records)/84,'fixed_baseline_errors':len(better),'introduced_errors':len(worse),
             'fixed_points':[p['point_id'] for p in better],'introduced_error_points':[p['point_id'] for p in worse],
             'classifier_error_points':[p['point_id'] for p in records if not p['classifier_correct']],
             'folds':fold_summary,'by_level':{str(l):{'n':len(g),'baseline_correct':sum(p['baseline_correct'] for p in g),'classifier_correct':sum(p['classifier_correct'] for p in g)} for l in [1,2,3,4] if (g:=[p for p in records if p['road_level']==l])},
             'limitation':'Single fixed grouped 5-fold CV on 84 certain points. Each reported prediction is out-of-fold. Final all-data refit is for future validation and its training accuracy is not reported.'}
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    (OUT/'oof_predictions.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
    (OUT/'fold_members.json').write_text(json.dumps(fold_members,ensure_ascii=False,indent=2))
    with (OUT/'comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['point_id','road_level','validation_fold','human','baseline','classifier','baseline_correct','classifier_correct'])
        for p in records:w.writerow([p['point_id'],p['road_level'],p['fold'],p['human'],p['baseline'],p['classifier'],p['baseline_correct'],p['classifier_correct']])
    # Distinct final artifact trained on all known certain labels; never used for OOF evaluation.
    full=classifier();full.fit(features,truth)
    np.savez(OUT/'classifier_all84.npz',coef=full.coef_,intercept=full.intercept_,classes=full.classes_)
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
