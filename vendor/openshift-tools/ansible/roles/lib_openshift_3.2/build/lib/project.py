# pylint: skip-file

# pylint: disable=too-many-instance-attributes
class ProjectConfig(OpenShiftCLIConfig):
    ''' project config object '''
    def __init__(self, rname, namespace, kubeconfig, project_options):
        super(ProjectConfig, self).__init__(rname, rname, kubeconfig, project_options)

# pylint: disable=too-many-public-methods
class Project(Yedit):
    ''' Class to wrap the oc command line tools '''
    annotations_path = "metadata.annotations"
    kind = 'Service'
    annotation_prefix = 'openshift.io/'

    def __init__(self, content):
        '''Service constructor'''
        super(Project, self).__init__(content=content)

    def get_annotations(self):
        ''' get a list of ports '''
        return self.get(Project.annotations_path) or {}

    def add_annotations(self, inc_annos):
        ''' add a port object to the ports list '''
        if not isinstance(inc_annos, list):
            inc_annos = [inc_annos]

        annos = self.get_annotations()
        if not annos:
            self.put(Project.annotations_path, inc_annos)
        else:
            for anno in inc_annos:
                for key, value in anno.items():
                    annos[key] = value

        return True

    def find_annotation(self, key):
        ''' find a specific port '''
        annotations = self.get_annotations()
        for anno in annotations:
            if Project.annotation_prefix + key == anno:
                return annotations[anno]

        return None

    def delete_annotation(self, inc_anno_keys):
        ''' remove an annotation from a project'''
        if not isinstance(inc_anno_keys, list):
            inc_anno_keys = [inc_anno_keys]

        annos = self.get(Project.annotations_path) or {}

        if not annos:
            return True

        removed = False
        for inc_anno in inc_anno_keys:
            anno = self.find_annotation(inc_anno)
            if anno:
                del annos[Project.annotation_prefix + anno]
                removed = True

        return removed

    def update_annotation(self, key, value):
        ''' remove an annotation from a project'''
        annos = self.get(Project.annotations_path) or {}

        if not annos:
            return True

        updated = False
        anno = self.find_annotation(key)
        if anno:
            annos[Project.annotation_prefix + key] = value
            updated = True

        else:
            self.add_annotations({Project.annotation_prefix + key: value})

        return updated
