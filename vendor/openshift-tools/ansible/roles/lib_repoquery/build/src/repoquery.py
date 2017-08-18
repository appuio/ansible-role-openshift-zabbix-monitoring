# pylint: skip-file

class Repoquery(RepoqueryCLI):
    ''' Class to wrap the repoquery
    '''
    # pylint: disable=too-many-arguments
    def __init__(self,
                 name,
                 query_type,
                 show_duplicates,
                 match_version,
                 verbose
                ):
        ''' Constructor for YumList '''
        super(Repoquery, self).__init__(None)
        self.name = name
        self.query_type = query_type
        self.show_duplicates = show_duplicates
        self.match_version = match_version
        self.verbose = verbose

        if self.match_version:
            self.show_duplicates = True

        self.query_format = "%{version}|%{release}|%{arch}|%{repo}|%{version}-%{release}"

    def build_cmd(self):
        ''' build the repoquery cmd options '''

        repo_cmd = []

        repo_cmd.append("--pkgnarrow=" + self.query_type)
        repo_cmd.append("--queryformat=" + self.query_format)

        if self.show_duplicates:
            repo_cmd.append('--show-duplicates')

        repo_cmd.append(self.name)

        return repo_cmd

    @staticmethod
    def process_versions(query_output):
        ''' format the package data into something that can be presented '''

        version_dict = defaultdict(dict)

        for version in query_output.split('\n'):
            pkg_info = version.split("|")

            pkg_version = {}
            pkg_version['version'] = pkg_info[0]
            pkg_version['release'] = pkg_info[1]
            pkg_version['arch'] = pkg_info[2]
            pkg_version['repo'] = pkg_info[3]
            pkg_version['version_release'] = pkg_info[4]

            version_dict[pkg_info[4]] = pkg_version

        return version_dict

    def format_versions(self, formatted_versions):
        ''' Gather and present the versions of each package '''

        versions_dict = {}
        versions_dict['available_versions_full'] = formatted_versions.keys()

        # set the match version, if called
        if self.match_version:
            versions_dict['matched_versions_full'] = []
            versions_dict['requested_match_version'] = self.match_version
            versions_dict['matched_versions'] = []

        # get the "full version (version - release)
        versions_dict['available_versions_full'].sort(key=LooseVersion)
        versions_dict['latest_full'] = versions_dict['available_versions_full'][-1]

        # get the "short version (version)
        versions_dict['available_versions'] = []
        for version in versions_dict['available_versions_full']:
            versions_dict['available_versions'].append(formatted_versions[version]['version'])

            if self.match_version:
                if version.startswith(self.match_version):
                    versions_dict['matched_versions_full'].append(version)
                    versions_dict['matched_versions'].append(formatted_versions[version]['version'])

        versions_dict['available_versions'].sort(key=LooseVersion)
        versions_dict['latest'] = versions_dict['available_versions'][-1]

        # finish up the matched version
        if self.match_version:
            if versions_dict['matched_versions_full']:
                versions_dict['matched_version_found'] = True
                versions_dict['matched_versions'].sort(key=LooseVersion)
                versions_dict['matched_version_latest'] = versions_dict['matched_versions'][-1]
                versions_dict['matched_version_full_latest'] = versions_dict['matched_versions_full'][-1]
            else:
                versions_dict['matched_version_found'] = False
                versions_dict['matched_versions'] = []
                versions_dict['matched_version_latest'] = ""
                versions_dict['matched_version_full_latest'] = ""

        return versions_dict

    def repoquery(self):
        '''perform a repoquery '''

        repoquery_cmd = self.build_cmd()

        rval = self._repoquery_cmd(repoquery_cmd, True, 'raw')

        # check to see if there are actual results
        if rval['results']:
            processed_versions = Repoquery.process_versions(rval['results'].strip())
            formatted_versions = self.format_versions(processed_versions)

            rval['package_found'] = True
            rval['versions'] = formatted_versions
            rval['package_name'] = self.name

            if self.verbose:
                rval['raw_versions'] = processed_versions
            else:
                del rval['results']

        # No packages found
        else:
            rval['package_found'] = False

        return rval
