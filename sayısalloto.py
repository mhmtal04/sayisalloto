import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter

st.set_page_config(page_title="Loto AI - Master Reasoning", layout="wide")

st.title("🛡️ Master Muhakeme Yetenekli Loto Botu")
st.markdown("""
Bu bot; **Hibrit Trend Analizi**, **Pusu Skoru** ve **Pozisyonel Güç** verilerini harmanlar. 
Sadece istatistiğe değil, sayıların arasındaki 'sosyal ilişkilere' göre karar verir.
""")

uploaded_file = st.file_uploader("CSV Dosyasını Yükle", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    
    # 1. VERİ TEMİZLEME VE HAZIRLIK
    draws_raw = df[cols].values
    draws = []
    for row in draws_raw:
        clean_row = [int(x) for x in row if pd.notnull(x) and str(x).replace('.0','').isdigit()]
        if len(clean_row) == 6: draws.append(clean_row)
    draws = np.array(draws)

    # 2. DERİN ANALİZ KATMANLARI
    # A. Global & Trend Sinerji Matrisleri
    co_matrix_global = np.zeros((91, 91))
    co_matrix_trend = np.zeros((91, 91)) # Son 50 çekiliş
    
    for idx, d in enumerate(draws):
        for i in range(len(d)):
            for j in range(i + 1, len(d)):
                n1, n2 = d[i], d[j]
                if 0 < n1 < 91 and 0 < n2 < 91:
                    co_matrix_global[n1][n2] += 1
                    co_matrix_global[n2][n1] += 1
                    if idx < 50: # Son 50 çekiliş 'Moda' analizi
                        co_matrix_trend[n1][n2] += 1
                        co_matrix_trend[n2][n1] += 1

    # B. Pozisyonel Başarı ve Bekleme Süresi
    pos_freq = {c: Counter(df[c]) for c in cols}
    last_seen = {n: i for i, d in enumerate(draws) for n in d}
    
    # C. Örüntü (Pattern) Analizi
    def get_pattern(draw):
        counts, _ = np.histogram(draw, bins=[1, 11, 21, 31, 41, 51, 61, 71, 81, 91])
        return tuple(counts)
    all_patterns = [get_pattern(d) for d in draws]

    # 3. MARKOV ZİNCİRİ (ÖRÜNTÜ TAHMİNİ)
    last_p = all_patterns[0]
    successors = [all_patterns[i] for i in range(len(all_patterns) - 1) if all_patterns[i+1] == last_p]
    predicted_pattern = Counter(successors).most_common(1)[0][0] if successors else Counter(all_patterns).most_common(1)[0][0]

    # 4. BOTUN GELİŞMİŞ MUHAKEME (REASONING) MOTORU
    def get_master_score(n, pos_idx, current_res):
        pos_name = cols[pos_idx]
        region_idx = (n-1) // 10
        
        # Temel Puan: Pozisyon Başarısı (%40) + Gecikme Süresi (%60)
        score = (pos_freq[pos_name][n] * 0.4) + (last_seen.get(n, 100) * 0.6)
        
        if current_res:
            for prev in current_res:
                # A. Hibrit Sinerji: Tüm zamanlar (1x) + Son 50 Trend (3x)
                global_syn = co_matrix_global[n][prev]
                trend_syn = co_matrix_trend[n][prev]
                score += (global_syn * 1.0) + (trend_syn * 3.0)
                
                # B. Pusu Bonusu: İki sayı partnerse ve ikisi de soğuksa (Pusuya yatmışlarsa)
                if last_seen.get(n, 0) > 20 and last_seen.get(prev, 0) > 20:
                    if global_syn > 5:
                        score += global_syn * 4.0 # Geri dönüş ihtimalini ödüllendir
            
            # C. Bölgesel Fren: 20'ler veya 70'ler gibi gruplar doyduysa ikilem sayıyı engelle
            same_region_count = sum(1 for s in current_res if (s-1)//10 == region_idx)
            if same_region_count >= 1:
                recent_activity = np.sum([p[region_idx] for p in all_patterns[:15]])
                if recent_activity > 4:
                    score -= 250 # Bölge nadasa bırakılır
        
        # D. Isı Filtresi: Son 15 çekilişte 3+ kez çıkan sayıya ağır ceza
        if np.sum(draws[:15] == n) >= 3:
            score -= 400
            
        return score

    # 5. KOLON ÜRETİMİ
    def make_master_col(p, rank_offset=0):
        res = []
        bins = [1, 11, 21, 31, 41, 51, 61, 71, 81, 91]
        for i, count in enumerate(p):
            if count > 0:
                candidates = [n for n in range(bins[i], bins[i+1]) if n not in res]
                candidates.sort(key=lambda x: get_master_score(x, i if i<6 else 5, res), reverse=True)
                res.extend(candidates[rank_offset : rank_offset + count])
        return sorted(res[:6])

    # --- ARAYÜZ TASARIMI ---
    st.divider()
    c1, c2 = st.columns([1, 2])

    with c1:
        st.subheader("🔮 Stratejik Analiz Raporu")
        st.info(f"Yöntem: **Hibrit Markov & Pusu Analizi**")
        st.write(f"Tahmin Edilen Diziliş: **{'-'.join(map(str, [x for x in predicted_pattern if x>0]))}**")
        
        waiting = sorted(last_seen.items(), key=lambda x: x[1], reverse=True)[:3]
        st.warning(f"🚨 En Çok Bekleyenler: {', '.join([str(x[0]) for x in waiting])}")

    with c2:
        st.subheader("🎰 Üretilen Master Kolonlar")
        k1 = make_master_col(predicted_pattern, 0)
        k2 = make_master_col(predicted_pattern, 2) # Sürpriz kolon için offset artırıldı
        st.markdown(f"### 🥇 1. Kolon (Trend & Güç): `{k1}`")
        st.markdown(f"### 🥈 2. Kolon (Pusu & Sürpriz): `{k2}`")

    # --- İSTATİSTİK PANELLERİ ---
    st.divider()
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("🔥 Son 50 Çekiliş: Moda İkililer")
        trend_pairs = []
        for i in range(1, 91):
            for j in range(i+1, 91):
                if co_matrix_trend[i][j] > 0:
                    trend_pairs.append((f"{i} - {j}", int(co_matrix_trend[i][j])))
        top_trend = sorted(trend_pairs, key=lambda x: x[1], reverse=True)[:5]
        st.table(pd.DataFrame(top_trend, columns=['İkili', 'Trend Frekansı']))

    with g2:
        st.subheader("💤 Pusudaki 'Eski Dost' İkililer")
        pusu_list = []
        for i in range(1, 91):
            for j in range(i+1, 91):
                if co_matrix_global[i][j] > 8: # Güçlü bağ
                    sogukluk = (last_seen.get(i, 0) + last_seen.get(j, 0)) / 2
                    if sogukluk > 20:
                        pusu_list.append((f"{i} - {j}", int(co_matrix_global[i][j]), int(sogukluk)))
        top_pusu = sorted(pusu_list, key=lambda x: x[1], reverse=True)[:5]
        st.table(pd.DataFrame(top_pusu, columns=['İkili', 'Global Güç', 'Ort. Bekleme']))
