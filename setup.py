from setuptools import setup, find_packages

setup(
    name="selfprivacy_api",
    version="1.2.0",
    packages=find_packages(),
    scripts=[
        "selfprivacy_api/app.py",
    ],
)
