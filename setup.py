import re

from setuptools import setup, find_packages

def match(x):
    #ignore comments
    if re.search(r'(^\s*#)', x):
        return False
    return True

def replace(x):
    match_replace = re.search(r'egg=(.*)', x)
    if match_replace:
        return match_replace.group(1)
    return x

with open('requirements.txt') as f:
    required = [replace(x) for x in f.read().splitlines()
                if match(x)]

with open('VERSION') as f:
    version = f.read().strip()

setup(
    name='sugarcoat',
    version=version,
    description='Sugarcoat',
    long_description='Easier to consume APIs.',
    author='Brian Price',
    author_email='brian.price@badcure.com',
    url='https://github.com/badcure/sugarcoat/',
    packages=find_packages() + ['sugarcoat.api.templates'],
    include_package_data=True,
    package_data={'sugarcoat': ['api/templates/*', 'api/static/*'], },
    zip_safe=False,
    install_requires=required,
)