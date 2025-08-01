#######
# Macro for adding a tinyml benchmark to CTest
#######

macro(add_Benchmark TEST SOURCE_DIR TEST_BUILD_DIR)

    set(TEST_NAME ${TEST}) #need to add a suffix, ctest doesnt allow 'test' as a test name
    
    add_executable(${TEST_NAME})

    target_include_directories(${TEST_NAME} PRIVATE
        ${SOURCE_DIR}
        ${SOURCE_DIR}/model_data
    )

    target_sources(${TEST_NAME} PUBLIC
        ${SOURCE_DIR}/${TEST}.cpp
        ${SOURCE_DIR}/${TEST}_data/${TEST}_input_data.cc
        ${SOURCE_DIR}/${TEST}_data/${TEST}_input_data.h
        ${SOURCE_DIR}/${TEST}_data/${TEST}_model_data.cc
        ${SOURCE_DIR}/${TEST}_data/${TEST}_model_data.h
        ${SOURCE_DIR}/${TEST}_data/${TEST}_model_settings.cc
        ${SOURCE_DIR}/${TEST}_data/${TEST}_model_settings.h
        ${SOURCE_DIR}/${TEST}_data/${TEST}_output_data_ref.cc
        ${SOURCE_DIR}/${TEST}_data/${TEST}_output_data_ref.h
    )

    #Set Linker
    target_link_options(${TEST_NAME} PRIVATE "-nostartfiles")

    target_link_options(${TEST_NAME} PRIVATE "-T${BSP_TOP}/lld_link.ld")


    #Link BSP
    target_link_libraries(${TEST_NAME} PRIVATE bsp_Vicuna UART_Vicuna tflm)

    add_custom_command(TARGET ${TEST_NAME}
                       POST_BUILD
                       COMMAND ${RISCV_LLVM_PREFIX}/llvm-objcopy -O binary ${TEST_NAME}.elf ${TEST_NAME}.bin
                       COMMAND srec_cat ${TEST_NAME}.bin -binary -offset 0x0000 -byte-swap 4 -o ${TEST_NAME}.vmem -vmem
                       COMMAND rm -f prog_${TEST_NAME}.txt
                       COMMAND echo -n "${TEST_BUILD_DIR}/${TEST_NAME}.vmem ${TEST_BUILD_DIR}/${TEST_NAME}_unused.txt " > prog_${TEST_NAME}.txt
                       COMMAND readelf -s ${TEST_NAME}.elf | sed '2,13 s/ //1' | grep vref_start | cut -d " " -f 6 | tr [=["\n"]=] " " >> prog_${TEST_NAME}.txt
                       COMMAND readelf -s ${TEST_NAME}.elf | sed '2,13 s/ //1' | grep vref_end | cut -d " " -f 6 | tr [=["\n"]=] " " >> prog_${TEST_NAME}.txt
                       COMMAND echo -n "${TEST_BUILD_DIR}/${TEST_NAME}_vicuna_sim_out.txt " >> prog_${TEST_NAME}.txt
                       COMMAND readelf -s ${TEST_NAME}.elf | sed '2,13 s/ //1' | grep vdata_start | cut -d " " -f 6 | tr [=["\n"]=] " " >> prog_${TEST_NAME}.txt
                       COMMAND readelf -s ${TEST_NAME}.elf | sed '2,13 s/ //1' | grep vdata_end | cut -d " " -f 6 | tr [=["\n"]=] " " >> prog_${TEST_NAME}.txt
                       COMMAND ${RISCV_LLVM_PREFIX}/llvm-objdump -D ${TEST_NAME}.elf > ${TEST_NAME}_dump.txt
                       )
    
    #VERY DANGEROUS TO USE TRACE
    set(INST_TRACE_ARGS "${BUILD_DIR}/Testing/inst_trace.txt")

    if(TRACE)
        set(MEM_TRACE_ARGS "${BUILD_DIR}/Testing/last_test_mem.csv")
        set(VCD_TRACE_ARGS "${BUILD_DIR}/Testing/last_test_sig.vcd")

    else()
        set(MEM_TRACE_ARGS "")
        set(VCD_TRACE_ARGS "")
    endif()
                       
	              

    #Add Test
    add_test(NAME ${TEST_NAME} 
             COMMAND ./${MODEL_DIR}/verilated_model ${TEST_BUILD_DIR}/prog_${TEST_NAME}.txt ${MEM_W} 4194304 ${MEM_LATENCY} 1 ${INST_TRACE_ARGS} ${MEM_TRACE_ARGS} ${VCD_TRACE_ARGS}  #TODO: PASS ALL THESE ARGUMENTS IN FROM USER
             WORKING_DIRECTORY ${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/../..)
             
    set_tests_properties(${TEST_NAME} PROPERTIES TIMEOUT 0) #TODO: Find a reasonable timeout for these tests

    message(STATUS "Successfully added ${TEST_NAME}")

endmacro()



macro(add_Benchmark_Spike TEST SOURCE_DIR TEST_BUILD_DIR)

    set(TEST_NAME ${TEST}_Spike) #need to add a suffix, ctest doesnt allow 'test' as a test name
    
    add_executable(${TEST_NAME})

    target_include_directories(${TEST_NAME} PRIVATE
        ${SOURCE_DIR}
        ${SOURCE_DIR}/model_data
    )

    target_sources(${TEST_NAME} PUBLIC
        ${SOURCE_DIR}/${TEST}.cpp
        ${SOURCE_DIR}/${TEST}_data/${TEST}_input_data.cc
        ${SOURCE_DIR}/${TEST}_data/${TEST}_input_data.h
        ${SOURCE_DIR}/${TEST}_data/${TEST}_model_data.cc
        ${SOURCE_DIR}/${TEST}_data/${TEST}_model_data.h
        ${SOURCE_DIR}/${TEST}_data/${TEST}_model_settings.cc
        ${SOURCE_DIR}/${TEST}_data/${TEST}_model_settings.h
        ${SOURCE_DIR}/${TEST}_data/${TEST}_output_data_ref.cc
        ${SOURCE_DIR}/${TEST}_data/${TEST}_output_data_ref.h
    )

    #Set Linker
    target_link_options(${TEST_NAME} PRIVATE "-nostartfiles")

    target_link_options(${TEST_NAME} PRIVATE "-T${BSP_TOP}/Spike_Support/lld_link.ld")

    


    #Link BSP
    target_link_libraries(${TEST_NAME} PRIVATE bsp_Spike tflm)   

    add_custom_command(TARGET ${TEST_NAME}
                        COMMAND ${RISCV_LLVM_PREFIX}/llvm-objdump -D ${TEST_NAME}.elf > ${TEST_NAME}_dump.txt)    
	              

    #Add Test
    add_test(NAME ${TEST_NAME} 
             COMMAND ${SPIKE_DIR}/spike --isa=rv32imf_zicntr_zihpm_zfh_zve32f_zvfh_zvl${VREG_W}b ${TEST_BUILD_DIR}/${TEST_NAME}.elf   #TODO: PASS ALL THESE ARGUMENTS IN FROM USER
             WORKING_DIRECTORY ${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/../..)
             
    set_tests_properties(${TEST_NAME} PROPERTIES TIMEOUT 0) #TODO: Find a reasonable timeout for these tests

    message(STATUS "Successfully added ${TEST_NAME}")

endmacro()




