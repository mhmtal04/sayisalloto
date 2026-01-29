import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter

st.set_page_config(page_title="Pattern Master AI - Pro", layout="wide")

st.title("🧩 Stratejik Örüntü Analizli Loto Botu (Gelişmiş)")
st.markdown("Bu bot, dizilişleri birer 'zincir' olarak analiz eder, **birlikte çıkma (sinerji)** ve **pozisyonel güç** verilerini kullanarak tahmin yapar.")

uploaded_file = st.file_uploader("CSV Dosyasını Yükle", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    
    # Veri Temizleme: Boşlukları ve hatalı sayıları ayıkla
    draws_raw = df[cols].values
    draws = []
    for row in draws_raw:
        clean_row = [int(x) for x in row if pd.notnull(x) and str(x).replace('.0','').isdigit()]
        if len(clean_row) == 6:
            draws.append(clean_row)
    draws = np.array(draws)

    # --- EKSTRA ANALİZ KATMANLARI ---
    # 1. Birlikte Çıkma Matrisi (Sinerji)
    co_matrix = np.zeros((91, 91))
    for d in draws:
        for i in range(len(d)):
            for j in range(i + 1, len(d)):
                n1, n2 = d[i], d[j]
                if 0 < n1 < 91 and 0 < n2 < 91:
                    co_matrix[n1][n2] += 1
                    co_matrix[n2][n1] += 1

    # 2. Pozisyonel Frekans (T1-T6 başarısı)
    pos_freq = {c: Counter(df[c]) for c in cols}

    # 3. Temel İstatistikler
    all_nums = draws.flatten()
    freq = Counter(all_nums)
    last_seen = {n: i for i, d in enumerate(draws) for n in d}

    # --- ÖRÜNTÜ GEÇİŞ ANALİZİ (MARKOV) ---
    def get_pattern(draw):
        counts, _ = np.histogram(draw, bins=[1, 11, 21, 31, 41, 51, 61, 71, 81, 91])
        return tuple(counts)

    all_patterns = [get_pattern(d) for d in draws]
    last_p = all_patterns[0]
    successors = [all_patterns[i] for i in range(len(all_patterns) - 1) if all_patterns[i+1] == last_p]
    
    if successors:
        predicted_pattern = Counter(successors).most_common(1)[0][0]
        prediction_method = "Örüntü Geçiş Analizi (Markov Chain)"
    else:
        predicted_pattern = Counter(all_patterns).most_common(1)[0][0]
        prediction_method = "Genel En Çok Çıkan Diziliş"

    # --- GELİŞMİŞ SAYI PUANLAMA ---
    def get_pro_score(n, pos_idx, current_res):
        pos_name = cols[pos_idx]
        # 1. Pozisyonel Başarı + Bekleme Süresi (%70)
        score = (pos_freq[pos_name][n] * 0.4) + (last_seen.get(n, 100) * 0.6)
        
        # 2. Sinerji (Seçilen diğer sayılarla uyumu - %30)
        if current_res:
            synergy = sum([co_matrix[n][prev] for prev in current_res])
            score += synergy * 1.5
            
        # 3. Dinamik Filtre: Son 15 çekiliş doygunluk cezası (20'ler ve 40 kuralı)
        recent_count = np.sum(draws[:15] == n)
        if recent_count >= 3: score -= 200 
        
        return score

    # --- KOLON ÜRETİMİ ---
    def make_col_pro(p, rank=0):
        res = []
        bins = [1, 11, 21, 31, 41, 51, 61, 71, 81, 91]
        for i, count in enumerate(p):
            if count > 0:
                candidates = [n for n in range(bins[i], bins[i+1]) if n not in res]
                # Sinerji ve pozisyon puanına göre sırala
                candidates.sort(key=lambda x: get_pro_score(x, i if i<6 else 5, res), reverse=True)
                res.extend(candidates[rank : rank + count])
        return sorted(res[:6])

    # --- PANEL GÖRÜNÜMÜ ---
    st.divider()
    c1, c2 = st.columns([1, 2])

    with c1:
        st.subheader("🔮 Tahmin Algoritması")
        st.write(f"Son Çekiliş Dizilişi: **{'-'.join(map(str, [x for x in last_p if x>0]))}**")
        st.success(f"Tahmin Edilen Bir Sonraki Diziliş: **{'-'.join(map(str, [x for x in predicted_pattern if x>0]))}**")
        st.info(f"Yöntem: {prediction_method}")
        
        # Ekstra: En çok bekleyenler
        waiting = sorted(last_seen.items(), key=lambda x: x[1], reverse=True)[:3]
        st.warning(f"🚨 En Çok Bekleyen Sayılar: {', '.join([str(x[0]) for x in waiting])}")

    with c2:
        st.subheader("🎰 Üretilen Stratejik Kolonlar")
        k1 = make_col_pro(predicted_pattern, 0)
        k2 = make_col_pro(predicted_pattern, 1)
        st.markdown(f"### 🥇 1. Kolon (Maksimum Sinerji): `{k1}`")
        st.markdown(f"### 🥈 2. Kolon (Alternatif Güç): `{k2}`")
        st.caption("Not: Bu kolonlar pozisyonel başarı ve sayıların birlikte çıkma oranlarına göre optimize edilmiştir.")

    # --- GRAFİKLER ---
    st.divider()
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("📈 En Sık Görülen 5 Diziliş Tipi")
        p_counts = Counter(["-".join(map(str, [x for x in p if x>0])) for p in all_patterns])
        st.bar_chart(pd.DataFrame(p_counts.most_common(5), columns=['Diziliş', 'Adet']).set_index('Diziliş'))

    with g2:
        st.subheader("🔗 Birlikte Çıkmayı Seven İkililer")
        pairs = []
        for i in range(1, 91):
            for j in range(i+1, 91):
                if co_matrix[i][j] > 0:
                    pairs.append((f"{i}-{j}", co_matrix[i][j]))
        top_pairs = sorted(pairs, key=lambda x: x[1], reverse=True)[:5]
        st.table(pd.DataFrame(top_pairs, columns=['Sayı Çifti', 'Birlikte Çıkma Sayısı']))
