from setuptools import setup, find_packages

setup(
    name="selfprivacy_api",
    version="1.2.6",
    packages=find_packages(),
    scripts=[
        "selfprivacy_api/app.py",
    ],
)
