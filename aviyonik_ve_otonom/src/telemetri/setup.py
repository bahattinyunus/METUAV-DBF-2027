import os
from glob import glob
from setuptools import setup, find_packages

package_name = 'telemetri'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools', 'pymavlink'],
    zip_safe=True,
    maintainer='Bahattin Yunus ÇETİN',
    maintainer_email='bahattinyunuscetin@hotmail.com',
    description='AIAA DBF 2027 MAVLink GCS Yer İstasyonu ve Otopilot Telemetri Köprüsü',
    license='MIT',
    entry_points={
        'console_scripts': [
            'mavlink_bridge_node = telemetri.mavlink_bridge_node:main',
        ],
    },
)
