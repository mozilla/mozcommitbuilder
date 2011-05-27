from distutils.core import setup
setup(name='mozcommitbuilder',
      version='0.1',
      py_modules=['mozcommitbuilder'],
      entry_points="""
          [console_scripts]
          mozcommitbuilder = mozcommitbuilder:cli
        """
      )
