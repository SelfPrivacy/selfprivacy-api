from setuptools import setup, find_packages

setup(
    name="selfprivacy_api",
    version="3.0.0",
    packages=find_packages(),
    scripts=[
        "selfprivacy_api/app.py",
    ],
)
