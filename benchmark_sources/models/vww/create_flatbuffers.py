import os
from pathlib import Path
import keras
import tensorflow as tf
from tensorflow.keras.layers import Input, Conv2D, DepthwiseConv2D, BatchNormalization, Activation, Add, AveragePooling2D, Flatten, Dense
from tensorflow.keras.models import Model
from tensorflow.keras.regularizers import l2
import numpy as np
import re

import get_dataset as vww_data
from keras_model import mobilenet_v1
from utils import (
    write_flatbuffer_input_data, write_input_data_header,
    write_model_flatbuffer, write_model_data_header,
    write_model_settings, write_model_settings_header,
    write_output_data, write_output_data_header,
    write_cmakelists_file
)

cwd = str(Path.cwd())


def depthwise_block(x, num_filters, stride):
    x = DepthwiseConv2D(kernel_size=3, strides=stride, padding='same',
                        kernel_initializer='he_normal', kernel_regularizer=l2(1e-4))(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)

    x = Conv2D(num_filters, kernel_size=1, strides=1, padding='same',
               kernel_initializer='he_normal', kernel_regularizer=l2(1e-4))(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    return x


def build_stem():
    inputs = Input(shape=(96, 96, 3), name="input_stem")
    x = Conv2D(8, kernel_size=3, strides=2, padding='same',
               kernel_initializer='he_normal', kernel_regularizer=l2(1e-4))(inputs)
    x = BatchNormalization()(x)
    out = Activation('relu')(x)
    return Model(inputs=inputs, outputs=out, name="stem")


def build_block0():
    inputs = Input(shape=(48, 48, 8), name="input_block0")
    num_filters = 16
    out = depthwise_block(inputs, num_filters, stride=1)
    return Model(inputs=inputs, outputs=out, name="block0")


def build_block1():
    inputs = Input(shape=(48, 48, 16), name="input_block1")
    num_filters = 32
    out = depthwise_block(inputs, num_filters, stride=2)
    return Model(inputs=inputs, outputs=out, name="block1")


def build_block2():
    inputs = Input(shape=(24, 24, 32), name="input_block2")
    num_filters = 32
    out = depthwise_block(inputs, num_filters, stride=1)
    return Model(inputs=inputs, outputs=out, name="block2")


def build_block3():
    inputs = Input(shape=(24, 24, 32), name="input_block3")
    num_filters = 64
    out = depthwise_block(inputs, num_filters, stride=2)
    return Model(inputs=inputs, outputs=out, name="block3")


def build_block4():
    inputs = Input(shape=(12, 12, 64), name="input_block4")
    num_filters = 64
    out = depthwise_block(inputs, num_filters, stride=1)
    return Model(inputs=inputs, outputs=out, name="block4")


def build_block5():
    inputs = Input(shape=(12, 12, 64), name="input_block5")
    num_filters = 128
    out = depthwise_block(inputs, num_filters, stride=2)
    return Model(inputs=inputs, outputs=out, name="block5")


def build_block6():
    inputs = Input(shape=(6, 6, 128), name="input_block6")
    num_filters = 128
    out = depthwise_block(inputs, num_filters, stride=1)
    return Model(inputs=inputs, outputs=out, name="block6")


def build_block7():
    inputs = Input(shape=(6, 6, 128), name="input_block7")
    num_filters = 128
    out = depthwise_block(inputs, num_filters, stride=1)
    return Model(inputs=inputs, outputs=out, name="block7")


def build_block8():
    inputs = Input(shape=(6, 6, 128), name="input_block8")
    num_filters = 128
    out = depthwise_block(inputs, num_filters, stride=1)
    return Model(inputs=inputs, outputs=out, name="block8")


def build_block9():
    inputs = Input(shape=(6, 6, 128), name="input_block9")
    num_filters = 128
    out = depthwise_block(inputs, num_filters, stride=1)
    return Model(inputs=inputs, outputs=out, name="block9")


def build_block10():
    inputs = Input(shape=(6, 6, 128), name="input_block10")
    num_filters = 128
    out = depthwise_block(inputs, num_filters, stride=1)
    return Model(inputs=inputs, outputs=out, name="block10")


def build_block11():
    inputs = Input(shape=(6, 6, 128), name="input_block11")
    num_filters = 256
    out = depthwise_block(inputs, num_filters, stride=2)
    return Model(inputs=inputs, outputs=out, name="block11")


def build_block12():
    inputs = Input(shape=(3, 3, 256), name="input_block12")
    num_filters = 256
    out = depthwise_block(inputs, num_filters, stride=1)
    return Model(inputs=inputs, outputs=out, name="block12")


def build_head():
    inputs = Input(shape=(3, 3, 256), name="input_head")
    x = AveragePooling2D(pool_size=inputs.shape[1:3])(inputs)
    x = Flatten()(x)
    outputs = Dense(2, activation='softmax')(x)
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
                data_dir = cwd + "/dataset/vw_coco2014_96"
                dataset_dir = os.path.join(data_dir, "person")
                for idx, image_file in enumerate(os.listdir(dataset_dir)):
                    # 10 representative images should be enough for calibration.
                    if idx > 10:
                        return
                    full_path = os.path.join(dataset_dir, image_file)
                    if os.path.isfile(full_path):
                        img = tf.keras.preprocessing.image.load_img(
                            full_path, color_mode='rgb').resize((96, 96))
                        arr = tf.keras.preprocessing.image.img_to_array(img)
                        # Scale input to [0, 1.0] like in training.
                        yield [arr.reshape(1, 96, 96, 3) / 255.]
            else:  # random input
                for _ in range(100):
                    yield [tf.random.normal(input_shape, dtype=np.float32)]

        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.representative_dataset = representative_dataset_gen
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.int8  # or tf.uint8; should match dat_q in eval_quantized_model.py
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
        input_data = np.array(input_data/input_scale + input_zero_point, dtype=np.int8)  # int8 input

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

    parser = argparse.ArgumentParser(description="Convert MobileNetV1 to TFLite  and create flatbuffers")
    parser.add_argument("--quant_mode", type=str, help="Quantization Mode",  default="fp16", choices=["fp32", "fp16", "int8"])
    parser.add_argument("--out_dir", type=str, help="Output directory to save the created flatbuffers", required=True)
    parser.add_argument('--separate_layers', action='store_true', help='Convert the MobileNetV1 layers separately')
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

    # Get input data
    cwd = str(Path.cwd())
    data_dir = cwd + "/dataset/vw_coco2014_96"
    generator = vww_data.get_vww_generator(data_dir, batch_size=1)
    data, label = next(generator)
    print(data.shape)
    data_flat = data.flatten()
    data_len = data_flat.size
    print(data_len)
    class_names = ["non_person", "person"]

    # Load pretrained model
    model = keras.models.load_model(cwd + "/models/vww_96.h5")
    # model = mobilenet_v1()
    # Convert to TFLite
    keras2tflite(model, "vww", quant_mode, full_model=True, class_names=class_names)
    # Run forward and save the input data
    x = data
    out = run_block(x, "vww", quant_mode)


    if args.separate_layers:
        # Separate the layers of the full MobileNetV1 model and create flatbuffers for each of them

        # Convert to TFLite
        keras2tflite(build_stem(), "vww_block_stem", quant_mode, class_names=class_names)
        keras2tflite(build_block0(), "vww_block_0", quant_mode, class_names=class_names)
        keras2tflite(build_block1(), "vww_block_1", quant_mode, class_names=class_names)
        keras2tflite(build_block2(), "vww_block_2", quant_mode, class_names=class_names)
        keras2tflite(build_block3(), "vww_block_3", quant_mode, class_names=class_names)
        keras2tflite(build_block4(), "vww_block_4", quant_mode, class_names=class_names)
        keras2tflite(build_block5(), "vww_block_5", quant_mode, class_names=class_names)
        keras2tflite(build_block6(), "vww_block_6", quant_mode, class_names=class_names)
        keras2tflite(build_block7(), "vww_block_7", quant_mode, class_names=class_names)
        keras2tflite(build_block8(), "vww_block_8", quant_mode, class_names=class_names)
        keras2tflite(build_block9(), "vww_block_9", quant_mode, class_names=class_names)
        keras2tflite(build_block10(), "vww_block_10", quant_mode, class_names=class_names)
        keras2tflite(build_block11(), "vww_block_11", quant_mode, class_names=class_names)
        keras2tflite(build_block12(), "vww_block_12", quant_mode, class_names=class_names)
        keras2tflite(build_head(), "vww_block_head", quant_mode, class_names=class_names)

        # Run forward
        x = data
        x = run_block(x, "vww_block_stem", quant_mode)
        x = run_block(x, "vww_block_0", quant_mode)
        x = run_block(x, "vww_block_1", quant_mode)
        x = run_block(x, "vww_block_2", quant_mode)
        x = run_block(x, "vww_block_3", quant_mode)
        x = run_block(x, "vww_block_4", quant_mode)
        x = run_block(x, "vww_block_5", quant_mode)
        x = run_block(x, "vww_block_6", quant_mode)
        x = run_block(x, "vww_block_7", quant_mode)
        x = run_block(x, "vww_block_8", quant_mode)
        x = run_block(x, "vww_block_9", quant_mode)
        x = run_block(x, "vww_block_10", quant_mode)
        x = run_block(x, "vww_block_11", quant_mode)
        x = run_block(x, "vww_block_12", quant_mode)
        y = run_block(x, "vww_block_head", quant_mode)
