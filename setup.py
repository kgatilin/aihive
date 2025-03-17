from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="aihive",
    version="0.1.0",
    description="AI-driven development pipeline with asynchronous workflow",
    author="AI Hive Team",
    author_email="kgatilin@users.noreply.github.com",
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.9",
) 