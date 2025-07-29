


total_cycles = 0

rv32_major_opcode_key = [
    [0x00000073, "system"],
    [0x0000000f, "fence"],
    [0x00000033, "op"],
    [0x00000013, "op-imm"],
    [0x00000023, "store"],
    [0x00000003, "load"],
    [0x00000063, "branch"],
    [0x00000067, "jalr"],
    [0x0000006f, "jal"],
    [0x00000017, "auipc"],
    [0x00000037, "lui"],
    [0x0000002F, "amo"],
    [0x00000007, "load-fp"],
    [0x00000027, "store-fp"],
    [0x00000057, "vector"],
    [0x00000043, "fmadd"],
    [0x0000004F, "fnmadd"],
    [0x00000047, "fmsub"],
    [0x0000004B, "fnmsub"],
    [0x00000053, "op-fp"],
    ]


rv32_imm_opcode_key = [
    [0x0000]
    ]

rv32_vector_opcode_key = [
    [0x00000000, "vadd.vv"],
    [0x00003000, "vadd.vi"],
    [0x00004000, "vadd.vx"],
    [0x00002000, "vredsum.vs"],
    [0x08000000, "vsub.vv"],
    [0x08004000, "vsub.vx"],
    [0x08004000, "vredor.vv"],
    [0x0C003000, "vrsub.vi"],
    [0x0C004000, "vrsub.vx"],
    [0x10000000, "vminu.vv"],
    [0x10004000, "vminu.vx"],
    [0x14000000, "vmin.vv"],
    [0x14004000, "vmin.vx"],
    [0x40000000, "vadc.vv"],
    [0x40003000, "vadc.vi"],
    [0x40004000, "vadc.vx"],
    [0x40002000, "vmv.x.s"], #possibly popc or vfirst
    [0x40006000, "vmv.s.x"],
    [0x5C000000, "vmv/vmerge.vv"],
    [0x5C003000, "vmv/vmerge.vi"],
    [0x5C004000, "vmv/vmerge.vx"],
    [0x5C002000, "vcompress.vv"],
    [0x48000000, "vsbc.vv"],
    [0x48003000, "vsbc.vi"],
    [0x48004000, "vsbc.vx"],
    [0x48002000, "v[z|s]ext"],
    [0xB4000000, "vnsra.vv"],
    [0xB4003000, "vnsra.vi"],
    [0xB4004000, "vnsra.vx"],
    [0xB4002000, "vmacc.vv"],
    [0xB4006000, "vmacc.vx"],
    [0x40001000, "vfmv.fs"],
    [0x5C005000, "vfmv.vf"],
    [0x90002000, "vmulhu.vv"],
    [0x90006000, "vmulhu.vx"],
    [0x90001000, "vfmul.vv"],
    [0x90005000, "vfmul.vf"],
    [0x0C003000, "vrsub.vi"],
    [0x0C004000, "vrsub.vx"],
    [0x0C001000, "vfredosum.vv"],
    [0x0C002000, "vredxor.vv"],
    [0x9C003000, "vmv<nr>r.vi"],
    [0x9C002000, "vmulh.vv"],
    [0x9C006000, "vmulh.vx"],
    [0x9C000000, "vsmul.vv"],
    [0x9C004000, "vsmul.vx"],
    [0x9C005000, "vfrsub.vf"],
    [0x08001000, "vfsub.vv"],
    [0x08005000, "vfsub.vx"]
]



current_inst_log = []

#vsetvl(i) instructions follow different opcode scheme.  These are checked first.  For simplicity, already add this to log list (there should always be one of these present anyways)
current_vector_log = [
    ["vsetvl(i)", 0, 0]
]


# For logs of fp opcodes, follow different approach due to use of multiple different fields to determine type of instruction
load_fp_log = [
    [0, 0, "unit-stride"],
    [0, 0, "unit-stride segmented"],
    [0, 0, "unit-stride whole register"],
    [0, 0, "unit-stride segmented whole register"],
    [0, 0, "unit-stride mask load EEW=8"],
    [0, 0, "unit-stride segmented mask load EEW=8"],
    [0, 0, "unit-stride fault-only-first"],
    [0, 0, "unit-stride segmented fault-only-first"],
    [0, 0, "indexed-unordered"],
    [0, 0, "indexed-unordered segmeneted"],
    [0, 0, "strided"],
    [0, 0, "strided segmented"],
    [0, 0, "indexed-ordered"],
    [0, 0, "indexed-ordered segmented"],
    [0, 0, "other"],
    [0, 0, "Scalar FP Load"],
    [0, 0, "Scalar HFP Load"]
]

store_fp_log = [
    [0, 0, "unit-stride"],
    [0, 0, "unit-stride segmented"],
    [0, 0, "unit-stride whole register"],
    [0, 0, "unit-stride segmented whole register"],
    [0, 0, "unit-stride mask store EEW=8"],
    [0, 0, "unit-stride segmented mask load EEW=8"],
    [0, 0, "indexed-unordered"],
    [0, 0, "indexed-unordered segmeneted"],
    [0, 0, "strided"],
    [0, 0, "strided segmented"],
    [0, 0, "indexed-ordered"],
    [0, 0, "indexed-ordered segmented"],
    [0, 0, "other"],
    [0, 0, "Scalar FP Store"],
    [0, 0, "Scalar HFP Store"],
]
log = open("/home/parker/Desktop/Vicuna_Repo_Refactor/benchmarks/tinyml_benchmarks/build_benchmarks/build/Testing/inst_trace.txt", "r")

#for every line in log
new_pc = False
for line in log :

    #check if current cycle is a stall cycle
    if (not (line.find("NEW PC") == -1)):
        new_pc=True
        continue

    total_cycles += 1

    instr = int(line, 16)
    opcode_mask = int ("0000007f", 16)
    opcode = instr & opcode_mask
    instr_identified = False
    #check to see if opcode matches
    for op_key in rv32_major_opcode_key :

        if (op_key[0] == opcode):
            # if it matches, increment counter
            instr_identified = True
            instr_added = False
            for cur in current_inst_log:
                if (cur[0] == op_key[1]):
                    instr_added = True
                    cur[1] += 1
                    if (new_pc):
                        cur[2]+= 1


            if (not instr_added) :
                current_inst_log.append([op_key[1], 1, 1])

            #parse specific opcode to determine instruction type
            #LOAD FP
            if (op_key[1] == "load-fp"):

                width_mask = int ("00007000", 16)
                match instr & width_mask:
                    case 0x00002000:
                        load_fp_log[15][0]+=1 #Scalar FP Load
                        if (new_pc):
                            load_fp_log[15][1]+=1

                    case 0x00001000:
                        load_fp_log[16][0]+=1 #Scalar HFP Load
                        if (new_pc):
                            load_fp_log[16][1]+=1
                    case _:

                        mop_mask = int ("0C000000", 16)
                        match instr & mop_mask:
                            case 0x00000000:
                                #unit stride has another opcode option
                                lumop_mask = int ("01F00000", 16)
                                match instr & lumop_mask:
                                    case 0x00000000:
                                        #Determine if segmented or not
                                        nf_mask = int ("E0000000", 16)
                                        match instr & nf_mask:
                                            case 0x00000000:
                                                load_fp_log[0][0]+=1 #unit stride load
                                                if (new_pc):
                                                    load_fp_log[0][1]+=1
                                            case _:
                                                load_fp_log[1][0]+=1 #unit stride segmented load
                                                if (new_pc):
                                                    load_fp_log[1][1]+=1
                                    case 0x00800000:
                                        #Determine if segmented or not
                                        nf_mask = int ("E0000000", 16)
                                        match instr & nf_mask:
                                            case 0x00000000:
                                                load_fp_log[2][0]+=1 #unit stride whole register load
                                                if (new_pc):
                                                    load_fp_log[2][1]+=1
                                            case _:
                                                load_fp_log[3][0]+=1 #unit stride whole register segmented load
                                                if (new_pc):
                                                    load_fp_log[3][1]+=1

                                    case 0x00B00000:
                                            #Determine if segmented or not
                                        nf_mask = int ("E0000000", 16)
                                        match instr & nf_mask:
                                            case 0x00000000:
                                                load_fp_log[4][0]+=1 #unit stride mask load eew=8
                                                if (new_pc):
                                                    load_fp_log[4][1]+=1
                                            case _:
                                                load_fp_log[5][0]+=1 #unit stride mask load eew=8 segmented
                                                if (new_pc):
                                                    load_fp_log[5][1]+=1
                                    case 0x01000000:
                                            #Determine if segmented or not
                                        nf_mask = int ("E0000000", 16)
                                        match instr & nf_mask:
                                            case 0x00000000:
                                                load_fp_log[6][0]+=1 #unit stride fault only first
                                                if (new_pc):
                                                    load_fp_log[6][1]+=1
                                            case _:
                                                load_fp_log[7][0]+=1 #unit stride fault only first segmented
                                                if (new_pc):
                                                    load_fp_log[7][1]+=1
                                    case _:
                                        load_fp_log[14][0]+=1 #Unknown
                                        if (new_pc):
                                            load_fp_log[14][1]+=1


                            case 0x04000000:
                                #Determine if segmented or not
                                nf_mask = int ("E0000000", 16)
                                match instr & nf_mask:
                                    case 0x00000000:
                                        load_fp_log[8][0]+=1 #indexed_unordered
                                        if (new_pc):
                                            load_fp_log[8][1]+=1
                                    case _:
                                        load_fp_log[9][0]+=1 #indexed_unordered segmented
                                        if (new_pc):
                                            load_fp_log[9][1]+=1

                            case 0x08000000:
                                #Determine if segmented or not
                                nf_mask = int ("E0000000", 16)
                                match instr & nf_mask:
                                    case 0x00000000:
                                        load_fp_log[10][0]+=1 #strided
                                        if (new_pc):
                                            load_fp_log[10][1]+=1
                                    case _:
                                        load_fp_log[11][0]+=1 #strided segmented
                                        if (new_pc):
                                            load_fp_log[11][1]+=1

                            case 0x0C000000:
                                #Determine if segmented or not
                                nf_mask = int ("E0000000", 16)
                                match instr & nf_mask:
                                    case 0x00000000:
                                        load_fp_log[12][0]+=1 #indexed-ordered
                                        if (new_pc):
                                            load_fp_log[12][1]+=1
                                    case _:
                                        load_fp_log[13][0]+=1 #indexed-ordered segmented
                                        if (new_pc):
                                            load_fp_log[13][1]+=1

                            case _:
                                load_fp_log[14][0]+=1 #Unknown
                                if (new_pc):
                                    load_fp_log[14][1]+=1
            #store FP     
            elif (op_key[1] == "store-fp"):
                width_mask = int ("00007000", 16)
                match instr & width_mask:
                    case 0x00002000:
                        store_fp_log[13][0]+=1 #Scalar FP Load
                        if (new_pc):
                            store_fp_log[13][1]+=1

                    case 0x00001000:
                        store_fp_log[14][0]+=1 #Scalar HFP Load
                        if (new_pc):
                            store_fp_log[14][1]+=1
                    case _:
                        mop_mask = int ("0C000000", 16)
                        match instr & mop_mask:
                            case 0x00000000:
                                #unit stride has another opcode option
                                lumop_mask = int ("01F00000", 16)
                                match instr & lumop_mask:
                                    case 0x00000000:
                                        #Determine if segmented or not
                                        nf_mask = int ("E0000000", 16)
                                        match instr & nf_mask:
                                            case 0x00000000:
                                                store_fp_log[0][0]+=1 #unit stride load
                                                if (new_pc):
                                                    store_fp_log[0][1]+=1
                                            case _:
                                                store_fp_log[1][0]+=1 #unit stride segmented load
                                                if (new_pc):
                                                    store_fp_log[1][1]+=1
                                    case 0x00800000:
                                        #Determine if segmented or not
                                        nf_mask = int ("E0000000", 16)
                                        match instr & nf_mask:
                                            case 0x00000000:
                                                store_fp_log[2][0]+=1 #unit stride whole register load
                                                if (new_pc):
                                                    store_fp_log[2][1]+=1
                                            case _:
                                                store_fp_log[3][0]+=1 #unit stride whole register segmented load
                                                if (new_pc):
                                                    store_fp_log[3][1]+=1

                                    case 0x00B00000:
                                            #Determine if segmented or not
                                        nf_mask = int ("E0000000", 16)
                                        match instr & nf_mask:
                                            case 0x00000000:
                                                store_fp_log[4][0]+=1 #unit stride mask load eew=8
                                                if (new_pc):
                                                    store_fp_log[4][1]+=1
                                            case _:
                                                store_fp_log[5][0]+=1 #unit stride mask load eew=8 segmented
                                                if (new_pc):
                                                    store_fp_log[5][1]+=1
                                    case _:
                                        store_fp_log[12][0]+=1 #Unknown
                                        if (new_pc):
                                            store_fp_log[12][1]+=1


                            case 0x04000000:
                                #Determine if segmented or not
                                nf_mask = int ("E0000000", 16)
                                match instr & nf_mask:
                                    case 0x00000000:
                                        store_fp_log[6][0]+=1 #indexed_unordered
                                        if (new_pc):
                                            store_fp_log[6][1]+=1
                                    case _:
                                        store_fp_log[7][0]+=1 #indexed_unordered segmented
                                        if (new_pc):
                                            store_fp_log[7][1]+=1

                            case 0x08000000:
                                #Determine if segmented or not
                                nf_mask = int ("E0000000", 16)
                                match instr & nf_mask:
                                    case 0x00000000:
                                        store_fp_log[8][0]+=1 #strided
                                        if (new_pc):
                                            store_fp_log[8][1]+=1
                                    case _:
                                        store_fp_log[9][0]+=1 #strided segmented
                                        if (new_pc):
                                            store_fp_log[9][1]+=1

                            case 0x0C000000:
                                #Determine if segmented or not
                                nf_mask = int ("E0000000", 16)
                                match instr & nf_mask:
                                    case 0x00000000:
                                        store_fp_log[10][0]+=1 #indexed-ordered
                                        if (new_pc):
                                            store_fp_log[10][1]+=1
                                    case _:
                                        store_fp_log[11][0]+=1 #indexed-ordered segmented
                                        if (new_pc):
                                            store_fp_log[11][1]+=1

                            case _:
                                store_fp_log[12][0]+=1 #Unknown
                                if (new_pc):
                                    store_fp_log[12][1]+=1

            elif (op_key[1] == "vector"):

                vsetvl_mask = int ("00007000", 16)

                if ( (instr & vsetvl_mask) == 0x00007000):
                    current_vector_log[0][1]+=1  #vsetvl always placed at beginning of log
                    if (new_pc):
                        current_vector_log[0][2]+=1
                else:
                    vector_identified = False
                    vector_mask = int ("FC007000", 16)
                    cur_vector_opcode = instr & vector_mask
                    for vector_op in rv32_vector_opcode_key:

                        if vector_op[0] == cur_vector_opcode:
                            vector_identified = True
                            instr_added = False
                            for cur_vec in current_vector_log:
                                if (cur_vec[0] == vector_op[1]):
                                    instr_added = True
                                    cur_vec[1] += 1
                                    if (new_pc):
                                        cur_vec[2]+=1

                            if (not instr_added) :
                                current_vector_log.append([vector_op[1], 1, 1])
                                print(vector_op[1])
                                strHex = "0x%0.8X" % instr
                                print(strHex)

                    if (not vector_identified):
                        current_vector_log.append([cur_vector_opcode, 1, 1])
                        strHex = "0x%0.8X" % cur_vector_opcode
                        print(strHex)
                    

        
    
    # If the instruction is not identified, append instr code   
    if (not instr_identified) :
        hex_instr = "0x%0.8X" % instr
        current_inst_log.append([hex_instr, 1, 1])
        print(hex_instr)
    #To get here, new pc needs to be set to false (stall or already processed new pc)
    new_pc=False

            




print("Total Cycles = " + str(total_cycles) + "\n")
for instr in current_inst_log:
    print(instr)
    print("Percentage of Total = " + str(instr[1]/total_cycles * 100))
    print("CPI = " + str(instr[1]/instr[2]) + "\n")


print("\nLOAD-FP:\n")
for instr in load_fp_log:
    if (not (instr[0] == 0)):
        print(instr)
        print("Percentage of Total = " + str(instr[0]/total_cycles * 100))
        print("CPI = " + str(instr[0]/instr[1]) + "\n")

print("\nSTORE-FP:\n")
for instr in store_fp_log:
    if (not (instr[0] == 0)):
        print(instr)
        print("Percentage of Total = " + str(instr[0]/total_cycles * 100))
        print("CPI = " + str(instr[0]/instr[1]) + "\n")


print("\nVECTOR:\n")
for instr in current_vector_log:
    print(instr)
    print("Percentage of Total = " + str(instr[1]/total_cycles * 100))
    print("CPI = " + str(instr[1]/instr[2]) + "\n")



