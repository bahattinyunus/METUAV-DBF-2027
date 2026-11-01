import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_dir = get_package_share_directory('telemetri')
    config_file = os.path.join(pkg_dir, 'config', 'telemetry_config.yaml')

    return LaunchDescription([
        Node(
            package='telemetri',
            executable='mavlink_bridge_node',
            name='mavlink_bridge_node',
            output='screen',
            parameters=[config_file]
        )
    ])
