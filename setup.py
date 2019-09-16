
from setuptools import setup, find_packages
import os.path
import re

# reading package's version (same way sqlalchemy does)
with open(
    os.path.join(os.path.dirname(__file__), 'sshtuntap', '__init__.py')
) as v_file:
    package_version = \
        re.compile('.*__version__ = \'(.*?)\'', re.S)\
        .match(v_file.read())\
        .group(1)


dependencies = [
    'easycli',
    'pymlconf >= 2',
]


setup(
    name='sshtuntap',
    version=package_version,
    author='Vahid Mardani',
    author_email='vahid.mardani@gmail.com',
    url='http://github.com/pylover/sshtuntap',
    description='Linux tuntap using openssh',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',  # This is important!
    install_requires=dependencies,
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'ssh-tuntap-server = sshtuntap.server:main',
            'ssh-tuntap-client = sshtuntap.client:main',
        ]
    },
    license='MIT',
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Development Status :: 5 - Production/Stable',
        'License :: Other/Proprietary License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ]
)
