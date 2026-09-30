from enum import Enum


class DataMode(str, Enum):
    LAST_CLOSE = "LAST_CLOSE"


class LearningMode(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class ModelStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SHADOW = "SHADOW"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class PredictionStatus(str, Enum):
    PENDING = "PENDING"
    EVALUATED = "EVALUATED"
    INVALID = "INVALID"
