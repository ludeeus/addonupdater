"""Enable CLI."""
import click


@click.command()
@click.option('--token', '-T', help='GitHub access_token.')
@click.option('--addon', '-A', help='Addon name.')
@click.option('--repo', '-R', default=None, help='Addon repo.')
@click.option('--test', is_flag=True, help="Test run, will not commit.")
@click.option('--verbose', is_flag=True, help="Print more stuff.")
@click.option('--release', default=None, help="Publish a release.")
@click.option('--org', default=None, help="Specify GitHub org.")
@click.option('--skip_apk', is_flag=True, help="Skip apk updates.")
@click.option('--skip_pip', is_flag=True, help="Skip pip updates.")
@click.option('--skip_custom', is_flag=True, help="Skip custom updates.")
@click.option('--pull_request', '-PR', is_flag=True, help="Create a PR instead"
              "of commiting to master.")
def cli(token, addon, repo, test, verbose, release,
        skip_apk, skip_pip, skip_custom, org, pull_request):
    """CLI for this package."""
    from addonupdater.updater import AddonUpdater
    updater = AddonUpdater(token, addon, repo, test, verbose, release,
                           skip_apk, skip_pip, skip_custom, org, pull_request)
    updater.update_addon()


cli()  # pylint: disable=E1120
