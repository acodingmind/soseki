#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

import click
import os
import shutil


@click.group()
def cli():
    """Soseki CLI - Tools for managing Soseki applications"""
    pass


@cli.command('init')
@click.argument('app_name', required=False, default='app')
def init_command(app_name):
    """Initialize a new Soseki application with standard folder structure."""
    
    if os.path.exists(app_name):
        click.echo(f'Error: Directory "{app_name}" already exists')
        return
    
    # Get the path to the blanco_app template
    blanco_app_path = os.path.join(os.path.dirname(__file__), 'blanco_app')
    
    if not os.path.exists(blanco_app_path):
        click.echo(f'Error: Template directory not found at {blanco_app_path}')
        return
    
    # Copy the entire blanco_app directory
    try:
        shutil.copytree(blanco_app_path, app_name)
        click.echo(f'Created: {app_name}/ (from template)')
        
        # Get the parent directory where app_name is being created
        parent_dir = os.path.dirname(os.path.abspath(app_name))
        
        # Copy bin directory next to app folder
        blanco_bin_path = os.path.join(os.path.dirname(__file__), 'blanco_bin')
        bin_dest = os.path.join(parent_dir, 'bin')
        
        if os.path.exists(blanco_bin_path):
            if os.path.exists(bin_dest):
                shutil.rmtree(bin_dest)
            shutil.copytree(blanco_bin_path, bin_dest)
            click.echo(f'Created: bin/ (from template)')
        
        # Copy jup directory next to app folder
        blanco_jup_path = os.path.join(os.path.dirname(__file__), 'blanco_jup')
        jup_dest = os.path.join(parent_dir, 'jup')
        
        if os.path.exists(blanco_jup_path):
            if os.path.exists(jup_dest):
                shutil.rmtree(jup_dest)
            shutil.copytree(blanco_jup_path, jup_dest)
            click.echo(f'Created: jup/ (from template)')
        
        # List created structure
        for root, dirs, files in os.walk(app_name):
            level = root.replace(app_name, '').count(os.sep)
            indent = ' ' * 2 * level
            click.echo(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                click.echo(f'{subindent}{file}')
        
        click.echo(f'\nSuccessfully initialized Soseki application in "{app_name}/"')
        click.echo(f'\nNext steps:')
        click.echo(f'  # Edit cfg/lite.yaml with your settings')
        click.echo(f'  ./bin/run_app.sh')
        
    except Exception as e:
        click.echo(f'Error: Failed to create application: {e}')


if __name__ == '__main__':
    cli()
