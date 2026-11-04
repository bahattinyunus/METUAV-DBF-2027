import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_dir = get_package_share_directory('ucus_kontrol')
    config_file = os.path.join(pkg_dir, 'config', 'flight_controller_params.yaml')

    return LaunchDescription([
        Node(
            package='ucus_kontrol',
            executable='flight_control_node',
            name='flight_control_node',
            output='screen',
            parameters=[config_file],
            remappings=[
                ('dbf/imu/data', '/imu/data'),
                ('dbf/gps/fix', '/gps/fix'),
                ('dbf/airspeed', '/airspeed'),
            ]
        )
    ])
