from setuptools import setup, find_packages

setup(
    name="pyconvert",
    version="1.0.0",
    author="cobrapy-x",  
    author_email="",  
    description="A Python module for unit and number system conversion",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/cobrapy-x/pyconvert",  # Make sure this points to your GitHub repo
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.6",
)
