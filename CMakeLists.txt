cmake_minimum_required(VERSION 3.10)
project(enhanced_rle VERSION 0.1.0)

set(CMAKE_CXX_STANDARD 14) 
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_TRY_COMPILE_TARGET_TYPE "STATIC_LIBRARY")

add_subdirectory(pybind11)
pybind11_add_module(enhanced_rle pattern_on_the_fly/enhancedRLE.cpp)
target_include_directories(enhanced_rle PRIVATE ./pattern_on_the_fly)

# EXAMPLE_VERSION_INFO is defined by setup.py and passed into the C++ code as a
# define (VERSION_INFO) here.
target_compile_definitions(enhanced_rle
                           PRIVATE VERSION_INFO=${EXAMPLE_VERSION_INFO})