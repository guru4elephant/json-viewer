from setuptools import setup

setup(
    name='jv',
    version='0.1.0',
    py_modules=['jv'],
    install_requires=[
        'click',
        'prompt_toolkit',
    ],
    entry_points={
        'console_scripts': [
            'jv=jv:main',
        ],
    },
    author='dongdaxiang',
    author_email='guru4elephant@gmai.com',
    description='一个用于查看和浏览 JSONL 文件的 CLI 工具',
    url='https://github.com/guru4elephant/json-viewer',  # 如果有仓库，请更新为你的仓库地址
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
) 
