#!/usr/bin/env python
'''
  Generate the openshift-tools/ansible/roles/lib_openshift_cli/library/ modules.
'''

import os

# pylint: disable=anomalous-backslash-in-string
GEN_STR = "#!/usr/bin/env python # pylint: disable=too-many-lines\n" + \
          "#     ___ ___ _  _ ___ ___    _ _____ ___ ___\n"          + \
          "#    / __| __| \| | __| _ \  /_\_   _| __|   \\\n"        + \
          "#   | (_ | _|| .` | _||   / / _ \| | | _|| |) |\n"        + \
          "#    \___|___|_|\_|___|_|_\/_/_\_\_|_|___|___/_ _____\n"  + \
          "#   |   \ / _ \  | \| |/ _ \_   _| | __|   \_ _|_   _|\n" + \
          "#   | |) | (_) | | .` | (_) || |   | _|| |) | |  | |\n"   + \
          "#   |___/ \___/  |_|\_|\___/ |_|   |___|___/___| |_|\n"

OPENSHIFT_ANSIBLE_PATH = os.path.dirname(os.path.realpath(__file__))


FILES = {'oc_obj.py': ['lib/base.py',
                       '../../lib_yaml_editor/build/src/yedit.py',
                       'src/oc_obj.py',
                       'ansible/oc_obj.py',
                      ],
         'oc_version.py': ['lib/base.py',
                           '../../lib_yaml_editor/build/src/yedit.py',
                           'src/oc_version.py',
                           'ansible/oc_version.py',
                          ],
         'oc_secret_add.py': ['lib/base.py',
                              '../../lib_yaml_editor/build/src/yedit.py',
                              'src/oc_secret_add.py',
                              'lib/serviceaccount.py',
                              'ansible/oc_secret_add.py',
                             ],
         'oc_secret.py': ['lib/base.py',
                          '../../lib_yaml_editor/build/src/yedit.py',
                          'src/oc_secret.py',
                          'ansible/oc_secret.py',
                         ],
         'oc_service.py': ['lib/base.py',
                           '../../lib_yaml_editor/build/src/yedit.py',
                           'lib/service.py',
                           'src/oc_service.py',
                           'ansible/oc_service.py',
                          ],
         'oc_volume.py': ['lib/base.py',
                          '../../lib_yaml_editor/build/src/yedit.py',
                          'lib/volume.py',
                          'lib/deploymentconfig.py',
                          'src/oc_volume.py',
                          'ansible/oc_volume.py',
                         ],
         'oc_scale.py': ['lib/base.py',
                         '../../lib_yaml_editor/build/src/yedit.py',
                         'lib/deploymentconfig.py',
                         'lib/replicationcontroller.py',
                         'src/oc_scale.py',
                         'ansible/oc_scale.py',
                        ],
         'oc_edit.py': ['lib/base.py',
                        '../../lib_yaml_editor/build/src/yedit.py',
                        'src/oc_edit.py',
                        'ansible/oc_edit.py',
                       ],
         'oc_env.py': ['lib/base.py',
                       '../../lib_yaml_editor/build/src/yedit.py',
                       'lib/deploymentconfig.py',
                       'src/oc_env.py',
                       'ansible/oc_env.py',
                      ],
         'oadm_router.py': ['lib/base.py',
                            '../../lib_yaml_editor/build/src/yedit.py',
                            'lib/service.py',
                            'lib/deploymentconfig.py',
                            'lib/secret.py',
                            'lib/serviceaccount.py',
                            'lib/rolebinding.py',
                            'src/oadm_router.py',
                            'ansible/oadm_router.py',
                           ],
         'oadm_registry.py': ['lib/base.py',
                              '../../lib_yaml_editor/build/src/yedit.py',
                              'lib/volume.py',
                              'lib/service.py',
                              'lib/deploymentconfig.py',
                              'src/oc_version.py',
                              'src/oadm_registry.py',
                              'ansible/oadm_registry.py',
                             ],
         'oadm_ca.py': ['lib/base.py',
                        '../../lib_yaml_editor/build/src/yedit.py',
                        'src/oadm_certificate_authority.py',
                        'ansible/oadm_certificate_authority.py',
                       ],
         'oadm_project.py': ['lib/base.py',
                             '../../lib_yaml_editor/build/src/yedit.py',
                             'lib/project.py',
                             'src/oadm_project.py',
                             'ansible/oadm_project.py',
                            ],
         'oadm_manage_node.py': ['lib/base.py',
                                 '../../lib_yaml_editor/build/src/yedit.py',
                                 'src/oadm_manage_node.py',
                                 'ansible/oadm_manage_node.py',
                                ],
         'oc_route.py': ['lib/base.py',
                         '../../lib_yaml_editor/build/src/yedit.py',
                         'lib/route.py',
                         'src/oc_route.py',
                         'ansible/oc_route.py',
                        ],
         'oc_serviceaccount.py': ['lib/base.py',
                                  '../../lib_yaml_editor/build/src/yedit.py',
                                  'lib/serviceaccount.py',
                                  'src/oc_serviceaccount.py',
                                  'ansible/oc_serviceaccount.py',
                                 ],
         'oc_label.py': ['lib/base.py',
                         '../../lib_yaml_editor/build/src/yedit.py',
                         'src/oc_label.py',
                         'ansible/oc_label.py',
                        ],
         'oc_user.py': ['lib/base.py',
                        '../../lib_yaml_editor/build/src/yedit.py',
                        'lib/user.py',
                        'src/oc_user.py',
                        'ansible/oc_user.py',
                       ],
         'oc_group.py': ['lib/base.py',
                         '../../lib_yaml_editor/build/src/yedit.py',
                         'lib/group.py',
                         'src/oc_group.py',
                         'ansible/oc_group.py',
                        ],
         'oadm_policy_user.py': ['lib/base.py',
                                 '../../lib_yaml_editor/build/src/yedit.py',
                                 'lib/role.py',
                                 'lib/rolebinding.py',
                                 'lib/scc.py',
                                 'src/oadm_policy_user.py',
                                 'ansible/oadm_policy_user.py',
                                ],
         'oc_process.py': ['lib/base.py',
                           '../../lib_yaml_editor/build/src/yedit.py',
                           'src/oc_process.py',
                           'ansible/oc_process.py',
                          ],

         'oc_pvc.py': ['lib/base.py',
                       '../../lib_yaml_editor/build/src/yedit.py',
                       'lib/pvc.py',
                       'src/oc_pvc.py',
                       'ansible/oc_pvc.py',
                      ],
         'oc_image.py': ['lib/base.py',
                         '../../lib_yaml_editor/build/src/yedit.py',
                         'src/oc_image.py',
                         'ansible/oc_image.py',
                        ],
        }


def main():
    ''' combine the necessary files to create the ansible module '''
    library = os.path.join(OPENSHIFT_ANSIBLE_PATH, '..', 'library/')
    for fname, parts in FILES.items():
        with open(os.path.join(library, fname), 'w') as afd:
            afd.seek(0)
            afd.write(GEN_STR)
            for fpart in parts:
                with open(os.path.join(OPENSHIFT_ANSIBLE_PATH, fpart)) as pfd:
                    # first line is pylint disable so skip it
                    for idx, line in enumerate(pfd):
                        if idx == 0 and 'skip-file' in line:
                            continue

                        afd.write(line)


if __name__ == '__main__':
    main()


