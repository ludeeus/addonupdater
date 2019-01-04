"""Update dependecies for add-ons in the community add-on project."""
import requests
from alpinepkgs.packages import get_package
from github import Github
from github.GithubException import UnknownObjectException

COMMIT_MSG = ':arrow_up: Upgrades {} to version {}'
REPO = "{}/{}"
ORG = 'hassio-addons'


class AddonUpdater():
    """Class for addon updater."""

    def __init__(self, token, name, repo=None, test=False,
                 verbose=False, release=None):
        """Initilalize."""
        self.name = name
        self.repo = repo
        self.test = test
        self.token = token
        self.verbose = verbose
        self.release = release
        self.github = Github(token)

    def update_addon(self):
        """Run through updates for an addon."""
        if self.repo is None:
            self.repo = "addon-" + self.name

        if self.verbose:
            print("Addon name", self.name)
            print("Addon repo", self.repo)
            print("GitHub token", self.token)

        if self.release is not None:
            self.create_release()
        else:
            print("Starting upgrade sequence for", self.name)

            # Add-on spesific updates
            if self.name == 'tautulli':
                self.addon_tautulli()
            elif self.name == 'matrix':
                self.addon_matrix()
            elif self.name == 'phlex':
                self.addon_phlex()
            elif self.name == 'magicmirror':
                self.addon_magicmirror()
            elif self.name == 'mqtt':
                self.addon_mqtt()
            elif self.name == 'home-panel':
                self.addon_home_panel()

            # Update APK packages
            print('Checking for apk uppdates')
            self.update_apk()

            # Update PIP packages
            print('Checking for pip uppdates')
            self.update_pip()

    def create_release(self):
        """Create and publish a release."""
        print("Creating release for", self.name, "with version", self.release)
        repository = "{}/{}".format(ORG, self.repo)
        repo = self.github.get_repo(repository)
        last_commit = list(repo.get_commits())[0].sha
        prev_tag = list(repo.get_tags())[0].name
        prev_tag_sha = list(repo.get_tags())[0].commit.sha
        body = '## Changes\n\n'
        for commit in list(repo.get_commits()):
            if commit.sha == prev_tag_sha:
                break

            body = body + '- ' + repo.get_git_commit(commit.sha).message + '\n'

        url = "https://github.com/hassio-addons/"
        url = url + self.repo + "/compare/" + prev_tag + "..." + self.release
        body = body + "\n\n[Changelog](" + url + ")"
        if self.verbose:
            print("Version", self.release)
            print("Body")
            print(body)
            print("Last commit", last_commit)

        if not self.test:
            repo.create_git_tag_and_release(self.release,
                                            '',
                                            self.release,
                                            body,
                                            last_commit,
                                            '')
        else:
            print("Test was enabled, skipping release")

    def update_apk(self):
        """Get APK packages in use with updates."""
        file = "{}/Dockerfile".format(self.name)
        remote_file = self.get_file_obj(file)
        masterfile = self.get_file_content(remote_file)
        run = masterfile.split('RUN')[1].split('LABEL')[0]
        packages = []
        updates = []
        if 'apk' in run:
            cmds = run.split('&&')
            for cmd in cmds:
                if 'apk add' in cmd:
                    all_apk_lines = cmd.replace(' ', '').split('\\\n')
                    for pkg in all_apk_lines:
                        if '=' in pkg:
                            if '@legacy' in pkg:
                                package = pkg.split('@')[0]
                                branch = 'v3.7'
                            elif '@edge' in pkg:
                                package = pkg.split('@')[0]
                                branch = 'edge'
                            else:
                                package = pkg.split('=')[0]
                                branch = 'v3.8'
                            version = pkg.split('=')[1]

                            this = {'package': package,
                                    'branch': branch,
                                    'version': version,
                                    'search_string': pkg}
                            packages.append(this)

        for pkg in packages:
            if 'apkadd--no-cache' in pkg['package']:
                pack = pkg['package'].replace('apkadd--no-cache', "")
            else:
                pack = pkg['package']
            if self.verbose:
                print("Checking versions for", pack)
            data = get_package(pack, pkg['branch'])
            package = data['package']
            if len(data['versions']) == 1:
                version = data['versions'][0]
            else:
                version = data['x86_64']['version']  # Fallback to x86_64
            if self.verbose:
                print("Current version", pkg['version'])
                print("Available version", pkg['version'])
            if version.split()[0] != pkg['version'].split()[0]:
                this = {'package': package,
                        'version': version,
                        'search_string': pkg['search_string']}
                updates.append(this)
            else:
                print(pack, "Already have the newest version", version)
        if updates:
            for package in updates:
                msg = COMMIT_MSG.format(package['package'], package['version'])

                file = "{}/Dockerfile".format(self.name)
                remote_file = self.get_file_obj(file)

                search_string = package['search_string'].split('=')
                replace_string = search_string[0] + '=' + package['version']
                find_string = package['search_string'].split()[0]

                if self.verbose:
                    print("Find string '" + find_string + "'")
                    print("Replace with '" + replace_string + "'")

                new_content = self.get_file_content(remote_file)
                new_content = new_content.replace(find_string, replace_string)
                self.commit(file, msg, new_content, remote_file.sha)

    def update_pip(self):
        """Get APK packages in use with updates."""
        file = "{}/requirements.txt".format(self.name)
        packages = []
        updates = []
        try:
            repo = self.github.get_repo("{}/{}".format(ORG, self.repo))
            repo.get_contents(file)
            has_requirements = True
        except UnknownObjectException:
            has_requirements = False
        if has_requirements:
            if self.verbose:
                print("This repo has a requirements.txt file")
            remote_file = self.get_file_obj(file)
            masterfile = self.get_file_content(remote_file)
            lines = masterfile.split('\n')
            if self.verbose:
                print("Lines", lines)
            for line in lines:
                if line != '':
                    if self.verbose:
                        print("Line", line)
                    package = line.split('==')[0]
                    version = line.split('==')[1]
                    this = {'package': package,
                            'version': version,
                            'search_string': line}
                    packages.append(this)
        else:
            file = "{}/Dockerfile".format(self.name)
            remote_file = self.get_file_obj(file)
            masterfile = self.get_file_content(remote_file)
            run = masterfile.split('RUN')[1].split('LABEL')[0]
            if 'pip' in run or 'pip3' in run:
                cmds = run.split('&&')
                for cmd in cmds:
                    if 'pip install' in cmd or 'pip3 install' in cmd:
                        all_apk_lines = cmd.replace(' ', '').split('\\\n')
                        for pkg in all_apk_lines:
                            if '==' in pkg:
                                package = pkg.split('==')[0]
                                version = pkg.split('==')[1]

                                this = {'package': package,
                                        'version': version,
                                        'search_string': pkg}
                                packages.append(this)

        for pkg in packages:
            if 'pip3install--upgrade' in pkg['package']:
                pack = pkg['package'].replace('pip3install--upgrade', "")
            elif 'pipinstall--upgrade' in pkg['package']:
                pack = pkg['package'].replace('pipinstall--upgrade', "")
            elif 'pip3install' in pkg['package']:
                pack = pkg['package'].replace('pip3install', "")
            elif 'pipinstall' in pkg['package']:
                pack = pkg['package'].replace('pipinstall', "")
            else:
                pack = pkg['package']
            if self.verbose:
                print("Checking versions for", pack)
            url = "https://pypi.org/pypi/{}/json".format(pack)
            data = requests.get(url).json()
            version = data['info']['version']
            if self.verbose:
                print("Current version", pkg['version'])
                print("Available version", pkg['version'])
            if version.split()[0] != pkg['version'].split()[0]:
                this = {'package': pack,
                        'version': version,
                        'search_string': pkg['search_string']}
                updates.append(this)
            else:
                print(pack, "Already have the newest version", version)
        if updates:
            for package in updates:
                msg = COMMIT_MSG.format(package['package'], package['version'])
                remote_file = self.get_file_obj(file)

                search_string = package['search_string'].split('==')
                find_string = package['search_string'].split()[0]
                replace_string = search_string[0] + '==' + package['version']

                if self.verbose:
                    print("Find string '" + find_string + "'")
                    print("Replace with '" + replace_string + "'")

                new_content = self.get_file_content(remote_file)
                new_content = new_content.replace(find_string, replace_string)
                self.commit(file, msg, new_content, remote_file.sha)

    def commit(self, path, msg, content, sha):
        """Commit changes."""
        print(msg)
        if not self.test:
            repository = "{}/{}".format(ORG, self.repo)
            ghrepo = self.github.get_repo(repository)
            if self.verbose:
                print("Repository", repository)
                print("Path", path)
                print("Msg", msg)
                print("Sha", sha)
            print(ghrepo.update_file(path, msg, content, sha))
        else:
            print("Test was enabled, skipping commit")

    def get_file_obj(self, file):
        """Return the file object."""
        repository = "{}/{}".format(ORG, self.repo)
        ghrepo = self.github.get_repo(repository)
        obj = ghrepo.get_contents(file)
        return obj

    def get_file_content(self, obj):
        """Return the content of the file."""
        return obj.decoded_content.decode()

    def addon_tautulli(self):
        """Spesial updates for tautulli."""
        print("Checking Tautulli version")
        tautulli = self.github.get_repo('Tautulli/Tautulli')
        remote_version = list(tautulli.get_releases())[0].tag_name
        file = "{}/Dockerfile".format(self.name)
        remote_file = self.get_file_obj(file)
        masterfile = self.get_file_content(remote_file)
        file_version = masterfile.split('ENV TAUTULLI_VERSION ')[1]
        file_version = file_version.split('\n')[0]
        file_version = file_version.replace("'", "")
        if self.verbose:
            print("Current version", file_version)
            print("Available version", remote_version)
        if remote_version != file_version:
            msg = COMMIT_MSG.format('Tautulli', remote_version)
            new_content = self.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.commit(file, msg, new_content, remote_file.sha)
        else:
            print("Tautulli already have the newest version", file_version)

    def addon_matrix(self):
        """Spesial updates for matrix."""
        print("Checking riot-web version")
        riotweb = self.github.get_repo('vector-im/riot-web')
        remote_version = list(riotweb.get_releases())[0].title
        file = "{}/Dockerfile".format(self.name)
        remote_file = self.get_file_obj(file)
        masterfile = self.get_file_content(remote_file)
        file_version = masterfile.split('releases/download/')[1]
        file_version = file_version.split('/')[0]
        if self.verbose:
            print("Current version", file_version)
            print("Available version", remote_version)
        if remote_version != file_version:
            msg = COMMIT_MSG.format('riot-web', remote_version)
            new_content = self.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.commit(file, msg, new_content, remote_file.sha)
        else:
            print("riot-web already have the newest version", file_version)

    def addon_phlex(self):
        """Spesial updates for Phlex."""
        print("Checking phlex version")
        phlex = self.github.get_repo('d8ahazard/Phlex')
        remote_version = list(phlex.get_commits())[0].sha
        file = "{}/Dockerfile".format(self.name)
        remote_file = self.get_file_obj(file)
        masterfile = self.get_file_content(remote_file)
        file_version = masterfile.split('Phlex/archive/')[1]
        file_version = file_version.split('.zip')[0]
        if self.verbose:
            print("Current version", file_version)
            print("Available version", remote_version)
        if remote_version != file_version:
            msg = COMMIT_MSG.format('Phlex', remote_version)
            new_content = self.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.commit(file, msg, new_content, remote_file.sha)
        else:
            print("Phlex already have the newest version", file_version)

    def addon_magicmirror(self):
        """Spesial updates for magicmirror."""
        print("Checking Magicmirror version")
        magicmirror = self.github.get_repo('MichMich/MagicMirror')
        remote_version = list(magicmirror.get_releases())[0].tag_name
        file = "{}/Dockerfile".format(self.name)
        remote_file = self.get_file_obj(file)
        masterfile = self.get_file_content(remote_file)
        file_version = masterfile.split('ENV MM_VERSION = ')[1]
        file_version = file_version.split('\n')[0]
        file_version = file_version.replace('"', "")
        if self.verbose:
            print("Current version", file_version)
            print("Available version", remote_version)
        if remote_version != file_version:
            msg = COMMIT_MSG.format('Magicmirror', remote_version)
            new_content = self.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.commit(file, msg, new_content, remote_file.sha)
        else:
            print("Magicmirror already have the newest version", file_version)

    def addon_mqtt(self):
        """Spesial updates for Mqtt."""
        print("Checking hivemq-mqtt-web-client version")
        phlex = self.github.get_repo('hivemq/hivemq-mqtt-web-client')
        remote_version = list(phlex.get_commits())[0].sha
        file = "{}/Dockerfile".format(self.name)
        remote_file = self.get_file_obj(file)
        masterfile = self.get_file_content(remote_file)
        file_version = masterfile.split('client/archive/')[1]
        file_version = file_version.split('.zip')[0]
        if self.verbose:
            print("Current version", file_version)
            print("Available version", remote_version)
        if remote_version != file_version:
            msg = COMMIT_MSG.format('Hivemq-mqtt-web-client', remote_version)
            new_content = self.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.commit(file, msg, new_content, remote_file.sha)
        else:
            print("Hivemq-mqtt-web-client already have the newest version",
                  file_version)

    def addon_home_panel(self):
        """Spesial updates for Home-panel."""
        print("Checking home-panel-api version")
        api = self.github.get_repo('timmo001/home-panel-api')
        remote_version = list(api.get_releases())[0].tag_name
        file = "{}/Dockerfile".format(self.name)
        remote_file = self.get_file_obj(file)
        masterfile = self.get_file_content(remote_file)
        file_version = masterfile.split('clone --branch ')[1]
        file_version = file_version.split(' --depth')[0]
        file_version = file_version.replace('"', '')
        if self.verbose:
            print("Current version", file_version)
            print("Available version", remote_version)
        if remote_version != file_version:
            msg = COMMIT_MSG.format('Home-panel-api', remote_version)
            new_content = self.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.commit(file, msg, new_content, remote_file.sha)
        else:
            print("Home-panel-api already have the newest version",
                  file_version)
        print("Checking home-panel version")
        api = self.github.get_repo('timmo001/home-panel')
        remote_version = list(api.get_releases())[0].tag_name
        file = "{}/Dockerfile".format(self.name)
        remote_file = self.get_file_obj(file)
        masterfile = self.get_file_content(remote_file)
        file_version = masterfile.split('releases/download/')[1]
        file_version = file_version.split('/')[0]
        if self.verbose:
            print("Current version", file_version)
            print("Available version", remote_version)
        if remote_version != file_version:
            msg = COMMIT_MSG.format('Home-panel', remote_version)
            new_content = self.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.commit(file, msg, new_content, remote_file.sha)
        else:
            print("Home-panel already have the newest version", file_version)
