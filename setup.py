from setuptools import setup

setup(
    name = "freezam",
    version = "0.1.0",
    packages = ["freezam"],
    entry_points = {
        "console_scripts" : [
            "fz = freezam.fzcl:Freezam",
            "freezam = freezam.fzcl:Freezam"
        ]
    }

)