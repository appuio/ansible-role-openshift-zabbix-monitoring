#!/usr/bin/env python
# vim: expandtab:tabstop=4:shiftwidth=4

"""
 This is a library that can identify OpenShift EBS volume types and return them.

 Usage:

    # Create Snapshots

    regions = ebs_snapshotter.EbsSnapshotter.get_supported_regions()

    for region in regions:
        # This example doesn't skip any volume ids, but it is highly useful to do so.
        skip_volume_ids = []
        vol_ids = eu.get_classified_volume_ids(skip_volume_ids)

        print vol_ids
"""


import re
from collections import namedtuple
from openshift_tools.cloud.aws.base import Base
from openshift_tools.cloud.aws.instance_util import InstanceUtil

OpenShiftVolumeIdTypes = namedtuple('OpenShiftVolumeIdTypes',
                                    ['master_root',
                                     'node_root',
                                     'docker_storage',
                                     'autoprovisioned_pv',
                                     'manually_provisioned_pv',
                                     'unidentified'
                                    ])


PURPOSE_TAG_KEY = 'purpose'
NAME_TAG_KEY = 'Name'

STABLE_ATTACH_STATUSES = ['attached', 'detached', None]

class EbsUtil(Base):
    """ Useful utility methods for EBS """

    def __init__(self, region, verbose=False):
        """ Initialize the class """
        super(EbsUtil, self).__init__(region, verbose)

        self.instance_util = InstanceUtil(region, verbose)

    @staticmethod
    def generate_volume_uri(vol):
        """
            Returns an AWS URI that can uniquely identify the volume.

            Example: aws://us-east-1c/vol-0a0112a0e303fe909
        """
        return str("aws://%s/%s" % (vol.zone, vol.id))

    def get_instance_volume_ids(self, skip_volume_ids=None):
        """ Returns the volume IDs attached to different instance types. """
        master_root_volume_ids = set()
        node_root_volume_ids = set()
        docker_storage_volume_ids = set()

        if not skip_volume_ids:
            skip_volume_ids = []

        # Ensure that we use a set so that we can't have multiple entries of the
        # same volume ID to skip.
        skip_volume_ids = set(skip_volume_ids)

        for inst in self.ec2.get_only_instances():
            hosttype = inst.tags.get('host-type')
            for device, vol in inst.block_device_mapping.iteritems():

                # We'll skip any volumes in this list. Useful to skip already tagged volumes.
                if vol.volume_id in skip_volume_ids:
                    continue

                # Etcd is stored on the root volume on the masters. This is
                # also how we backup the ca.crt private keys and other master
                # specific data.
                if hosttype == 'master' and device == inst.root_device_name:
                    # We're only going to keep the volume_id because we'll be filtering these out.
                    master_root_volume_ids.add(vol.volume_id)

                # nodes are cattle. We don't care about their root volumes.
                if hosttype == 'node' and device == inst.root_device_name:
                    node_root_volume_ids.add(vol.volume_id)

                # masters and nodes have their docker storage volume on xvdb
                if hosttype in ['master', 'node'] and device == '/dev/xvdb':
                    docker_storage_volume_ids.add(vol.volume_id)

        return (master_root_volume_ids, node_root_volume_ids, docker_storage_volume_ids)

    def get_auto_prov_pv_volume_ids(self, skip_volume_ids=None):
        """ Returns a list of volume IDs for PVs that the autoprovisioner created """
        if not skip_volume_ids:
            skip_volume_ids = []

        # Ensure that we use a set so that we can't have multiple entries of the
        # same volume ID to skip.
        skip_volume_ids = set(skip_volume_ids)

        # Identify the volumes that were autoprovisioned for PVs
        autoprovisioned_pv_volume_ids = set()
        for vol in self.ec2.get_all_volumes():
            if vol.id in skip_volume_ids:
                continue

            for tkey in vol.tags.keys():
                if re.match("kubernetes.io/created-for", tkey):
                    autoprovisioned_pv_volume_ids.add(vol.id)

        return autoprovisioned_pv_volume_ids


    def get_trans_attach_status_vols(self, skip_volume_ids=None):
        """ Returns the volumes that are in a transition state (attaching, detaching, busy, etc) """

        if not skip_volume_ids:
            skip_volume_ids = []

        all_vols = self.ec2.get_all_volumes()
        trans_vols = [vol for vol in all_vols \
                      if vol.id not in skip_volume_ids and \
                         vol.attach_data.status not in STABLE_ATTACH_STATUSES]

        return trans_vols


    def get_manual_prov_pv_volume_ids(self, skip_volume_ids=None):
        """ Returns a list of volume IDs for PVs that were created manually """
        if not skip_volume_ids:
            skip_volume_ids = []

        # Ensure that we use a set so that we can't have multiple entries of the
        # same volume ID to skip.
        skip_volume_ids = set(skip_volume_ids)

        # Identify the volumes that were manually provisioned for PVs
        retval = set()
        for vol in self.ec2.get_all_volumes():
            if vol.id in skip_volume_ids:
                continue


            vol_name = vol.tags.get('Name')

            if vol_name and re.match("^pv-", vol_name):
                retval.add(vol.id)

        return retval

    def get_classified_volume_ids(self, skip_volume_ids=None):
        """ Returns a DTO of all of the volume ID types identified """

        # make a set
        if not skip_volume_ids:
            skip_volume_ids = []

        # Ensure that we use a set so that we can't have multiple entries of the
        # same volume ID to skip.
        skip_volume_ids = set(skip_volume_ids)

        mids, nids, dsids = self.get_instance_volume_ids(skip_volume_ids)

        skip_volume_ids = skip_volume_ids.union(mids).union(nids).union(dsids)

        apids = self.get_auto_prov_pv_volume_ids(skip_volume_ids)

        skip_volume_ids = skip_volume_ids.union(apids)

        mpids = self.get_manual_prov_pv_volume_ids(skip_volume_ids)

        skip_volume_ids = skip_volume_ids.union(mpids)

        # These are all of the rest of the volumes. aka "unidentified"
        uids = [v.id for v in self.ec2.get_all_volumes() if v.id not in skip_volume_ids]

        return OpenShiftVolumeIdTypes(master_root=mids,
                                      node_root=nids,
                                      docker_storage=dsids,
                                      autoprovisioned_pv=apids,
                                      manually_provisioned_pv=mpids,
                                      unidentified=uids
                                     )

    def set_volume_purpose_tag(self, volume_ids, purpose, prefix="", dry_run=False):
        """ Adds a tag to the EBS volume describing the purpose of this volume """
        self.verbose_print("Setting tag '%s: %s' on %d volume(s): %s" % \
                           (PURPOSE_TAG_KEY, purpose, len(volume_ids), volume_ids),
                           prefix=prefix)

        if dry_run:
            self.print_dry_run_msg(prefix=prefix + "  ")
        else:
            self.ec2.create_tags(list(volume_ids), {PURPOSE_TAG_KEY: purpose})

    def set_volume_name_tag(self, volume_ids, prefix="", dry_run=False):
        """ Adds a tag to the EBS volume of the name of the host it belongs to """

        all_instances = self.instance_util.get_all_instances_as_dict()
        all_vols = self.ec2.get_all_volumes()

        for volume_id in volume_ids:
            volumes = [vol for vol in all_vols if vol.id == volume_id]

            if not volumes or len(volumes) != 1:
                # no need to keep going if we can't fine the volume for the volume id.
                continue

            volume = volumes[0]

            if not volume.attach_data or not volume.attach_data.instance_id:
                # no need to keep going if the volume isn't attached to a host.
                continue

            inst_id = volume.attach_data.instance_id

            inst_name = all_instances[inst_id].tags.get('Name')

            if not inst_name:
                # no need to keep going if we weren't able to get a name from the instance.
                continue

            self.verbose_print("Setting tag '%s: %s' on %d volume(s): %s" % \
                               (NAME_TAG_KEY, inst_name, 1, volume_id),
                               prefix=prefix)

            if dry_run:
                self.print_dry_run_msg(prefix=prefix + "  ")
            else:
                self.ec2.create_tags([volume_id], {NAME_TAG_KEY: inst_name})

