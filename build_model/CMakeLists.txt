cmake_minimum_required(VERSION 3.10)
message(STATUS "CMake Version ${CMAKE_MAJOR_VERSION}.${CMAKE_MINOR_VERSION}.${CMAKE_PATCH_VERSION}")

###This file is used to build the verilated models of CV32E40X and Vicuna###

########################
# Arguments
#
# RV_ARCH : select the processor architecture configuration to verilate
# TRACE   : If defined, enable vcd trace outputs.  WARNING: Traces can be very large (GBs)
# TRACE_FULL   : If defined, trace outputs of ENTIRE model WARNING: Traces can be very VERY large (GBs) (requires TRACE=ON)
# CACHE :   Enable a cache configuration


#####################
# Setup the CMake Project
####################

project(Verilated-Builds LANGUAGES C CXX DESCRIPTION "Environment for Verilating Models")
find_package(verilator HINTS ${CMAKE_CURRENT_SOURCE_DIR}/../Toolchain/verilator)

# See whats going in CMake while getting the build process up and running
set(CMAKE_VERBOSE_MAKEFILE ON)

# Using C and C++ 11
set(CMAKE_C_STANDARD 14)
set(CMAKE_CXX_STANDARD 14)


#Currently Supported: rv32im, rv32im_zve32x, rv32imf, rv32imf_zhf, rv32imf_zve32x, rv32imf_zve32f
set(RISCV_ARCH rv32im CACHE STRING "Specify the configuration")

option(TRACE "Enable minimal VCD trace outputs" OFF)
option(TRACE_FULL "Enable FULL VCD trace outputs" OFF) #TODO: prevent this option from being cached, force user to always manually enable it

set(VREG_W 128 CACHE STRING "VREG_W")
set(VMEM_W 32 CACHE STRING "VMEM_W")
set(MEM_W 32 CACHE STRING "MEM_W")
set(VLANE_W 32 CACHE STRING "VLANE_W")
set(DCACHE_LINE_W 128 CACHE STRING "DCACHE_LINE_W") 

set(MEM_SZ 4194304)

######################
# Extension Flags
######################

if(${RISCV_ARCH} STREQUAL "rv32im") #Build only CV32E40X
    #Verilog Flags
    set(XIF_FLAG "" )
    set(RISCV_F "" )
    set(RISCV_ZFH "" )
    set(RISCV_ZVE32X "" )
    set(RISCV_ZVE32F "" )
    set(RISCV_ZVFH "" )

elseif(${RISCV_ARCH} STREQUAL "rv32imf") #Build CV32E40X with FPU on the Xif interface
    #Verilog Flags
    set(XIF_FLAG "-DXIF_ON" )
    set(RISCV_F "-DRISCV_F" )
    set(RISCV_ZFH "" )
    set(RISCV_ZVE32X "" )
    set(RISCV_ZVE32F "" )
    set(RISCV_ZVFH "" )
    #C++ Flags
    add_definitions(-DRISCV_F)

elseif(${RISCV_ARCH} STREQUAL "rv32imf_zfh") #Build CV32E40X with FPU on the Xif interface with half-float support
    #Verilog Flags
    set(XIF_FLAG "-DXIF_ON" )
    set(RISCV_F "-DRISCV_F" )
    set(RISCV_ZFH "-DRISCV_ZFH" )
    set(RISCV_ZVE32X "" )
    set(RISCV_ZVE32F "" )
    set(RISCV_ZVFH "" )
    #C++ Flags
    add_definitions(-DRISCV_F)
    add_definitions(-DRISCV_ZFH)

elseif(${RISCV_ARCH} STREQUAL "rv32im_zve32x") #Build CV32E40X with Vicuna on the Xif interface
    #Verilog Flags
    set(XIF_FLAG "-DXIF_ON" )
    set(RISCV_F "" )
    set(RISCV_ZFH "" )
    set(RISCV_ZVE32X "-DRISCV_ZVE32X" )
    set(RISCV_ZVE32F "" )
    set(RISCV_ZVFH "" )
    #C++ Flags
    add_definitions(-DRISCV_ZVE32X)

elseif(${RISCV_ARCH} STREQUAL "rv32imf_zve32f") #Build CV32E40X with Vicuna and FPU on the Xif interface
    #Verilog Flags
    set(XIF_FLAG "-DXIF_ON" )
    set(RISCV_F "-DRISCV_F" )
    set(RISCV_ZFH "" )
    set(RISCV_ZVE32X "-DRISCV_ZVE32X" )
    set(RISCV_ZVE32F "-DRISCV_ZVE32F" )
    set(RISCV_ZVFH "" )
    #C++ Flags
    add_definitions(-DRISCV_F)
    add_definitions(-DRISCV_ZVE32X)
    add_definitions(-DRISCV_ZVE32F)

elseif(${RISCV_ARCH} STREQUAL "rv32imf_zfh_zve32f_zvfh") #Build CV32E40X with Vicuna (+floating point + half precision float) and FPU on the Xif interface
    #Verilog Flags
    set(XIF_FLAG "-DXIF_ON" )
    set(RISCV_F "-DRISCV_F" )
    set(RISCV_ZFH "-DRISCV_ZFH" )
    set(RISCV_ZVE32X "-DRISCV_ZVE32X" )
    set(RISCV_ZVE32F "-DRISCV_ZVE32F" )
    set(RISCV_ZVFH "-DRISCV_ZVFH" )
    #C++ Flags
    add_definitions(-DRISCV_F)
    add_definitions(-DRISCV_ZFH)
    add_definitions(-DRISCV_ZVE32X)
    add_definitions(-DRISCV_ZVE32F)
    add_definitions(-DRISCV_ZVFH)

else()
    message(FATAL_ERROR "Unsupported RISCV_ARCH selected")

endif()

######################
# Sources/Include Directories
######################

#Path to CV32E40X sources               
set(DESIGN_RTL_DIR_CV32E40X ${CMAKE_CURRENT_SOURCE_DIR}/../rtl/cv32e40x/rtl)

#Path to FPU_SS sources
set(DESIGN_RTL_DIR_FPU_SS ${CMAKE_CURRENT_SOURCE_DIR}/../rtl/fpu_ss/src)

set(CV32E40X_SOURCE ${DESIGN_RTL_DIR_CV32E40X}/include/cv32e40x_pkg.sv                  #Sources Needed for CV32E40X
                    ${DESIGN_RTL_DIR_CV32E40X}/if_c_obi.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/if_xif.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/../bhv/cv32e40x_sim_clock_gate.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_core.sv 
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_a_decoder.sv 
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_alignment_buffer.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_alu.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_alu_b_cpop.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_b_decoder.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_clic_int_controller.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_compressed_decoder.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_controller.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_controller_bypass.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_controller_fsm.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_csr.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_cs_registers.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_data_obi_interface.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_decoder.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_div.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_ex_stage.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_ff_one.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_i_decoder.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_id_stage.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_if_stage.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_instr_obi_interface.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_int_controller.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_load_store_unit.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_lsu_response_filter.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_m_decoder.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_mpu.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_mult.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_pc_target.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_pma.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_popcnt.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_prefetcher.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_prefetch_unit.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_register_file.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_register_file_wrapper.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_sequencer.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_sleep_unit.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_wb_stage.sv
                    ${DESIGN_RTL_DIR_CV32E40X}/cv32e40x_write_buffer.sv
                    )
               

set(CV32E40X_INCLUDE ${DESIGN_RTL_DIR_CV32E40X}                                         #CV32E40X Include Dirs
                    ${DESIGN_RTL_DIR_CV32E40X}/include
                    ${DESIGN_RTL_DIR_CV32E40X}/../bhv)
                   
set(FPU_SS_SOURCE   ${DESIGN_RTL_DIR_FPU_SS}/fpu_ss_pkg.sv                              #FPU_SS Sources
                    ${DESIGN_RTL_DIR_FPU_SS}/fpu_ss_prd_f_pkg.sv
                    ${DESIGN_RTL_DIR_FPU_SS}/fpu_ss_prd_f_zfh_pkg.sv
                    ${DESIGN_RTL_DIR_FPU_SS}/fpu_ss_prd_zfinx_pkg.sv
                    ${DESIGN_RTL_DIR_FPU_SS}/fpu_ss_instr_pkg.sv
                    ${DESIGN_RTL_DIR_FPU_SS}/fpu_ss.sv
                    ${DESIGN_RTL_DIR_FPU_SS}/fpu_ss_compressed_predecoder.sv
                    ${DESIGN_RTL_DIR_FPU_SS}/fpu_ss_controller.sv
                    ${DESIGN_RTL_DIR_FPU_SS}/fpu_ss_csr.sv
                    ${DESIGN_RTL_DIR_FPU_SS}/fpu_ss_decoder.sv
                    ${DESIGN_RTL_DIR_FPU_SS}/fpu_ss_predecoder.sv
                    ${DESIGN_RTL_DIR_FPU_SS}/fpu_ss_regfile.sv )


set(FPU_SS_INCLUDE  ${DESIGN_RTL_DIR_FPU_SS} )                                          #FPU_SS Include Dirs


set(VICUNA_TOP_DIR  ${CMAKE_CURRENT_SOURCE_DIR}/../rtl/vproc_rtl )  
add_subdirectory(${VICUNA_TOP_DIR} vicuna) # Include vicuna and cvfpu with VICUNA_SRCS, VICUNA_INCS

### TRACE FLAGS

if(TRACE)
    add_definitions(-DTRACE_VCD) #Add flag for C++ sources.
    set(TRACE TRACE)
    
    if(TRACE_FULL)
        set(TRACE_FLAG  ) #no --trace-depth flag defaults to entire model
    else()
        set(TRACE_FLAG --trace-depth 2)
    endif()
endif()

### Experimental Features flags
if(OLD_VICUNA)
    set(VICUNA_MODE -DOLD_VICUNA)
endif()

if(FORCE_ALIGNED_READS)
    set(READ_MODE -DFORCE_ALIGNED_READS)
endif()

#Create the verilated model.  Include verilator_main.cpp and verilator_support.h functions 
add_executable(verilated_model)

target_include_directories(verilated_model PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${VICUNA_TOP_DIR})

target_sources(verilated_model PUBLIC
    ${VICUNA_TOP_DIR}/verilator_support.h
    ${VICUNA_TOP_DIR}/verilator_support.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/verilator_main.cpp)

verilate(verilated_model SOURCES  ${CV32E40X_SOURCE} ${VICUNA_SRCS} ${FPU_SS_SOURCE} ${CMAKE_CURRENT_SOURCE_DIR}/vproc_top.sv
               INCLUDE_DIRS  ${CV32E40X_INCLUDE} ${VICUNA_INCS} ${FPU_SS_INCLUDE} ${CMAKE_CURRENT_SOURCE_DIR}
               TOP_MODULE vproc_top 
               PREFIX Vvproc_top
               ${TRACE}                                    
               VERILATOR_ARGS -cc -exe verilator_main.cpp --unroll-count 1024
                              -Wno-WIDTH -Wno-PINMISSING -Wno-UNOPTFLAT   
	                          -Wno-UNSIGNED -Wno-IMPLICIT -Wno-LITENDIAN -Wno-CASEINCOMPLETE        
	                          -Wno-SYMRSVDWORD -Wno-BLKANDNBLK -Wno-BLKSEQ -Wno-SYNCASYNCNET        
	                          -Wno-COMBDLY 
	                          -Wno-WIDTHCONCAT         
                              #+define+COREV_ASSERT_OFF       #Fixes UVM error with CV32E40X (Needed when not using -DVPROC_SVA)
	                          --clk clk_i
	                          ${TRACE_FLAG} 
	                          --assert -DVPROC_SVA
                              -GMEM_W=${MEM_W} -GVMEM_W=${VMEM_W}
                              ${VICUNA_MODE}
                              ${READ_MODE}
                              ${XIF_FLAG}
                              ${RISCV_F}
                              ${RISCV_ZFH}
                              ${RISCV_ZVE32X}
                              ${RISCV_ZVE32F}
                              ${RISCV_ZVFH}
                              -CFLAGS "-std=gnu++14 -O2")
                              
