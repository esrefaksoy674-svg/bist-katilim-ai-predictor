from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LearningControl:
    """
    Öğrenme modunun durumunu yönetir.

    ENABLED:
        Yeni öğrenme olayları ana öğrenme belleğine alınabilir.

    DISABLED:
        Mevcut ana öğrenme belleği/modeli değiştirilmez.
        Tarama ve tahmin işlemleri devam edebilir.
    """

    enabled: bool = True

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    def is_enabled(self) -> bool:
        return self.enabled

    def can_learn(self) -> bool:
        return self.enabled


learning_control = LearningControl()
