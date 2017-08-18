#!/bin/bash -e

# This is useful so we can debug containers running inside of OpenShift that are
# failing to start properly.
if [ "$OO_PAUSE_ON_START" = "true" ] ; then
  echo
  echo "This container's startup has been paused indefinitely because OO_PAUSE_ON_START has been set."
  echo
  while sleep 10; do
    true
  done
fi

# interactive shells read .bashrc (which this script doesn't execute as) so force it
source /root/.bashrc

# Configure the container
time ansible-playbook /root/config.yml

# Send a heartbeat when the container starts up
/usr/bin/ops-metric-client --send-heartbeat

# fire off the check pmcd status script
check-pmcd-status.sh &
# fire off the pmcd script
/usr/share/pcp/lib/pmcd start &

# Run the main service of this container
echo
echo 'Starting crond'
echo '---------------'
exec /usr/sbin/crond -n -m off

