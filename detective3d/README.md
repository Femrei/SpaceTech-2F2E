# Trend Dedektifi 3B (owner: D)

Projenin ana arayüzü. Repodaki analiz kodunu (A'nın verisi, B'nin `trend.py`'si, D'nin `detective.py`'si ve C'nin `api.py`'si) yalnızca okur, hiçbirini değiştirmez.

## Çalıştırma

Harita ve dedektif ajanı tek sunucudan çalışır. Gerekli paketler repo kökündeki `requirements.txt` ile kurulur (`pip install -r requirements.txt`).

```bash
# repo kökünden
python detective3d/agent_server.py
```

Ardından tarayıcıda http://localhost:8765 adresini aç.

İnternet bağlantısı gerekir; harita karoları ve MapLibre kütüphanesi CDN'den yüklenir. Sadece haritaya bakmak istersen `detective3d/` içinde `python -m http.server 8765` da yeterli. O durumda sohbet "sunucu kapalı" der.

## Ajan için ücretsiz LLM (önerilen: Groq)

1. https://console.groq.com adresinde ücretsiz hesap aç. Kredi kartı gerekmiyor.
2. **API Keys → Create API Key** ile bir anahtar oluştur. Anahtar `gsk_...` ile başlar.
3. `detective3d/` klasöründe `.env.example` dosyasını kopyala, adını `.env` yap ve `LLM_API_KEY=` satırına anahtarı yapıştır. `LLM_PROVIDER=groq` zaten yazılı.
4. Sunucuyu yeniden başlat. Konsolda `LLM: açık (Groq · …)` yazmalı; sohbet panelinde de "çevrimiçi" görünmeli.

`.env` dosyası `.gitignore` sayesinde git'e girmez. Asla commit etme, kimseyle paylaşma, sohbete yapıştırma. Yayındaki sunucuda (Render vb.) anahtarı `.env` yerine sunucunun gizli ortam değişkeni (`LLM_PROVIDER`, `LLM_API_KEY`) olarak tanımla.

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
  - `analyze_place` (C): üç bölge dışındaki herhangi bir yer ("Gaziantep'te toprak ne durumda?"). Koordinat önce `cities.js` şehir listesinden, yoksa modelin verdiği enlem/boylamdan alınır. Yerin çevresindeki ~1°'lik kutuda NASA POWER 1981–2025 verisi B'nin analiziyle incelenir (1981–2025 ve 2001–2025 trendi); harita kutuyu "Alan seç" panelinde açar. Çevrimdışı modda da cümlede geçen şehir bulunur.
- **Harita kontrolü:** `control_map` aracıyla ajan haritayı yönetir: bölgeye uçar, değişkeni/ayı/modu değiştirir, NDVI katmanını açıp kapatır.
- **Kurallar (sistem talimatı):** Her sayı bir araçtan gelir. Trend neden değildir. Bölge ortalaması tarla ölçümü değildir. Gübre/sulama dozu önerilmez.
- **Çevrimdışı mod:** LLM tanımlı değilse anahtar kelimelerden bölge ve değişken bulunur, istatistik ve D'nin ipucu gösterilir.
- **Sohbet geçmişi:** Sunucu belleğinde tutulur, sunucu kapanınca silinir.

## Veriyi yenileme

Uygulama, betiklerin ürettiği hazır `*.js` veri dosyalarıyla çalışır; bunlar repoda. Betiklerin ham indirme klasörleri (`power_raw/`, `ne_raw/`) repoya girmez (`.gitignore`); betik tekrar çalıştırılınca yeniden indirilir.

`build_data.py`, repodaki `api.py` fonksiyonlarını yalnızca okuyarak çağırır ve `data.js` dosyasını üretir. İçinde B'nin trend analizi ve D'nin kataloğu kullanılır.

```bash
python detective3d/build_data.py
```

Kaynak linkleri (veri seti adı ve tam Giovanni isteği) A'nın `data/SOURCES.md` dosyasından okunur.

`build_power.py`, NASA POWER'dan 1981–2025 aylık verisini indirir ve `power_data.js` dosyasını üretir. Anahtar gerekmez.

- **İndirilenler:** Her bölge kutusundaki POWER ızgara noktaları, toplam 24 nokta. Ham yanıtlar `power_raw/` klasörüne kaydedilir.
- **Değişkenler:** `T2M`, `T2M_MAX`, `PRECTOTCORR` ve `GWETROOT` (kök bölgesi ıslaklığı, %).
- **Analiz:** B'nin `analyze_trend` fonksiyonu 1981–2025 ve 2001–2025 dönemlerinde ayrı ayrı çalıştırılır.

```bash
python detective3d/build_power.py
```

## Ekranda neler var

- **Harita ve arazi:** 3B eğik kamera. Arazi AWS Terrain Tiles ile 2.2× abartılı gösteriliyor. Taban harita Esri uydu görüntüsü ya da NASA Blue Marble olabilir.
- **Bölge kutuları:** 12 aylık ortalamanın normalden sapmasına göre renkleniyor.
  - Ortadaki 3B sütunun yüksekliği sapmanın büyüklüğünü (σ) gösteriyor.
- **Yere bağlı kartlar:** Her bölgede o ayın değeri, sapma, bir sparkline ve Sen trendi ile anlamlılık rozeti var.
- **Zaman oynatıcı (2001→2025):** Hız seçilebilir. Space tuşu oynatır/durdurur, ← → tuşları birer ay ilerler/geriler.
- **Önce/Sonra karşılaştırması:** 2001–05 ile 2021–25 ortalamaları.
- **Karar kartı:** Sol panelin en üstünde. Ne / nerede / ne kadar (Sen eğimi /10 yıl ve %) / anlamlı mı (p değeri ve rozet) satırlarını gösterir. Eğilim anlamlı değilse B'nin `years_needed_estimate` alanından "yaklaşık X yıl daha veriyle anlamlı olabilir" yazar; 50 yıldan fazla ek veri gerekiyorsa sayı yerine "ayırt edilemeyecek kadar zayıf" der. Bu bir kaba tahmindir ve eğimin aynı kaldığını varsayar. "Alan seç" sonuçlarında da aynı kart çıkar.
- **İpucu kutusu:** Değişkenin tek cümlelik tanımı (`short_description` / `short_description_tr`) ve "Bu ne anlama geliyor?" metni, kaynaklarıyla.
- **Sıradaki ipucu:** Katalogdaki dedektif ipucu (`hints[].text` / `text_tr`) ve onu izleyen düğme; sohbetteki ipucuyla aynıdır.
- **Güven aralıkları:** Kutudaki aralık Sen eğiminin kendi %95 güven aralığıdır (B'nin `sen_ci_low` / `sen_ci_high`; mevsimsel Kendall eğimi, Gilbert 1987). OLS eğimi ve onun aralığı altında ayrı bir satırda, adıyla yazılır.
- **Grafiği büyüt:** Eksenli büyük grafik: y ekseni ve değer etiketleri, üzerinde gezinince ay ve değer, ham / mevsimsellikten arındırılmış geçişi, Sen eğimi ve güven aralığı bandı. Esc ya da × kapatır.
- **Bu ne anlama geliyor? (D):** İpucu kutusundaki bağlam metni katalogdan gelir (`variables[].context` / `context_tr`), kaynaklarıyla.
- **Sol panel ("Dedektif dosyası"):** Karar kartı, ipucu kutusu, istatistikler ve seri grafiği. Bütün yazılar TR/EN sözlüğünden gelir.
- **NDVI katmanı:** NASA GIBS üzerinden MODIS Terra 16 günlük NDVI. Yalnızca görseldir, analizde kullanılmaz.
- **Otomatik tur:** Genel görünümden sırayla her bölgeye uçar (Katmanlar menüsü).
- **Yıllık şeritler:** Sol panelde her yıl bir renkli şerit olarak görünür: o yılın aylık sapmalarının (mevsim etkisi çıkarılmış) ortalaması. Renk kuru/ıslak ya da serin/sıcak yönü, koyuluk büyüklüğü gösterir; ölçek ±2 standart sapmada doygunlaşır. "25 yıl" Giovanni, "45 yıl" NASA POWER verisidir.
  - **Büyüt** iki görünümlü bir pencere açar. **Yıllar:** üstte şerit, altında her yılın sapması çubuk olarak. **Yıl × ay:** her hücre o ayın kendi ortalamasından sapması, sağda yılın ortalaması.
  - Fareyle üzerine gelince değer görünür. Giovanni'de bir hücreye tıklayınca harita ve zaman çubuğu o aya gider.
- **45 yıllık kontrol:** Aynı kutu için NASA POWER ile 1981–2025 ve 2001–2025 trendleri gösterilir.
  - İki veri seti ters yön gösteriyorsa ⚠️ uyarısı çıkar.
  - İkisi aynı yönde ve anlamlıysa ✓ işareti çıkar.
  - 45 yılda ve son 25 yılda anlamlılık farklıysa 🕵️ ipucu çıkar.
- **Kaynaklar:** Veri seti adı, tam Giovanni isteğinin linki ve POWER API belgesi. Kutusu denize ya da göle taşan bölgelerde (Doğu Karadeniz ~%15 deniz, Van ~%14 göl; `scripts/check_bbox_water.py`) bunu söyleyen bir not da çıkar. Ajanın cevaplarının altında da kullandığı veri setleri link olarak görünür.
- **CSV indir:** Seçili bölge ve değişken için Giovanni ve POWER aylık serileri tek dosyada indirilir.
- **Alan seç (C):** Sağ üstteki **Alan seç** düğmesi haritayı tepeden görünüme alır.
  - **Nokta:** Haritaya tıklayınca o noktayı içeren NASA POWER ızgara hücresi (~55 km) analiz edilir.
  - **Kare çiz:** İki karşı köşeye tıklanır (en fazla 10° × 10°). Kutunun içindeki hücrelerin alan ağırlıklı ortalaması analiz edilir.
  - Veri sunucunun `/api/point` ve `/api/box` adreslerinden canlı gelir (C'nin `api.py` + `power_loader.py`, 1981–2025). Trend B'nin aynı analiziyle hesaplanır; internet gerekir.
  - Sonuç sol panelde gösterilir: hikâye cümlesi, istatistikler, grafik, yıllık şeritler ve CSV. **Bölgelere dön** ile üç bölgeye dönülür.
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

Veriler Giovanni'den alınmış bölge ortalamalarıdır (~25 km ızgara). Tarla ölçeğinde parsel yoktur; NDVI katmanı yalnızca görseldir. Bunlar Faz 2'deki ayrı agri projesinin konusu.
