from setuptools import setup


setup(
    name = 'pynisher',
    version = "0.4.1",
    packages = ['pynisher'],
    install_requires = ['docutils>=0.3', 'setuptools', 'psutil'],
    author = "Stefan Falkner",
    author_email = "sfalkner@informatik.uni-freiburg.de",
    description = "A small Python library to limit the resources used by a function by executing it inside a subprocess.",
    include_package_data = False,
    keywords = "resources",
    license = "MIT",
    url = "https://github.com/sfalkner/pynisher",
    download_url = "https://github.com/sfalkner/pynisher/tarball/0.4.1"
)
