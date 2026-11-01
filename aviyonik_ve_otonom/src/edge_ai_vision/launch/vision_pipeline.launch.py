from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='edge_ai_vision',
            executable='target_detector_node',
            name='target_detector_node',
            output='screen',
            parameters=[{'use_sim_time': True}]
        ),
        Node(
            package='edge_ai_vision',
            executable='drop_ballistics_computer',
            name='drop_ballistics_computer',
            output='screen',
            parameters=[{
                'payload_mass_kg': 2.5,
                'drag_coefficient': 0.45,
                'frontal_area_m2': 0.018
            }]
        )
    ])
