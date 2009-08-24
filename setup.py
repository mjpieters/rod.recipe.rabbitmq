"""Setup script."""

import os
from setuptools import setup, find_packages


def read(*rnames):
    return open(os.path.join(os.getcwd(), *rnames)).read()


setup(
    name="rod.recipe.rabbitmq",
    version=read('version.txt').strip(),
    author="Tobias Rodaebel",
    author_email="tobias (dot) rodaebel (at) googlemail (dot) com",
    description="ZC Buildout recipe for setting up RabbitMQ.",
    license="LGPL 3",
    keywords="rabbitmq zc.buildout recipe",
    url='http://pypi.python.org/pypi/rod.recipe.rabbitmq',
    long_description=(
        read('README.txt')
        + '\n' +
        read('src', 'rod', 'recipe', 'rabbitmq', 'README.txt')
        + '\n' +
        read('CHANGES.txt')
        ),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Buildout',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: POSIX',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    packages=find_packages('src'),
    include_package_data=True,
    package_dir={'': 'src'},
    package_data={'rod.recipe.rabbitmq': ['README.txt']},
    namespace_packages=['rod', 'rod.recipe'],
    install_requires=[
        'setuptools',
        'simplejson',
        'zc.buildout',
        'zc.recipe.egg',
        ],
    entry_points={'zc.buildout': ['default = rod.recipe.rabbitmq:Recipe']},
    zip_safe=False,
    )
