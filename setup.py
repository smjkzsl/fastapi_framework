from setuptools import setup
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setup(
    name='fastapi_mvc_framework',
    version='0.3',
    author='Bruce chou',
    author_email='smjkzsl@gmail.com',
    description='MVC framework implemented by fastapi',
    long_description=long_description,
    long_description_content_type="text/markdown",

    url='https://github.com/smjkzsl/fastapi_framework',
    packages=['fastapi_mvc_framework'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
