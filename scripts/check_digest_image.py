"""Reproduce the upstream digest-label rejection and prove only labels change."""
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import yaml

ROOT=Path(__file__).resolve().parents[1]
TAG='26.9.0.129388-community'
DIGEST='sha256:58b068af30bdfdccf91222de36e310529033e853dfae221b429cba80d10d5751'
IMAGE='docker.io/library/sonarqube:'+TAG+'@'+DIGEST
LABEL=re.compile(r'(?:[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?)?\Z')

def require(value,message):
    if not value:raise ValueError(message)

def invalid_labels(value):
    errors=[]
    if isinstance(value,dict):
        for key,item in value.items():
            if key=='labels' and isinstance(item,dict):
                for name,text in item.items():
                    if not isinstance(text,str) or len(text)>63 or not LABEL.fullmatch(text):errors.append((name,text))
            errors.extend(invalid_labels(item))
    elif isinstance(value,list):
        for item in value:errors.extend(invalid_labels(item))
    return errors

def render(chart,kind,tag):
    raw=subprocess.check_output(['helm','template','sonarqube',str(chart),'-n','tooling-sonarqube',
        '--kube-version','1.36.1','--set-string','app.image.repository=docker.io/library/sonarqube',
        '--set-string','app.image.tag='+tag,'--set-string','app.deploymentType='+kind])
    return raw,[o for o in yaml.safe_load_all(raw) if o]

def main():
    out=ROOT/'evidence/digest-labels';out.mkdir(parents=True,exist_ok=True)
    results=[]
    with tempfile.TemporaryDirectory() as temp:
        old=Path(temp)/'sonarqube';shutil.copytree(ROOT/'charts/sonarqube',old)
        (old/'templates/_digest-labels.tpl').unlink()
        for kind in ['StatefulSet','Deployment']:
            bad_raw,bad=render(old,kind,TAG+'@'+DIGEST)
            raw,objects=render(ROOT/'charts/sonarqube',kind,TAG+'@'+DIGEST)
            require(invalid_labels(bad),'original digest-label defect not reproduced')
            require(not invalid_labels(objects),'invalid repaired Kubernetes labels')
            expected=copy.deepcopy(bad)
            for obj in expected:
                if obj['kind']==kind:obj['metadata']['labels']['app.kubernetes.io/version']=TAG
            require(objects==expected,'change beyond version label')
            workload=next(o for o in objects if o['kind']==kind)
            require(workload['spec']['template']['spec']['containers'][0]['image']==IMAGE,'digest pin altered')
            _,plain=render(ROOT/'charts/sonarqube',kind,TAG)
            _,old_plain=render(old,kind,TAG)
            require(plain==old_plain,'plain-tag behavior changed')
            (out/(kind+'.yaml')).write_bytes(raw)
            results.append({'kind':kind,'original_rejected':True,'labels_valid':True,'only_version_label_changed':True,
                'image':IMAGE,'render_sha256':hashlib.sha256(raw).hexdigest(),'plain_tag_unchanged':True})
    (out/'receipt.json').write_text(json.dumps({'passed':True,'cases':results},indent=2)+'\n')
    print('PASS: original label rejection, immutable image, both workload kinds and unchanged plain tags')

if __name__=='__main__':main()
