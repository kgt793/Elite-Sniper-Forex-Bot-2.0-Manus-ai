"""
TensorFlow configuration module for Elite Sniper Forex Bot.
This module configures TensorFlow to reduce warnings and optimize performance.
"""

import os
import tensorflow as tf

def configure_tensorflow():
    """
    Configure TensorFlow to suppress warnings and optimize performance.
    Call this function before importing or using any TensorFlow functionality.
    """
    # Suppress TensorFlow logging
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 0=all, 1=INFO, 2=WARNING, 3=ERROR
    
    # Disable eager execution for better performance with TF 2.x
    try:
        tf.compat.v1.disable_eager_execution()
    except:
        pass
    
    # Configure GPU memory growth if GPU is available
    gpus = tf.config.experimental.list_physical_devices('GPU')
    if gpus:
        try:
            # Currently, memory growth needs to be the same across GPUs
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
        except RuntimeError as e:
            # Memory growth must be set before GPUs have been initialized
            print(f"GPU memory growth configuration error: {e}")
    
    # Set thread pool parameters
    tf.config.threading.set_inter_op_parallelism_threads(2)
    tf.config.threading.set_intra_op_parallelism_threads(4)
    
    # Return the TensorFlow version for logging purposes
    return tf.__version__

# Configure TensorFlow when this module is imported
tensorflow_version = configure_tensorflow()
