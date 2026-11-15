# Trend Dedektifi 3B: yerel prototip

Bu klasör **repo dışında** duruyor. SpaceTech-2F2E'de hiçbir dosyayı değiştirmez.

## Çalıştırma

Harita ve dedektif ajanı tek sunucudan çalışır. Gerekli paketler klasördeki `.venv` sanal ortamında kurulu.

```bash
cd "D:/Nasa Space Apps/prototype-3d"
.venv/Scripts/python agent_server.py
```

Ardından tarayıcıda http://localhost:8765 adresini aç.

İnternet bağlantısı gerekir; harita karoları ve MapLibre kütüphanesi CDN'den yüklenir. Sadece haritaya bakmak istersen `python -m http.server 8765` da yeterli. O durumda sohbet "sunucu kapalı" der.

## Ajan için ücretsiz LLM (önerilen: Groq)

1. https://console.groq.com adresinde ücretsiz hesap aç. Kredi kartı gerekmiyor.
2. **API Keys → Create API Key** ile bir anahtar oluştur. Anahtar `gsk_...` ile başlar.
3. Bu klasörde `.env.example` dosyasını kopyala, adını `.env` yap ve `LLM_API_KEY=` satırına anahtarı yapıştır. `LLM_PROVIDER=groq` zaten yazılı.
4. Sunucuyu yeniden başlat. Konsolda `LLM: açık (Groq · …)` yazmalı; sohbet panelinde de "çevrimiçi" görünmeli.

`.env` dosyası repo dışında durur. Asla commit etme, kimseyle paylaşma, sohbete yapıştırma.

### Diğer seçenekler (hepsi `.env` ile değiştirilir)

| `LLM_PROVIDER` | Ücret | Not |
|---|---|---|
| `groq` | Ücretsiz katman | Çok hızlı. Dakikalık ve günlük istek/token sınırları var. Varsayılan model `openai/gpt-oss-120b`. |
| `gemini` | Ücretsiz katman | Anahtar https://aistudio.google.com/apikey adresinden alınır. Türkçesi güçlü ama günlük istek sınırı düşük olabilir. Ücretsiz katmanda veriler Google'ın ürün geliştirmesinde kullanılabilir. |
| `openrouter` | `:free` modeller ücretsiz | Günlük istek sınırı düşük. |
| `ollama` | Tamamen ücretsiz, çevrimdışı | Anahtar ve sınır yok. Önce `ollama pull qwen2.5:7b` ile ~4.7 GB model indirilir. Bu bilgisayarda ekran kartı yok, sadece işlemci var; bir cevap 30–90 sn sürebilir. |
| `anthropic` | Ücretli | En iyi kalite. `ANTHROPIC_API_KEY` ve `AGENT_MODEL` ile çalışır. |

Ücretsiz katmanların sınırları sık değişiyor; güncel değerler sağlayıcının kendi konsolunda yazar. Varsayılan model kaldırılmışsa sohbet, kullanılabilir modelleri listeleyen bir hata gösterir. O zaman listeden birini `.env`'deki `LLM_MODEL=` satırına yaz.

Ücretsiz kotaya takılmamak için sunucu her sohbette yalnızca son 4 soruyu geçmişte tutar.

## Dedektif ajanı (`agent_server.py`)

Sağ alttaki **Dedektife sor** düğmesi sohbet panelini açar.

- **Araç döngüsü:** Ücretsiz sağlayıcılar OpenAI uyumlu Chat Completions API'sini, Claude ise kendi SDK'sını kullanır. Araçlar ve kurallar ikisinde de aynıdır.
- **Araçlar:** Hepsi repodaki fonksiyonları salt-okunur çağırır.
  - `get_trend`: B'nin Mann-Kendall + Sen analizi ve D'nin ipucu/bağlam metinleri
  - `compare_regions`
  - `get_overview`
  - `get_period_stats`
  - `get_background`
- **Harita kontrolü:** `control_map` aracıyla ajan haritayı yönetir: bölgeye uçar, değişkeni/ayı/modu değiştirir, NDVI katmanını açıp kapatır.
- **Kurallar (sistem talimatı):** Her sayı bir araçtan gelir. Trend neden değildir. Bölge ortalaması tarla ölçümü değildir. Gübre/sulama dozu önerilmez.
- **Çevrimdışı mod:** LLM tanımlı değilse anahtar kelimelerden bölge ve değişken bulunur, istatistik ve D'nin ipucu gösterilir.
- **Sohbet geçmişi:** Sunucu belleğinde tutulur, sunucu kapanınca silinir.

## Veriyi yenileme

`build_data.py`, repodaki `api.py` fonksiyonlarını yalnızca okuyarak çağırır ve `data.js` dosyasını üretir. İçinde B'nin trend analizi ve D'nin kataloğu kullanılır.

```bash
.venv/Scripts/python build_data.py ../SpaceTech-2F2E
```

Kaynak linkleri (veri seti adı ve tam Giovanni isteği) A'nın `data/SOURCES.md` dosyasından okunur.

`build_power.py`, NASA POWER'dan 1981–2025 aylık verisini indirir ve `power_data.js` dosyasını üretir. Anahtar gerekmez.

- **İndirilenler:** Her bölge kutusundaki POWER ızgara noktaları, toplam 24 nokta. Ham yanıtlar `power_raw/` klasörüne kaydedilir.
- **Değişkenler:** `T2M`, `T2M_MAX`, `PRECTOTCORR` ve `GWETROOT` (kök bölgesi ıslaklığı, %).
- **Analiz:** B'nin `analyze_trend` fonksiyonu 1981–2025 ve 2001–2025 dönemlerinde ayrı ayrı çalıştırılır.

```bash
.venv/Scripts/python build_power.py ../SpaceTech-2F2E
```

`build_ndvi.py`, MODIS NDVI 2001–2025 verisini işleyip `ndvi_data.js` dosyasını üretir.

- **Veri:** MOD13Q1 v061 (250 m, 16 günlük). ORNL DAAC'nin hesap istemeyen MODIS servisinden gelir.
- **İndirme:** Servis istek başına en çok 10 tarih verdiği için seri yaklaşık 175 parçada iner; her parça ~30 sn sürer. Parçalar `ndvi_raw/` klasöründe saklanır. Yarıda kesilirse tekrar çalıştırınca kaldığı yerden devam eder.
- **Pencereler:** Her bölgede 10 km × 10 km'lik bir pencere kullanılır. Pencereler MODIS arazi örtüsüne (MCD12Q1 2020, IGBP) bakılarak seçildi:

| Bölge | Pencere | Arazi örtüsü |
|---|---|---|
| Konya | Çumra ovası (37.57°K, 32.77°D) | %90 tarım |
| Van | Erciş ovası (39.03°K, 43.35°D) | %64 tarım, %20 çayır |
| Doğu Karadeniz | Rize kıyı yamaçları (40.97°K, 40.55°D) | Tarım sınıfı yok; odunsu savan ve orman. Doğal bitki örtüsü penceresi olarak etiketlendi. |

- **Yöntem:**
  - Her kompozitte penceredeki geçerli piksellerin ortalaması alınır.
  - Aylık değer, o aydaki kompozitlerin en yükseğidir (bulut etkisini azaltır).
  - Trend için B'nin `analyze_trend` fonksiyonu kullanılır. Her yılın zirve NDVI'si için ayrıca Mann-Kendall testi ve Sen eğimi hesaplanır.

```bash
.venv/Scripts/python build_ndvi.py ../SpaceTech-2F2E
```

ORNL sunucusu yoğunken çok sayıda "502" hatası verir. Betik inmeyen parçaları 6 tura kadar yeniden dener; yine de eksik kalırsa durur. Sadece tamamlanmış bölgelerle sonuç üretmek için:

```bash
NDVI_PARTIAL=1 .venv/Scripts/python build_ndvi.py ../SpaceTech-2F2E
```

**Şu anki durum (2026-11-15):**
- Konya ve Van tamamlandı.
- Doğu Karadeniz'in 58 parçasından 11'i indi. Panel ve ajan "veri henüz yok" diyor.
- Betiği normal çalıştırınca Karadeniz kaldığı yerden tamamlanır.

**İlk sonuçlar:**

| Pencere | Aylık NDVI trendi | Yıllık zirve trendi |
|---|---|---|
| Konya · Çumra | +0,029 /10 yıl, p≈5e-10 | +0,076 /10 yıl, p≈5e-5 |
| Van · Erciş | +0,021 /10 yıl, p≈2e-11 | +0,035 /10 yıl, p≈6e-4 |

İki pencerede de anlamlı yeşillenme var.

## Ekranda neler var

- **Harita ve arazi:** 3B eğik kamera. Arazi AWS Terrain Tiles ile 2.2× abartılı gösteriliyor. Taban harita Esri uydu görüntüsü ya da NASA Blue Marble olabilir.
- **Bölge kutuları:** 12 aylık ortalamanın normalden sapmasına göre renkleniyor.
  - Ortadaki 3B sütunun yüksekliği sapmanın büyüklüğünü (σ) gösteriyor.
- **Yere bağlı kartlar:** Her bölgede o ayın değeri, sapma, bir sparkline ve Sen trendi ile anlamlılık rozeti var.
- **Zaman oynatıcı (2001→2025):** Hız seçilebilir. Space tuşu oynatır/durdurur, ← → tuşları birer ay ilerler/geriler.
- **Önce/Sonra karşılaştırması:** 2001–05 ile 2021–25 ortalamaları.
- **Sol panel ("Dedektif dosyası"):** Türkçe hikâye cümlesi, istatistikler ve tam seri grafiği.
- **NDVI katmanı:** NASA GIBS üzerinden MODIS Terra 16 günlük NDVI. Yalnızca görseldir, analizde kullanılmaz.
- **Otomatik tur:** Genel görünümden sırayla her bölgeye uçar.
- **Isı haritası (yıl × ay):** Sol panelde yer alır. Her hücre, o ayın kendi ortalamasından sapmasını gösterir. "25 yıl" Giovanni, "45 yıl" NASA POWER verisidir.
- **45 yıllık kontrol:** Aynı kutu için NASA POWER ile 1981–2025 ve 2001–2025 trendleri gösterilir.
  - İki veri seti ters yön gösteriyorsa ⚠️ uyarısı çıkar.
  - İkisi aynı yönde ve anlamlıysa ✓ işareti çıkar.
  - 45 yılda ve son 25 yılda anlamlılık farklıysa 🕵️ ipucu çıkar.
- **Kaynaklar:** Veri seti adı, tam Giovanni isteğinin linki ve POWER API belgesi. Ajanın cevaplarının altında da kullandığı veri setleri link olarak görünür.
- **Bitki örtüsü · MODIS NDVI:**
  - Sol panelde tarım penceresi, arazi örtüsü, aylık ve yıllık zirve NDVI trendleri ve zirve NDVI çubuk grafiği yer alır.
  - Pencereler haritada yeşil karelerle gösterilir.
  - Ajan bu veriyi `get_ndvi_trend` aracıyla kullanır.
- **CSV indir:** Seçili bölge ve değişken için Giovanni ve POWER aylık serileri tek dosyada indirilir.
- **Ajan aracı `get_long_record`:** "Uzun vadede de böyle mi?" sorusunu POWER verisiyle cevaplar. Veri setleri çelişirse ajan bunu söyler ve yerel istasyon (MGM) kontrolü önerir.

### Veri setlerinin çeliştiği yer: Doğu Karadeniz

- **Giovanni (GLDAS, 0–10 cm):** Toprak neminde anlamlı **azalma** var.
- **NASA POWER (kök bölgesi):** Islaklıkta anlamlı **artış** var. Yağış da artıyor.

Olası nedenler:
- Farklı ürünler ve derinlikler
- Kaba ızgara
- Kutunun çoğunun dağlık olması

Bunu saklamıyoruz; dedektif hikâyesinin parçası olarak gösteriyoruz.

## Sınırlar

Veriler Giovanni'den alınmış bölge ortalamalarıdır (~25 km ızgara). Tarla ölçeğinde parsel ya da NDVI bölgesi yoktur. Bunlar Faz 2'deki ayrı agri projesinin konusu.
