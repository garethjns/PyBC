import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pybit",
    version="0.1.0",
    author="Gareth Jones",
    author_email="garethj4@gmail.com",
    description="",
    #long_description=long_description,
    #long_description_content_type="text/markdown",
    url="https://github.com/garethjns/PyBC",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)