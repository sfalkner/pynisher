from setuptools import setup, find_packages


setup(
    name = "pynisher",
    version = "0.2",
    packages = find_packages(),
    install_requires = ['docutils>=0.3', 'setuptools'],
    author = "Stefan Falkner",
    author_email = "sfalkner@informatik.uni-freiburg.de",
    description = "A small Python library to limit the resources used by a function by executing it inside a subprocess.",
    include_package_data = False,
    keywords = "resources",
    license = "MIT",
    url = "https://github.com/sfalkner/pynisher"
)
