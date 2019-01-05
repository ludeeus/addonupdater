# addonupdater [![Build Status](https://travis-ci.com/ludeeus/addonupdater.svg?branch=master)](https://travis-ci.com/ludeeus/addonupdater)

_Update dependencies in Community add-ons._  
**NB!: This package is intended only for maintainers of the community add-ons project.**

## Install

**Require Python version 3.5.3+**

```bash
pip install addonupdater
```

### Example

```bash
addonupdater --token AAAAAAAAAAAAAAAAAAAAA --addon sqlite-web --test
Starting upgrade sequence for sqlite-web
Checking for apk uppdates
g++ Allready have the newest version 6.4.0-r9
gcc Allready have the newest version 6.4.0-r9
make Allready have the newest version 4.2.1-r2
python3-dev Allready have the newest version 3.6.6-r0
apache2-utils Allready have the newest version 2.4.35-r0
nginx Allready have the newest version 1.14.2-r0
python3 Allready have the newest version 3.6.6-r0
cython Allready have the newest version 0.28.2-r0
Checking for pip uppdates
flask Allready have the newest version 1.0.2
sqlite-web Allready have the newest version 0.3.5
:arrow_up: Upgrades peewee to version 3.8.0
Test was enabled, skipping commit
:arrow_up: Upgrades datasette to version 0.26
Test was enabled, skipping commit
```

#### CLI options

param | alias | description
-- | -- | --
`--token` | `-T` | An GitHub Access token with `repo` permissions.
`--addon` | `-A` | Name of the add-on, this has to match the dir that contains the `Dockerfile`.
`--repo` | `-R` | Name of the repo for the add-on, this is optional and defaults to `addon-ADDONNAME`.
`--test` | `None` | If this flag is used commits will be omitted.
`--verbose` | `None` | Print more stuff to the console.
`--release` | `None` | Creates a new release this argument require release version eg. `v1.0.3`.
`--skip_apk` | `None` | Skip apk updates.
`--skip_custom` | `None` | Skip custom updates.
`--skip_pip` | `None` | Skip pip updates.
`--org` | `None` | Specify GitHub org, defaults to 'hassio-addons'.
`-pull_request` | `-PR` | Create a PR instead of pushing directly to master.

***

[![BuyMeCoffee](https://camo.githubusercontent.com/cd005dca0ef55d7725912ec03a936d3a7c8de5b5/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f6275792532306d6525323061253230636f666665652d646f6e6174652d79656c6c6f772e737667)](https://www.buymeacoffee.com/ludeeus)