// Copyright TU Wien
// Licensed under the Solderpad Hardware License v2.1, see LICENSE.txt for details
// SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1


#include <stdio.h>
#include <stdint.h>
#include <errno.h>
#include "Vvproc_top.h"

#include "Vvproc_top_vproc_top.h"
#include "Vvproc_top_cv32e40x_core__pi1.h"
//#include "Vvproc_top_vproc_core__pi2.h"
//#include "Vvproc_top_vproc_decoder__pi9.h"
//#include "Vvproc_top_vproc_decoder__V800_Cb_X20_Dz3.h"
//#include "Vvproc_top_vproc_decoder__V800_Cb_X40_Dz3.h"




#include "verilated.h"

#ifdef TRACE_VCD
#include "verilated_vcd_c.h"
typedef VerilatedVcdC VerilatedTrace_t;
#else
#ifdef TRACE_FST
#include "verilated_fst_c.h"
typedef VerilatedFstC VerilatedTrace_t;
#else
typedef int VerilatedTrace_t;
#endif
#endif

static void log_cycle(Vvproc_top *top, VerilatedTrace_t *tfp, FILE *fcsv);

int main(int argc, char **argv) {
    fprintf(stderr, "Starting Verilator Main()\n");
    
    int exit_code = 0;
    
    if (argc != 6 && argc != 7 && argc != 8 && argc != 9) {
        fprintf(stderr, "Usage: %s PROG_PATHS_LIST MEM_W MEM_SZ MEM_LATENCY EXTRA_CYCLES [INST_TRACE_FILE] [MEM_TRACE_FILE] [WAVEFORM_FILE]\n", argv[0]);
        return 1;
    }
    
    int csv_out = 0;

    fprintf(stderr, "testing: %d\n", argc);

    int inst_trace_out = 0;
    
    if(argc > 7){
        csv_out = 1;
    }

    if(argc > 6){
        inst_trace_out = 1;
    }
    

    int mem_w, mem_sz, mem_latency, extra_cycles;
    {
        char *endptr;
        mem_w = strtol(argv[2], &endptr, 10);
        if (mem_w == 0 || *endptr != 0) {
            fprintf(stderr, "ERROR: invalid MEM_W argument\n");
            return 1;
        }
        mem_sz = strtol(argv[3], &endptr, 10);
        if (mem_sz == 0 || *endptr != 0) {
            fprintf(stderr, "ERROR: invalid MEM_SZ argument\n");
            return 1;
        }
        mem_latency = strtol(argv[4], &endptr, 10);
        if (*endptr != 0) {
            fprintf(stderr, "ERROR: invalid MEM_LATENCY argument\n");
            return 1;
        }
        extra_cycles = strtol(argv[5], &endptr, 10);
        if (*endptr != 0) {
            fprintf(stderr, "ERROR: invalid EXTRA_CYCLES argument\n");
            return 1;
        }
    }

    Verilated::traceEverOn(true);
    //Verilated::commandArgs(argc, argv);

    FILE *fprogs = fopen(argv[1], "r");
    if (fprogs == NULL) {
        fprintf(stderr, "ERROR: opening `%s': %s\n", argv[1], strerror(errno));
        return 2;
    }
    
    FILE *fcsv;
    if (csv_out == 1) {
    
        fcsv = fopen(argv[7], "w");
        if (fcsv == NULL) {
            fprintf(stderr, "ERROR: opening `%s': %s\n", argv[7], strerror(errno));
            return 2;
        }
        fprintf(fcsv, "rst_ni;mem_req;mem_addr;pend_vreg_wr_map_o;\n");
    }

    FILE *inst_trace;
    if (inst_trace_out == 1) {
        inst_trace = fopen(argv[6], "w");
    }

    unsigned char *mem = (unsigned char *)malloc(mem_sz);
    if (mem == NULL) {
        fprintf(stderr, "ERROR: allocating %d bytes of memory: %s\n", mem_sz, strerror(errno));
        return 3;
    }

    int32_t *mem_rvalid_queue = (int32_t *)malloc(sizeof(int32_t) * mem_latency);
    unsigned char **mem_rdata_queue  = (unsigned char **)malloc(sizeof(unsigned char *) * mem_latency); //memory data port
    int32_t *mem_err_queue    = (int32_t *)malloc(sizeof(int32_t) * mem_latency);

    for(int queue_pos = 0; queue_pos < mem_latency; queue_pos++)
    {
        mem_rdata_queue[queue_pos] = (unsigned char *)malloc(sizeof(unsigned char) * mem_w/8);
    }

    int32_t *mem_ivalid_queue = (int32_t *)malloc(sizeof(int32_t) * mem_latency);
    int32_t *mem_idata_queue    = (int32_t *)malloc(sizeof(int32_t) * mem_latency);                     //memory instruction port
    int32_t *mem_ierr_queue    = (int32_t *)malloc(sizeof(int32_t) * mem_latency);

    Vvproc_top *top = new Vvproc_top;
    VerilatedTrace_t *tfp = NULL;
#if defined(TRACE_VCD) || defined(TRACE_FST)
    if (argc == 9) {
        tfp = new VerilatedTrace_t;
        top->trace(tfp, 99);  // Trace 99 levels of hierarchy
        tfp->open(argv[8]);
    }
#endif

    char *line = NULL, *prog_path = NULL, *ref_path = NULL, *dump_path = NULL;
    size_t line_sz = 0;
    while (getline(&line, &line_sz, fprogs) > 0) {
        // allocate sufficient storage space for the four paths (length of the
        // line, or at least 32 bytes)
        if (line_sz < 32) {
            line_sz = 32;
        }
        prog_path = (char *)realloc(prog_path, line_sz);
        ref_path  = (char *)realloc(ref_path,  line_sz);
        dump_path = (char *)realloc(dump_path, line_sz);
        strcpy(ref_path,  "/dev/null");
        strcpy(dump_path, "/dev/null");

        int ref_start  = 0,
            ref_end    = 0,
            dump_start = 0,
            dump_end   = 0,
            items;
        items = sscanf(line, "%s %s %x %x %s %x %x", prog_path, ref_path, &ref_start, &ref_end, dump_path, &dump_start, &dump_end);
        if (items == 0 || items == EOF) {
            continue;
        }

        // read program file
        {
            FILE *ftmp = fopen(prog_path, "r");
            if (ftmp == NULL) {
                fprintf(stderr, "WARNING: skipping `%s': %s\n", prog_path, strerror(errno));
                continue;
            }
            memset(mem, 0, mem_sz);
            char buf[256];
            int addr = 0;
            while (fgets(buf, sizeof(buf), ftmp) != NULL) {
                if (buf[0] == '#' || buf[0] == '/')
                    continue;
                char *ptr = buf;
                if (buf[0] == '@') {
                    addr = strtol(ptr + 1, &ptr, 16) * 4;
                    while (*ptr == ' ')
                        ptr++;
                }
                while (*ptr != '\n' && *ptr != 0) {
                    int data = strtol(ptr, &ptr, 16);
                    int i;
                    for (i = 0; i < 4; i++)
                        mem[addr+i] = data >> (8*i);
                    addr += 4;
                    while (*ptr == ' ')
                        ptr++;
                }
            }
            fclose(ftmp);
        }

        // write reference file
        {
            FILE *ftmp = fopen(ref_path, "w");
            if (ftmp == NULL) {
                fprintf(stderr, "ERROR: opening `%s': %s\n", ref_path, strerror(errno));
            }
            int addr;
            for (addr = ref_start; addr < ref_end; addr += 4) {
                int data = mem[addr] | (mem[addr+1] << 8) | (mem[addr+2] << 16) | (mem[addr+3] << 24);
                fprintf(ftmp, "%08x\n", data);
            }
            fclose(ftmp);
        }

        // simulate program execution
        {
            int i;
            for (i = 0; i < mem_latency; i++) {
                mem_rvalid_queue[i] = 0;
            }
            top->mem_rvalid_i = 0;
            top->clk_i        = 0;
            top->rst_ni       = 0;
            for (i = 0; i < 10; i++) {
                top->clk_i = 1;
                top->eval();
                top->clk_i = 0;
                top->eval();
                if (csv_out == 1) {
                    log_cycle(top, tfp, fcsv);
                }
            }
            top->rst_ni = 1;
            top->eval();

            int end_cnt    = 0, // count number of cycles after address 0 was requested
                abort_cnt  = 0; // count number of cycles since mem_req_o last toggled
                
            
            
            bool main_reached = true; //detect if main has been reached to begin collecting statistics
            bool exiting = false;
            
            //Variables for stall detection
            int current_IF_PC = 0;
            int last_IF_PC = 0;
            int cycles_stalled = 0;
            
            
            //Variables for processor metrics
            int cycles = 0;         //Cycle count
            int current_WB_PC = 0;
            int last_WB_PC = 0;
            int instructions = 0;   //Instruction Count
            
            
            int cycles_stalled_XIF = 0; //Cycles stalled due to waiting for a result from the XIF interface
            int cycles_stalled_XIF_loadstore = 0; //Cycles stalled due to a load/store on the XIF interface
            
            int instr_offloaded_count = 0;
            int vector_loads = 0;
            int vector_stores = 0;
            int other_vector_ops = 0;
            
            //avg vector length calcs
            int sum_vec_lengths = 0;
            int sum_vec_lengths_bytes = 0;
            float sum_vec_percentage = 0.0;
            int num_vec_instr = 0;
           
            int  cycles_begin_trace = 0;  //Trace begins at this cycle count.  TODO: expose to the command line
            
            while (end_cnt < extra_cycles) {
                // if ABORT_CYCLES is defined, then it specifies the number of cycles after which
                // simulation is aborted in case there is no activity on the memory interface
#ifdef ABORT_CYCLES
                
                if (abort_cnt >= ABORT_CYCLES) {
                    fprintf(stderr, "WARNING: memory interface inactive for %d cycles, "
                                    "aborting simulation\n", ABORT_CYCLES);
                    exit_code = 1;
                    break;
                }
                
                
#endif
                //update last IF_PC
                last_IF_PC = current_IF_PC;
                last_WB_PC = current_WB_PC;

                // fulfill request on the normal memory port
                // read memory request
                bool     valid = top->mem_addr_o < mem_sz;
                unsigned addr  = top->mem_addr_o;//remove clearing of bottom address bits.  memory now byte addressible (only works when scalar core set to work with non-aligned reads)
                
                for (int byte = 0; byte < mem_w/8; byte++)
                {
                    mem_rdata_queue[0][byte] = 0;
                }

                if (valid) {
                    // write/read memory content if the address is in the valid range
                    if (top->mem_req_o && top->mem_we_o) {
                        for (i = 0; i < mem_w / 8; i++) {
                          for (i = 0; i < mem_w / 8; i++) {
                            unsigned char* w_port = (unsigned char*)&(top->mem_wdata_o);
                            unsigned char* be_port = (unsigned char*)&(top->mem_be_o);
                            if ((be_port[i/8] & (1<<(i%8)))) {
                                
                                mem[addr+i] = w_port[i];
                            }
                        }
                        }
                    }
                    for (i = 0; i < mem_w / 8; i++) {
                        mem_rdata_queue[0][i] |= mem[addr+i];
                    }
                }
                else if (top->mem_req_o) {
                    // test for memory-mapped registers in case of a request for an invalid addr
                    switch (addr) {
                        case 0xFF000000u: // UART data register
                            valid              = true;
                            for (int byte = 0; byte < mem_w/8; byte++)
                            {
                                mem_rdata_queue[0][byte] = 0xf;   // always reads as -1, i.e. no data received
                            }
                            if (top->mem_we_o) {
                                uint32_t* w_port = (uint32_t*)&(top->mem_wdata_o);
                                putc(*w_port & 0xFF, stdout); //TODO: Verify this still works
                            }
                            break;
                        case 0xFF000004u: // UART status register
                            valid              = true;
                            for (int byte = 0; byte < mem_w/8; byte++)
                            {
                                mem_rdata_queue[0][byte] = 0;    // always ready to transmit
                            }
                            break;
                    }
                }


                mem_rvalid_queue[0] = top->mem_req_o;
                mem_err_queue   [0] = !valid;


                int mem_req_o_tmp = top->mem_req_o; //used to determine when to abort on stall TODO: move to location to be clearer + rename


                // Fulfill request on the instruction memory port

                bool     valid_instr = top->mem_iaddr_o < mem_sz;
                unsigned addr_instr  = top->mem_iaddr_o;//remove clearing of bottom address bits.  memory now byte addressible (only works when scalar core set to work with non-aligned reads)
                
                mem_idata_queue[0] = 0;

                if (valid_instr) {
                    for (i = 0; i < 32 / 8; i++) { //port always 32 bits wide
                        mem_idata_queue[0] |= (mem[addr_instr+i] << (8*i));
                    }
                }

                mem_ivalid_queue[0] = top->mem_ireq_o;
                mem_ierr_queue  [0] = !valid_instr;
                

                // rising clock edge
                top->clk_i = 1;
                top->eval();

                // fulfill memory request on main port
                top->mem_rvalid_i = mem_rvalid_queue[mem_latency-1];
                
                for (int byte = 0; byte < mem_w/8; byte++)
                {
                    unsigned char* mem_port = (unsigned char*)&(top->mem_rdata_i);
                    mem_port[byte]  = mem_rdata_queue[mem_latency-1][byte];
                    //top->mem_rdata_i = mem_rdata_queue[mem_latency-1][byte];
                }
                top->mem_err_i    = mem_err_queue   [mem_latency-1];

                //fullfill memory request on instruction port
                top->mem_irvalid_i = mem_ivalid_queue[mem_latency-1];    
                top->mem_irdata_i = mem_idata_queue[mem_latency-1];
                top->mem_ierr_i   = mem_ierr_queue[mem_latency-1];

                top->eval();

                //updating queue for main read port
                for (i = mem_latency-1; i > 0; i--) {
                    mem_rvalid_queue[i] = mem_rvalid_queue[i-1];
                    for (int byte = 0; byte < mem_w/8; byte++)
                    {
                        mem_rdata_queue [i][byte] = mem_rdata_queue [i-1][byte];
                    }
                    mem_err_queue   [i] = mem_err_queue   [i-1];
                }
                //updating queue for instruction read port
                for (i = mem_latency-1; i > 0; i--) {
                    mem_ivalid_queue[i] = mem_ivalid_queue[i-1];
                    mem_idata_queue [i] = mem_idata_queue [i-1];
                    mem_ierr_queue   [i] = mem_ierr_queue   [i-1];
                }


                // falling clock edge
                top->clk_i = 0;
                top->eval();
                 
                
                
                main_reached = (current_IF_PC == 0x00002000u) | main_reached;  //Vicuna Linker always puts MAIN (or run_test) at addr 2000.  Wait to check for a stall/abort until this has passed.
                
                //Need to use PC to exit/abort due to I cache
                current_IF_PC = top->vproc_top->core->pc_if;
                
                //////////
                // Check Exit Conditions
                //////////
                
                //A jump to address 0x78 is a failed test caused by mismatched output
                if ( current_IF_PC == 0x00000078u ) {
                
                   fprintf(stderr, "ERROR: TEST FAILURE - Output Mismatch\n");
                   exit_code = 1;
                   break;
                }
                //A jump to address 0x74 is a failed test caused by an interrupt being called (all other interrupts also funnel here)
                if ( current_IF_PC == 0x000000074u ) {
                
                   fprintf(stderr, "ERROR: TEST FAILURE - Interrupt Called\n");
                   exit_code = 1;
                   break;
                }
                
                if (end_cnt > 0 || ((top->mem_req_o == 1 || top->mem_ireq_o == 1) && current_IF_PC == 0x0000007Cu)) {
                    end_cnt++;
                    fprintf(stderr, "SUCCESS: TEST PASS - Output Match\n");
                    exiting = true;
                }

                //After 10000 cycles at the same fetch PC, exit
                if(current_IF_PC == last_IF_PC){
                    cycles_stalled++; 
                } else{
                    cycles_stalled = 0;
                }
                
                if(cycles_stalled >= 10000) { //TODO: Expose this to the command line
                    fprintf(stderr, "ERROR: SIMULATION STALLED FOR 10000 CYCLES AT IF_PC = 0x%x\n", current_IF_PC);
                    exit_code = 1;
                    break;
                }
                
                //////////
                // Outputs + Statistics
                //////////
                
                //Log File
                if (csv_out == 1 && main_reached && cycles > cycles_begin_trace) {
                // log data once main has been reached and desired start point has been reached
                    log_cycle(top, tfp, fcsv);
                }
                
                //Cycle count and instruction count
                current_WB_PC = top->vproc_top->core->instruction_wb_pc;
                if(main_reached) {
                    if(!exiting)
                    {
                        cycles++;
                        if (inst_trace_out == 1) {
                            fprintf(inst_trace, "%08x\n", top->vproc_top->core->instruction_wb);
                        }
                    }
                    abort_cnt = (top->mem_req_o == mem_req_o_tmp) ? abort_cnt + 1 : 0;
                    if ((current_WB_PC != last_WB_PC) && !exiting)
                    {
                        instructions++;
                    }
                }
                
                
                //Check if a result from the vector unit is ready and accepted
                //By checking here instead of issue, current VL is correct for vsetvli
                if( top->vproc_top->vcore_result_valid && top->vproc_top->vcore_result_ready && main_reached)
                {
                    num_vec_instr++;
                    sum_vec_lengths+= top->vproc_top->csr_vl_o; //running sum of number of elements in vectors
                    int cur_vec_len_bytes = 0;
                    switch ((top->vproc_top->csr_vtype_o >> 3) & 7) //sew stored in bits [5:3]
                    { 
                      case 0: //sew == 8
                        sum_vec_lengths_bytes+= top->vproc_top->csr_vl_o; //each element is one byte
                        cur_vec_len_bytes = top->vproc_top->csr_vl_o;
                        break;
                      case 1: //sew == 16
                        sum_vec_lengths_bytes+= top->vproc_top->csr_vl_o * 2; // each element two bytes
                        cur_vec_len_bytes = top->vproc_top->csr_vl_o * 2;
                        break;
                      case 2: //sew == 32
                        sum_vec_lengths_bytes+= top->vproc_top->csr_vl_o * 4; // each element four bytes
                        cur_vec_len_bytes = top->vproc_top->csr_vl_o * 4;
                        break;
                      default:
                        fprintf(stderr, "UNSUPPORTED SEW DETECTED\n");
                    }
                    
                    switch (top->vproc_top->csr_vtype_o & 7) //LMUL stored in bits [2:0]
                    { 
                      case 0: //LMUL = 1
                          sum_vec_lengths_bytes+= ((float)cur_vec_len_bytes)/((float)top->vproc_top->csr_vlen_b_o); //each element is one byte

                      case 1: //LMUL == 2
                          sum_vec_percentage += ((float)cur_vec_len_bytes)/((float)top->vproc_top->csr_vlen_b_o * 2); // 2 vector regs in group
                        break;
                      case 2: //LMUL == 4
                          sum_vec_lengths_bytes+= ((float)cur_vec_len_bytes)/((float)top->vproc_top->csr_vlen_b_o * 4); // 4 vector regs in group
                        break;
                      case 4: //LMUL == 8
                          sum_vec_lengths_bytes+= ((float)cur_vec_len_bytes)/((float)top->vproc_top->csr_vlen_b_o * 8); // 4 vector regs in group
                      break;
                      case 7: //LMUL = 1/2
                          sum_vec_lengths_bytes+= ((float)cur_vec_len_bytes)/((float)top->vproc_top->csr_vlen_b_o/2.0); //each element is one byte
                      case 6: //LMUL = 1/4
                          sum_vec_lengths_bytes+= ((float)cur_vec_len_bytes)/((float)top->vproc_top->csr_vlen_b_o/4.0); //each element is one byte
                      case 5: //LMUL = 1/8
                          sum_vec_lengths_bytes+= ((float)cur_vec_len_bytes)/((float)top->vproc_top->csr_vlen_b_o/8.0); //each element is one byte
                      default:
                          sum_vec_lengths_bytes+= ((float)cur_vec_len_bytes)/((float)top->vproc_top->csr_vlen_b_o); //each element is one byte
                        break;
                    }
                
                
                }
                
                
            }
            
            fprintf(stderr, "Total Cycles: %d\n", cycles);
            fprintf(stderr, "Instruction Count: %d CPI : %f \n\n", instructions, ((float)(cycles))/((float)instructions));
            
            fprintf(stderr, "Number of Vector Instructions Executed: %d  \n", num_vec_instr);
            fprintf(stderr, "AVG VL Elements: %f  \n", ((float)(sum_vec_lengths))/((float)num_vec_instr));
            fprintf(stderr, "AVG VL Bytes: %f  \n\n", ((float)(sum_vec_lengths_bytes))/((float)num_vec_instr));
            fprintf(stderr, "AVG VREG Usage %: %f  \n\n", ((float)(sum_vec_percentage))/((float)num_vec_instr) * 100);
            
            fprintf(stderr, "Vector Loads     : %d\n", vector_loads);
            fprintf(stderr, "Vector Stores    : %d\n", vector_stores);
            fprintf(stderr, "Other Vector Ops : %d\n", other_vector_ops);

            
        }

        // write dump file
        {
            FILE *ftmp = fopen(dump_path, "w");
            if (ftmp == NULL) {
                fprintf(stderr, "ERROR: opening `%s': %s\n", dump_path, strerror(errno));
            }
            int addr;
            for (addr = dump_start; addr < dump_end; addr += 4) {
                int data = mem[addr] | (mem[addr+1] << 8) | (mem[addr+2] << 16) | (mem[addr+3] << 24);
                fprintf(ftmp, "%08x\n", data);
            }
            fclose(ftmp);
        }
    }

#if defined(TRACE_VCD) || defined(TRACE_FST)
    if (tfp != NULL)
        tfp->close();
#endif
    top->final();
    free(prog_path);
    free(ref_path);
    free(dump_path);
    free(line);
    free(mem);
    free(mem_rvalid_queue);
    for(int queue_pos = 0; queue_pos < mem_latency; queue_pos++)
    {
        free(mem_rdata_queue[queue_pos]);
    }
    free(mem_rdata_queue);
    free(mem_idata_queue);
    free(mem_err_queue);
    if (csv_out == 1) {
        fclose(fcsv);
    }

    fclose(fprogs);


    if (inst_trace_out == 1) {
        fclose(inst_trace);
    }
    return exit_code;
}

vluint64_t main_time = 0;
double sc_time_stamp() {
    return main_time;
}

static void log_cycle(Vvproc_top *top, VerilatedTrace_t *tfp, FILE *fcsv) {
    fprintf(fcsv, "%d;%d;%08X;%08X;%08X;\n",
            top->rst_ni, top->mem_req_o, top->mem_addr_o, top->pend_vreg_wr_map_o, 0);
    main_time++;
#if defined(TRACE_VCD) || defined(TRACE_FST)
    if (tfp != NULL)
        tfp->dump(main_time);
#endif
}
