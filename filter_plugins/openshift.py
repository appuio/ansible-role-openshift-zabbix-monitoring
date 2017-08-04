__metaclass__ = type

def select_by_label(hosts, label, value, hostvars):
  return [host for host in hosts if hostvars[host].get('openshift_node_labels', {}).get(label, '') == value]

class FilterModule(object):

    def filters(self):
        filters = {
            'select_by_label': select_by_label,
        }

        return filters
