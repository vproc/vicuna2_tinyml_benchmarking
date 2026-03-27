import os
import re
from pathlib import Path
import keras
import tensorflow as tf
from tensorflow.keras.layers import Input, Conv2D, BatchNormalization, Activation, Add, AveragePooling2D, Flatten, Dense
from tensorflow.keras.models import Model
from tensorflow.keras.regularizers import l2
import numpy as np

import get_dataset as cifar10_data
from utils import (
    write_flatbuffer_input_data, write_input_data_header,
    write_model_flatbuffer, write_model_data_header,
    write_model_settings, write_model_settings_header,
    write_output_data, write_output_data_header,
    write_cmakelists_file
)

cwd = str(Path.cwd())


def build_stem():
    inputs = Input(shape=(32, 32, 3), name="input_stem")

    x = Conv2D(16, 3, padding='same', kernel_initializer='he_normal',
               kernel_regularizer=tf.keras.regularizers.l2(1e-4))(inputs)
    x = BatchNormalization()(x)
    out = Activation('relu')(x)

    return Model(inputs=inputs, outputs=out, name="stem")


def build_block0():
    inputs = Input(shape=(32, 32, 16), name="input_block0")

    y = Conv2D(16, 3, padding='same', kernel_initializer='he_normal',
               kernel_regularizer=tf.keras.regularizers.l2(1e-4))(inputs)
    y = BatchNormalization()(y)
    y = Activation('relu')(y)

    y = Conv2D(16, 3, padding='same', kernel_initializer='he_normal',
               kernel_regularizer=tf.keras.regularizers.l2(1e-4))(y)
    y = BatchNormalization()(y)

    out = Add()([inputs, y])
    out = Activation('relu')(out)

    return Model(inputs=inputs, outputs=out, name="block0")


def build_block1():
    inputs = Input(shape=(32, 32, 16), name="input_block1")

    y = Conv2D(32, 3, strides=2, padding='same', kernel_initializer='he_normal',
               kernel_regularizer=tf.keras.regularizers.l2(1e-4))(inputs)
    y = BatchNormalization()(y)
    y = Activation('relu')(y)

    y = Conv2D(32, 3, padding='same', kernel_initializer='he_normal',
               kernel_regularizer=tf.keras.regularizers.l2(1e-4))(y)
    y = BatchNormalization()(y)

    shortcut = Conv2D(32, 1, strides=2, padding='same', kernel_initializer='he_normal',
                      kernel_regularizer=tf.keras.regularizers.l2(1e-4))(inputs)

    out = Add()([shortcut, y])
    out = Activation('relu')(out)

    return Model(inputs=inputs, outputs=out, name="block1")


def build_block2():
    inputs = Input(shape=(16, 16, 32), name="input_block2")

    y = Conv2D(64, 3, strides=2, padding='same', kernel_initializer='he_normal',
               kernel_regularizer=tf.keras.regularizers.l2(1e-4))(inputs)
    y = BatchNormalization()(y)
    y = Activation('relu')(y)

    y = Conv2D(64, 3, padding='same', kernel_initializer='he_normal',
               kernel_regularizer=tf.keras.regularizers.l2(1e-4))(y)
    y = BatchNormalization()(y)

    shortcut = Conv2D(64, 1, strides=2, padding='same', kernel_initializer='he_normal',
                      kernel_regularizer=tf.keras.regularizers.l2(1e-4))(inputs)

    out = Add()([shortcut, y])
    out = Activation('relu')(out)

    return Model(inputs=inputs, outputs=out, name="block2")


def build_head():
    inputs = Input(shape=(8, 8, 64), name="input_head")
    pool_size = int(np.amin(inputs.shape[1:3]))

    x = AveragePooling2D(pool_size=pool_size)(inputs)
    x = Flatten()(x)
    outputs = Dense(10, activation='softmax', kernel_initializer='he_normal')(x)

    return Model(inputs=inputs, outputs=outputs, name="head")


def convert_to_tflite(model, save_path, quant_mode="fp32", full_model=False):
    assert quant_mode in ["fp32", "fp16", "int8"]

    if quant_mode == "fp32":
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        tflite_model = converter.convert()
        with tf.io.gfile.GFile(save_path, 'wb') as f:
            f.write(tflite_model)
    elif quant_mode == "fp16":
        converter = tf.lite.TFLiteConverter.from_keras_model(model)   

        converter.experimental_enable_resource_variables = True   
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.target_spec.supported_ops = [
            tf.lite.OpsSet.TFLITE_BUILTINS,
        ]
        converter.target_spec.supported_types = [tf.float16]

        #converter.inference_input_type = tf.float16
        #converter.inference_output_type = tf.float16 
        tflite_model = converter.convert()

        with tf.io.gfile.GFile(save_path, 'wb') as f:
            f.write(tflite_model)
    elif quant_mode == "int8":
        converter = tf.lite.TFLiteConverter.from_keras_model(model)

        input_shape = list(model.input_shape)
        batch_size = 1
        input_shape[0] = batch_size
        input_shape = tuple(input_shape)
        def representative_dataset_gen():
            if full_model:
                data_dir = cwd + "/dataset/cifar-10-batches-py"
                train_data, train_filenames, train_labels, test_data, test_filenames, test_labels, label_names = \
                    cifar10_data.load_cifar_10_data(data_dir)
                _idx = np.load(cwd + '/calibration_samples_idxs.npy')
                for i in _idx:
                    sample_img = np.expand_dims(np.array(test_data[i], dtype=np.float32), axis=0)
                    yield [sample_img]
            else:  # random input
                for _ in range(100):
                    yield [tf.random.normal(input_shape, dtype=np.float32)]

        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.representative_dataset = representative_dataset_gen
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.int8  # or tf.uint8
        converter.inference_output_type = tf.int8  # or tf.uint8
        tflite_model = converter.convert()
        with tf.io.gfile.GFile(save_path, 'wb') as f:
            f.write(tflite_model)


def keras2tflite(keras_model, name, quant_mode, full_model=False, create_model_flatbuffers=True, class_names=None):
    model_dir = os.path.join(OUT_DIR, name)
    os.makedirs(model_dir, exist_ok=True)
    tflite_save_path = os.path.join(model_dir, f"{name}_{quant_mode}.tflite")
    convert_to_tflite(keras_model, tflite_save_path, quant_mode, full_model=full_model)

    if create_model_flatbuffers:
        output_dir = os.path.join(model_dir, f"{name}_{quant_mode}_data")
        os.makedirs(output_dir, exist_ok=True)
        dtype_name = quant_mode
        write_model_flatbuffer(output_dir, tflite_save_path)
        write_model_data_header(output_dir, name, dtype_name)
        class_names = class_names or []
        num_classes = len(class_names)
        write_model_settings(output_dir, class_names, name, dtype_name)
        write_model_settings_header(output_dir, num_classes, name, dtype_name)
        write_output_data(output_dir, name, dtype_name)
        write_output_data_header(output_dir, name, dtype_name)

        cpp_file_path = os.path.join(model_dir, f"{name}_{quant_mode}.cpp")
        cpp_template_path = cwd + f"/template_{quant_mode}.cpp"
        update_model_name_in_cpp(cpp_file_path, cpp_template_path, "model_name_replace", f"{name}_{quant_mode}")
        write_cmakelists_file(model_dir, name, quant_mode)


def get_np_dtype(dtype_name):
    if dtype_name == "fp32":
        np_dtype = np.float32
    elif dtype_name == "fp16":
        np_dtype = np.float16
    elif dtype_name == "int8":
        np_dtype = np.int8
    return np_dtype


def run_block(input_tensor, block_name, quant_mode, create_input_flatbuffers=True):
    assert quant_mode in ["fp32", "fp16", "int8"]

    model_dir = os.path.join(OUT_DIR, block_name)
    os.makedirs(model_dir, exist_ok=True)
    tflite_model_path = os.path.join(model_dir, f"{block_name}_{quant_mode}.tflite")

    # Load TFLite model
    interpreter = tf.lite.Interpreter(model_path=tflite_model_path)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    # input_type = interpreter.get_input_details()[0]['dtype']
    if quant_mode in ["fp32", "fp16"]:
        # NOTE: tflite expects fp32 input for fp16 model
        input_data = np.array(input_tensor, dtype=np.float32)
    elif quant_mode == "int8":
        input_data = np.array(input_tensor, dtype=np.float32)
        input_scale, input_zero_point = input_details[0]["quantization"]
        input_data = np.array(input_data/input_scale + input_zero_point, dtype=np.int8)  # quantized int8 input

    if create_input_flatbuffers:
        dtype_name = quant_mode
        output_dir = os.path.join(model_dir, f"{block_name}_{quant_mode}_data")
        os.makedirs(output_dir, exist_ok=True)

        data_flat = input_data.flatten()
        np_dtype = get_np_dtype(dtype_name)
        data_flat = np.array(data_flat, dtype=np_dtype)

        write_flatbuffer_input_data(output_dir, data_flat, block_name, dtype_name, num_samples=1)
        write_input_data_header(output_dir, block_name, dtype_name, num_samples=1)

    # Set input
    interpreter.set_tensor(input_details[0]['index'], input_data)

    # Inference
    interpreter.invoke()

    # Get output
    output = interpreter.get_tensor(output_details[0]['index'])
    return output


def update_model_name_in_cpp(output_file_path, cpp_template_path, old_model_name, new_model_name):
    path = Path(cpp_template_path)
    if not path.exists():
        print(f"Error: File '{cpp_template_path}' not found.")
        return

    with path.open("r", encoding="utf-8") as f:
        content = f.read()

    # Replace all occurrences of the old model name
    updated_content = re.sub(old_model_name, new_model_name, content)
    # print(updated_content)

    # Optional: backup the original file
    # backup_path = path.with_suffix(".cpp.bak")
    # path.rename(backup_path)

    # Write the modified content to the original file path
    output_file_path = Path(output_file_path)
    with output_file_path.open("w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"Written cpp file in {output_file_path}")
    # print(f"Updated model name from '{old_model_name}' to '{new_model_name}' in '{output_file_path}'.")
    # print(f"Original file backed up as '{backup_path}'.")


if __name__ == "__main__":
    import argparse
    from keras_model import resnet_v1_eembc

    parser = argparse.ArgumentParser(description="Convert ResNet8 to TFLite and create flatbuffers")
    parser.add_argument("--quant_mode", type=str, help="Quantization Mode",  default="fp32", choices=["fp32", "fp16", "int8"])
    parser.add_argument("--out_dir", type=str, help="Output directory to save the created flatbuffers", required=True)
    parser.add_argument('--separate_layers', action='store_true', help='Convert the Resnet8 layers separately')
    args = parser.parse_args()
    quant_mode = args.quant_mode

    # Create directory to save TFLite models
    if quant_mode == "int8":
        dir_name = "Int8"
    elif quant_mode == "fp16":
        dir_name = "FP16"
    elif quant_mode == "fp32":
        dir_name = "FP32"
    OUT_DIR = os.path.join(args.out_dir, dir_name)
    os.makedirs(OUT_DIR, exist_ok=True)

    # Get CIFAR10 data
    cwd = str(Path.cwd())
    data_dir = cwd + "/dataset/cifar-10-batches-py"
    generator = cifar10_data.get_cifar10_generator(data_dir)
    data, label = next(generator)
    print(data.shape)  # (1, 32, 32, 3)
    data_flat = data.flatten()
    print(data_flat.size)  # 3072
    class_names = ["plane", "car", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]

    # Load pretrained model
    model = keras.models.load_model(cwd + "/models/pretrainedResnet.h5")
    # model = resnet_v1_eembc()
    # Convert to TFLite
    keras2tflite(model, "resnet8", quant_mode, full_model=True, class_names=class_names)
    # Run forward and save the input data
    # x = np.random.rand(1, 32, 32, 3).astype(np.float32)
    x = data
    y = run_block(x, "resnet8", quant_mode)

    if args.separate_layers:
        # Separate the layers of the full ResNet model and create flatbuffers for each of them

        # Convert to TFLite
        stem = build_stem()
        keras2tflite(stem, "resnet8_block_stem", quant_mode, class_names=class_names)
        block0 = build_block0()
        keras2tflite(block0, "resnet8_block_res0", quant_mode, class_names=class_names)
        block1 = build_block1()
        keras2tflite(block1, "resnet8_block_res1", quant_mode, class_names=class_names)
        block2 = build_block2()
        keras2tflite(block2, "resnet8_block_res2", quant_mode, class_names=class_names)
        head = build_head()
        keras2tflite(head, "resnet8_block_head", quant_mode, class_names=class_names)

        # Run forward and save the input data
        # x = np.random.rand(1, 32, 32, 3).astype(np.float32)
        x = data
        x = run_block(x, "resnet8_block_stem", quant_mode)
        x = run_block(x, "resnet8_block_res0", quant_mode)
        x = run_block(x, "resnet8_block_res1", quant_mode)
        x = run_block(x, "resnet8_block_res2", quant_mode)
        y = run_block(x, "resnet8_block_head", quant_mode)
