from setuptools import setup, find_packages

setup(
    name="selfprivacy_api",
    version="2.3.1",
    packages=find_packages(),
    scripts=[
        "selfprivacy_api/app.py",
    ],
)
