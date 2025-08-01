# Copyright TU Wien
# Licensed under the Solderpad Hardware License v2.1, see LICENSE.txt for details
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1


.section .vectors, "ax", @progbits
.option norvc;

    # redirect all interrupts to the execption wrapper
    .rept 29
    nop
    .endr
    nop
    nop                # failed tests jump here.  Spike failure means total failure of unit test, abort
    nop

    # the reset vector is redirected to _start
    j _start

.text
.align 10
.global _start
_start:
    csrr            a0, mstatus
    li              a1, 0x00002200      #Init FS bits to enable F-EXT and VS bits to enable V-EXT
    or              a0, a0, a1
    csrw            mstatus, a0
    j main


    .data
    .align 10
    .global tohost
    .global fromhost
tohost:
    .word 0x00000000
fromhost:
    .word 0x00000000




