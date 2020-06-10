from setuptools import setup

with open("readme.md", "r") as f:
      long_description = f.read()

setup(name='terminal-preroll',
      version='1.0',
      description='Stream Preroll Animation for Python',
      long_description=long_description,
      author='Zac Adam-MacEwen',
      author_email='zadammac@kenshosec.com',
      url='https://www.github.com/zadammac/terminal_preroll',
      packages=['terminal-preroll'],
      install_requires=['blessings', 'termcolor'],
      long_description_content_type="text/markdown"
     )