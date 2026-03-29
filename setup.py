from setuptools import setup, find_packages

setup(
    name="email-triage-env",
    version="1.0.0",
    description="Real-world email triage OpenEnv environment",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "fastapi==0.109.0",
        "uvicorn==0.27.0", 
        "pydantic==2.6.0",
        "requests==2.31.0",
        "pyyaml==6.0.1",
    ],
)
