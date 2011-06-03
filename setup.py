from distutils.core import setup
#from setuptools import setup, find_packages
setup(name='mozcommitbuilder',
      packages=['mozcommitbuilder'],
      version='0.3',
      description ="""Regression finder using Mozilla central repo""",
      author="Sam Liu",
      author_email="sam@ambushnetworks.com",
      url='http://github.com/samliu/moz-commitbuilder',
      entry_points="""
          [console_scripts]
          mozcommitbuilder = mozcommitbuilder:buildercli
        """,
      install_requires = ['mozrunner >= 2.5.4', 'httplib2 >= 0.6.0'],
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Developers',
                   'Operating System :: OS Independent'
                  ]

      )
