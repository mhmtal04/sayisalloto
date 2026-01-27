import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter

# Sayfa Konfigürasyonu
st.set_page_config(page_title="AI Sayısal Loto Botu", page_icon="🤖", layout="wide")

st.title("🤖 Otonom Sayısal Loto Analiz Merkezi")
st.markdown("853 çekilişlik veri seti üzerinde **hiçbir insan müdahalesi olmadan** analiz yapar.")

# 1. Dosya Yükleme
uploaded_file = st.file_uploader("Çekiliş Verilerini (CSV) Yükle", type="csv")

if uploaded_file is not None:
    # Veriyi oku
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    draws = df[cols].values
    
    # --- BOTUN ANALİZ PARAMETRELERİ ---
    LOOKBACK = 15 # Son 15 çekiliş doygunluk filtresi
    
    # A. Örüntü Analizi (Diziliş Tahmini)
    def get_pattern(draw):
        return tuple(np.histogram(draw, bins=[1, 11, 21, 31, 41, 51, 61, 71, 81, 91])[0])

    patterns = [get_pattern(d) for d in draws]
    # Son dizilişten sonra en sık gelen dizilişi bul (Markov Zinciri)
    last_p = patterns[0]
    transitions = [patterns[i] for i in range(len(patterns)-1) if patterns[i+1] == last_p]
    next_pattern = Counter(transitions).most_common(1)[0][0] if transitions else last_p

    # B. Gelişmiş Puanlama Sistemi (Otonom)
    all_numbers = draws.flatten()
    freq = Counter(all_numbers)
    last_seen = {n: i for i, d in enumerate(draws) for n in d}

    def get_score(n):
        # 1. Tarihsel Başarı (%40)
        score = freq[n] * 0.4 
        # 2. Bekleme Süresi Primi (%60) - Ne kadar zamandır çıkmıyorsa o kadar iyi
        score += last_seen.get(n, 100) * 0.6
        
        # 3. Son 15 Çekiliş Filtresi (Doygunluk Cezası)
        recent_count = np.sum(draws[:LOOKBACK] == n)
        if recent_count >= 3: # 40 gibi aşırı ısınanlara ağır ceza
            score -= 200
        elif recent_count >= 1: # Son dönemde çıkanlara hafif ceza
            score -= 40
            
        return score

    # C. Kolon Üretici
    def generate_col(rank_offset=0):
        col = []
        bins = [1, 11, 21, 31, 41, 51, 61, 71, 81, 91]
        for i, count in enumerate(next_pattern):
            if count > 0:
                candidates = [n for n in range(bins[i], bins[i+1])]
                candidates.sort(key=get_score, reverse=True)
                # Çeşitlilik için rank_offset kullan
                idx = rank_offset % len(candidates)
                col.extend(candidates[idx : idx + count])
        return sorted(col)

    # --- EKRAN ÇIKTILARI ---
    st.divider()
    c1, c2 = st.columns([1, 2])

    with c1:
        st.subheader("🕵️ Botun Gözlemleri")
        st.info(f"Analiz Edilen Çekiliş: **{len(df)}**")
        st.warning(f"Karantina Süresi: Son **{LOOKBACK}** Çekiliş")
        
        # Diziliş Tipini Göster (Sıfırları Temizle)
        p_str = "-".join([str(x) for x in next_pattern if x > 0])
        st.success(f"Tahmin Edilen Diziliş: **{p_str}**")

    with c2:
        st.subheader("🏆 Otonom Üretilen Altın Kolonlar")
        k1 = generate_col(rank_offset=0)
        k2 = generate_col(rank_offset=1)
        
        st.markdown(f"### 🥇 Altın Kolon 1: `{k1}`")
        st.markdown(f"### 🥈 Altın Kolon 2: `{k2}`")

    # Görselleştirme
    st.divider()
    st.subheader("📊 Tarihsel Frekans Dağılımı")
    hist_data = pd.DataFrame(freq.items(), columns=['Sayı', 'Frekans']).sort_values('Sayı')
    st.bar_chart(hist_data.set_index('Sayı'))

else:
    st.info("Lütfen bilgisayarındaki 'C.sayısaloto (1).csv' dosyasını yukarıdaki alana sürükle.")
