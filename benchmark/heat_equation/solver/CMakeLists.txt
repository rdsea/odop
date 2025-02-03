cmake_minimum_required(VERSION 3.18)

project(heat_equation VERSION 1.0 DESCRIPTION "Heat equation w/ cmake, ctest and gtest" LANGUAGES CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(common_dir "${CMAKE_SOURCE_DIR}/../common")
set(install_dir "${PROJECT_NAME}")
set(dependencies "${CMAKE_SOURCE_DIR}/include")

add_subdirectory(src)
