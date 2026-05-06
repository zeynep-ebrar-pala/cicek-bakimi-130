import os
import json
import datetime
from data import PLANTS, DISEASES
from database import get_my_garden, update_care, add_log, update_learned_knowledge, set_agent_setting, get_agent_setting

class BotanicaAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.name = "Botanica Akıllı Yönetim Merkezi"
        self.system_prompt = """
        Sen 'Botanica AI' uygulamasının beynisin. 
        Kullanıcıya sadece veri göstermekle kalmaz, bahçenin tüm yönetimini otonom olarak üstlenebilirsin.
        Profesyonel, çözüm odaklı ve proaktif bir dil kullan.
        """

    def _safe_date(self, value):
        if isinstance(value, datetime.date):
            return value
        if not value:
            return datetime.date.today()
        try:
            return datetime.date.fromisoformat(str(value))
        except Exception:
            return datetime.date.today()

    def process_command(self, user_input):
        """Kullanıcı komutunu işler."""
        user_input = user_input.lower()
        
        if any(word in user_input for word in ["rapor", "analiz", "durum"]):
            return self.generate_report()
        elif any(word in user_input for word in ["sula", "strateji", "su", "optimize"]):
            return self.update_watering_strategy(user_input)
        elif any(word in user_input for word in ["hastalık", "anomali", "sorun", "teşhis"]):
            return self.diagnose_plant_anomalies()
        else:
            return {
                "status": "info",
                "message": f"🤖 **{user_input}** konusundaki talebinizi anladım. Şu an bahçenizin raporlamasını yapabilir, sulama stratejilerini optimize edebilir ve sağlık taraması gerçekleştirebilirim. Hangi işlemi başlatmamı istersiniz?",
                "data": None
            }

    def generate_report(self):
        """Bahçe durum raporu oluşturur."""
        my_plants = get_my_garden()
        if not my_plants:
            return {"status": "error", "message": "Bahçenizde henüz bitki yok."}
        
        report = "### 📊 Haftalık Botanica Analiz Raporu\n"
        anomalies = []
        
        for p in my_plants:
            plant_data = next((pd for pd in PLANTS if pd["id"] == p["plant_id"]), None)
            last_w = self._safe_date(p["last_watered"])
            days_since = (datetime.date.today() - last_w).days
            
            status = "Sağlıklı" if not p["is_sick"] else "Tedavide"
            report += f"- **{p['nickname']}** ({plant_data['name']}): {status}. Son sulama {days_since} gün önce.\n"
            
            if days_since > 7 and plant_data["water_level"] > 1:
                anomalies.append(f"{p['nickname']} kritik susuzluk sınırında!")

        if anomalies:
            report += "\n⚠️ **Anomaliler Tespit Edildi:**\n"
            for a in anomalies:
                report += f"- {a}\n"
        
        return {"status": "success", "message": report, "data": {"anomalies": anomalies}}

    def update_watering_strategy(self, command):
        """Sulama stratejisini günceller."""
        # Mockup: Veritabanında bir ayar günceller
        set_agent_setting("watering_adjustment", "-10%")
        return {
            "status": "success", 
            "message": "Sulama algoritması otonom olarak %10 optimize edildi. Bitkileriniz artık daha verimli su tüketecek.",
            "data": {"adjustment": -10}
        }

    def diagnose_plant_anomalies(self):
        """Proaktif olarak sorunları tarar."""
        my_plants = get_my_garden()
        findings = []
        for p in my_plants:
            if p["is_sick"]:
                findings.append(f"{p['nickname']} bitkinizde devam eden bir hastalık var. 3. aşama tedavi modülünü başlatmamı ister misiniz?")
            
            last_w = self._safe_date(p["last_watered"])
            if (datetime.date.today() - last_w).days > 10:
                findings.append(f"{p['nickname']} uzun süredir sulanmamış. Bu durum kök çürümesine yol açabilir.")

        if not findings:
            return {"status": "success", "message": "Harika! Şu an tüm bitkileriniz stabil görünüyor.", "data": []}
        
        return {"status": "success", "message": "\n".join(findings), "data": findings}

    def optimize_care_knowledge(self):
        """Öğrenilen bilgilerle DB'yi optimize eder."""
        # Mockup: Geri bildirimlerden öğrenme simülasyonu
        update_learned_knowledge(1, "watering", "Paşa Kılıcı için kışın 3 hafta ideal.", 0.95)
        return {
            "status": "success", 
            "message": "Kullanıcı alışkanlıkları analiz edildi. Paşa Kılıcı bakım kılavuzu kış şartlarına göre güncellendi.",
            "data": None
        }
