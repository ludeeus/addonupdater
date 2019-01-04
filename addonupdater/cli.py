"""Enable CLI."""
import click


@click.command()
@click.option('--token', '-T', help='GitHub access_token.')
@click.option('--addon', '-A', help='Addon name.')
@click.option('--repo', '-R', default=None, help='Addon repo.')
@click.option('--test', is_flag=True, help="Test run, will not commit.")
@click.option('--verbose', is_flag=True, help="Print more stuff.")
@click.option('--release', default=None, help="Publish a release.")
@click.option('--skip_apk', default=None, help="Skip apk updates.")
@click.option('--skip_pip', default=None, help="Skip pip updates.")
@click.option('--skip_custom', default=None, help="Skip custom updates.")
def cli(token, addon, repo, test, verbose, release,
        skip_apk, skip_pip, skip_custom):
    """CLI for this package."""
    from addonupdater.updater import AddonUpdater
    updater = AddonUpdater(token, addon, repo, test, verbose, release,
                           skip_apk, skip_pip, skip_custom)
    updater.update_addon()


cli()  # pylint: disable=E1120
