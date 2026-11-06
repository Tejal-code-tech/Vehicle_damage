import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import numpy as np
import os
import json



# Configuration
IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 50

# Dataset paths - UPDATED FOR YOUR KAGGLE DATASET
TRAIN_DIR = '../dataset/training'  # Changed from 'train' to 'training'
VAL_DIR = '../dataset/validation'   # Changed from 'val' to 'validation'
MODEL_SAVE_PATH = 'model_weights/damage_detector.h5'

def create_binary_cnn_model():
    """
    Creates CNN for binary classification (damaged vs whole)
    Using Transfer Learning with MobileNetV2
    """
    base_model = keras.applications.MobileNetV2(
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        include_top=False,
        weights='imagenet'
    )
    
    # Freeze base model initially
    base_model.trainable = False
    
    # Create full model for binary classification
    model = keras.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dropout(0.3),
        layers.Dense(256, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.Dense(128, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.2),
        layers.Dense(64, activation='relu'),
        layers.Dense(2, activation='softmax')  # 2 classes: damage/whole
    ])
    
    return model

def train_model():
    """Train the binary damage detection model"""
    
    print("=" * 70)
    print("TRAINING BINARY CAR DAMAGE CLASSIFIER")
    print("Dataset: Kaggle Car Damage Detection")
    print("Classes: 00-damage, 01-whole")
    print("=" * 70)
    
    # Data augmentation for training
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=25,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        zoom_range=0.2,
        shear_range=0.15,
        brightness_range=[0.8, 1.2],
        fill_mode='nearest'
    )
    
    # Validation data generator
    val_datagen = ImageDataGenerator(rescale=1./255)
    
    # Load training data
    train_generator = train_datagen.flow_from_directory(
        TRAIN_DIR,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        shuffle=True
    )
    
    # Load validation data
    val_generator = val_datagen.flow_from_directory(
        VAL_DIR,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        shuffle=False
    )
    
    print(f"\nTraining samples: {train_generator.samples}")
    print(f"Validation samples: {val_generator.samples}")
    print(f"Class labels: {train_generator.class_indices}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Steps per epoch: {train_generator.samples // BATCH_SIZE}")
    
    # Create model
    model = create_binary_cnn_model()
    
    # Compile model
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
    )
    
    print("\nModel Architecture:")
    model.summary()
    
    # Callbacks
    callbacks = [
        keras.callbacks.EarlyStopping(
            patience=10,
            restore_best_weights=True,
            monitor='val_accuracy'
        ),
        keras.callbacks.ReduceLROnPlateau(
            factor=0.5,
            patience=5,
            min_lr=1e-7,
            monitor='val_loss'
        ),
        keras.callbacks.ModelCheckpoint(
            MODEL_SAVE_PATH,
            save_best_only=True,
            monitor='val_accuracy',
            verbose=1
        )
    ]
    
    print("\nStarting training...")
    print("=" * 70)
    
    # Train model - Stage 1: Frozen base
    history = model.fit(
        train_generator,
        epochs=20,
        validation_data=val_generator,
        callbacks=callbacks,
        verbose=1
    )
    
    # Stage 2: Fine-tune last layers of base model
    print("\n" + "=" * 70)
    print("STAGE 2: Fine-tuning last layers")
    print("=" * 70)
    
    base_model = model.layers[0]
    base_model.trainable = True
    
    # Freeze all layers except last 20
    for layer in base_model.layers[:-20]:
        layer.trainable = False
    
    # Recompile with lower learning rate
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.0001),
        loss='categorical_crossentropy',
        metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
    )
    
    # Continue training
    history_finetune = model.fit(
        train_generator,
        epochs=5,
        validation_data=val_generator,
        callbacks=callbacks,
        verbose=1
    )
    
    # Save class labels
    class_labels = {v: k for k, v in train_generator.class_indices.items()}
    with open('model_weights/class_labels.json', 'w') as f:
        json.dump(class_labels, f, indent=2)
    
    print("\n" + "=" * 70)
    print("TRAINING COMPLETE!")
    print("=" * 70)
    print(f"Model saved: {MODEL_SAVE_PATH}")
    print(f"Labels saved: model_weights/class_labels.json")
    print(f"Final validation accuracy: {max(history_finetune.history['val_accuracy']):.4f}")
    print(f"Final validation precision: {max(history_finetune.history['val_precision']):.4f}")
    print(f"Final validation recall: {max(history_finetune.history['val_recall']):.4f}")

if __name__ == '__main__':
    # Create model_weights directory
    os.makedirs('model_weights', exist_ok=True)
    
    # Check if dataset exists
    if not os.path.exists(TRAIN_DIR):
        print(f"\nERROR: Training directory not found at: {TRAIN_DIR}")
        print("\nYour dataset should be structured as:")
        print("dataset/")
        print("  training/")
        print("    00-damage/")
        print("    01-whole/")
        print("  validation/")
        print("    00-damage/")
        print("    01-whole/")
        print("\nPlease organize your Kaggle dataset accordingly.")
    else:
        train_model()