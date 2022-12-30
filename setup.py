from setuptools import setup, find_packages

setup(
    name="selfprivacy_api",
    version="2.1.0",
    packages=find_packages(),
    scripts=[
        "selfprivacy_api/app.py",
    ],
)
