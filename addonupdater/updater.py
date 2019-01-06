"""Update dependecies for add-ons in the community add-on project."""
import json
import requests
from alpinepkgs.packages import get_package
from github import Github
from github.GithubException import UnknownObjectException

COMMIT_MSG = ':arrow_up: Upgrades {} to version {}'
REPO = "{}/{}"
NEW_BRANCH = "update-{}-to-version-{}"
ORG = 'hassio-addons'
PR_BODY = """
# Proposed Changes

This PR will upgrade `{package}` to version `{version}`.

This PR was created automatically, please check the "Files changed" tab
before merging!

***

This PR was created with [addonupdater][addonupdater] :tada:

[addonupdater]: https://pypi.org/project/addonupdater/
"""


class AddonUpdater():
    """Class for addon updater."""

    def __init__(self, token, name, repo=None, test=False,
                 verbose=False, release=None, skip_apk=False, skip_pip=False,
                 skip_custom=False, org=None, pull_request=False, fork=False,
                 skip_base=False):
        """Initilalize."""
        self.name = name
        self.repo = repo
        self.test = test
        self.token = token
        self.fork = fork
        self.pull_request = pull_request
        self.verbose = verbose
        self.release = release
        self.skip_apk = skip_apk
        self.skip_pip = skip_pip
        self.skip_base = skip_base
        self.org = ORG if org is None else org
        self.skip_custom = skip_custom
        self.github = Github(token)

    def update_addon(self):
        """Run through updates for an addon."""
        if self.repo is None:
            self.repo = "addon-" + self.name

        if self.verbose:
            print("Addon name", self.name)
            print("Addon repo", self.repo)
            print("GitHub org", self.org)

        if self.release is not None:
            self.create_release()
        else:
            print("Starting upgrade sequence for", self.name)

            if not self.skip_base:
                # Base image updates
                print('Checking for base image uppdates')
                self.base_image()

            if not self.skip_custom:
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
                elif self.name == 'ssh':
                    self.addon_ssh()
                elif self.name == 'tasmoadmin':
                    self.addon_tasmoadmin()

            if not self.skip_apk:
                # Update APK packages
                print('Checking for apk uppdates')
                self.update_apk()

            if not self.skip_pip:
                # Update PIP packages
                print('Checking for pip uppdates')
                self.update_pip()

    def create_release(self):
        """Create and publish a release."""
        print("Creating release for", self.name, "with version", self.release)
        repository = "{}/{}".format(self.org, self.repo)
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
                        pkg = pkg.split('\n')[0]
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
                            version = pkg.split('=')[1].split()[0]

                            this = {'package': package,
                                    'branch': branch,
                                    'version': version,
                                    'search_string': pkg}
                            packages.append(this)

        for pkg in packages:
            if 'apkadd--no-cache' in str(pkg['package']):
                pack = str(pkg['package']).replace('apkadd--no-cache', "")
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
                print("Available version", version.split()[0])
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
                if 'apkadd--no-cache' in package['search_string']:
                    string = package['search_string']
                    string = string.replace('apkadd--no-cache', "")
                    package['search_string'] = string
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
            repo = self.github.get_repo("{}/{}".format(self.org, self.repo))
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
                print("Available version", version.split()[0])
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
            repository = "{}/{}".format(self.org, self.repo)
            ghrepo = self.github.get_repo(repository)
            if self.pull_request:
                print("Creating new PR for", self.repo)
                info = msg.split()
                package = info[2]
                version = info[-1]
                title = msg[11:]
                body = PR_BODY.format(package=package, version=version)
                if self.fork:
                    user = self.github.get_user()
                    fork_branch = NEW_BRANCH.format(package, version)
                    branch = user.login + ':' + fork_branch
                    print("Forking " + self.org + '/' +
                          self.repo + " to " + branch)
                    user.create_fork(ghrepo)
                    fork = self.github.get_repo(user.login + '/' + self.repo)
                    ref = 'refs/heads/' + fork_branch
                    source = fork.get_branch('master')
                    if self.verbose:
                        print("Forked to user", user.login)
                        print("Repository", user.login + '/' + self.repo)
                        print("Msg", msg)
                        print("Branch", branch)
                    print(fork.create_git_ref(ref=ref, sha=source.commit.sha))
                    print(fork.update_file(path, msg, content, sha,
                                           fork_branch))
                else:
                    branch = NEW_BRANCH.format(package, version)
                    source = ghrepo.get_branch('master')
                    if self.verbose:
                        print("Org", self.org)
                        print("Repository", repository)
                        print("Msg", msg)
                        print("Branch", branch)
                    print(ghrepo.create_git_ref(ref=ref,
                                                sha=source.commit.sha))
                    print(ghrepo.update_file(path, msg, content, sha, branch))
                print(ghrepo.create_pull(title, body, 'master', branch))
            else:
                if self.verbose:
                    print("Org", self.org)
                    print("Repository", repository)
                    print("Path", path)
                    print("Msg", msg)
                    print("Sha", sha)
                print("Creating new commit in master for", self.repo)
                print(ghrepo.update_file(path, msg, content, sha))
        else:
            print("Test was enabled, skipping PR/commit")

    def get_file_obj(self, file):
        """Return the file object."""
        repository = "{}/{}".format(self.org, self.repo)
        ghrepo = self.github.get_repo(repository)
        obj = ghrepo.get_contents(file)
        return obj

    def get_file_content(self, obj):
        """Return the content of the file."""
        return obj.decoded_content.decode()

    def base_image(self):
        """Update for base image."""
        dockerfile = "{}/Dockerfile".format(self.name)
        buildfile = "{}/build.json".format(self.name)

        remote_dockerfile = self.get_file_obj(dockerfile)
        dockerfile_content = self.get_file_content(remote_dockerfile)

        remote_buildfile = self.get_file_obj(buildfile)
        buildfile_content = self.get_file_content(remote_buildfile)

        used_file = dockerfile_content.split('BUILD_FROM=hassioaddons/')[1]
        used_file = used_file.split('\n')[0]

        base = used_file.split(':')[1]
        version = used_file.split(':')[1]

        if base == 'ubuntu-base':
            repo = self.github.get_repo('hassio-addons/addon-ubuntu-base')
        else:
            repo = self.github.get_repo('hassio-addons/addon-base')

        remote_version = list(repo.get_releases())[0].tag_name[1:]

        if self.verbose:
            print("Current version", version)
            print("Available version", remote_version)

        if remote_version != version:
            msg = COMMIT_MSG.format('add-on base image', remote_version)

            new_dockerfile = dockerfile_content.replace(version,
                                                        remote_version)
            self.commit(dockerfile, msg, new_dockerfile, remote_dockerfile.sha)

            current_buildfile = json.loads(buildfile_content)
            new_buildfile = {}
            for item in current_buildfile:
                new_buildfile[item] = {}
                for subitem in current_buildfile[item]:
                    value = current_buildfile[item][subitem]
                    value = value.replace(version, remote_version)
                    new_buildfile[item][subitem] = value
            new_buildfile = json.dumps(new_buildfile, indent=4, sort_keys=True)
            self.commit(buildfile, msg, new_buildfile, remote_buildfile.sha)
        else:
            print("Base image already have the newest version", version)

    def addon_tautulli(self):
        """Spesial updates for tautulli."""
        print("Checking Tautulli version")
        repo = self.github.get_repo('Tautulli/Tautulli')
        releases = list(repo.get_releases())
        index = 0
        while True:
            remote_version = releases[index].tag_name
            if 'b' in remote_version:
                index = index + 1
            else:
                break
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
        repo = self.github.get_repo('vector-im/riot-web')
        releases = list(repo.get_releases())
        index = 0
        while True:
            remote_version = releases[index].tag_name
            if 'b' in remote_version:
                index = index + 1
            else:
                break
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
        repo = self.github.get_repo('d8ahazard/Phlex')
        remote_version = list(repo.get_commits())[0].sha
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
        repo = self.github.get_repo('MichMich/MagicMirror')
        releases = list(repo.get_releases())
        index = 0
        while True:
            remote_version = releases[index].tag_name
            if 'b' in remote_version:
                index = index + 1
            else:
                break
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
        repo = self.github.get_repo('hivemq/hivemq-mqtt-web-client')
        remote_version = list(repo.get_commits())[0].sha
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
        repo = self.github.get_repo('timmo001/home-panel-api')
        releases = list(repo.get_releases())
        index = 0
        while True:
            remote_version = releases[index].tag_name
            if 'b' in remote_version:
                index = index + 1
            else:
                break
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
        repo = self.github.get_repo('timmo001/home-panel')
        releases = list(repo.get_releases())
        index = 0
        while True:
            remote_version = releases[index].tag_name
            if 'b' in remote_version:
                index = index + 1
            else:
                break
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

    def addon_ssh(self):
        """Spesial updates for SSH."""
        print("Checking hassio-cli version")
        repo = self.github.get_repo('home-assistant/hassio-cli')
        releases = list(repo.get_releases())
        index = 0
        while True:
            remote_version = releases[index].tag_name
            if 'b' in remote_version:
                index = index + 1
            else:
                break
        file = "{}/Dockerfile".format(self.name)
        remote_file = self.get_file_obj(file)
        masterfile = self.get_file_content(remote_file)
        file_version = masterfile.split('releases/download/')[1]
        file_version = file_version.split('/')[0]
        if self.verbose:
            print("Current version", file_version)
            print("Available version", remote_version)
        if remote_version != file_version:
            msg = COMMIT_MSG.format('hassio-cli', remote_version)
            new_content = self.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.commit(file, msg, new_content, remote_file.sha)
        else:
            print("hassio-cli already have the newest version", file_version)

        print("Checking ttyd version")
        repo = self.github.get_repo('tsl0922/ttyd')
        releases = list(repo.get_releases())
        index = 0
        while True:
            remote_version = releases[index].tag_name
            if 'b' in remote_version:
                index = index + 1
            else:
                break
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
            msg = COMMIT_MSG.format('ttyd', remote_version)
            new_content = self.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.commit(file, msg, new_content, remote_file.sha)
        else:
            print("ttyd already have the newest version", file_version)

    def addon_tasmoadmin(self):
        """Spesial updates for tasmoadmin."""
        print("Checking TasmoAdmin version")
        repo = self.github.get_repo('reloxx13/TasmoAdmin')
        releases = list(repo.get_releases())
        index = 0
        while True:
            remote_version = releases[index].tag_name
            if 'b' in remote_version:
                index = index + 1
            else:
                break
        file = "{}/Dockerfile".format(self.name)
        remote_file = self.get_file_obj(file)
        masterfile = self.get_file_content(remote_file)
        file_version = masterfile.split('--branch ')[1]
        file_version = file_version.split(' --depth')[0]
        if self.verbose:
            print("Current version", file_version)
            print("Available version", remote_version)
        if remote_version != file_version:
            msg = COMMIT_MSG.format('TasmoAdmin', remote_version)
            new_content = self.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.commit(file, msg, new_content, remote_file.sha)
        else:
            print("TasmoAdmin already have the newest version", file_version)
