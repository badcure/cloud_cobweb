import re
import os
import setuptools


def match(x):
    # ignore comments
    if re.search(r'(^\s*#)', x):
        return False
    return True


def replace(x):
    match_replace = re.search(r'egg=(.*)', x)
    if match_replace:
        return match_replace.group(1)
    return x

def find_templates(path, parent=None, include_dir=False):
    results = []

    if parent is None:
        parent = []
    else:
        parent = parent.copy()
    parent.append(path)

    for possible_dir in os.listdir('/'.join(parent)):
        possible_path = '/'.join(parent + [possible_dir])

        if not os.path.isdir(possible_path):
            continue
        if possible_dir in ['templates','static'] and parent[-1] == 'blueprint':
            include_dir = True

        if os.path.isdir(possible_path):
            if include_dir:
                results.append('{0}/*'.format(possible_path))
            results += find_templates(possible_dir, parent, include_dir)

    return results

with open('requirements.txt') as f:
    required = [replace(x) for x in f.read().splitlines()
                if match(x)]

with open('VERSION') as f:
    version = f.read().strip()

setuptools.setup(
    name='sugarcoat',
    version=version,
    description='Sugarcoat',
    long_description='Easier to consume APIs.',
    author='Brian Price',
    author_email='brian.price@badcure.com',
    url='https://github.com/badcure/sugarcoat/',
    packages=setuptools.find_packages() + ['sugarcoat.api.templates'],
    include_package_data=True,
    package_data={'sugarcoat': ['api/templates/*', 'api/static/*.js', 'api/static/*.css', 'api/static/js/*',
                                'api/static/css/*', 'api/static/fonts/*'] + find_templates('sugarcoat') },
    zip_safe=False,
    install_requires=required,
)
