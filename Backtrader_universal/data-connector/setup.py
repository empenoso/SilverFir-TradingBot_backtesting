from setuptools import setup, find_packages

setup(
    name="TinkoffPy",
    version="1.0.0",
    description="Tinkoff Invest API Python wrapper",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.6",
)