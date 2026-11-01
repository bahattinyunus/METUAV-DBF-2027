cmake_minimum_required(VERSION 3.20)
project(ucus_kontrol)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic -O3)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)

include_directories(include)

# Flight Control Library
add_library(ucus_kontrol_core
  src/adaptive_pid_controller.cpp
  src/mission_manager.cpp
  src/fast_boot_calibrator.cpp
  src/extended_kalman_filter.cpp
  src/energy_manager.cpp
)
ament_target_dependencies(ucus_kontrol_core
  rclcpp
  geometry_msgs
  sensor_msgs
  nav_msgs
  std_msgs
  tf2
  tf2_geometry_msgs
)

# Main Executable Node
add_executable(flight_control_node src/main_flight_node.cpp)
target_link_libraries(flight_control_node ucus_kontrol_core)
ament_target_dependencies(flight_control_node
  rclcpp
  geometry_msgs
  sensor_msgs
  nav_msgs
  std_msgs
)

install(TARGETS
  ucus_kontrol_core
  flight_control_node
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY include/
  DESTINATION include/
)

install(DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
