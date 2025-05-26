cmake_minimum_required(VERSION 3.10)
project(enhanced_rle VERSION 0.1.0)

set(CMAKE_CXX_STANDARD 14) 
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(pybind11 REQUIRED)
pybind11_add_module(enhanced_rle enhancedRLE.cpp)

execute_process(
  COMMAND "${PYTHON_EXECUTABLE}" -c "if True:
    import site
    print(site.getsitepackages()[0])"
  OUTPUT_VARIABLE Python_SITELIB
  OUTPUT_STRIP_TRAILING_WHITESPACE
)

install(TARGETS enhanced_rle DESTINATION ${Python_SITELIB})