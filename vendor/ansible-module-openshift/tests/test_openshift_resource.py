import mock
import json
import library.openshift_resource

from mock import ANY

@mock.patch('library.openshift_resource.ResourceModule.patch_resource', autospec=True)
@mock.patch('library.openshift_resource.ResourceModule.export_resource', autospec=True)
@mock.patch('library.openshift_resource.AnsibleModule', autospec=True)
def test_patch_change(module_cls, export_resource, patch_resource):
  with open('tests/data/dc_openshift3-docker-hello.json', 'r') as f:
    dc = json.load(f)

  export_resource.return_value = dc

  with open('tests/data/dc_patch1.json', 'r') as f:
    dc_patch = json.load(f)

  module = module_cls.return_value
  module.params = {
    "namespace": "test",
    "type": "dc",
    "name": "openshift3-hello-world",
    "patch": dc_patch,
  }

  library.openshift_resource.main()

  patch_resource.assert_called_once_with(ANY, 'dc', 'openshift3-hello-world', dc_patch)

  module.exit_json.assert_called_with(msg=ANY, changed=True)

@mock.patch('library.openshift_resource.ResourceModule.patch_resource', autospec=True)
@mock.patch('library.openshift_resource.ResourceModule.export_resource', autospec=True)
@mock.patch('library.openshift_resource.AnsibleModule', autospec=True)
def test_patch_no_change(module_cls, export_resource, patch_resource):
  with open('tests/data/dc_openshift3-docker-hello_2.json', 'r') as f:
    dc = json.load(f)

  export_resource.return_value = dc

  with open('tests/data/dc_patch1.json', 'r') as f:
    dc_patch = json.load(f)

  module = module_cls.return_value
  module.params = {
    "namespace": "test",
    "type": "dc",
    "name": "openshift3-hello-world",
    "patch": dc_patch,
  }

  library.openshift_resource.main()

  assert patch_resource.call_count == 0

  module.exit_json.assert_called_with(msg=ANY, changed=False)

@mock.patch('library.openshift_resource.ResourceModule.patch_resource', autospec=True)
@mock.patch('library.openshift_resource.ResourceModule.export_resource', autospec=True)
@mock.patch('library.openshift_resource.ResourceModule.process_template', autospec=True)
@mock.patch('library.openshift_resource.AnsibleModule', autospec=True)
def test_template(module_cls, process_template, export_resource, patch_resource):
  with open('tests/data/template_pruner.json', 'r') as f:
    template = json.load(f)

  with open('tests/data/is_rhel7.json', 'r') as f:
    imagestream = json.load(f)

  process_template.return_value = template
  export_resource.return_value = imagestream 

  with open('tests/data/dc_patch1.json', 'r') as f:
    dc_patch = json.load(f)

  module = module_cls.return_value
  module.params = {
    "namespace": "test",
    "template": template,
  }

  library.openshift_resource.main()

  assert patch_resource.call_count == 0

  module.exit_json.assert_called_with(msg=ANY, changed=False)
