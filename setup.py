from setuptools import setup, find_packages

setup(
    name="selfprivacy_api",
    version="3.6.2",
    packages=find_packages(),
    scripts=[
        "selfprivacy_api/app.py",
    ],
    include_package_data=True,
)
