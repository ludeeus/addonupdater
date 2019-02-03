"""Update dependecies for add-ons in the community add-on project."""
from github import Github
from repoupdater.updater import RepoUpdater

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

    def __init__(
            self, token, name, repo=None, test=False, verbose=False,
            skip_apk=False, skip_pip=False, skip_custom=False, org=None,
            pull_request=False, apk_version=3.9):
        """Initilalize."""
        self.name = name
        self.repo = repo
        if repo is None:
            self.repo = "addon-" + name
        self.test = test
        self.token = token
        self.pull_request = pull_request
        self.verbose = verbose
        self.apk_version = apk_version
        self.skip_apk = skip_apk
        self.skip_pip = skip_pip
        self.org = ORG if org is None else org
        self.skip_custom = skip_custom
        self.github = Github(token)
        self.repoupdater = RepoUpdater(
            token=self.token, repo="{}/{}".format(self.org, self.repo),
            apk=True if not self.skip_apk else False,
            pip=True if not self.skip_pip else False, test=self.test,
            verbose=self.verbose, docker_path=self.name,
            python_req_path=self.name, pull_request=self.pull_request,
            apk_version=self.apk_version)

    def update_addon(self):
        """Run through updates for an addon."""
        if self.verbose:
            print("Addon name", self.name)
            print("Addon repo", self.repo)
            print("GitHub org", self.org)

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
            self.repoupdater.update_apk()

        if not self.skip_pip:
            # Update PIP packages
            print('Checking for pip uppdates')
            self.repoupdater.update_pip()

    def get_file_obj(self, file):
        """Return the file object."""
        repository = "{}/{}".format(self.org, self.repo)
        ghrepo = self.github.get_repo(repository)
        obj = ghrepo.get_contents(file)
        return obj

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
        masterfile = self.repoupdater.get_file_content(remote_file)
        file_version = masterfile.split('ENV TAUTULLI_VERSION ')[1]
        file_version = file_version.split('\n')[0]
        file_version = file_version.replace("'", "")
        if self.verbose:
            print("Current version", file_version)
            print("Available version", remote_version)
        if remote_version != file_version:
            msg = COMMIT_MSG.format('Tautulli', remote_version)
            new_content = self.repoupdater.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.repoupdater.commit(file, msg, new_content, remote_file.sha)
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
        masterfile = self.repoupdater.get_file_content(remote_file)
        file_version = masterfile.split('releases/download/')[1]
        file_version = file_version.split('/')[0]
        if self.verbose:
            print("Current version", file_version)
            print("Available version", remote_version)
        if remote_version != file_version:
            msg = COMMIT_MSG.format('riot-web', remote_version)
            new_content = self.repoupdater.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.repoupdater.commit(file, msg, new_content, remote_file.sha)
        else:
            print("riot-web already have the newest version", file_version)

    def addon_phlex(self):
        """Spesial updates for Phlex."""
        print("Checking phlex version")
        repo = self.github.get_repo('d8ahazard/Phlex')
        remote_version = list(repo.get_commits())[0].sha
        file = "{}/Dockerfile".format(self.name)
        remote_file = self.get_file_obj(file)
        masterfile = self.repoupdater.get_file_content(remote_file)
        file_version = masterfile.split('Phlex/archive/')[1]
        file_version = file_version.split('.zip')[0]
        if self.verbose:
            print("Current version", file_version)
            print("Available version", remote_version)
        if remote_version != file_version:
            msg = COMMIT_MSG.format('Phlex', remote_version)
            new_content = self.repoupdater.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.repoupdater.commit(file, msg, new_content, remote_file.sha)
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
        masterfile = self.repoupdater.get_file_content(remote_file)
        file_version = masterfile.split('ENV MM_VERSION = ')[1]
        file_version = file_version.split('\n')[0]
        file_version = file_version.replace('"', "")
        if self.verbose:
            print("Current version", file_version)
            print("Available version", remote_version)
        if remote_version != file_version:
            msg = COMMIT_MSG.format('Magicmirror', remote_version)
            new_content = self.repoupdater.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.repoupdater.commit(file, msg, new_content, remote_file.sha)
        else:
            print("Magicmirror already have the newest version", file_version)

    def addon_mqtt(self):
        """Spesial updates for Mqtt."""
        print("Checking hivemq-mqtt-web-client version")
        repo = self.github.get_repo('hivemq/hivemq-mqtt-web-client')
        remote_version = list(repo.get_commits())[0].sha
        file = "{}/Dockerfile".format(self.name)
        remote_file = self.get_file_obj(file)
        masterfile = self.repoupdater.get_file_content(remote_file)
        file_version = masterfile.split('client/archive/')[1]
        file_version = file_version.split('.zip')[0]
        if self.verbose:
            print("Current version", file_version)
            print("Available version", remote_version)
        if remote_version != file_version:
            msg = COMMIT_MSG.format('Hivemq-mqtt-web-client', remote_version)
            new_content = self.repoupdater.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.repoupdater.commit(file, msg, new_content, remote_file.sha)
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
        masterfile = self.repoupdater.get_file_content(remote_file)
        file_version = masterfile.split('clone --branch ')[1]
        file_version = file_version.split(' --depth')[0]
        file_version = file_version.replace('"', '')
        if self.verbose:
            print("Current version", file_version)
            print("Available version", remote_version)
        if remote_version != file_version:
            msg = COMMIT_MSG.format('Home-panel-api', remote_version)
            new_content = self.repoupdater.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.repoupdater.commit(file, msg, new_content, remote_file.sha)
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
        masterfile = self.repoupdater.get_file_content(remote_file)
        file_version = masterfile.split('releases/download/')[1]
        file_version = file_version.split('/')[0]
        if self.verbose:
            print("Current version", file_version)
            print("Available version", remote_version)
        if remote_version != file_version:
            msg = COMMIT_MSG.format('Home-panel', remote_version)
            new_content = self.repoupdater.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.repoupdater.commit(file, msg, new_content, remote_file.sha)
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
        masterfile = self.repoupdater.get_file_content(remote_file)
        file_version = masterfile.split('releases/download/')[1]
        file_version = file_version.split('/')[0]
        if self.verbose:
            print("Current version", file_version)
            print("Available version", remote_version)
        if remote_version != file_version:
            msg = COMMIT_MSG.format('hassio-cli', remote_version)
            new_content = self.repoupdater.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.repoupdater.commit(file, msg, new_content, remote_file.sha)
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
        masterfile = self.repoupdater.get_file_content(remote_file)
        file_version = masterfile.split('clone --branch ')[1]
        file_version = file_version.split(' --depth')[0]
        file_version = file_version.replace('"', '')
        if self.verbose:
            print("Current version", file_version)
            print("Available version", remote_version)
        if remote_version != file_version:
            msg = COMMIT_MSG.format('ttyd', remote_version)
            new_content = self.repoupdater.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.repoupdater.commit(file, msg, new_content, remote_file.sha)
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
        masterfile = self.repoupdater.get_file_content(remote_file)
        file_version = masterfile.split('--branch ')[1]
        file_version = file_version.split(' --depth')[0]
        if self.verbose:
            print("Current version", file_version)
            print("Available version", remote_version)
        if remote_version != file_version:
            msg = COMMIT_MSG.format('TasmoAdmin', remote_version)
            new_content = self.repoupdater.get_file_content(remote_file)
            new_content = new_content.replace(file_version, remote_version)
            self.repoupdater.commit(file, msg, new_content, remote_file.sha)
        else:
            print("TasmoAdmin already have the newest version", file_version)
