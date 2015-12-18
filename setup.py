from setuptools import setup, find_packages

setup(
    name='vopaas_statistics',
    version='1.0.0',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/its-dirg/vopaas_statistics',
    license='Apache License 2.0',
    author='DIRG',
    author_email='dirg@its.umu.se',
    install_requires=["pyjwkest", "Flask", "Flask-Babel", "Flask-Mako", "dataset"]
)
