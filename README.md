# BIST Katılım AI Predictor

Yapay zeka destekli BIST Katılım hisseleri tahmin sistemi.

## Amaç

- %5'in üzerinde yükselen Katılım hisselerinin önceki işlem günündeki verilerini öğrenmek
- RSI, MACD, VWAP, ATR, hacim ve diğer teknik göstergeleri analiz etmek
- KAP, şirket, sektör ve ekonomik haberleri teknik verilerle ilişkilendirmek
- Öğrenilmiş örüntülerden kalıcı bir AI hafızası oluşturmak
- Tüm Katılım hisselerini günlük olarak taramak
- En yüksek potansiyele sahip 10 hisseyi tahmini yükseliş oranı ve güven değeriyle listelemek
- Geçmiş tahminlerin doğruluğunu ölçmek
- Modeli kontrollü şekilde geliştirmek
- Öğrenmeyi açıp kapatabilmek
- Model sürümlerini korumak ve gerektiğinde önceki modele dönmek

## Çalışma prensibi

Öğrenme verisi yalnızca %5'in üzerinde yükselen Katılım hisselerinden oluşturulur.

Tahmin aşamasında ise BIST Katılım Tüm Payları kapsamındaki tüm hisseler değerlendirilir.

## Güvenlik

Bu proje gerçek para ile otomatik alım-satım yapmaz.

Model geçmiş verilerle test edilir ve yeni model mevcut modelden daha iyi olduğu doğrulanmadan otomatik olarak etkinleştirilmez.
