#! /usr/bin/env python3

"""
Command-line script to allow only AMI deployments to stage - and no other environments.
"""
from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import io
import sys
import logging
import traceback
import click
import yaml

from tubular import asgard  # pylint: disable=wrong-import-position


logging.basicConfig(stream=sys.stdout, level=logging.INFO)


@click.command()
@click.option(
    '--config_file',
    envvar='CONFIG_FILE',
    help='The config file from which to get the previous deploy information.'
)
@click.option(
    '--dry_run',
    envvar='DRY_RUN',
    help='Don\'t actually rollback.',
    is_flag=True,
    default=False
)
@click.option(
    '--out_file',
    envvar='OUT_FILE',
    help='Output file for the YAML rollback information.',
    default=None
)
def rollback(config_file, dry_run, out_file):
    """
    Roll back to an existing ASG. If the desired ASG(s) are not available to roll back (have since been deleted)
    and an AMI_ID is specified a new ASG using that AMI ID will be used.

    Configuration file input:
    ---
    current_asgs:
      loadtest-edx-edxapp:
        - loadtest-edx-edxapp-v099
      loadtest-edx-worker:
        - loadtest-edx-worker-v099
    disabled_asgs:
      loadtest-edx-edxapp:
        - loadtest-edx-edxapp-v058
        - loadtest-edx-edxapp-v059
      loadtest-edx-worker:
        - loadtest-edx-worker-v034
    ami_id: ami-a1b1c1d0

    The disabled_asgs will be enabled and the current_asgs will be disabled.
    """
    config = yaml.safe_load(io.open(config_file, 'r'))
    current_asgs = config['current_asgs']
    disabled_asgs = config['disabled_asgs']
    ami_id = config['ami_id']

    try:
        if not dry_run:
            rollback_info = asgard.rollback(current_asgs, disabled_asgs, ami_id)
        else:
            click.echo('Would have triggered a rollback of {}'.format(ami_id))
            rollback_info = {}

        if out_file:
            with io.open(out_file, 'w') as stream:
                yaml.safe_dump(rollback_info, stream, default_flow_style=False, explicit_start=True)
        else:
            print(yaml.safe_dump(rollback_info, default_flow_style=False, explicit_start=True))

    except Exception as err:  # pylint: disable=broad-except
        traceback.print_exc()
        click.secho('Error rolling back AMI: {0}.\nMessage: {1}'.format(ami_id, err), fg='red')
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    rollback()  # pylint: disable=no-value-for-parameter
