# ResNet8 for CIFAR10 Image Classification

### Steps
1. Download the CIFAR10 dataset and put it inside the /dataset folder.
2. Create flatbuffers:  `python -m create_flatbuffers --out_dir **OUT_DIR**--quant_mode **Q_MODE**`. \
The arguments are as follows:
    - OUT_DIR is the output directory where the generated flatbuffers will be saved
    - Q_MODE can be either "fp32", "fp16", or "int8".
    - Use the option `--separate_layers` to separate the layers of the full ResNet8 model and create flatbuffers for each of them