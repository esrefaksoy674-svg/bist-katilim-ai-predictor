from __future__ import annotations

from copy import deepcopy
from datetime import date

from app.models.learning_event import LearningEvent


class LearningMemory:
    """
    Öğrenilmiş olayların yaşam döngüsünü yönetir.

    Bu katman şimdilik kalıcı veritabanından bağımsızdır.
    Veritabanı katmanı bağlandığında aynı sözleşme korunacaktır.
    """

    def __init__(self):
        self._events: list[LearningEvent] = []

    def add(self, event: LearningEvent) -> None:
        """
        Yeni öğrenme olayını belleğe ekler.

        Aynı sembol + sinyal tarihi kombinasyonu ikinci kez
        eklenmez.
        """

        for existing in self._events:
            if (
                existing.symbol == event.symbol
                and existing.signal_date == event.signal_date
            ):
                return

        self._events.append(
            deepcopy(event)
        )

    def add_many(
        self,
        events: list[LearningEvent],
    ) -> int:
        before = len(self._events)

        for event in events:
            self.add(event)

        return len(self._events) - before

    def all(self) -> list[LearningEvent]:
        return deepcopy(self._events)

    def count(self) -> int:
        return len(self._events)

    def get_by_symbol(
        self,
        symbol: str,
    ) -> list[LearningEvent]:
        symbol = symbol.upper()

        return [
            deepcopy(event)
            for event in self._events
            if event.symbol == symbol
        ]

    def get_before(
        self,
        target_date: date,
    ) -> list[LearningEvent]:
        """
        Yalnızca belirtilen tarihten önce oluşmuş
        öğrenme olaylarını döndürür.

        Backtest sırasında gelecekteki olayların kullanılmasını
        engellemek için kullanılacaktır.
        """

        return [
            deepcopy(event)
            for event in self._events
            if event.signal_date < target_date
        ]

    def clear(self) -> None:
        """
        Test ortamı için belleği temizler.

        Üretim öğrenme akışında otomatik olarak çağrılmaz.
        """

        self._events.clear()


learning_memory = LearningMemory()
