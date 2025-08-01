# Vicuna TinyML Benchmarking

### Overview

This repository contains the system for running TinyML Benchmarks on a system with the CV32E40X scalar core and Vicuna 2.0 on the CV-X-IF interface.  It currently supports two benchmarks from the [MLPerfTiny Suite](https://github.com/mlcommons/tiny), anomaly detection (toycar) and keyword spotting (aww).

Due to the limitations of CMake support for native and cross-compiliation within the same project, two separate CMake projects are used.  The first, defined in the **/build_model** directory, uses Verilator version v5.030 to create a executable Verilator model of Vicuna for the selected configuration.  The second, defined in **/build_benchmarks**, uses the LLVM version 18.1.4 and [Tensorflow Lite for Microcontrollers](https://github.com/tensorflow/tflite-micro) to compile the benchmarks for the selected configuration of Vicuna.  Each compiled benchmark is registered with CTest.

### Directory Structure

- **/CMake**              : directory containing CMake helper files
- **/benchmark_sources**  : directory containing benchmark source files and benchmark generators
- **/bsp**                : directory containing support libraries and linker files
- **/build_benchmarks**   : build directory for benchmark code
- **/build_model**        : build directory for verilator model
- **/rtl**                : directory containing rtl submodules
- **/scripts**            : directory containing support scripts for setup and analysis


### Getting Started

The following steps should be followed in order to perform basic testing using this repository.

1. In the top level directory for the repository, initialize all submodules

```
git submodule update --init --recursive
```

2. Initialize the toolchain and other non-submodule dependencies (LLVM, GCC, Verilator, TFLM).  A setup script is provided which will also create and populate the required **/Toolchain** directory

```
./scripts/setup_toolchain.sh

```
3. Once the repository has been initialized, a verilator model of the desired dual-pipeline configuration can be built.

```
cd build_model
mkdir build
cd build
cmake .. -DRISCV_ARCH=**RISCV_ARCH** -DVREG_W=**VREG_W** -DVLANE_W=**VLANE_W** -DVMEM_W=**VMEM_W** -DTRACE=**ON/OFF** -DTRACE_FULL=**ON/OFF**
make
```

The arguments for the model CMake project are as follows:

- RISCV_ARCH : the RISC-V architecture of the system to simulate.  Accepted values are "rv32im", "rv32imf", "rv32imf_zfh", "rv32im_zve32x", "rv32imf_zve32f", "rv32imf_zfh_zve32f_zvfh".  Architectures without vector support will only build a scalar system without Vicuna.
- VREG_W     : the width of the vector registers in bits.
- VLANE_W    : the width of the vector pipeline containing all functional units in bits.
- VMEM_W     : the width of the vector pipeline containing the vector Load/Store unit in bits.  Also sets the width of the main data memory port.
- TRACE      : enable VCD trace outputs for the top two levels of the models.  Provides interface signals and program counter information.  Files can be large.
- TRACE_FULL : enable full VCD trace outputs.  Provides traces for all signals in the model. Files can be extremely large.

4. After a verilated model as been built, the benchmarks can be built and run.

```
cd build_benchmarks
mkdir build
cd build
cmake .. -DRISCV_ARCH=**RISCV_ARCH** -DMIN_VLEN=**MIN_VLEN** -DMEM_W=**MEM_W** -DTRACE=**ON/OFF**
make
```

The arguments for the benchmarks CMake project are as follows.  For proper results, they should match the arguments given to the model CMake project:

- RISCV_ARCH : the RISC-V architecture for the compiler to use.  Accepted values are "rv32im", "rv32imf", "rv32imf_zfh", "rv32im_zve32x", "rv32imf_zve32f", "rv32imf_zfh_zve32f_zvfh".
- MIN_VLEN   : the minimum VLEN argument used by the LLVM autovectorizer. Ignored if a scalar architecture is selected
- MEM_W      : the width of the data memory interface.
- TRACE      : enable VCD trace outputs.  Files can be large.

5. All benchmarks valid for the chosen RISC-V Architecture are added to CTest.  These can be run with the following:

```
ctest
```

Simulation results and traces are available in the **/build_benchmarks/build/Testing** directory after running the tests




