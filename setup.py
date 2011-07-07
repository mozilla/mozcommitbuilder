from setuptools import setup, find_packages
#from distutils.core import setup
#from setuptools import setup, find_packages
setup(name='mozcommitbuilder',
      version='0.4.6',
      description ="""Regression finder using Mozilla central repo""",
      author="Sam Liu",
      author_email="sam@ambushnetworks.com",
      url='http://github.com/samliu/mozcommitbuilder',
      license='MPL 1.1/GPL 2.0/LGPL 2.1',
      packages=find_packages(exclude=['legacy']),
      entry_points="""
          [console_scripts]
          mozcommitbuilder = mozcommitbuilder:buildercli
        """,
      install_requires = ['mozrunner >= 2.5.4', 'httplib2 >= 0.6.0', 'simplejson'],
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Developers',
                   'Operating System :: OS Independent'
                  ]

      )
