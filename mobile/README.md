# BIST Katılım AI — Telefon uygulaması

Uygulama tahminleri ve gerçekleşen sonuçları gösterir. Telefonda tek başına çalışır; bilgisayarda Expo Go veya geliştirme sunucusu açık kalmasına gerek yoktur. Güncel veriyi almak için internet bağlantısı gerekir. API adresi uygulama paketinde tanımlıdır ve veritabanı anahtarı içermez.

## Android'e yükleme

1. Bu depodaki **Actions → Build installable Android app** akışının son başarılı çalışmasını aç.
2. **Artifacts** bölümünden `bist-katilim-ai-android-apk` dosyasını telefona indir ve ZIP arşivini aç.
3. `app-debug.apk` dosyasına dokunup Android kurulum ekranındaki adımları uygula. Android, GitHub'dan indirdiğin dosya için tarayıcıya bir defalık “bilinmeyen uygulamaları yükle” izni isteyebilir.
4. Uygulamayı aç. Tahminler ve sonuç takibi sunucudaki API'den yüklenir.

Akış, `main` dalında mobil uygulama değiştiğinde otomatik çalışır; GitHub Actions sayfasından elle de başlatılabilir. Bu, telefona doğrudan kurulabilen Android APK'sıdır; Google Play sürümü değildir. Yeni bir APK farklı CI imzasıyla üretildiğinden, sonraki sürüme geçerken Android eski uygulamayı kaldırmanı isteyebilir.

## iPhone'a ekleme

iPhone'da App Store imzalı yerel sürüm yerine, mevcut web paneli Safari'den ana ekrana eklenebilir. Yayındaki paneli Safari'de açıp **Paylaş → Ana Ekrana Ekle** seç. Ana ekrandan uygulama gibi açılır; güncel tahminleri almak için internet gerekir. iOS için imzalı yerel IPA/TestFlight dağıtımı Apple Developer hesabı ve cihaz imzalama yapılandırması gerektirir.

## Geliştirici önizlemesi

Expo Go yalnızca geliştirme içindir. Geliştirici bilgisayarından `npm install` ve `npx expo start --tunnel` komutlarıyla çalıştırılabilir; telefonda gündelik kullanım için gerekmez.

Uygulama **Tahminler** ve **Sonuç takibi** ekranlarını içerir. Alım-satım yapmaz ve tahminler garanti değildir.
