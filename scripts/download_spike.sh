#!/bin/bash

cd ../Toolchain

#Build GCC
echo "Downloading Spike"
if [ -d $PWD/riscv-isa-sim ]; then
    echo "Spike source already downloaded. Cleaning Up."
    cd riscv-isa-sim
    rm -r build
else
    git clone https://github.com/riscv-software-src/riscv-isa-sim.git
    cd riscv-isa-sim
fi


mkdir build
cd build 
../configure --prefix=$PWD/../riscv
make -j$(nproc)
make install

