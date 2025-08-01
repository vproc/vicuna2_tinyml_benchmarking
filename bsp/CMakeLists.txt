
####
#Add bsp library for Vicuna
####
add_library(bsp_Vicuna STATIC)

target_include_directories(bsp_Vicuna PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}
)

target_sources(bsp_Vicuna PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}/crt0.S
)


add_library(UART_Vicuna STATIC)

target_include_directories(UART_Vicuna PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/lib
)

target_sources(UART_Vicuna PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}/lib/uart.h
  ${CMAKE_CURRENT_SOURCE_DIR}/lib/uart.c
  ${CMAKE_CURRENT_SOURCE_DIR}/lib/vicuna_crt.h
  ${CMAKE_CURRENT_SOURCE_DIR}/lib/vicuna_crt.c
  ${CMAKE_CURRENT_SOURCE_DIR}/lib/terminate_benchmark.h
  ${CMAKE_CURRENT_SOURCE_DIR}/lib/terminate_benchmark.c
)

####
#Add bsp library for Spike Baremetal
####
add_library(bsp_Spike STATIC)

target_include_directories(bsp_Spike PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/Spike_Support
)
target_sources(bsp_Spike PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}/Spike_Support/crt0.S
  ${CMAKE_CURRENT_SOURCE_DIR}/Spike_Support/terminate_benchmark.h
  ${CMAKE_CURRENT_SOURCE_DIR}/Spike_Support/uart.h
  ${CMAKE_CURRENT_SOURCE_DIR}/Spike_Support/terminate_benchmark.c
)


