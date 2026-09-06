"""Assert availability and credential contracts against the actual rendered workloads."""
from pathlib import Path
import json,yaml,re
root=Path(__file__).resolve().parents[1]
name=json.loads((root/'package.json').read_text())['name']
for profile in ['base','production']:
 docs=[o for o in yaml.safe_load_all((root/'k8s'/profile/'resources.yaml').read_text()) if o]
 def objects(kind):return [o for o in docs if o['kind']==kind]
 workloads=objects('Deployment')+objects('StatefulSet')
 policies=objects('NetworkPolicy')
 for policy in policies:
  selector=policy['spec']['podSelector'].get('matchLabels',{})
  if workloads:assert any(all(w['spec']['template']['metadata']['labels'].get(k)==v for k,v in selector.items()) for w in workloads), 'NetworkPolicy selects no workload: '+policy['metadata']['name']
 for w in workloads:
  for c in w['spec']['template']['spec'].get('containers',[])+(w['spec']['template']['spec'].get('initContainers') or []):
   assert not c['image'].endswith(':latest'),c['image']
 if name=='postgresql':
  spec=objects('Cluster')[0]['spec'];assert spec['instances']==3
  assert spec['postgresql']['synchronous']=={'method':'any','number':1,'dataDurability':'required'}
  assert spec['affinity']['podAntiAffinityType']=='required'
 elif name=='mysql':
  spec=objects('InnoDBCluster')[0]['spec'];assert spec['instances']==3 and spec['router']['instances']==2
  assert spec['secretName']=='mysql-credentials'
  assert spec['podSpec']['affinity']['podAntiAffinity']['requiredDuringSchedulingIgnoredDuringExecution'][0]['labelSelector']['matchLabels']['component']=='mysqld'
 elif name=='mongodb':
  spec=objects('PerconaServerMongoDB')[0]['spec'];assert len(spec['replsets'])==1
  rs=spec['replsets'][0];assert rs['size']==3 and rs['affinity']['antiAffinityTopologyKey']=='kubernetes.io/hostname'
  assert not spec.get('unsafeFlags',{}).get('replsetSize',False)
 elif name=='cassandra':
  spec=objects('CassandraDatacenter')[0]['spec'];assert spec['size']==3 and len(spec['racks'])==3
  assert spec['config']['cassandra-yaml']['authenticator']=='PasswordAuthenticator'
 elif name=='redis':
  sts=objects('StatefulSet')[0];assert sts['spec']['replicas']==3
  assert sts['spec']['template']['spec']['affinity']['podAntiAffinity']['requiredDuringSchedulingIgnoredDuringExecution']
  assert objects('Deployment')[0]['spec']['replicas']==2
 elif name=='couchdb':
  sts=objects('StatefulSet')[0];assert sts['spec']['replicas']==3
  anti=sts['spec']['template']['spec']['affinity']['podAntiAffinity']['requiredDuringSchedulingIgnoredDuringExecution'][0]
  assert all(sts['spec']['template']['metadata']['labels'].get(k)==v for k,v in anti['labelSelector']['matchLabels'].items())
  assert objects('Job'), 'Missing cluster bootstrap Job'
 elif name in ['jenkins','sonarqube','nexus']:
  assert len(workloads)==1 and workloads[0]['spec'].get('replicas',1)==1,'Single-writer application cannot use active-active replicas'
  if name=='nexus':assert workloads[0]['spec']['strategy']['type']=='Recreate'
 elif name=='fabric':
  assert len(objects('StatefulSet'))==7
  for w in workloads:
   labels=w['spec']['template']['metadata']['labels'];assert labels['fabric-role'] in ['orderer','peer-org1','peer-org2']
   assert w['spec']['replicas']==1 and w['spec']['volumeClaimTemplates']
   env={e['name']:e.get('value') for e in w['spec']['template']['spec']['containers'][0]['env']}
   assert env.get('CORE_PEER_TLS_ENABLED',env.get('ORDERER_GENERAL_TLS_ENABLED'))=='true'
 elif name=='selenium':
  hub=next(w for w in workloads if w['metadata']['name']=='selenium-hub')
  assert {'secretRef':{'name':'selenium-basic-auth'}} in hub['spec']['template']['spec']['containers'][0]['envFrom']
  expected=6 if profile=='production' else 2
  assert sum(w['spec'].get('replicas',1) for w in workloads)==expected
 elif name=='argocd' and profile=='production':
  byname={w['metadata']['name']:w for w in workloads}
  assert byname['argocd-redis-ha-server']['spec']['replicas']==3
  for component in ['argocd-server','argocd-repo-server','argocd-applicationset-controller']:
   assert byname[component]['spec']['replicas']==2
 print(profile,'topology and credential contracts: PASS')
for p in [root/'README.md']+list((root/'docs').glob('*.md')):
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if not re.match(r'[a-z]+://|#',target):assert (p.parent/target.split('#')[0]).exists(),(p,target)
print('Local documentation links: PASS')
