#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

#include "resnet8_int8_data/resnet8_int8_input_data.h"
#include "resnet8_int8_data/resnet8_int8_model_data.h"
#include "resnet8_int8_data/resnet8_int8_model_settings.h"
#include "resnet8_int8_data/resnet8_int8_output_data_ref.h"

#include "tensorflow/lite/micro/tflite_bridge/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"

extern "C" {
#include "runtime.h"
#include "uart.h"
#include "terminate_benchmark.h"
}

constexpr size_t tensor_arena_size = 256 * 1024;
alignas(16) uint8_t tensor_arena[tensor_arena_size];

//commit before array.h added - 6f2828619641503942f2bd69ddee006ff7823130

int run_test()
{
    tflite::MicroErrorReporter micro_error_reporter;
    tflite::ErrorReporter *error_reporter = &micro_error_reporter;

    const tflite::Model *model = tflite::GetModel(resnet8_int8_model_data);

    static tflite::MicroMutableOpResolver<8> resolver;
    resolver.AddFullyConnected();
    resolver.AddConv2D();
    resolver.AddDepthwiseConv2D();
    resolver.AddAveragePool2D();
    resolver.AddReshape();
    resolver.AddSoftmax();
    resolver.AddAdd();
    resolver.AddDequantize();

    tflite::MicroInterpreter interpreter(model, resolver, tensor_arena, tensor_arena_size);

    if (interpreter.AllocateTensors() != kTfLiteOk)
    {
        TF_LITE_REPORT_ERROR(error_reporter, "ERROR: In AllocateTensors().");
        return -1;
    }

    //for (size_t i = 0; i < resnet8_int8_data_sample_cnt; i++)
    for (size_t i = 0; i < 1; i++)
    {
        memcpy(interpreter.input(0)->data.int8, (int8_t *)resnet8_int8_input_data[i], resnet8_int8_input_data_len[i]);

        if (interpreter.Invoke() != kTfLiteOk)
        {
            TF_LITE_REPORT_ERROR(error_reporter, "ERROR: In Invoke().");
            return -1;
        }
        
        //start_cycle_count();

        int8_t top_index = 0;
        for (size_t j = 0; j < resnet8_int8_model_label_cnt; j++)
        {
            if (interpreter.output(0)->data.int8[j] > interpreter.output(0)->data.int8[top_index])
            {
                top_index = j;
            }
        }

        if (top_index != resnet8_int8_output_data_ref[i])
        {
            //uart_printf("ERROR: at #%d, top_index %d resnet8_int8_output_data_ref %d \n", i, top_index, resnet8_int8_output_data_ref[i]);
            return -1;
        }
        else
        {
            //uart_printf("Sample #%d pass, top_index %d matches ref %d \n", i, top_index, resnet8_int8_output_data_ref[i]);
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
