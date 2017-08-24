# pylint: skip-file

def main():
    '''
    ansible git module for cloning
    '''
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', type='str', choices=['present']),
            dest=dict(default=None, required=True, type='str'),
            repo=dict(default=None, required=True, type='str'),
            branch=dict(default=None, required=False, type='str'),
            bare=dict(default=False, required=False, type='bool'),
            ssh_key=dict(default=None, required=False, type='str'),
        ),
        supports_check_mode=False,
    )
    git = GitClone(module.params['dest'],
                   module.params['repo'],
                   module.params['branch'],
                   module.params['bare'],
                   module.params['ssh_key'])

    state = module.params['state']

    if state == 'present':
        results = git.clone()

        if results['returncode'] != 0:
            module.fail_json(msg=results)

        if results['no_clone_needed'] == True:
            module.exit_json(changed=False, results=results, state="present")

        module.exit_json(changed=True, results=results, state="present")

    module.exit_json(failed=True,
                     changed=False,
                     results='Unknown state passed. %s' % state,
                     state="unknown")

# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import, locally-disabled
# import module snippets.  This are required
if __name__ == '__main__':
    from ansible.module_utils.basic import *
    main()
