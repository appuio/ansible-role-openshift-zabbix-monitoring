#!/usr/bin/python

def main():
    module = AnsibleModule(
        argument_spec=dict(
            command = dict(choices=['create-server-cert'], required=True),
            signer_cert = dict(type='str', default='/etc/origin/master/ca.crt'),
            signer_key = dict(type='str', default='/etc/origin/master/ca.key'),
            signer_serial = dict(type='str', default='/etc/origin/master/ca.serial.txt'),
            hostnames = dict(type='list', required=True),
            cert = dict(type='str', required=True),
            key = dict(type='str', required=True),
        ),
        supports_check_mode=True
    )

    command = module.params['command']
    signer_cert = module.params['signer_cert']
    signer_key = module.params['signer_key']
    signer_serial = module.params['signer_serial']
    hostnames = module.params['hostnames']
    cert = module.params['cert']
    key = module.params['key']

    if os.path.isfile(cert) and os.path.isfile(key):
      module.exit_json(changed=False)

    msg = []

    if not module.check_mode:   
      (rc, stdout, stderr) = module.run_command(['oc', 'adm', 'ca', 'create-server-cert',
        "--signer-cert=" + signer_cert,
        "--signer-key=" + signer_key,
        "--signer-serial=" + signer_serial,
        "--hostnames=" + "'".join(hostnames),
        "--cert=" + cert,
        "--key=" + key]
      )

      if rc != 0:
        module.fail_json(msg=stderr)

    module.exit_json(changed=True, msg=command + " " + cert)

from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()
