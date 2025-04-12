from setuptools import setup, find_packages

setup(
    name="agisdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "playwright",
    ],
    author="Diego Caples",
    author_email="your.email@example.com",
    description="A benchmark SDK for evaluating AI agents",
    keywords="ai, benchmarking, evaluation",
)