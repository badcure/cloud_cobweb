import re

from setuptools import setup
def match(x):
    #ignore comments
    if re.search(r'(^\s*#)', x):
        return False
    return True

def replace(x):
    match = re.search(r'egg=(.*)', x)
    if match:
        return match.group(1)
    return x

with open('requirements.txt') as f:
    required = [replace(x) for x in f.read().splitlines()
                if match(x)]

with open('VERSION') as f:
    version = f.read().strip()

setup(
    name='rack_cloud_info',
    version=version,
    description='Rackspace Cloud Information',
    long_description='Rackspace Cloud Information - Connecting the different '
                     'services',
    author='Brian Price',
    author_email='brian.price@badcure.com',
    url='https://github.rackspace.com/badcure/rackspace_cloud_information/',
    packages=['rack_cloud_info'],
    include_package_data=True,
    zip_safe=False,
    install_requires=required,
)