from setuptools import setup, find_packages

setup(
    name="execbox",
    version="0.1.0",
    description="Code execution sandbox for AI agents",
    author="chu2bard",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "psutil>=5.9",
        "pydantic>=2.0",
    ],
)
