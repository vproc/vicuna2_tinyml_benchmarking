
#include "tensorflow/lite/micro/tflite_bridge/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"

#include "toycar_int8_data/toycar_int8_input_data.h"
#include "toycar_int8_data/toycar_int8_model_data.h"
#include "toycar_int8_data/toycar_int8_model_settings.h"
#include "toycar_int8_data/toycar_int8_output_data_ref.h"

extern "C" {
#include "runtime.h"
#include "uart.h"
#include "uart.c"
#include "terminate_benchmark.h"
}

constexpr size_t tensor_arena_size = 256 * 1024;
alignas(16) uint8_t tensor_arena[tensor_arena_size];

int run_test()
{
    //tflite::MicroErrorReporter micro_error_reporter;
    //tflite::ErrorReporter *error_reporter = &micro_error_reporter;

    const tflite::Model *model = tflite::GetModel(toycar_int8_model_data);

    static tflite::MicroMutableOpResolver<1> resolver;
    resolver.AddFullyConnected();

    tflite::MicroInterpreter interpreter(model, resolver, tensor_arena, tensor_arena_size);

    uart_printf("Started Program\n");

    if (interpreter.AllocateTensors() != kTfLiteOk)
    {
        //TF_LITE_REPORT_ERROR(error_reporter, "ERROR: In AllocateTensors().");
        return -1;
    }

    for (size_t i = 0; i < toycar_int8_data_sample_cnt; i++)
    {
        memcpy(interpreter.input(0)->data.int8, (int8_t *)toycar_int8_input_data[i], toycar_int8_input_data_len[i]);
        
        //start_cycle_count(); //RD cycle is illegal, causes a lock on attempted offload

        if (interpreter.Invoke() != kTfLiteOk)
        {
            //TF_LITE_REPORT_ERROR(error_reporter, "ERROR: In Invoke().");
            return -1;
        }

        int32_t sum = 0;
        for (size_t j = 0; j < toycar_int8_input_data_len[i]; j++)
        {
            int32_t diff1 = (int8_t)toycar_int8_input_data[i][j] - (int8_t)interpreter.output(0)->data.int8[j];
            int32_t square = diff1*diff1;
            sum += square;
        }
        sum /= toycar_int8_input_data_len[i];

        int32_t diff = abs(sum - toycar_int8_output_data_ref[i]);

        
        //store_result_int(diff);
        
        if (diff > 1)
        {
            #if defined(PRINT_OUTPUTS)
            uart_printf("ERROR: at #%d, sum %d ref %d diff %d \n", i, sum, toycar_int8_output_data_ref[i], diff);
            #endif
            return -1;
        }
        else
        {
            #if defined(PRINT_OUTPUTS)
            uart_printf("Sample #%d pass, sum %d ref %d diff %d \n", i, sum, toycar_int8_output_data_ref[i], diff);
            #endif
        }
    }

    return 0;
}

int main(int argc, char *argv[])
{
    int ret = run_test();
    if (ret != 0)
    {
        #if defined(PRINT_OUTPUTS)
        uart_printf("Test Failed!\n");
        #endif 
        benchmark_failure();

    }
    else
    {
        #if defined(PRINT_OUTPUTS)
        uart_printf("Test Success!\n");
        #endif
        benchmark_success(); 
    }

    return ret;
}
