# pylint: skip-file

# pylint: disable=too-many-instance-attributes
class OCObject(OpenShiftCLI):
    ''' Class to wrap the oc command line tools '''

    # pylint allows 5. we need 6
    # pylint: disable=too-many-arguments
    def __init__(self,
                 kind,
                 namespace,
                 rname=None,
                 selector=None,
                 kubeconfig='/etc/origin/master/admin.kubeconfig',
                 verbose=False,
                 all_namespaces=False):
        ''' Constructor for OpenshiftOC '''
        super(OCObject, self).__init__(namespace, kubeconfig,
                                       all_namespaces=all_namespaces)
        self.kind = kind
        self.namespace = namespace
        self.name = rname
        self.selector = selector
        self.kubeconfig = kubeconfig
        self.verbose = verbose

    def get(self):
        '''return a kind by name '''
        results = self._get(self.kind, rname=self.name, selector=self.selector)
        if results['returncode'] != 0 and results.has_key('stderr') and \
           '\"%s\" not found' % self.name in results['stderr']:
            results['returncode'] = 0

        return results

    def delete(self):
        '''return all pods '''
        return self._delete(self.kind, self.name)

    def create(self, files=None, content=None):
        '''
           Create a config

           NOTE: This creates the first file OR the first conent.
           TODO: Handle all files and content passed in
        '''
        if files:
            return self._create(files[0])

        content['data'] = yaml.dump(content['data'])
        content_file = Utils.create_files_from_contents(content)[0]

        return self._create(content_file['path'])

    # pylint: disable=too-many-function-args
    def update(self, files=None, content=None, force=False):
        '''run update dc

           This receives a list of file names and takes the first filename and calls replace.
        '''
        if files:
            return self._replace(files[0], force)

        if content and content.has_key('data'):
            content = content['data']

        return self.update_content(content, force)

    def update_content(self, content, force=False):
        '''update the dc with the content'''
        return self._replace_content(self.kind, self.name, content, force=force)

    def needs_update(self, files=None, content=None, content_type='yaml'):
        ''' check to see if we need to update '''
        objects = self.get()
        if objects['returncode'] != 0:
            return objects

        # pylint: disable=no-member
        data = None
        if files:
            data = Utils.get_resource_file(files[0], content_type)
        elif content and content.has_key('data'):
            data = content['data']
        else:
            data = content

            # if equal then no need.  So not equal is True
        return not Utils.check_def_equal(data, objects['results'][0], skip_keys=None, debug=False)

