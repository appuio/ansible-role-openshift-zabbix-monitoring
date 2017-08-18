# pylint: skip-file

def main():
    '''
    ansible git module for merging
    '''
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', type='str', choices=['present']),
            path=dict(default=None, required=True, type='str'),
            branch=dict(default=None, required=True, type='str'),
            merge_id=dict(default=None, required=True, type='str'),
            author=dict(default=None, required=False, type='str'),
        ),
        supports_check_mode=False,
    )
    git = GitMerge(module.params['path'],
                   module.params['merge_id'],
                   module.params['branch'],
                   module.params['author']
                  )

    state = module.params['state']

    if state == 'present':
        results = git.merge()

        if results['returncode'] != 0:
            module.fail_json(msg=results)

        if results.has_key('no_merge'):
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
