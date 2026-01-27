from setuptools import setup, find_packages

setup(
    name="selfprivacy_api",
    version="3.7.4",
    packages=find_packages(),
    scripts=[
        "selfprivacy_api/app.py",
    ],
    include_package_data=True,
    package_data={
        "selfprivacy_api": [
            "locale/**/LC_MESSAGES/*.mo",
            "locale/**/LC_MESSAGES/*.po",
            "locale/*.pot",
        ],
    },
)
