#!/bin/bash

#Top level script to setup dependencies/toolchain.  Each has a helper script to setup which is called here
#
#Necessary dependencies:
#   -verilator:  verilator is built from source.
#   -llvm 18  :  LLVM 18 is built from source
#   -GCC      :  RISCV GCC headers are needed for each supported architecture.  TODO: add these to the sync-and-share system used for muRISCV-nn.  currently built from source
#   -spike    :  the riscv-isa-sim is used to validate vicuna results.  built from source



######
# make Toolchain directory
######

cd ..
if [ -d $PWD/toolchain ]; then
    echo "Toolchain Directory already exists"
else
    echo "Making Toolchain Directory"
    mkdir toolchain
fi
cd scripts
######
#   Verilator setup
######

./build_verilator.sh

######
#   llvm setup
######

./build_llvm.sh


######
#   GCC setup
######

./build_gcc.sh rv32im ilp32
./build_gcc.sh rv32imf ilp32f
./build_gcc.sh rv32imf_zfh ilp32f
./build_gcc.sh rv32im_zve32x ilp32
./build_gcc.sh rv32imf_zve32f ilp32f
./build_gcc.sh rv32imf_zfh_zve32f_zvfh ilp32f

######
#   tflm setup
######

./download_tflm.sh

######
#   spike setup
######

./download_spike.sh
