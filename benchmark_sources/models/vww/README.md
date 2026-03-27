# MobileNetV1 for Visual Wake Words tasks (MLPerfTiny)

### Steps
1. Download the dataset and put it inside the /dataset folder:
    ```
    wget https://www.silabs.com/public/files/github/machine_learning/benchmarks/datasets/vw_coco2014_96.tar.gz
    tar -xvf vw_coco2014_96.tar.gz
    ```
2. Create flatbuffers:  `python -m create_flatbuffers --out_dir **OUT_DIR**--quant_mode **Q_MODE**`. \
The arguments are as follows:
    - OUT_DIR is the output directory where the generated flatbuffers will be saved
    - Q_MODE can be either "fp32", "fp16", or "int8".
    - Use the option `--separate_layers` to separate the layers of the full MobileNetV1 model and create flatbuffers for each of them