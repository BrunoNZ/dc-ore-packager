import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dc-ore-packager",
    version="0.0.1",
    author="Bruno Nocera Zanette",
    author_email="brunonzanette@gmail.com",
    description="A simple DublinCore/ORE SimpleArchive Packager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BrunoNZ/dc-ore-packager",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
