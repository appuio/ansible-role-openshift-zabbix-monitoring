# pylint: skip-file

class ManageNodeException(Exception):
    ''' manage-node exception class '''
    pass

class ManageNodeConfig(OpenShiftCLIConfig):
    ''' ManageNodeConfig is a DTO for the manage-node command.'''
    def __init__(self, kubeconfig, node_options):
        super(ManageNodeConfig, self).__init__(None, None, kubeconfig, node_options)

# pylint: disable=too-many-instance-attributes
class ManageNode(OpenShiftCLI):
    ''' Class to wrap the oc command line tools '''

    # pylint allows 5
    # pylint: disable=too-many-arguments
    def __init__(self,
                 config,
                 verbose=False):
        ''' Constructor for OCVolume '''
        super(ManageNode, self).__init__(None, config.kubeconfig)
        self.config = config

    def evacuate(self):
        ''' formulate the params and run oadm manage-node '''
        return self._evacuate(node=self.config.config_options['node']['value'],
                              selector=self.config.config_options['selector']['value'],
                              pod_selector=self.config.config_options['pod_selector']['value'],
                              dry_run=self.config.config_options['dry_run']['value'],
                              grace_period=self.config.config_options['grace_period']['value'],
                              force=self.config.config_options['force']['value'],
                             )
    def get_nodes(self, node=None, selector=''):
        '''perform oc get node'''
        _node = None
        _sel = None
        if node:
            _node = node
        if selector:
            _sel = selector

        results = self._get('node', rname=_node, selector=_sel)
        if results['returncode'] != 0:
            return results

        nodes = []
        items = None
        if results['results'][0]['kind'] == 'List':
            items = results['results'][0]['items']
        else:
            items = results['results']

        for node in items:
            _node = {}
            _node['name'] = node['metadata']['name']
            _node['schedulable'] = True
            if node['spec'].has_key('unschedulable'):
                _node['schedulable'] = False
            nodes.append(_node)

        return nodes

    def get_pods_from_node(self, node, pod_selector=None):
        '''return pods for a node'''
        results = self._list_pods(node=[node], pod_selector=pod_selector)

        if results['returncode'] != 0:
            return results

        # When a selector or node is matched it is returned along with the json.
        # We are going to split the results based on the regexp and then
        # load the json for each matching node.
        # Before we return we are going to loop over the results and pull out the node names.
        # {'node': [pod, pod], 'node': [pod, pod]}
        # 3.2 includes the following lines in stdout: "Listing matched pods on node:"
        all_pods = []
        if "Listing matched" in results['results']:
            listing_match = re.compile('\n^Listing matched.*$\n', flags=re.MULTILINE)
            pods = listing_match.split(results['results'])
            for pod in pods:
                if pod:
                    all_pods.extend(json.loads(pod)['items'])

        # 3.3 specific
        else:
            # this is gross but I filed a bug...
            # build our own json from the output.
            all_pods = json.loads(results['results'])['items']
            if all_pods is None:
                all_pods = []

        return all_pods

    def list_pods(self):
        ''' run oadm manage-node --list-pods'''
        _nodes = self.config.config_options['node']['value']
        _selector = self.config.config_options['selector']['value']
        _pod_selector = self.config.config_options['pod_selector']['value']

        if not _nodes:
            _nodes = self.get_nodes(selector=_selector)
        else:
            _nodes = [{'name': name} for name in _nodes]

        all_pods = {}
        for node in _nodes:
            results = self.get_pods_from_node(node['name'], pod_selector=_pod_selector)
            if isinstance(results, dict):
                return results
            all_pods[node['name']] = results

        results = {}
        results['nodes'] = all_pods
        results['returncode'] = 0
        return results

    def schedulable(self):
        '''oadm manage-node call for making nodes unschedulable'''
        nodes = self.config.config_options['node']['value']
        selector = self.config.config_options['selector']['value']

        if not nodes:
            nodes = self.get_nodes(selector=selector)
        else:
            tmp_nodes = []
            for name in nodes:
                tmp_result = self.get_nodes(name)
                if isinstance(tmp_result, dict):
                    tmp_nodes.append(tmp_result)
                    continue
                tmp_nodes.extend(self.get_nodes(name))
            nodes = tmp_nodes

        for node in nodes:
            if isinstance(node, dict) and node.has_key('returncode'):
                return {'results': nodes, 'returncode': node['returncode']}
            if isinstance(node, list) and node[0].has_key('returncode'):
                return {'results': nodes, 'returncode': node[0]['returncode']}
        # check all the nodes that were returned and verify they are:
        # node['schedulable'] == self.config.config_options['schedulable']['value']
        if any([node['schedulable'] != self.config.config_options['schedulable']['value'] for node in nodes]):

            return self._schedulable(node=self.config.config_options['node']['value'],
                                     selector=self.config.config_options['selector']['value'],
                                     schedulable=self.config.config_options['schedulable']['value'],
                                    )

        results = {}
        results['returncode'] = 0
        results['changed'] = False
        results['nodes'] = nodes

        return results


