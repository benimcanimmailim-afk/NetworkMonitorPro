# Ultra Network Monitor Pro v5

Bu program, yerel ağdaki cihazları izlemek, yönetmek ve çeşitli ağ araçlarını kullanmak için geliştirilmiş, modern bir grafiksel kullanıcı arayüzüne (GUI) sahip Python tabanlı bir ağ yönetim aracıdır.

## 🚀 Temel Özellikler

- **Gerçek Zamanlı İzleme:** Cihazların çevrimiçi durumlarını, gecikme sürelerini (ping) ve çalışma sürelerini (uptime) canlı olarak takip edin.
- **Gelişmiş Ağ Keşfi:** Belirli IP aralıklarını tarayarak ağdaki aktif cihazları otomatik olarak tespit edin.
- **Cihaz Yönetimi:** Cihazlara özel etiketler ekleyin, gruplayın ve cihaz listelerini paket olarak kaydedip yükleyin.
- **Entegre Ağ Araçları:**
  - **Hostname Çözümleme:** IP adresinden bilgisayar adını bulma.
  - **Üretici Tespiti:** MAC adresi üzerinden cihazın markasını (Cisco, Apple, HP vb.) belirleme.
  - **Port Tarama:** Kritik servislerin (SSH, HTTP, RDP vb.) açık olup olmadığını kontrol etme.
  - **Traceroute:** Verinin hedefe giderken izlediği yolu görüntüleme.
- **Uzak Bağlantı Desteği:** SSH ve RDP bağlantılarını tek tıkla başlatma (Windows öncelikli).
- **Modern Arayüz:** Karanlık ve Aydınlık mod desteği ile özelleştirilebilir kullanıcı deneyimi.

## 🛠️ Teknik Mimari

- **Dil:** Python 3
- **Arayüz:** Tkinter (Modern temalı)
- **Modüller:**
  - `main.py`: Kullanıcı arayüzü ve ana uygulama mantığı.
  - `network_utils.py`: Ağ operasyonları (Ping, ARP, Port Scan vb.) için yardımcı fonksiyonlar.
  - `config_manager.py`: Yapılandırma ve cihaz paketlerinin JSON formatında saklanması.
- **Uyumluluk:** Windows, Linux ve macOS platformları için optimize edilmiştir.

## 📦 Kurulum ve Çalıştırma

1. Gerekli bağımlılıkları yükleyin (Genellikle standart kütüphaneler kullanılır).
2. Uygulamayı başlatın:
   ```bash
   python main.py
   ```

---
*Bu doküman kullanıcı isteği üzerine programın işlevlerini açıklamak amacıyla oluşturulmuştur.*
