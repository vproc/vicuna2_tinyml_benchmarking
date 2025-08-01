
#include "tensorflow/lite/micro/tflite_bridge/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"

#include "toycar_fp32_data/toycar_fp32_input_data.h"
#include "toycar_fp32_data/toycar_fp32_model_data.h"
#include "toycar_fp32_data/toycar_fp32_model_settings.h"
#include "toycar_fp32_data/toycar_fp32_output_data_ref.h"

extern "C" {
#include "runtime.h"
#include "uart.h"
#include "terminate_benchmark.h"
}

constexpr size_t tensor_arena_size = 256 * 1024 * 4; //x4 for float
alignas(16) uint8_t tensor_arena[tensor_arena_size];

int run_test()
{
    //tflite::MicroErrorReporter micro_error_reporter;
    //tflite::ErrorReporter *error_reporter = &micro_error_reporter;

    const tflite::Model *model = tflite::GetModel(toycar_fp32_model_data);

    static tflite::MicroMutableOpResolver<1> resolver;
    resolver.AddFullyConnected();

    tflite::MicroInterpreter interpreter(model, resolver, tensor_arena, tensor_arena_size);

    if (interpreter.AllocateTensors() != kTfLiteOk)
    {
        //TF_LITE_REPORT_ERROR(error_reporter, "ERROR: In AllocateTensors().");
        return -1;
    }

    for (size_t i = 0; i < toycar_fp32_data_sample_cnt; i++)
    {
        memcpy(interpreter.input(0)->data.f, (float *)toycar_fp32_input_data[i], toycar_fp32_input_data_len[i] * 4); //Bytes to copy is 4*len
        
        //start_cycle_count();

        if (interpreter.Invoke() != kTfLiteOk)
        {
            //TF_LITE_REPORT_ERROR(error_reporter, "ERROR: In Invoke().");
            return -1;
        }

        float sum = 0;
        for (size_t j = 0; j < toycar_fp32_input_data_len[i]; j++)
        {
            float diff1 = (float)toycar_fp32_input_data[i][j] - (float)interpreter.output(0)->data.f[j];
            float square = diff1*diff1;
            sum += square;
        }
        sum /= (float)toycar_fp32_input_data_len[i];

        float diff = sum - toycar_fp32_output_data_ref[i]; //TODO:abs() makes negative error 0.00?
        
        //diff = 1.234;
        
        //store_result_float(diff);
        
        if (diff > 0.001f |  diff < -0.001f)
        {
            #if defined(PRINT_OUTPUTS)
            uart_printf("ERROR: at #%d, sum %f ref %f diff %f \n", i, sum, toycar_fp32_output_data_ref[i], diff);
            #endif
            return -1;
        }
        else
        {
            #if defined(PRINT_OUTPUTS)
            uart_printf("Sample #%d pass, sum %f ref %f diff %f \n", i, sum, toycar_fp32_output_data_ref[i], diff);
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
