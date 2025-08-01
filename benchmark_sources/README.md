# Benchmark Sources

This directory contains the benchmark code and TFLM support for half-precision operations, as well as the python scripts used to generate the data and quantized model flatbuffers.  Additionally, the TFLM source files are placed here once the testing repository has been initialized.

### Generation

The MLPerfTiny benchmarks are provided as trained models in single-precision floating point quantization.  Provided in the **/benchmark_sources/models/** directory is a python script for each benchmark to provide flatbuffers in Int8, FP32, and FP16 quantization for each benchmark.  These scripts also provide quantized versions of the inputs.  The process for the creation of these quantized models is taken from the [MLPerfTiny](https://github.com/mlcommons/tiny) repository, and is slightly different for each benchmark.

### Basic Half-Precision Floating-Point Support 

Tensorflow Lite and Tensorflow Lite for Microcontrollers do not currently support computation with half-precision floating-point intermediate values.  As full support for this would involve extensive changes to Tensorflow Lite and was out of scope for this project, basic support was added through custom TFLM kernels.  The following changes were made:

- The TFLM operator **DEQUANTIZE** was extended to support for FP16 to FP32.  When operating with FP16 intermediates, this performs a no-op.
- The default TFLM **CONV**, **DEPTHWISE_CONV**, **FULLY_CONNECTED**, **POOLING**, **RESHAPE**, and **SOFTMAX** floating-point operators were modified to cast the input pointer to half-precision floating-point before performing the computations.  Due to the no-op in **DEQUANTIZE** the data is still in the half-precision format, allowing it to be processed correctly.

These modified kernels are located in the **/benchmark_sources/FH_SUPPORT/** directory and are included instead of the default versions when including TFLM as a library for the project.

As a consequence of these changes, it is not possible to use single-precision and half-precision operations simultaneously.  Providing official support for half-precision operations in Tensorflow Lite and TFLM is future work that we hope this work can help to justify.
