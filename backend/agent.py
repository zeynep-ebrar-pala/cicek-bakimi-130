import os
import json
import datetime
import requests
from data import PLANTS, DISEASES
from database import get_my_garden, update_care

class BotanicaAgent:
    def __init__(self, api_key=None, groq_key=None):
        self.api_key = api_key
        self.groq_key = groq_key
        self.name = "Flora: Baş Botanikçi"
        
        # Garden context
        garden = get_my_garden(api_key or groq_key) if (api_key or groq_key) else []
        plant_list = ", ".join([f"{p['nickname']} ({p['plant_id']})" for p in garden])
        
        self.system_prompt = f"""
        Sen Nabzı Filiz uygulamasının 'Baş Botanikçisi' Flora'sın. 
        Kullanıcının bahçesindeki bitkiler: {plant_list if plant_list else 'Henüz bitki yok'}.
        
        Görevin:
        1. Kullanıcının bahçesindeki bitkileri takip etmek ve onlara özel bakım stratejileri geliştirmek.
        2. Bitki Doktoru acil teşhis koyarken, sen uzun vadeli sağlık ve gelişim danışmanısın.
        3. Bitki biyolojisi, doğru saksı seçimi, mevsimsel geçişler ve gübreleme konularında uzmansın.
        4. Yanıtların her zaman samimi, profesyonel ve çözüm odaklı olmalı.
        5. Eğer kullanıcı bitki sağlığı skorunu sorursa, bahçedeki su ihtiyaçlarını analiz et.
        6. Kullanıcıya her zaman botanik bilimiyle desteklenen, uygulanabilir tavsiyeler ver.
        """

    def call_gemini(self, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{"parts": [{"text": f"{self.system_prompt}\n\nKullanıcı Sorusu: {prompt}"}]}]
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            return f"Gemini hatası: Lütfen API anahtarınızın doğru olduğundan emin olun."

    def call_groq(self, prompt):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            return f"Groq hatası: Lütfen API anahtarınızın doğru olduğundan emin olun."

    def identify_plant_vision(self, image_bytes, mime_type="image/jpeg"):
        """Gemini Vision ile bitkiyi fotoğraftan tanımlar."""
        if not self.api_key:
            return None
            
        import base64
        img_b64 = base64.b64encode(image_bytes).decode()
        
        # Kütüphanedeki bitki isimleri
        plant_names = [p["name"] for p in PLANTS]
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        headers = {'Content-Type': 'application/json'}
        
        prompt = f"""
        Sen bir botanik uzmanısın. Bu resimdeki bitkiyi tanımla. 
        Sadece şu listedeki isimlerden birini söyle: {', '.join(plant_names)}.
        Eğer bitki listedeki hiçbir türe benzemiyorsa 'Unknown' de.
        Sadece bitki ismini yaz, başka açıklama yapma.
        """
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": img_b64
                        }
                    }
                ]
            }]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            result = response.json()
            if 'candidates' in result:
                return result['candidates'][0]['content']['parts'][0]['text'].strip()
            return None
        except Exception:
            return None

    def process_command(self, user_input):
        """AI desteğiyle komutu işler."""
        if self.groq_key:
            response = self.call_groq(user_input)
        elif self.api_key:
            response = self.call_gemini(user_input)
        else:
            # Fallback to simple matching if no keys
            if any(word in user_input.lower() for word in ["rapor", "durum", "nasıllar"]):
                return {"message": "Bahçenizdeki bitkileri analiz edebilmem için lütfen 'Profilim' sekmesinden bir API anahtarı (Gemini veya Groq) girin. Bu sayede size özel raporlar hazırlayabilirim!"}
            response = "Merhaba! Ben Flora. Size uzman botanik tavsiyeleri verebilmem için lütfen Profilim sekmesinden API anahtarınızı girin."

        return {"message": response}
