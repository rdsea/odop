cmake_minimum_required(VERSION 3.18)

# Get MPI
find_package(MPI REQUIRED)

# Set variables
set(staticlib ${PROJECT_NAME})
set(sharedlib ${PROJECT_NAME}-shared)
set(binary ${PROJECT_NAME}-bin)

# List all sources used by the libs
set(libsources 
    core.cpp
    field.cpp
    io.cpp
    lib.cpp
    parallel.cpp
    utilities.cpp
    "${common_dir}/pngwriter.c"
    )

# Build a static library, a shared library and an executable
# Don't use an object library so only shared library uses -fPIC
add_executable(${binary})
add_library(${staticlib} STATIC ${libsources})
add_library(${sharedlib} SHARED ${libsources})

# The executable only has main as a source, it links with the static library
target_sources(
    ${binary}
    PRIVATE
    main.cpp
    )

# Add some include directories with the SYSTEM flag.
# This means our own compile options don't trigger warnings/errors
# from those header files
target_include_directories(${staticlib}
    SYSTEM
    PRIVATE
    ${MPI_C_INCLUDE_DIRS}
    ${dependencies}
    )

target_include_directories(${sharedlib}
    SYSTEM
    PRIVATE
    ${MPI_C_INCLUDE_DIRS}
    ${dependencies}
    )


# Our own header files
target_include_directories(${staticlib}
    PRIVATE
    ${common_dir}
    ${CMAKE_CURRENT_SOURCE_DIR}
    )

target_include_directories(${sharedlib}
    PRIVATE
    ${common_dir}
    ${CMAKE_CURRENT_SOURCE_DIR}
    )

# Same for the executable
target_include_directories(${binary}
    SYSTEM
    PRIVATE
    ${MPI_C_INCLUDE_DIRS}
    ${dependencies}
    )

target_include_directories(${binary}
    PRIVATE
    ${common_dir}
    ${CMAKE_CURRENT_SOURCE_DIR}
    )

# The static and shared libraries link with MPI and the object library
target_link_libraries(${staticlib}
    PUBLIC
    ${objs}
    MPI::MPI_CXX
    stdc++fs
    )

target_link_libraries(${sharedlib}
    PUBLIC
    ${objs}
    MPI::MPI_CXX
    stdc++fs
    )

# The executable links with the static library
target_link_libraries(${binary} PUBLIC ${staticlib})

install(
    TARGETS ${staticlib} ${sharedlib} ${binary}
    CONFIGURATIONS Release ReleaseWithDebInfo
    ARCHIVE DESTINATION ${install_dir}/lib
    LIBRARY DESTINATION ${install_dir}/lib
    RUNTIME DESTINATION ${install_dir}/bin
    PUBLIC_HEADER DESTINATION ${install_dir}/include
    )
