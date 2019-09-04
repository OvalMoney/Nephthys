import io

from setuptools import setup


def make_long_description():
    with io.open("README.md", encoding="utf-8") as fp:
        long_description = fp.read()
    return long_description


setup(
    name="Nephthys",
    description="Advanced Python Logger",
    long_description=make_long_description(),
    long_description_content_type="text/markdown",
    version="0.1.0",
    author="Fabio Todaro",
    license="MIT",
    author_email="ft@ovalmoney.com",
    url="https://github.com/OvalMoney/Nephthys",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: OS Independent",
    ],
    packages=["nephthys"],
    install_requires=[],
)
