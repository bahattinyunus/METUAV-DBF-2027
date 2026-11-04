cmake_minimum_required(VERSION 3.20)
project(dbf_simulation)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch worlds models scripts
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
