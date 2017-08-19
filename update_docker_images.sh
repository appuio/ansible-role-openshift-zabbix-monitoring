#!/bin/bash

set -eo pipefail  # Exit with nonzero exit code if anything fails

# To check whether a build was triggered by cron, examine the TRAVIS_EVENT_TYPE environment variable to see if it has the value cron.

function build {
  IMAGE="$1"
  BRANCH="$2"

  RESULT=$(curl -H "Content-Type: application/json"  -H "Authorization: Bearer ${QUAY_TOKEN}" https://quay.io/api/v1/repository/appuio/oso-centos7-ops-base/trigger/)
  TRIGGER_ID=$(echo "${RESULT}" | jq -r '.triggers[0].id')
  [ "${TRIGGER_ID}" ] || return

  RESULT=$(curl -H "Content-Type: application/json"  -H "Authorization: Bearer ${QUAY_TOKEN}" --data "{\"branch_name\":\"${TRAVIS_BRANCH}\"}"  "https://quay.io/api/v1/repository/appuio/oso-centos7-ops-base/trigger/${TRIGGER_ID}/start")
  BUILD_ID=$(echo "$RESULT" | jq -r '.id')
  [ "${BUILD_ID}" ] || return

  PHASE=""
  while [ "${PHASE}" != "complete" ]; do
    RESULT=$(curl -H "Content-Type: application/json" -H "Authorization: Bearer ${QUAY_TOKEN}" "https://quay.io/api/v1/repository/appuio/oso-centos7-ops-base/build/${BUILD_ID}/status")
    PHASE=$(echo "${RESULT}" | jq -r .phase)
    [ "${PHASE}" != '{}' ] && [ "${PHASE}" != 'null' ] || break
    sleep 3
  done
}

if [ "$TRAVIS_PULL_REQUEST" != "false" ]; then
    echo "Skipping Docker build for pull request."
    exit 0
fi

read -r -d '' RESULT <<'EOF' || true
{
  "status": {},
  "error": null,
  "display_name": "f2ee5d9",
  "repository": {
    "namespace": "appuio",
    "name": "oso-centos7-ops-base"
  },
  "subdirectory": "/vendor/openshift-tools/docker/oso-ops-base/centos7/Dockerfile",
  "started": "Sat, 19 Aug 2017 18:36:26 -0000",
  "tags": [
    "master",
    "latest"
  ],
  "pull_robot": null,
  "trigger": {
    "service": "github",
    "can_invoke": true,
    "config": {
      "build_source": "appuio/ansible-role-openshift-zabbix-monitoring",
      "deploy_key_id": 24689474,
      "context": "/vendor/openshift-tools/docker/oso-ops-base/centos7",
      "hook_id": 15499787,
      "credentials": [
        {
          "name": "SSH Public Key",
          "value": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC3/DeFIqF2FgSS4tQOaRGnmBXZ9f44OVQugQT5mh5873KGe7mDmyH6ktF5lcNoRGb4m3hAwtQVfAqugjJiQaKKbRs4NSbBe1O/+jS+nHPd86kXMHWFYH2AKf0xt5qN/xl8VbMmSAtdJZAbE2gEULTrVSZHaKKnlNcW2H6yK6x3YfLnMal2NKI3tTKV+J7APAyo4hgzr96zquX5pHw8JWZ9IbS+IEb1Nq5HQ0AtfgBz7PUFm4byGX4X5DMnx8S0F85FJRsEISV5zL/fiigc7uQzGpX+tKgUJTY2iJpIRc1MWa7PCeR6k8l5I3h6q9Pb9UnEg/APCi0vJsMWhv9Wh15h"
        }
      ],
      "master_branch": "master",
      "dockerfile_path": "/vendor/openshift-tools/docker/oso-ops-base/centos7/Dockerfile"
    },
    "is_active": true,
    "repository_url": "https://github.com/appuio/ansible-role-openshift-zabbix-monitoring",
    "build_source": "appuio/ansible-role-openshift-zabbix-monitoring",
    "id": "f97ee414-f069-41c9-aefa-55e58c52c16b"
  },
  "trigger_metadata": {
    "default_branch": "master",
    "commit": "f2ee5d92e157c9ef61fa14159bd60c7623c5b129",
    "ref": "refs/heads/master",
    "git_url": "git@github.com:appuio/ansible-role-openshift-zabbix-monitoring.git",
    "commit_info": {
      "url": "https://github.com/appuio/ansible-role-openshift-zabbix-monitoring/commit/f2ee5d92e157c9ef61fa14159bd60c7623c5b129",
      "date": "Fri, 18 Aug 2017 18:42:03 GMT",
      "message": "Make Zabbix images configurable.",
      "author": {
        "username": "dtschan",
        "url": "https://github.com/dtschan",
        "avatar_url": "https://avatars3.githubusercontent.com/u/482784?v=4"
      },
      "committer": {
        "username": "dtschan",
        "url": "https://github.com/dtschan",
        "avatar_url": "https://avatars3.githubusercontent.com/u/482784?v=4"
      }
    }
  },
  "context": "/vendor/openshift-tools/docker/oso-ops-base/centos7",
  "is_writer": true,
  "phase": "waiting",
  "resource_key": null,
  "manual_user": "appuioorg",
  "id": "66bf45f6-73bd-4c56-a3d2-606e2bc8775f",
  "dockerfile_path": "/vendor/openshift-tools/docker/oso-ops-base/centos7/Dockerfile"
}
EOF



RESULT=$(curl -H "Content-Type: application/json"  -H "Authorization: Bearer ${QUAY_TOKEN}" https://quay.io/api/v1/repository/appuio/oso-centos7-ops-base/trigger/)
TRIGGER_ID=$(echo "${RESULT}" | jq -r '.triggers[0].id')

#RESULT=$(curl -H "Content-Type: application/json"  -H "Authorization: Bearer ${QUAY_TOKEN}" --data "{\"branch_name\":\"${TRAVIS_BRANCH}\"}"  "https://quay.io/api/v1/repository/appuio/oso-centos7-ops-base/trigger/${TRIGGER_ID}/start")
BUILD_ID=$(echo "$RESULT" | jq -r '.id')

RESULT=$(curl -H "Content-Type: application/json" -H "Authorization: Bearer ${QUAY_TOKEN}" "https://quay.io/api/v1/repository/appuio/oso-centos7-ops-base/build/${BUILD_ID}/status")
PHASE=$(echo "${RESULT}" | jq -r .phase)

if [ "${PHASE}" != "complete" ]; then
  echo "Building oso-centos7-ops-base failed!" >&2
fi

echo "Build of base image complete. Start building of dependent images"
build 'oso-centos7-zabbix-server' "${TRAVIS_BRANCH}"
#      ZABBIX_WEB_IMAGE: "quay.io/appuio/oso-centos7-zabbix-web:{{ version }}"
#      ZAGG_WEB_IMAGE: "quay.io/appuio/oso-centos7-zagg-web:{{ version }}"
#      HOST_MONITORING_IMAGE: "quay.io/appuio/oso-centos7-host-monitoring:{{ version }}"
#exit 0

# -o "$TRAVIS_BRANCH" != "$SOURCE_BRANCH"

# Save some useful information
REPO=`git config remote.origin.url`
SSH_REPO=${REPO/https:\/\/github.com\//git@github.com:}
SHA=`git rev-parse --verify HEAD`

# Clone the existing gh-pages for this repo into out/
# Create a new empty branch if gh-pages doesn't exist yet (should only happen on first deply)
git clone $REPO out
cd out
git checkout $TARGET_BRANCH || git checkout --orphan $TARGET_BRANCH
cd ..

# Clean out existing contents
rm -rf out/**/* || exit 0

# Run our compile script
doCompile

# Now let's go have some fun with the cloned repo
cd out
git config user.name "Travis CI"
git config user.email "$COMMIT_AUTHOR_EMAIL"

# If there are no changes to the compiled out (e.g. this is a README update) then just bail.
if [ -z "$(git status --porcelain)" ]; then
    echo "No changes to the output on this push; exiting."
    exit 0
fi

# Commit the "changes", i.e. the new version.
# The delta will show diffs between new and old versions.
git add -A .
git commit -m "Deploy to GitHub Pages: ${SHA}"

# Get the deploy key by using Travis's stored variables to decrypt deploy_key.enc
ENCRYPTED_KEY_VAR="encrypted_${ENCRYPTION_LABEL}_key"
ENCRYPTED_IV_VAR="encrypted_${ENCRYPTION_LABEL}_iv"
ENCRYPTED_KEY=${!ENCRYPTED_KEY_VAR}
ENCRYPTED_IV=${!ENCRYPTED_IV_VAR}
eval `ssh-agent -s`
openssl aes-256-cbc -K $ENCRYPTED_KEY -iv $ENCRYPTED_IV -in ../deploy_key.enc -d | ssh-add -

# Now that we're all set up, we can push.
git push $SSH_REPO $TARGET_BRANCH


#curl -H "Content-Type: application/json"  -H "Authorization: Bearer 4iecT4PPamZj9Dzurl5TRLd0qLwzwSTIz7Qq3Cr8" --data '{"branch_name":"master"}'  https://quay.io/api/v1/repository/appuio/oso-centos7-ops-base/trigger/f97ee414-f069-41c9-aefa-55e58c52c16b/start
#curl -H "Content-Type: application/json"  -H "Authorization: Bearer 4iecT4PPamZj9Dzurl5TRLd0qLwzwSTIz7Qq3Cr8"  https://quay.io/api/v1/repository/appuio/oso-centos7-ops-base/build/8ed22603-a83b-49d4-a594-8b9772c9328/status -w '%{http_code}'; echo $?
