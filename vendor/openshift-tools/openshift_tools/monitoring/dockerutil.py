#!/usr/bin/env python2
# vim: expandtab:tabstop=4:shiftwidth=4

'''
    wrapper for interfacing with docker
'''

# Adding the ignore because it does not like the naming of the script
# to be different than the class name
# pylint: disable=invalid-name


import re
from openshift_tools.timeout import timeout
from openshift_tools.cgrouputil import CgroupUtil


class DockerDiskStats(object):
    ''' Class to store docker storage information
    '''

    # Reason: disable pylint too-many-instance-attributes and too-few-public-methods
    #         because this is a DTO
    # Status: permanently disabled
    # pylint: disable=too-many-instance-attributes,too-few-public-methods
    def __init__(self):
        ''' construct the object
        '''
        self.data_space_used = None
        self.data_space_available = None
        self.data_space_total = None
        self.data_space_percent_available = None

        self.metadata_space_used = None
        self.metadata_space_available = None
        self.metadata_space_total = None
        self.metadata_space_percent_available = None

    def __repr__(self):
        ''' make it easy to see what's inside of this object
        '''
        return 'DockerDiskStats(\n' + \
               '  data_space_used: %r\n' % self.data_space_used + \
               '  data_space_available: %r\n' % self.data_space_available + \
               '  data_space_total: %r\n' % self.data_space_total + \
               '  data_space_percent_available: %r\n' % self.data_space_percent_available + \
               '  metadtata_space_used: %r\n' % self.metadata_space_used + \
               '  metadtata_space_available: %r\n' % self.metadata_space_available + \
               '  metadtata_space_total: %r\n' % self.metadata_space_total + \
               '  metadata_space_percent_available: %r\n' % self.metadata_space_percent_available + \
               ')'

class ParseError(Exception):
    ''' Exception class for when we can't parse the docker info
    '''
    pass

class DockerUtil(object):
    ''' Utility for interacting with Docker
    '''

    def __init__(self, docker_client=None, max_wait=15):
        ''' construct the object
        '''
        self._docker = docker_client
        self._max_wait = max_wait
        self.__docker_info = None

    @property
    def _cached_docker_info(self):
        ''' Returns 'docker info' output as long as it doesn't take too long '''
        if not self.__docker_info:
            with timeout(seconds=self._max_wait):
                self.__docker_info = self._docker.info()

        return self.__docker_info

    @property
    def is_devicemapper(self):
        ''' Returns whether the docker storage driver is devicemapper or not. '''
        return self._cached_docker_info['Driver'] == 'devicemapper'


    @property
    def is_loopback(self):
        ''' Returns whether the docker storage driver is loopback or not. '''

        dlf_value = self._get_driver_status_attr('Data loop file')
        return dlf_value != None

    @staticmethod
    def convert_to_size_in_gb(value):
        ''' Parses out the number and unit type and normalizes the data to GB
        '''
        matches = re.match(r"^(?P<num>[0-9.]+) (?P<unit>[a-zA-Z]+)", value)
        num = matches.group("num")
        unit = matches.group("unit")

        if unit == "TB":
            return float(num) * 1024

        if unit == "GB":
            return float(num)

        if unit == "MB":
            return float(num) / 1024

        if unit == "kB":
            return float(num) / (1024 * 1024)

        raise ParseError("Unknown Unit Size")

    def _get_driver_status_attr(self, key):
        ''' Gets the value for the specified key from the DriverStatus hash since it's
            an array of key/value pairs instead of a normal dict (PITA to work with otherwise)
        '''
        results = [a[1] for a in self._cached_docker_info['DriverStatus'] if a[0] == key]

        if not results:
            return None

        return results[0]

    def get_disk_usage(self):
        ''' Gathers the docker storage disk usage stats and puts them in a DTO.
        '''
        dds = DockerDiskStats()

        # Disk space usage metrics are only available in devicemapper and loopback.
        if not self.is_devicemapper and not self.is_loopback:
            return dds

        dds.data_space_used = DockerUtil.convert_to_size_in_gb( \
                                self._get_driver_status_attr('Data Space Used'))

        dds.data_space_available = DockerUtil.convert_to_size_in_gb( \
                                self._get_driver_status_attr('Data Space Available'))

        dds.data_space_total = DockerUtil.convert_to_size_in_gb( \
                                self._get_driver_status_attr('Data Space Total'))

        dds.metadata_space_used = DockerUtil.convert_to_size_in_gb( \
                                self._get_driver_status_attr('Metadata Space Used'))

        dds.metadata_space_available = DockerUtil.convert_to_size_in_gb( \
                                self._get_driver_status_attr('Metadata Space Available'))

        dds.metadata_space_total = DockerUtil.convert_to_size_in_gb( \
                                self._get_driver_status_attr('Metadata Space Total'))


        # Work around because loopback lies about its actual total space
        if not self.is_loopback:
            dds.data_space_total = dds.data_space_used + dds.data_space_available
            dds.metadata_space_total = dds.metadata_space_used + dds.metadata_space_available

        dds.data_space_percent_available = (dds.data_space_available / dds.data_space_total) * 100
        dds.metadata_space_percent_available = (dds.metadata_space_available / dds.metadata_space_total) * 100

        return dds

    @staticmethod
    def normalize_ctr_name(docker_name):
        ''' Docker stores the name of the container with a leading '/'.
            This method changes the name into what you normally see in Docker output.
        '''
        return docker_name[1:]

    @staticmethod
    def ctr_name_matches_regex(ctr, ctr_name_regex):
        ''' Returns true or false if the ctr_name_regex is in the list of names
            Docker is storing for the container.
        '''
        result = [ctr_name
                  for ctr_name in ctr['Names']
                  if re.match(ctr_name_regex, DockerUtil.normalize_ctr_name(ctr_name))
                 ]

        return len(result) > 0

    def get_ctrs_matching_names(self, ctr_name_regexes):
        ''' Returns all of the containers that match any of the regexes passed in.
        '''
        retval = {}

        for ctr in self._docker.containers():
            for ctr_name_regex in ctr_name_regexes:
                if DockerUtil.ctr_name_matches_regex(ctr, ctr_name_regex):
                    retval[DockerUtil.normalize_ctr_name(ctr['Names'][0])] = ctr

        return retval

    @staticmethod
    def _get_cgroup_entity_name(docker_id):
        ''' Takes a docker id and returns the cgroup name for that container. '''
        return "docker-%s.scope" % docker_id


    def get_ctr_stats(self, ctr, use_cgroups=False):
        ''' Gathers and returns the container stats in an easy to consume fashion.
        '''

        raw_stats = None
        if use_cgroups:
            cgroup_name = DockerUtil._get_cgroup_entity_name(ctr['Id'])
            cgu = CgroupUtil(cgroup_name)
            raw_stats = cgu.raw_stats()
        else:
            raw_stats = self._docker.stats(ctr['Id'], stream=False)

        return CgroupUtil.raw_stats_to_dtos(raw_stats)
