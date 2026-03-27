import os
import subprocess, sys
from pathlib import Path
import numpy as np


def get_c_dtype(dtype_name):
    if dtype_name == "fp32":
        c_dtype = "float"
    elif dtype_name == "fp16":
        c_dtype = "_Float16"
    elif dtype_name == "int8":
        c_dtype = "int8_t"
    return c_dtype


def write_output_data(output_dir, name, dtype_name):
    data_name = f"{name}_{dtype_name}_output_data_ref"
    output_path = os.path.join(output_dir, data_name)
    c_dtype = get_c_dtype(dtype_name)
    
    f = open(f"{output_path}.cc", "w")
    f.writelines(f"#include \"{name}_{dtype_name}_output_data_ref.h\"\n\n")

    f.writelines(f"extern const uint8_t {name}_{dtype_name}_output_data_ref[] = {{0}};\n")

    print("Output data file written to", output_path)


def write_output_data_header(output_dir, name, dtype_name):
    data_name = f"{name}_{dtype_name}_output_data_ref"
    output_path = os.path.join(output_dir, data_name)
    c_dtype = get_c_dtype(dtype_name)
    
    f = open(f"{output_path}.h", "w")
    f.writelines(f"#ifndef {data_name.upper()}_H\n")
    f.writelines(f"#define {data_name.upper()}_H\n\n")

    f.writelines(f"#include <stdint.h>\n")
    f.writelines(f"#include <stddef.h>\n\n")

    f.writelines(f"extern const uint8_t {name}_{dtype_name}_output_data_ref[];\n")

    f.writelines(f"#endif /* {data_name.upper()}_H */\n")

    print("Output data header file written to", output_path)


def write_model_settings(output_dir, class_names, name, dtype_name):
    # class_names = ["plane", "car", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
    data_name = f"{name}_{dtype_name}_model_settings"
    output_path = os.path.join(output_dir, data_name)
    c_dtype = get_c_dtype(dtype_name)
    
    f = open(f"{output_path}.cc", "w")
    f.writelines(f"#include \"{name}_{dtype_name}_model_settings.h\"\n")
    f.writelines(f'const char* {name}_{dtype_name}_model_labels[] = ' + '{' + ', '.join(f'"{cls}"' for cls in class_names) + '};')

    print("Model settings file written to", output_path)


def write_model_settings_header(output_dir, num_classes, name, dtype_name):
    data_name = f"{name}_{dtype_name}_model_settings"
    output_path = os.path.join(output_dir, data_name)
    c_dtype = get_c_dtype(dtype_name)
    
    f = open(f"{output_path}.h", "w")
    f.writelines(f"#ifndef {data_name.upper()}_H\n")
    f.writelines(f"#define {data_name.upper()}_H\n\n")

    f.writelines(f"#include <stdint.h>\n")
    f.writelines(f"#include <stddef.h>\n\n")

    f.writelines(f"const size_t {name}_{dtype_name}_model_label_cnt = {num_classes};\n")
    f.writelines(f"extern const char* {name}_{dtype_name}_model_labels[];\n")

    f.writelines(f"#endif /* {data_name.upper()}_H */\n")

    print("Input header file written to", output_path)


def write_input_data_header(output_dir, name, dtype_name, num_samples=1):
    data_name = f"{name}_{dtype_name}_input_data"
    output_path = os.path.join(output_dir, data_name)
    c_dtype = get_c_dtype(dtype_name)
    
    f = open(f"{output_path}.h", "w")
    f.writelines(f"#ifndef {data_name.upper()}_H\n")
    f.writelines(f"#define {data_name.upper()}_H\n\n")
    f.writelines(f"#include <stdint.h>\n")
    f.writelines(f"#include <stddef.h>\n\n")

    f.writelines(f"const size_t {name}_{dtype_name}_data_sample_cnt = {num_samples};\n")
    f.writelines(f"extern const {c_dtype}* {name}_{dtype_name}_input_data[];\n")
    f.writelines(f"extern const size_t {name}_{dtype_name}_input_data_len[];\n")

    f.writelines(f"#endif /* {data_name.upper()}_H */\n")

    print("Input header file written to", output_path)


def write_flatbuffer_input_data(output_dir, data, name, dtype_name, num_samples=1):
    data_name = f"{name}_{dtype_name}_input_data"
    output_path = os.path.join(output_dir, data_name)
    f = open(f"{output_path}.cc", "w")
    f.writelines(f"#include \"{data_name}.h\"\n")

    if dtype_name == "fp32":
        c_dtype = "float"
    elif dtype_name == "fp16":
        c_dtype = "_Float16"
    elif dtype_name == "int8":
        c_dtype = "int8_t"

    # for j in range(num_samples):
    j = num_samples
    sample_name = f"{data_name}_000{j-1}"
    f.writelines(f"const {c_dtype} {sample_name}[] = " + "{\n")
    for i in range(len(data)):
        f.write(str(data[i])+", ")
        if((i+1)%12 == 0):
            f.write("\n")

    f.writelines("};\n")
    data_size = np.prod(data.shape)
    f.writelines(f"const size_t {sample_name}_len = {data_size};\n\n")

    f.writelines(f"const {c_dtype}* {data_name}[] = {{{sample_name}}};\n")
    f.writelines(f"const size_t {data_name}_len[] = {{{sample_name}_len}};\n")
    f.close()

    print("Input flatbuffer written to", output_path)


def write_model_data_header(output_dir, name, dtype_name):
    data_name = f"{name}_{dtype_name}_model_data"
    output_path = os.path.join(output_dir, data_name)
    # c_dtype = get_c_dtype(dtype_name)
    
    f = open(f"{output_path}.h", "w")
    f.writelines(f"#ifndef {data_name.upper()}_H\n")
    f.writelines(f"#define {data_name.upper()}_H\n\n")

    f.writelines(f"#include <stdint.h>\n")
    f.writelines(f"#include <stddef.h>\n\n")

    f.writelines(f"extern const uint8_t {name}_{dtype_name}_model_data[];\n")
    f.writelines(f"extern const size_t {name}_{dtype_name}_model_data_size;\n")

    f.writelines(f"#endif /* {data_name.upper()}_H */\n")

    print("Model data header file written to", output_path)


def write_model_flatbuffer(output_dir, tflite_model_path):
    assert tflite_model_path.endswith('.tflite')

    # Create Flatbuffer of tflite models
    model_name = os.path.basename(tflite_model_path).split('.')[0]  # e.g., resnet8_int8.tflite -> resnet8_int8
    model_data_name = f"{model_name}_model_data"  # e.g., resnet8_int8 -> resnet8_int8_model_data
    model_data_path = os.path.join(output_dir, f"{model_data_name}.cc")  # e.g., resnet8_int8_model_data.cc

    # Flatbuffer
    subprocess.run("xxd -i " + tflite_model_path + " > " + model_data_path, shell=True, executable="/bin/bash")
    fb = open(model_data_path, "r+")
    flatbuffer_contents = []
    flatbuffer_contents.append(f"#include \"{model_data_name}.h\"\n")
    flatbuffer_contents.append(f"const uint8_t {model_data_name}[] __attribute__((aligned(16))) =" + "{\n")
    fb_old_name=""
    for line in fb:
        if fb_old_name != "":
            line_temp = line.replace("unsigned int", "const size_t")
            line_temp = line_temp.replace(fb_old_name, model_data_name)
            flatbuffer_contents.append(line_temp)

        if "unsigned char " in line:
            fb_old_name = line.replace("unsigned char ", "")
            fb_old_name = fb_old_name.replace("[] = {", "")
            fb_old_name = fb_old_name.replace("\n","")

    fb.seek(0)
    fb.truncate()
    for line in flatbuffer_contents:
        fb.writelines(line)

    fb.close()
    print("Model flatbuffer written to", model_data_path)


def write_cmakelists_file(output_dir, name, dtype_name):
    model_name = f"{name}_{dtype_name}"
    data_name = f"CMakeLists.txt"
    output_path = os.path.join(output_dir, data_name)

    if dtype_name == "int8":
        dir_name = "Int8"
    elif dtype_name == "fp16":
        dir_name = "FP16"
    elif dtype_name == "fp32":
        dir_name = "FP32"

    f = open(output_path, "w")
    f.writelines(f"add_Benchmark({name}_{dtype_name} ${{CMAKE_CURRENT_SOURCE_DIR}} ${{BUILD_DIR}}/benchmark_sources/{dir_name}/{name})")

    print("CMakeLists file written to", output_path)
