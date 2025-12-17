from setuptools import setup, find_packages

setup(
    name="selfprivacy_api",
    version="3.7.1",
    packages=find_packages(),
    scripts=[
        "selfprivacy_api/app.py",
    ],
    include_package_data=True,
)
