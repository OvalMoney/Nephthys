import io

from setuptools import setup, find_packages


def make_long_description():
    with io.open("README.md", encoding="utf-8") as fp:
        long_description = fp.read()
    return long_description


setup(
    name="nephthys",
    description="Advanced Python Logger",
    long_description=make_long_description(),
    long_description_content_type="text/markdown",
    version="1.0.0",
    author="Fabio Todaro",
    license="MIT",
    author_email="ft@ovalmoney.com",
    url="https://github.com/OvalMoney/Nephthys",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["tests", "requirements"]),
    install_requires=["webob"],
    extras_require={"JSON": ["python-rapidjson"], "requests": ["requests"]},
)
