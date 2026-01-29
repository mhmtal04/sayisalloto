import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter

st.set_page_config(page_title="Pro Loto Analist v11", layout="wide")

st.title("🛡️ Profesyonel Stratejik Analiz Botu")
st.markdown("854 çekilişlik veriyi **Birlikte Çıkma**, **Pozisyonel Güç** ve **Lag** analiziyle işler.")

uploaded_file = st.file_uploader("CSV Dosyasını Yükle", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    draws = df[cols].values

    # --- 1. DERİN ANALİZ KATMANLARI ---
      
    # A. Birlikte Çıkma Matrisi (Korelasyon) - GÜVENLİ VERSİYON
    co_matrix = np.zeros((100, 100)) # Sınırı biraz genişletelim (Hata payı)
    
    for draw in draws:
        # Satırdaki verileri temizle: Sadece 1-90 arası tam sayıları al, boşlukları ele
        clean_draw = [int(n) for n in draw if pd.notnull(n) and str(n).replace('.0','').isdigit()]
        clean_draw = [n for n in clean_draw if 0 < n < 100]
        
        for i in range(len(clean_draw)):
            for j in range(i + 1, len(clean_draw)):
                n1, n2 = clean_draw[i], clean_draw[j]
                co_matrix[n1][n2] += 1
                co_matrix[n2][n1] += 1

    # B. Pozisyonel Frekans (T1-T6 başarısı)
    pos_freq = {c: Counter(df[c]) for c in cols}

    # C. Lag (Bekleme Süresi) Analizi
    last_seen = {n: i for i, d in enumerate(draws) for n in d}
    all_nums = draws.flatten()
    global_freq = Counter(all_nums)

    # --- 2. ÖRÜNTÜ GEÇİŞ ANALİZİ (MEVCUT YAPI) ---
    all_patterns = []
    def get_pattern(draw):
        counts, _ = np.histogram(draw, bins=[1, 11, 21, 31, 41, 51, 61, 71, 81, 91])
        return tuple(counts)

    for d in draws: all_patterns.append(get_pattern(d))
    
    last_p = all_patterns[0]
    successors = [all_patterns[i] for i in range(len(all_patterns)-1) if all_patterns[i+1] == last_p]
    predicted_pattern = Counter(successors).most_common(1)[0][0] if successors else Counter(all_patterns).most_common(1)[0][0]

    # --- 3. GELİŞTİRİLMİŞ PUANLAMA (SİNERJİ ODAKLI) ---
    def get_serious_score(n, position_idx, current_col):
        pos_name = cols[position_idx]
        # Temel Puan: Pozisyonel Başarı + Bekleme Süresi
        score = (pos_freq[pos_name][n] * 0.5) + (last_seen.get(n, 100) * 0.5)
        
        # Sinerji: Seçilen diğer sayılarla daha önce kaç kez çıktı?
        if current_col:
            synergy = sum([co_matrix[n][prev] for prev in current_col])
            score += (synergy * 2.0) # Beraber çıkma ağırlığı
        
        # Otonom Filtre: Son 15 çekilişte doygunluk (Senin sezginin kodu)
        recent_count = np.sum(draws[:15] == n)
        if recent_count >= 3: score -= 300 # 40 gibi sayılar elenir
        
        # Bölge Yoğunluk Cezası: Eğer son 10 çekilişte bu bölge çok çıktıysa (20'ler gibi)
        region_idx = (n-1) // 10
        region_saturation = np.sum([p[region_idx] for p in all_patterns[:10]])
        if region_saturation > 4: score -= 50 # Bölge nadasa bırakılır
            
        return score

    # --- 4. AKILLI KOLON ÜRETİMİ ---
    def make_serious_col(pattern, rank_offset=0):
        res = []
        bins = [1, 11, 21, 31, 41, 51, 61, 71, 81, 91]
        
        # Her bölge için sırayla sayı seç
        for i, count in enumerate(pattern):
            if count > 0:
                candidates = [n for n in range(bins[i], bins[i+1])]
                # Seçilen sayılarla sinerjisine göre sırala
                candidates.sort(key=lambda x: get_serious_score(x, i if i<6 else 5, res), reverse=True)
                
                # Çeşitlilik için offset kullan
                start = rank_offset % len(candidates)
                res.extend(candidates[start : start + count])
        return sorted(list(set(res))[:6])

    # --- ARAYÜZ ---
    st.divider()
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("🕵️ Veri Madenciliği Raporu")
        st.write(f"Son Çekiliş Dizilişi: `{'-'.join(map(str, [x for x in last_p if x>0]))}`")
        st.success(f"Tahmin Edilen Diziliş: `{'-'.join(map(str, [x for x in predicted_pattern if x>0]))}`")
        
        # En çok bekleyen 3 sayı
        waiting = sorted(last_seen.items(), key=lambda x: x[1], reverse=True)[:3]
        st.info(f"En Çok Bekleyenler: {', '.join([str(x[0]) for x in waiting])}")

    with col_right:
        st.subheader("🏆 Stratejik Altın Kolonlar")
        k1 = make_serious_col(predicted_pattern, 0)
        k2 = make_serious_col(predicted_pattern, 1)
        
        st.markdown(f"### 🥇 1. Kolon (Maksimum Sinerji): `{k1}`")
        st.write("*(Bu kolon, sayılar arasındaki tarihsel bağları ve pozisyonel gücü esas alır.)*")
        
        st.markdown(f"### 🥈 2. Kolon (Yüksek Potansiyel): `{k2}`")
        st.write("*(Bu kolon, 'ikinci en iyi' sinerjiye sahip alternatifleri değerlendirir.)*")

    # Korelasyon Görseli (Top 5 İkili)
    st.divider()
    st.subheader("🔗 Birlikte Çıkmayı Seven 'İkilem' Sayılar")
    pairs = []
    for i in range(1, 91):
        for j in range(i+1, 91):
            if co_matrix[i][j] > 0:
                pairs.append((i, j, co_matrix[i][j]))
    
    top_pairs = sorted(pairs, key=lambda x: x[2], reverse=True)[:5]
    for p in top_pairs:
        st.write(f"🔹 **{p[0]}** ve **{p[1]}** sayıları toplam **{int(p[2])}** kez beraber çıktı.")

 
