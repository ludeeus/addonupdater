"""Update dependecies for add-ons in the community add-on project."""
import requests
from alpinepkgs.packages import get_package
from github import Github

COMMIT_MSG = ':arrow_up: Upgrades {} to version {}'
REPO = "{}/{}"
ORG = 'hassio-addons'


class AddonUpdater():
    """Class for addon updater."""

    def __init__(self, token, name, repo=None, test=False):
        """Initilalize."""
        self.name = name
        self.repo = repo
        self.test = test
        self.github = Github(token)

    def update_addon(self):
        """Run through updates for an addon."""
        print("Starting upgrade sequence for", self.name)
        if self.repo is None:
            self.repo = "addon-" + self.name

        # Add-on spesific updates
        if self.name == 'tautulli':
            self.addon_tautulli()
        elif self.name == 'matrix':
            self.addon_matrix()

        # Update APK packages
        print('Checking for apk uppdates')
        self.update_apk()

        # Update PIP packages
        print('Checking for pip uppdates')
        self.update_pip()

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
            data = get_package(pack, pkg['branch'])
            package = data['package']
            if len(data['versions']) == 1:
                version = data['versions'][0]
            else:
                version = data['x86_64']['version']  # Fallback to x86_64
            if version != pkg['version']:
                this = {'package': package,
                        'version': version,
                        'search_string': pkg['search_string']}
                updates.append(this)
            else:
                print(pack, "Allready have the newest version", version)
        if updates:
            for package in updates:
                msg = COMMIT_MSG.format(package['package'], package['version'])

                file = "{}/Dockerfile".format(self.name)
                remote_file = self.get_file_obj(file)

                search_string = package['search_string'].split('=')
                replace_string = search_string[0] + '=' + package['version']

                new_content = self.get_file_content(remote_file)
                new_content = new_content.replace(package['search_string'],
                                                  replace_string)
                self.commit(file, msg, new_content, remote_file.sha)

    def update_pip(self):
        """Get APK packages in use with updates."""
        file = "{}/Dockerfile".format(self.name)
        remote_file = self.get_file_obj(file)
        masterfile = self.get_file_content(remote_file)
        run = masterfile.split('RUN')[1].split('LABEL')[0]
        packages = []
        updates = []
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
            url = "https://pypi.org/pypi/{}/json".format(pack)
            data = requests.get(url).json()
            version = data['info']['version']
            if version != pkg['version']:
                this = {'package': pack,
                        'version': version,
                        'search_string': pkg['search_string']}
                updates.append(this)
            else:
                print(pack, "Allready have the newest version", version)
        if updates:
            for package in updates:
                msg = COMMIT_MSG.format(package['package'], package['version'])

                file = "{}/Dockerfile".format(self.name)
                remote_file = self.get_file_obj(file)

                search_string = package['search_string'].split('==')
                replace_string = search_string[0] + '==' + package['version']

                new_content = self.get_file_content(remote_file)
                new_content = new_content.replace(package['search_string'],
                                                  replace_string)
                self.commit(file, msg, new_content, remote_file.sha)

    def commit(self, path, msg, content, sha):
        """Commit changes."""
        print(msg)
        if not self.test:
            repository = "{}/{}".format(ORG, self.repo)
            ghrepo = self.github.get_repo(repository)
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
        remote_version = list(tautulli.get_releases())[0].title.split(' ')[1]
        file = "tautulli/Dockerfile"
        remote_file = self.get_file_obj(file)
        masterfile = self.get_file_content(remote_file)
        file_version = masterfile.split('ENV TAUTULLI_VERSION ')[1]
        file_version = file_version.split('\n')[0]
        file_version = file_version.replace("'", "")
        if remote_version != file_version:
            msg = COMMIT_MSG.format('Tautulli', remote_version)
            new_content = self.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.commit(file, msg, new_content, remote_file.sha)
        else:
            print("Tautulli allready have the newest version", file_version)

    def addon_matrix(self):
        """Spesial updates for matrix."""
        print("Checking riot-web version")
        riotweb = self.github.get_repo('vector-im/riot-web')
        remote_version = list(riotweb.get_releases())[0].title
        file = "matrix/Dockerfile"
        remote_file = self.get_file_obj(file)
        masterfile = self.get_file_content(remote_file)
        file_version = masterfile.split('releases/download/')[1]
        file_version = file_version.split('/')[0]
        if remote_version != file_version:
            msg = COMMIT_MSG.format('riot-web', remote_version)
            new_content = self.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.commit(file, msg, new_content, remote_file.sha)
        else:
            print("riot-web allready have the newest version", file_version)
