#!/usr/bin/python

import json

class PolicyModule:

  def __init__(self, module):
    self.module = module

    self.changed = False
    self.msg = []

    for key in module.params:
      setattr(self, key, module.params[key])


  def update(self):
    if self.cluster_roles:
      (rc, stdout, stderr) = self.module.run_command('oc export clusterrolebinding -o json', check_rc=True)
      roleBindings = json.loads(stdout)

      for cluster_role in self.cluster_roles:
        if self.groups:
          self.update_role_binding(roleBindings, cluster_role, 'group', self.groups)

        if self.users:
          self.update_role_binding(roleBindings, cluster_role, 'user', self.users)

    if self.sccs:
      (rc, stdout, stderr) = self.module.run_command('oc export scc -o json', check_rc=True)
      securityContextConstraints = json.loads(stdout)

      for scc in self.sccs:
        if self.groups:
          self.update_scc(securityContextConstraints, scc, 'group', self.groups)

        if self.users:
          self.update_scc(securityContextConstraints, scc, 'user',self.users)


  def update_role_binding(self, roleBindings, cluster_role, principal_type, principals):
    cmd = 'oc adm policy '
    if self.state == 'present':
      cmd += 'add-cluster-role-to-' + principal_type
    else:
      cmd += 'remove-cluster-role-from-' + principal_type

    changedPrincipals = []
    for principal in principals:
      roleBinding = [rb for rb in roleBindings['items'] if rb['roleRef']['name'] == cluster_role and principal in (rb[principal_type + 'Names'] or [])]
      if bool(roleBinding) != (self.state == 'present'):
        changedPrincipals.append(principal)

    if changedPrincipals:
      self.changed = True
      args = cmd + " " + cluster_role + " " + " ".join(changedPrincipals)
      self.msg.append(args + "; ")
      if not self.module.check_mode:
        (rc, stdout, stderr) = self.module.run_command(args, check_rc=True)


  def update_scc(self, securityContextConstraints, scc, principal_type, principals):
    cmd = 'oc adm policy '
    if self.state == 'present':
      cmd += 'add-scc-to-' + principal_type
    else:
      cmd += 'remove-scc-from-' + principal_type

    changedPrincipals = []
    for principal in principals:
      inScc = [s for s in securityContextConstraints['items'] if s['metadata']['name'] == scc and principal in (s[principal_type + 's'] or [])]
      if bool(inScc) != (self.state == 'present'):
        changedPrincipals.append(principal)

    if changedPrincipals:
      self.changed = True
      args = cmd + " " + scc + " " + " ".join(changedPrincipals)
      self.msg.append(args + "; ")
      if not self.module.check_mode:
        (rc, stdout, stderr) = self.module.run_command(args, check_rc=True)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            state = dict(default='present', choices=['present', 'absent']),
            cluster_roles = dict(type='list'),
            sccs = dict(type='list'),
            groups = dict(type='list'),
            users = dict(type='list'),
        ),
        supports_check_mode=True
    )

    policy = PolicyModule(module)
    policy.update()

    module.exit_json(changed=policy.changed, msg=" ".join(policy.msg))


from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()
