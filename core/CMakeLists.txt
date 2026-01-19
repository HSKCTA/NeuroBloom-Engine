cmake_minimum_required(VERSION 3.10)
project(NeuroBloomEngine)

set(CMAKE_CXX_STANDARD 17)

# Include directories
include_directories(include)

# Source files
file(GLOB SOURCES "src/*.cpp")

# Find OpenCV
find_package(OpenCV REQUIRED)
include_directories(${OpenCV_INCLUDE_DIRS})

# Find OpenSSL
find_package(OpenSSL REQUIRED)
include_directories(${OPENSSL_INCLUDE_DIR})

# Executable
add_executable(neuro_hybrid ${SOURCES})

# Link libraries
target_link_libraries(neuro_hybrid ${OpenCV_LIBS} ${OPENSSL_LIBRARIES} pthread zmq)
