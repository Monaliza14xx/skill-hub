from setuptools import setup, find_packages

setup(
    name="skill-hub",
    version="1.0.0",
    description="Universal Skill and Plugin Hub for Multi-Agent AI Tools",
    author="AI Developer Team",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "skill-hub = skill_hub.cli:main",
        ],
    },
    python_requires=">=3.7",
)
