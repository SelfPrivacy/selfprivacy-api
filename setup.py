from setuptools import find_packages, setup

setup(
    name="selfprivacy_api",
    version="3.8.3",
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
