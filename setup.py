from setuptools import setup, find_packages

setup(
    name="adqlm",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask",
        "astro-datalab",
        "google-generativeai",
        "beautifulsoup4",
        "requests",
        "numpy",
        "scikit-learn",
        "sentence-transformers",
        "pandas"
    ],
    description="A library to query NOIRLab data using natural language",
    author="Jules",
)
