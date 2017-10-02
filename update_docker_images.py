import os
import subprocess
import requests
import time
import re

token = os.environ['QUAY_TOKEN']
headers = {'Authorization':'Bearer %s' % token}
endpoint = 'https://quay.io/api/v1/repository'

def build(docker_repo, tag, github_project, docker_context, dockerfile_path = 'Dockerfile'):
#    response = requests.get('%s/%s/trigger' % (endpoint, repo), headers=headers)
#    response.raise_for_status()

    #commit_sha = subprocess.check_output(['git', 'rev-parse', tag])
#    trigger_id = response.json()['triggers'][0]['id']
#    data = {'tag_name': tag}
#    response = requests.post('%s/%s/trigger/%s/start' % (endpoint, repo, trigger_id), headers=headers, json=data)
#    response.raise_for_status()

    github_owner, github_repo = github_project.split('/')
    match = re.match(r'v([0-9.]+)', tag)
    if match:
        tag2 = match.group(1)
    else:
        tag2 = tag
    docker_tags = [tag, 'latest']
    data = {
        "archive_url": "https://github.com/%s/archive/%s.tar.gz" % (github_project, tag),
        "docker_tags": docker_tags,
        "context": "/%s-%s%s" % (github_repo, tag2, docker_context),
        "dockerfile_path": "/%s-%s%s%s" % (github_repo, tag2, docker_context, dockerfile_path)
    }
    response = requests.post('%s/%s/build/' % (endpoint, docker_repo), headers=headers, json=data)
    response.raise_for_status()

    build_id = response.json()['id']
    print 'Started build https://quay.io/repository/%s/build/%s/' % (docker_repo, build_id)
    build_phase = ''
    while build_phase != 'complete' and build_phase != 'error':
      response = requests.get('%s/%s/build/%s/status' % (endpoint, docker_repo, build_id), headers=headers)
      response.raise_for_status()
      build_phase = response.json()['phase']
      print build_phase
      if build_phase == 'error' or build_phase == 'expired':
          raise RuntimeError('Docker build failed!')
      time.sleep(5)

try:
    github_project = os.environ['TRAVIS_REPO_SLUG']
    if os.environ['TRAVIS_EVENT_TYPE'] == 'cron':
        build_tags = re.split(', *', os.environ['BUILD_TAGS'])
    else:
        build_tags = [os.environ['TRAVIS_BRANCH']]

    i = 1
    while os.environ.get('BUILD_IMAGE%d' % i, None):
        for build_tag in build_tags:
            docker_repo, docker_context = re.split(', *', os.environ['BUILD_IMAGE%d' % i])
            build(docker_repo, build_tag, github_project, docker_context)
        i += 1

except requests.exceptions.RequestException as e:
    if e.response.headers['Content-Type'] == 'application/json':
        detail = ', ' + e.response.json().get('detail', '')
    else:
        detail = ''
    print '%s: %s%s' % (e.request.url, e.message, detail)
