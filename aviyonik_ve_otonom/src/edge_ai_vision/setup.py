import os
from glob import glob
from setuptools import setup, find_packages

package_name = 'edge_ai_vision'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools', 'numpy', 'opencv-python'],
    zip_safe=True,
    maintainer='Bahattin Yunus ÇETİN',
    maintainer_email='bahattinyunuscetin@hotmail.com',
    description='METUAV DBF 2027 Edge-AI Hedef Tespiti ve Hassas Bırakma Balistik Bilgisayarı',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'target_detector_node = edge_ai_vision.target_detector_node:main',
            'drop_ballistics_computer = edge_ai_vision.drop_ballistics_computer:main',
        ],
    },
)
