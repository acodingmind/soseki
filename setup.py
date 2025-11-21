#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist
import re
import os
import shutil

def sync_blanco_app():
    """Copy app directory to ssk/blanco_app before building."""
    app_dir = 'app'
    blanco_app_dir = 'ssk/blanco_app'
    
    if os.path.exists(app_dir):
        # Remove existing blanco_app if it exists
        if os.path.exists(blanco_app_dir):
            shutil.rmtree(blanco_app_dir)
        
        # Copy app to blanco_app, excluding templates and static
        def ignore_patterns(dir, files):
            # Ignore templates and static directories at the root level
            if dir == app_dir:
                return {'templates', 'static'}
            return set()
        
        shutil.copytree(app_dir, blanco_app_dir, ignore=ignore_patterns)
        print(f"Synced {app_dir}/ to {blanco_app_dir}/ (excluding templates and static)")
    else:
        print(f"Warning: {app_dir}/ directory not found, skipping sync")
    
    # Sync bin directory
    bin_dir = 'bin'
    blanco_bin_dir = 'ssk/blanco_bin'
    
    if os.path.exists(bin_dir):
        if os.path.exists(blanco_bin_dir):
            shutil.rmtree(blanco_bin_dir)
        shutil.copytree(bin_dir, blanco_bin_dir)
        print(f"Synced {bin_dir}/ to {blanco_bin_dir}/")
    else:
        print(f"Warning: {bin_dir}/ directory not found, skipping sync")
    
    # Sync jup directory
    jup_dir = 'jup'
    blanco_jup_dir = 'ssk/blanco_jup'
    
    if os.path.exists(jup_dir):
        if os.path.exists(blanco_jup_dir):
            shutil.rmtree(blanco_jup_dir)
        shutil.copytree(jup_dir, blanco_jup_dir)
        print(f"Synced {jup_dir}/ to {blanco_jup_dir}/")
    else:
        print(f"Warning: {jup_dir}/ directory not found, skipping sync")


class CustomBuildPy(build_py):
    """Custom build command that syncs blanco_app before building."""
    def run(self):
        sync_blanco_app()
        build_py.run(self)


class CustomSdist(sdist):
    """Custom sdist command that syncs blanco_app before creating source distribution."""
    def run(self):
        sync_blanco_app()
        sdist.run(self)


# Read version without importing the module
with open('ssk/ssk_consts.py', 'r') as f:
    version_file = f.read()
    version_match = re.search(r"^SSK_VER = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        SSK_VER = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string.")

# Read long description from README
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Filter out comments and empty lines
install_requires = []
for req in requirements:
    req = req.strip()
    if req and not req.startswith('#'):
        install_requires.append(req)

setup(
    name='soseki',
    version=SSK_VER,
    description='a lightweight foundation for building Python web tools.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://codingminds.io/soseki',
    author='Michał Świtała',
    author_email='michal@codingminds.io',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Framework :: Flask',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    keywords='flask web framework user-management scheduling',
    packages=find_packages(exclude=['tests', 'tests.*', 'app', 'app.*', 'scripts', 'jup', 'docs']),
    python_requires='>=3.10',
    install_requires=install_requires,
    package_data={
        'ssk': [
            'templates/**/*',
            'static/**/*',
            'blanco_app/**/*',
            'blanco_bin/**/*',
            'blanco_jup/**/*',
        ]
    },
    include_package_data=True,
    zip_safe=False,
    cmdclass={
        'build_py': CustomBuildPy,
        'sdist': CustomSdist,
    },
    entry_points={
        'console_scripts': [
            'soseki=ssk.cli:cli',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/acodingmind/soseki/issues',
        'Source': 'https://github.com/acodingmind/soseki',
    },
)
