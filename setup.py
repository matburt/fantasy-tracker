from setuptools import setup, find_packages

requirements = ['ClientForm',
                'PyRSS2GEen',
                'mechanize',
                'BeautifulSoup'
               ]

commands = ['scripts/fantasy_stats']

setup(
    name='fantasy-tracker',
    version='0.2',
    description='Library to fetch Fantasy Football statistics',
    packages=find_packages(),
    package_data = config_data,
    scripts=commands,
    install_requires=requirements,
    zip_safe=False
)
