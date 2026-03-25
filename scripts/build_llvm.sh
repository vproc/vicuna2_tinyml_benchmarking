#!/bin/bash
#
# Copyright (C) 2024 TUWien
#
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the License); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an AS IS BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

set -e

cd ../toolchain


echo "Downloading LLVM"
if [ -d $PWD/llvm-project ]; then
    echo "LLVM source already downloaded. Cleaning it up"
    cd llvm-project
    make clean
else
    git clone https://github.com/llvm/llvm-project.git
    cd llvm-project
    git checkout tags/llvmorg-18.1.4
fi

ls
#cmake -S llvm -B build -DCMAKE_INSTALL_PREFIX=$PWD/../llvm-18 -DCMAKE_C_COMPILER=clang  -DCMAKE_CXX_COMPILER=clang++ -DCMAKE_BUILD_TYPE=Release -DLLVM_TARGETS_TO_BUILD="RISCV" -DLLVM_ENABLE_PROJECTS="clang;lld"  -DLLVM_DEFAULT_TARGET_TRIPLE="riscv32-unknown-elf" -DLLVM_INSTALL_TOOLCHAIN_ONLY=On -G Ninja

#cmake --build  <LLVM_BUILD_PATH> --target install

 cmake -B $PWD/../llvm-18 -DCMAKE_INSTALL_PREFIX=$PWD/../llvm-18 -DCMAKE_C_COMPILER=clang  -DCMAKE_CXX_COMPILER=clang++ -DCMAKE_BUILD_TYPE=Release -DLLVM_TARGETS_TO_BUILD="RISCV" -DLLVM_ENABLE_PROJECTS="clang;lld"  -DLLVM_DEFAULT_TARGET_TRIPLE="riscv32-unknown-linux-gnu" -DLLVM_INSTALL_TOOLCHAIN_ONLY=On -DDEFAULT_SYSROOT=../sysroot -G Ninja $PWD/llvm

 cmake --build  $PWD/../llvm-18 --target install
