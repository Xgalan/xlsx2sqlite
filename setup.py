import setuptools

setuptools.setup(
    name="xlsx2sqlite",
    version="0.1.0",
    url="https://github.com/Xgalan/xlsx2sqlite",

    author="Erik Mascheri",
    author_email="erik_mascheri@fastmail.com",

    description="Generate a Sqlite3 database from a Office Open XML file.",
    long_description=open('README.rst').read(),

    packages=setuptools.find_packages(),

    install_requires=[
        "openpyxl==2.5.8",
        "tablib==0.12.1",
        "Click==7.0",
        ],

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    entry_points='''
        [console_scripts]
        xlsx2sqlite=xlsx2sqlite.cli:cli
    ''',
)
