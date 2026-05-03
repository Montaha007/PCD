"""
inference/  — §5.2 Model Layer
Exposes the three inference functions that produce inputs for the Agent Layer.
"""
from .sleep_inference     import predict_insomnia      # §5.2.1
from .lifestyle_inference import predict_sleep_time    # §5.2.2
from .nlp_inference       import predict_mental_state  # §5.2.3

__all__ = ["predict_insomnia", "predict_sleep_time", "predict_mental_state"]
