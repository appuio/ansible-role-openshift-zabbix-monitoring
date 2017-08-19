import os
import requests
import time

token = os.environ['QUAY_TOKEN']
headers = {'Authorization':'Bearer %s' % token}
endpoint = 'https://quay.io/api/v1/repository'

def build(repo, tag):
    response = requests.get('%s/%s/trigger' % (endpoint, repo), headers=headers)
    response.raise_for_status()

    trigger_id = response.json()['triggers'][0]['id']
    data = {'branch_name': tag}
    response = requests.post('%s/%s/trigger/%s/start' % (endpoint, repo, trigger_id), headers=headers, json=data)
    response.raise_for_status()

    build_id = response.json()['id']
    print 'Started build https://quay.io/repository/%s/build/%s/' % (repo, build_id)
    build_phase = ''
    while build_phase != 'complete':
      response = requests.get('%s/%s/build/%s/status' % (endpoint, repo, build_id), headers=headers)
      response.raise_for_status()
      build_phase = response.json()['phase']
      print build_phase
      time.sleep(5)

try:
    build('appuio/oso-centos7-ops-base', 'v1.0.0')
    build('appuio/oso-centos7-zabbix-server', 'v1.0.0')
    build('appuio/oso-centos7-zabbix-web', 'v1.0.0')
    build('appuio/oso-centos7-zagg-web', 'v1.0.0')
    build('appuio/oso-centos7-host-monitoring', 'v1.0.0')
except requests.exceptions.RequestException as e:
    print '%s: %s, %s' % (e.request.url, e.message, e.response.json()['detail'])
