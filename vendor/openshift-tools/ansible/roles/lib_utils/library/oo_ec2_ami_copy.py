#!/usr/bin/env python
'''
ansible module for copying AWS AMIs
'''
# vim: expandtab:tabstop=4:shiftwidth=4
#
#   AWS AMI ansible module
#
#
#   Copyright 2016 Red Hat Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# Jenkins environment doesn't have all the required libraries
# pylint: disable=import-error
import time
from dateutil.parser import parse
import boto3
import OpenSSL
# Ansible modules need this wildcard import
# pylint: disable=unused-wildcard-import, wildcard-import, redefined-builtin
from ansible.module_utils.basic import *


class AwsAmi(object):
    ''' AWS AMI class '''
    def __init__(self):
        self.module = None
        self.ec2_client = None
        self.account_id = None

    def get_kms_alias_arn(self, alias):
        ''' return IAM KMS arn from provided alias '''

        msg = "Did not find key with alias name: {}".format(alias)

        kms_client = boto3.client('kms')
        aliases = kms_client.list_aliases()['Aliases']
        my_alias = [x for x in aliases if x['AliasName'] == alias]
        if my_alias == []:
            self.module.exit_json(failed=True, msg=msg)

        key = [key for key in kms_client.list_keys()['Keys'] if key['KeyId'] == my_alias[0]['TargetKeyId']][0]

        if key:
            return key['KeyArn']

        self.module.exit_json(failed=True, msg=msg)

    def get_ami_by_id(self, ami_id):
        ''' return an ami by its id'''
        response = self.ec2_client.describe_images(ImageIds=[ami_id])

        # if no results, then no AMI by that id
        if len(response['Images']) == 0:
            msg = "Could not find ami with id: {}".format(ami_id)
            self.module.exit_json(failed=True, msg=msg)

        return response['Images'][0]

    def get_ami_by_name(self, ami_name):
        ''' check whether AMI with same name already exists '''
        name_filter = [{'Name': 'name',
                        'Values': [ami_name]
                       }]
        response = self.ec2_client.describe_images(Filters=name_filter)

        # if no results, then no AMI by that name
        if len(response['Images']) == 0:
            return None
        else:
            return response['Images'][0]

    def wait_for_ami_available(self, ami_id, wait_sec):
        ''' spin waiting for AMI to enter state 'available' '''

        start_time = time.time()
        while True:
            try:
                time.sleep(10)
                response = self.ec2_client.describe_images(ImageIds=[ami_id])
                if len(response['Images']) == 1 \
                   and response['Images'][0]['State'] == 'available':
                    return response['Images'][0]

                if time.time() - start_time > wait_sec:
                    msg = "Timed out waiting for AMI to become 'available'"
                    self.module.exit_json(failed=True, changed=True, msg=msg)

            except OpenSSL.SSL.Error:
                # just keep trying regardless of these intermitent errors
                pass

    def tag_ami(self, ami_id, tag_name, tag_value):
        ''' apply tag to object '''

        if tag_name and tag_value:
            resources = [ami_id]
            tags = [{'Key': tag_name, 'Value': tag_value}]
            response = self.ec2_client.create_tags(Resources=resources,
                                                   Tags=tags)

            if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                msg = "Failed to apply tag to AMI {}".format(ami_id)
                self.module.exit_json(failed=True, changed=True, msg=msg)

    def get_ami_by_kmsid(self, kmsid):
        '''fetch all amis that were encrypted with a specific kms key'''

        amis = []
        for image in self.ec2_client.describe_images(Owners=[self.account_id])['Images']:
            # image information is tied to the snapshot
            snapshotid = None
            if ('BlockDeviceMappings' in image and
                    len(image['BlockDeviceMappings']) > 0 and
                    'Ebs' in  image['BlockDeviceMappings'][0] and
                    'SnapshotId' in image['BlockDeviceMappings'][0]['Ebs']):
                snapshotid = image['BlockDeviceMappings'][0]['Ebs']['SnapshotId']

                snapshot = self.ec2_client.describe_snapshots(SnapshotIds=[snapshotid])

                if (len(snapshot['Snapshots']) > 0 and
                        'KmsKeyId' in snapshot['Snapshots'][0] and
                        kmsid == snapshot['Snapshots'][0]['KmsKeyId']):
                    amis.append(image)

        return sorted(amis, key=lambda img: parse(img['CreationDate']), reverse=True)

    def main(self):
        ''' module entrypoint '''

        self.module = AnsibleModule(
            argument_spec=dict(
                state=dict(default='list', choices=['list', 'present'], type='str'),
                ami_id=dict(default=None, required=True, type='str'),
                name=dict(default=None, type='str'),
                region=dict(default=None, required=True, type='str'),
                encrypt=dict(default=False, type='bool'),
                kms_arn=dict(default='', type='str'),
                kms_alias=dict(default=None, type='str'),
                aws_access_key=dict(default=None, type='str'),
                aws_secret_key=dict(default=None, type='str'),
                tag_name=dict(default=None, type='str'),
                tag_value=dict(default=None, type='str'),
                wait_sec=dict(default=1200, type='int'),
            ),
            mutually_exclusive=[['kms_arn', 'kms_alias']],
            #supports_check_mode=True
        )

        state = self.module.params['state']
        ami_id = self.module.params['ami_id']
        aws_access_key = self.module.params['aws_access_key']
        aws_secret_key = self.module.params['aws_secret_key']
        wait_sec = self.module.params['wait_sec']
        tag_name = self.module.params['tag_name']
        tag_value = self.module.params['tag_value']

        if aws_access_key and aws_secret_key:
            boto3.setup_default_session(aws_access_key_id=aws_access_key,
                                        aws_secret_access_key=aws_secret_key,
                                        region_name=self.module.params['region'])
        else:
            boto3.setup_default_session(region_name=self.module.params['region'])

        self.ec2_client = boto3.client('ec2')
        self.account_id = boto3.client('sts').get_caller_identity()['Account']


        if state == 'list':
            if ami_id != None:
                ami = self.ec2_client.describe_images(ImageIds=[ami_id])['Images'][0]
                self.module.exit_json(changed=False, results=ami,
                                      state="list")

        if state == 'present':
            # create request to make an AMI copy
            region = self.module.params['region']
            ami_name = self.module.params['name']
            encrypt = self.module.params['encrypt']
            kms_arn = self.module.params['kms_arn']
            kms_alias = self.module.params['kms_alias']

            if not ami_name:
                self.module.exit_json(failed=True, changed=False,
                                      msg="No AMI name provided")
            if kms_alias:
                kms_arn = self.get_kms_alias_arn(kms_alias)

            # get all amis encrypted with the kms
            amis = self.get_ami_by_kmsid(kms_arn)

            # amis returned, check their dates
            if amis != []:

                # fetch source ami so we can compare
                base_ami = self.get_ami_by_id(ami_id)

                # fail if no base ami was found
                if base_ami is None:
                    self.module.fail_json(failed=True, msg='Could not find base_ami with id: %s' % ami_id)

                curr_ami_date = parse(amis[0]['CreationDate'])

                base_ami_date = parse(base_ami['CreationDate'])

                if curr_ami_date > base_ami_date:
                    self.module.exit_json(changed=False, msg="AMI already exists", results=amis[0])

            response = self.ec2_client.copy_image(SourceRegion=region,
                                                  SourceImageId=ami_id,
                                                  Name=ami_name,
                                                  Encrypted=encrypt,
                                                  KmsKeyId=kms_arn)

            if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                self.module.exit_json(failed=True, changed=True,
                                      results=response)
            else:
                current_stats = self.wait_for_ami_available(response['ImageId'],
                                                            wait_sec)
                self.tag_ami(response['ImageId'], tag_name, tag_value)
                self.module.exit_json(changed=True, results=current_stats)

        self.module.exit_json(failed=True,
                              changed=False,
                              results='Unknown state passed. %s' % state,
                              state="unknown")

#This is not a module, but pylint thinks it is.  This is a command.
#pylint: disable=invalid-name
if __name__ == '__main__':
    AwsAmi().main()
