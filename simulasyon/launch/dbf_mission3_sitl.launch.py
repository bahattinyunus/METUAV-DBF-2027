#!/usr/bin/env python3
"""
METUAV DBF 2027 - Mission 3 SITL Launch File
Launches Gazebo simulation with DBF airfield world, spawns dbf_aircraft,
and initializes flight controller, vision node, and drop ballistics computer.
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    world_path = os.path.join(pkg_dir, 'worlds', 'dbf_airfield.world')
    model_path = os.path.join(pkg_dir, 'models', 'dbf_aircraft', 'model.sdf')

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=world_path,
            description='Path to Gazebo world'
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation clock'
        ),

        # Start Gazebo Server & Client (commented out or executed depending on environment)
        ExecuteProcess(
            cmd=['gzserver', '--verbose', '-s', 'libgazebo_ros_init.so', '-s', 'libgazebo_ros_factory.so', world_path],
            output='screen'
        ),

        # Spawn Aircraft in Gazebo
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            name='spawn_dbf_aircraft',
            arguments=['-entity', 'dbf_aircraft', '-file', model_path, '-x', '0.0', '-y', '0.0', '-z', '0.2'],
            output='screen'
        ),

        # Start Flight Controller Node
        Node(
            package='ucus_kontrol',
            executable='flight_control_node',
            name='flight_control_node',
            output='screen',
            parameters=[{'use_sim_time': True}]
        ),

        # Start Edge-AI Vision & Drop Ballistics Computer
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
            parameters=[{'use_sim_time': True}]
        ),

        # Start Telemetry Bridge
        Node(
            package='telemetri',
            executable='mavlink_bridge_node',
            name='mavlink_bridge_node',
            output='screen',
            parameters=[{'use_sim_time': True}]
        )
    ])
