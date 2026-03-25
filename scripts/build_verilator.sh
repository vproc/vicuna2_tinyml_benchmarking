#!/bin/bash


INSTALL_PATH=$PWD/verilator

cd ../toolchain

#Download
git clone https://github.com/verilator/verilator
unset VERILATOR_ROOT
cd verilator
#git checkout tags/v4.210 # unique_ptr issue with new Ubuntu 24.  known issue, Verilator suggestion is to upgrade
git checkout tags/v5.030
autoconf
./configure --prefix $INSTALL_PATH
make -j8
