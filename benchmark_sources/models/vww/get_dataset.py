import os
import tensorflow as tf
import argparse

IMAGE_SIZE = 96


def get_vww_generator(data_dir, batch_size=1):
    datagen = tf.keras.preprocessing.image.ImageDataGenerator(
        rotation_range=10,
        width_shift_range=0.05,
        height_shift_range=0.05,
        zoom_range=.1,
        horizontal_flip=True,
        validation_split=0.1,
        rescale=1. / 255
    )
    train_generator = datagen.flow_from_directory(
        data_dir,
        target_size=(IMAGE_SIZE, IMAGE_SIZE),
        batch_size=batch_size,
        subset='training',
        color_mode='rgb'
    )
    val_generator = datagen.flow_from_directory(
        data_dir,
        target_size=(IMAGE_SIZE, IMAGE_SIZE),
        batch_size=batch_size,
        subset='validation',
        color_mode='rgb'
    )

    return train_generator
