OpenShift Zabbix Monitoring Role
================================

This Ansible role installs and configures Zabbix on OpenShift for OpenShift monitoring.
It's based on https://github.com/openshift/openshift-tools/blob/prod/docs/zabbix_3.0.asciidoc 
and https://blog.openshift.com/build-monitoring-solution-look-openshift-tools/.
After installation you'll have a working Zabbix installation, pre-configured with a range of
OpenShift specific items and triggers.

Requirements
------------

* OpenShift Container Platform 3.3 or later or OpenShift Origin M5 1.3 or later.
* Persistent storage volume with a size of at least 10 GB.
* OpenShift Ansible inventory. Currently only tested with "bring your own" (byo) setups.

Masters and nodes that should be monitored must be labeled as followed:

* Masters: ``host-monitoring=master``
* Infrastructure nodes: ``host-monitoring=infra``
* Compute nodes: ``host-monitoring=node``

Please note the the role reads the labels from the inventory, not from the cluster.

Role Variables
--------------

| Name                       | Default value                                        | Description                                                                                                  |
|----------------------------|------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| zabbix_password            | None (required)                                      | Password of Zabbix `Admin` user                                                                              |
| version                    | *role_version*, latest                               | Version of the Zabbix monitoring images to deploy                                                            |
| namespace                  | monitoring                                           | Namespace to deploy Zabbix to                                                                                |
| zabbix_hostname            | monitoring.{{ openshift_master_default_subdomain }}" | External hostname of Zabbix web frontend                                                                     |
| zagg_hostname              | zagg.{{ openshift_master_default_subdomain }}        | External hostname of Zagg server                                                                             |
| volume_capacity            | 10Gi                                                 | Size of database persistent volume                                                                           |
| timezone                   | *appuio_container_timezone*, UTC                     | Timezone (TZ) of the containers, see https://en.wikipedia.org/wiki/List_of_tz_database_time_zones for a list |          
| zabbix_server_memory_limit | 512Mi                                                | Memory limit of Zabbix server                                                                                | 
| zabbix_web_memory_limit    | 256Mi                                                | Memory limit of Zabbix web frontend                                                                          |
| zagg_web_memory_limit      | 256Mi                                                | Memory limit of Zagg server                                                                                  |
| database_memory_limit      | 512Mi                                                | Memory limit of database server                                                                              |

Example Usage
-------------

`playbook.yml`:

    roles:
    - role: ansible-role-openshift-zabbix-monitoring
      zabbix_password: changeit
      version: v1.0.0

This repository also contains a playbook with allows to run the role manually. The playbook must be called from the parent directory of the checked out repository:

    ansible-playbook ansible-role-openmshift-zabbix-monitoring/playbook.yml -e zabbix_password='changeit' -e version='v1.0.0'
    
License
-------

Apache License Version 2.0

Author Information
------------------

APPUiO Team <info@appuio.ch>
