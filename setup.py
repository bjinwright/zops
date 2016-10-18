from setuptools import setup, find_packages
from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt', session=False)

version = '0.2.4'

LONG_DESCRIPTION = """
=====
Zops
=====

Zops - Utils for devops teams that want to deploy using Zappa

"""

setup(
    name='zops',
    version=version,
    description="""Utils for devops teams that want to deploy using Zappa""",
    long_description=LONG_DESCRIPTION,
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Environment :: Web Environment",
    ],
    keywords='zappa, aws, lambda',
    author='Brian Jinwright',
    author_email='opensource@ipoots.com',
    maintainer='Brian Jinwright',
    packages=find_packages(),
    py_modules=['zops.cli'],
    entry_points='''
    [console_scripts]
    zops=zops.cli:zops_ins
    ''',
    license='GNU GPL V3',
    install_requires=[str(ir.req) for ir in install_reqs],
    include_package_data=True,
    zip_safe=False,
)
