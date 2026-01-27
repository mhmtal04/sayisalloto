import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter

st.set_page_config(page_title="AI Loto Analisti Pro", page_icon="🧪", layout="wide")

st.title("🧪 Gelişmiş Otonom Analiz Botu (V2)")
st.markdown("Bot, son **15 çekilişi** tarayarak aşırı ısınan sayıları eler ve bölge doygunluğunu hesaplar.")

uploaded_file = st.file_uploader("Veri setini yükle (CSV)", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    draws = df[cols].values
    
    # --- ANALİZ PARAMETRELERİ ---
    LOOKBACK = 15  # Son 15 çekilişe göre filtreleme yapar
    
    # 1. Bölge Doygunluk Analizi
    def get_pattern(draw):
        return tuple(np.histogram(draw, bins=[1, 11, 21, 31, 41, 51, 61, 71, 81, 91])[0])

    patterns = [get_pattern(d) for d in draws]
    recent_patterns = patterns[:LOOKBACK]
    
    # En çok doyuma ulaşan bölgeyi bul (Örn: 20'ler çok çıktıysa o bölgeye ceza puanı)
    region_counts = np.sum(recent_patterns, axis=0)
    max_saturated_region = np.argmax(region_counts) # En çok çıkan 10'luk grup indexi

    # 2. Sayı Puanlama Sistemi
    all_numbers = draws.flatten()
    freq = Counter(all_numbers)
    last_app = {n: i for i, d in enumerate(draws) for n in d}

    def get_autonomous_score(n):
        base_score = freq[n] * 0.5  # Genel tarihsel başarı
        recency_bonus = last_app.get(n, 100) * 0.5 # Ne kadar süredir çıkmıyor? (Bekleyen sayı avantajı)
        
        # CEZA SİSTEMİ (Son 15 Çekiliş)
        count_in_recent = np.sum(draws[:LOOKBACK] == n)
        if count_in_recent >= 3: # Son 15 çekilişte 3 ve üzeri çıkan sayıya (40 gibi) ağır ceza
            base_score -= 200
        elif count_in_recent >= 1: # En az 1 kere çıkana hafif ceza
            base_score -= 50
            
        # Bölge Cezası (Eğer sayı en doygun bölgedeyse puan kır)
        n_region = (n-1) // 10
        if n_region == max_saturated_region:
            base_score -= 30
            
        return base_score + recency_bonus

    # 3. Kolon Üretimi
    def generate_smart_column():
        # Geçiş analizi ile en olası dizilişi bul
        transitions = [patterns[i] for i in range(len(patterns)-1) if patterns[i+1] == patterns[0]]
        best_p = Counter(transitions).most_common(1)[0][0] if transitions else patterns[0]
        
        col = []
        bins = [1, 11, 21, 31, 41, 51, 61, 71, 81, 91]
        for i, count in enumerate(best_p):
            if count > 0:
                candidates = [n for n in range(bins[i], bins[i+1])]
                candidates.sort(key=get_autonomous_score, reverse=True)
                col.extend(candidates[:count])
        return sorted(col), best_p

    # --- ARAYÜZ ---
    st.divider()
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("🕵️ Botun Gözlemleri")
        st.warning(f"Doygun Bölge: **{max_saturated_region*10}-{(max_saturated_region+1)*10}** arası")
        st.info(f"Filtreleme Aralığı: Son **{LOOKBACK}** Çekiliş")
        
        recent_hot = [num for num, count in Counter(draws[:LOOKBACK].flatten()).items() if count >= 3]
        st.error(f"Elenen/Cezalı Sayılar: {recent_hot}")

    with col2:
        st.subheader("🎯 Otonom Altın Kolonlar")
        for i in range(2):
            res, p_type = generate_smart_column()
            st.success(f"**Altın Kolon {i+1}:** {res}  \n*(Diziliş Tipi: {p_type})*")

    # Isı Haritası
    st.divider()
    st.subheader("📈 Sayıların Son 15 Çekilişteki Baskınlığı")
    recent_freq = Counter(draws[:LOOKBACK].flatten())
    rf_df = pd.DataFrame(recent_freq.items(), columns=['Sayı', 'Frekans']).sort_values(by='Sayı')
    st.bar_chart(rf_df.set_index('Sayı'))

else:
    st.info("Lütfen sol taraftan CSV dosyasını yükleyin.")
 
