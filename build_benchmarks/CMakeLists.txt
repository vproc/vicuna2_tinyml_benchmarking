cmake_minimum_required(VERSION 3.10)
message(STATUS "CMake Version ${CMAKE_MAJOR_VERSION}.${CMAKE_MINOR_VERSION}.${CMAKE_PATCH_VERSION}")

##########################
#
# Configuration variables:
# - RV_ARCH : select the processor architecture configuration for compilation
#
# FEATURES:
# - TRACE : enables .csv memory trace and .vcd signal trace output for unit tests.  Due to large file sizes, only trace of last test run will be kept.  Will be located in /build/Testing
#
#
##########################

#Set this on the command line to change configuration.  Currently Supported: rv32im, rv32imzve32x, rv32imf, rv32imfzve32x, rv32imfzve32f
set(RISCV_ARCH rv32im CACHE STRING "Specify the configuration")
set(MEM_LATENCY 1 CACHE STRING "Memory latency")
set(MIN_VLEN 128 CACHE STRING "LLVM Autovectorizer parameter for minimum VLEN in bits")  #Does the same thing as _ZvlXXXb architecture string
set(MEM_W 32 CACHE STRING "Width of main memory data port in bits")

option(TRACE        "Enable trace outputs"                                         OFF)
option(PRINT        "Enable print statements"                                      OFF)


#####
# Default Paths to Subdirectories
#####

set(BUILD_DIR ${CMAKE_CURRENT_SOURCE_DIR}/build)
set(MODEL_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../build_model/build)
set(BENCHMARKS_TOP ${CMAKE_CURRENT_SOURCE_DIR}/../benchmark_sources)
set(BSP_TOP ${CMAKE_CURRENT_SOURCE_DIR}/../bsp)


#####
# Select RISCV_ARCH and RISCV_ABI and Autovectorization flags based on selected features
#####

#These control benchmark configurations specific to the selected RISCV_ARCH
option(RISCV_F "Use the RISC-V F Extension" OFF)
option(RISCV_ZFH "Use the RISC-V ZFH Extension" OFF)
option(RISCV_ZVE32X "Use the RISC-V Embedded V Extension" OFF)
option(RISCV_ZVE32F "Use the RISC-V Embedded V Float Extension" OFF)
option(RISCV_ZVHF "Use the RISC-V V Half Float Extension" OFF)



set(AUTOVEC_FLAGS "")

if(${RISCV_ARCH} STREQUAL "rv32im") 
    set(RISCV_ABI ilp32)
    option(FH_OPS      "Use FP16 for intermediate operations (no conversion to float)"  OFF)
    
elseif(${RISCV_ARCH} STREQUAL "rv32imf")
    set(RISCV_ABI ilp32f)  
    set(RISCV_F ON)
    option(FH_OPS      "Use FP16 for intermediate operations (no conversion to float)"  OFF)
    
elseif(${RISCV_ARCH} STREQUAL "rv32imf_zfh")
    set(RISCV_ABI ilp32f)  
    set(RISCV_F ON)
    set(RISCV_ZFH ON)
    option(FH_OPS      "Use FP16 for intermediate operations (no conversion to float)"  ON)
    
elseif(${RISCV_ARCH} STREQUAL "rv32im_zve32x")
    set(RISCV_ABI ilp32) 
    set(RISCV_ZVE32X ON)
    set(AUTOVEC_FLAGS "-fvectorize -fslp-vectorize -mllvm -scalable-vectorization=on -mllvm --riscv-v-vector-bits-min=${MIN_VLEN}")
    option(FH_OPS      "Use FP16 for intermediate operations (no conversion to float)"  OFF)
    
elseif(${RISCV_ARCH} STREQUAL "rv32imf_zve32f")
    set(RISCV_ABI ilp32f) 
    set(RISCV_ZVE32X ON)
    set(RISCV_ZVE32F ON)
    set(RISCV_F ON)
    set(AUTOVEC_FLAGS "-fvectorize -fslp-vectorize -mllvm -scalable-vectorization=preferred -mllvm --riscv-v-vector-bits-min=${MIN_VLEN}")
    option(FH_OPS      "Use FP16 for intermediate operations (no conversion to float)"  OFF)
    
elseif(${RISCV_ARCH} STREQUAL "rv32imf_zfh_zve32f_zvfh")
    set(RISCV_ABI ilp32f) 
    set(RISCV_ZVE32X ON)
    set(RISCV_ZVE32F ON)
    set(RISCV_ZFH ON)
    set(RISCV_F ON)
    set(RISCV_ZVFH ON)
    set(AUTOVEC_FLAGS "-fvectorize -fslp-vectorize -mllvm -scalable-vectorization=preferred -mllvm --riscv-v-vector-bits-min=${MIN_VLEN}")
    option(FH_OPS      "Use FP16 for intermediate operations (no conversion to float)"  ON)
    

else()
    message(FATAL_ERROR "Unsupported RISCV_ARCH selected")
    
endif()

set(RISCV_CMODEL "medany" CACHE STRING "mcmodel argument to the compiler")


#####
#Set LLVM 18 as the Compiler
#####

# Tell CMake about our processor
set(CMAKE_SYSTEM_PROCESSOR ${RISCV_ARCH})
# The Generic system name is used for bare-metal targets (without OS) in CMake
set(CMAKE_SYSTEM_NAME Generic)


set(CMAKE_TOOLCHAIN_FILE "${CMAKE_CURRENT_SOURCE_DIR}/../CMake/llvm_18_toolchain.cmake")

####
# Set build mode, Release by default
####
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE RELEASE)
endif()

if(PRINT)
  add_definitions(-DPRINT_OUTPUTS)
endif()


####
# Set some compiler options for easier debug or faster builds
####

# See whats going in CMake while getting the build process up and running
set(CMAKE_VERBOSE_MAKEFILE ON)

# Using C and C++ 11
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 11)

set(CMAKE_C_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG} -O3 -g -ggdb ${AUTOVEC_FLAGS}")
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -O3 -g -ggdb ${AUTOVEC_FLAGS}")
set(CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE} -O3 ${AUTOVEC_FLAGS}")
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 ${AUTOVEC_FLAGS}")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Wextra -Wshadow -Wno-format -std=c11 ${AUTOVEC_FLAGS}") 
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -std=c++11 ${AUTOVEC_FLAGS}")


#####################
# Setup the CMake Project
####################

set(CMAKE_EXECUTABLE_SUFFIX_C .elf)
set(CMAKE_EXECUTABLE_SUFFIX_CXX .elf)
set(CMAKE_EXECUTABLE_SUFFIX_ASM .elf) 
set(CMAKE_EXECUTABLE_SUFFIX ".elf") #For some reason setting this works for ASM files but SUFFIX_ASM doesnt


project(Zvhf_Software_Env LANGUAGES C CXX ASM DESCRIPTION "Compilation and Test Environment for Verification Tests and Benchmarks")
include(CTest)

########
#Add Program Subdirectories
########

add_subdirectory(../benchmark_sources benchmark_sources)
add_subdirectory(../bsp bsp)

