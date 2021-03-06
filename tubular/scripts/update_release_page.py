#! /usr/bin/env python3

"""
Command-line script to create or update the release page for a specific release.
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from os import path
import sys
import logging

import click
import click_log
import yaml


# Add top-level module path to sys.path before importing tubular code.
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from tubular.confluence_api import ReleasePage, publish_page, AMI, ReleaseStatus  # pylint: disable=wrong-import-position
from tubular.github_api import (  # pylint: disable=wrong-import-position
    default_expected_release_date,
)

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
LOG = logging.getLogger(__name__)

EXPECTED_RELEASE_DATE = default_expected_release_date()


@click.command()
@click.option(
    '-c', '--compare', 'ami_pairs',
    help=u"A pair of paths to AMI description yaml files.",
    type=(click.File(), click.File()),
    multiple=True
)
@click.option(
    '--confluence-url',
    help=u"The base url of the confluence instance to publish the release page to.",
    default='https://openedx.atlassian.net/wiki',
)
@click.option(
    '--user',
    help=u"The username of the confluence user to post as.",
    required=True,
)
@click.option(
    '--password',
    help=u"The password for the confluence user.",
    required=True,
)
@click.option(
    '--parent-title',
    help=u"The title of the page to publish this page as a child of.",
)
@click.option(
    '--space',
    help=u"The space to publish this page in.",
)
@click.option(
    '--title',
    help=u"The title of this page.",
)
@click.option(
    '--github-token',
    help=u"The token to use when accessing the github api.",
    required=True,
)
@click.option(
    '--jira-url',
    help=u"The base url for the JIRA instance to link JIRA tickets to.",
    default='https://openedx.atlassian.net'
)
@click.option(
    '--gocd-url',
    help=u"The url of the GoCD pipeline that build this release.",
)
@click.option(
    '--status',
    help=u"The current status of this deployment",
    required=True,
    type=click.Choice(ReleaseStatus.__members__.keys()),  # pylint: disable=no-member
)
@click.option(
    '--out-file',
    help=u"File location to export metadata that can be used to update this page.",
    type=click.File(mode='w'),
    default=sys.stdout,
)
@click.option(
    '--in-file',
    help=u"File location to import metadata from to specify a page to update.",
    type=click.File(),
)
@click_log.simple_verbosity_option(default=u'INFO')
@click_log.init()
def create_release_page(
        ami_pairs, confluence_url, user, password, parent_title,
        space, title, github_token, jira_url, gocd_url, status,
        out_file, in_file
):
    """
    Create a new release page for edxapp.
    """
    if in_file and any([parent_title, space, title]):
        raise click.BadOptionUsage(
            "Either --in-file or --parent-title/--space/--title must be specified, but not both."
        )

    if in_file:
        in_data = yaml.safe_load(in_file)
        parent_title = in_data['parent_title']
        space = in_data['space']
        title = in_data['title']

    if title is None:
        title = "{:%Y-%m-%d} Release".format(EXPECTED_RELEASE_DATE)

    if space is None:
        space = 'RELEASES'

    if parent_title is None:
        parent_title = 'LMS/Studio Release Pages'

    ami_pairs = [
        (
            AMI(**yaml.safe_load(old)),
            AMI(**yaml.safe_load(new))
        )
        for old, new in ami_pairs
    ]

    page = ReleasePage(
        github_token,
        jira_url,
        getattr(ReleaseStatus, status),
        ami_pairs,
        gocd_url=gocd_url,
    )

    publish_page(confluence_url, user, password, space, parent_title, title, page.format())

    yaml.safe_dump({
        'parent_title': parent_title,
        'space': space,
        'title': title
    }, stream=out_file)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    create_release_page()
