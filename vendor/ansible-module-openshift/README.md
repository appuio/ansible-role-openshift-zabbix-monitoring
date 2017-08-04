OpenShift Ansible Modules
-------------------------

This repository contains an Ansible role providing Ansible modules for configuring
OpenShift 3 clusters.

The role is downloadable via `ansible-galaxy` and designed to be used as a dependency
of other roles, e.g.:

meta/main.yml of your role:

    dependencies:
      - src: git+https://github.com/appuio/ansible-module-openshift.git
        version: v1.0.0

Documentation of the roles is contained within the roles as per Ansible conventions.
