import os

from setuptools import setup, find_packages


setup(
    name='fjord',
    version='1.0',
    description='Django application.',
    long_description='',
    author='Mozilla Foundation',
    author_email='',
    license='BSD',
    url='https://github.com/mozilla/fjord',
    include_package_data=True,
    classifiers=[
        'Framework :: Django',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        ],
    packages=find_packages(exclude=['tests']),
    install_requires=[],
    )
