from setuptools import setup, find_packages

desc = """Regression range finder for Mozilla Central"""
summ = """Interactive regression range finder for Mozilla Central repo"""

setup(name="moz-commitbuilder",
      version="0.1",
      description=desc,
      long_description=summ,
      author='Sam Liu',
      author_email='',
      url='',
      license='MPL 1.1/GPL 2.0/LGPL 2.1',
      packages=find_packages(exclude=['legacy']),
      entry_points="""
          [console_scripts]
          moz-commitbuilder = moz-regression:main
        """,
      platforms =['Any'],
      install_requires = ['httplib2 >= 0.6.0', 'mozrunner >= 2.5.1', 'BeautifulSoup >= 3.0.4'],
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Intended Audience :: Developers',
                   'Operating System :: OSX'
                  ]
     )
