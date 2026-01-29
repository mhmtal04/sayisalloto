import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter

st.set_page_config(page_title="Loto AI - Stratejik Muhakeme", layout="wide")

st.title("🧩 Stratejik Muhakeme Yetenekli Loto Botu")
st.markdown("Bu bot; **Markov Zinciri**, **T-Pozisyonel Güç** ve **Global Partnerlik** verilerini kullanarak kupon üretir.")

uploaded_file = st.file_uploader("CSV Dosyasını Yükle (sayisal_loto.csv)", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    
    # 1. VERİ TEMİZLEME VE HAZIRLIK
    draws_raw = df[cols].values
    draws = []
    for row in draws_raw:
        clean_row = [int(x) for x in row if pd.notnull(x) and str(x).replace('.0','').isdigit()]
        if len(clean_row) == 6:
            draws.append(clean_row)
    draws = np.array(draws)

    # 2. DERİN ANALİZ KATMANLARI
    # A. Global Birlikte Çıkma (Korelasyon)
    co_matrix = np.zeros((91, 91))
    for d in draws:
        for i in range(len(d)):
            for j in range(i + 1, len(d)):
                n1, n2 = d[i], d[j]
                if 0 < n1 < 91 and 0 < n2 < 91:
                    co_matrix[n1][n2] += 1
                    co_matrix[n2][n1] += 1

    # B. Pozisyonel Başarı (T1...T6)
    pos_freq = {c: Counter(df[c]) for c in cols}
    
    # C. Lag (Bekleme Süresi) ve Genel Frekans
    last_seen = {n: i for i, d in enumerate(draws) for n in d}
    all_nums = draws.flatten()
    global_freq = Counter(all_nums)

    # 3. MARKOV ZİNCİRİ (ÖRÜNTÜ TAHMİNİ)
    def get_pattern(draw):
        counts, _ = np.histogram(draw, bins=[1, 11, 21, 31, 41, 51, 61, 71, 81, 91])
        return tuple(counts)

    all_patterns = [get_pattern(d) for d in draws]
    last_p = all_patterns[0]
    successors = [all_patterns[i] for i in range(len(all_patterns) - 1) if all_patterns[i+1] == last_p]
    predicted_pattern = Counter(successors).most_common(1)[0][0] if successors else Counter(all_patterns).most_common(1)[0][0]

    # 4. BOTUN MUHAKEME (REASONING) MOTORU
    def get_muhakeme_score(n, pos_idx, current_res):
        pos_name = cols[pos_idx]
        region_idx = (n-1) // 10  # Sayının hangi 10'luk grupta olduğu (0=1-10, 1=11-20...)
        
        # Temel Puan: Pozisyonel Başarı + Bekleme Süresi
        score = (pos_freq[pos_name][n] * 0.5) + (last_seen.get(n, 100) * 0.5)
        
        # SİNERJİ ANALİZİ (Global Partnerlik)
        if current_res:
            synergy = sum([co_matrix[n][prev] for prev in current_res])
            score += synergy * 2.0 # Sayılar 'kanka' ise puan uçar
            
            # BÖLGESEL MUHAKEME (Fren Mekanizması)
            # Eğer seçilenler listesinde aynı gruptan sayı varsa
            same_region_count = sum(1 for s in current_res if (s-1)//10 == region_idx)
            if same_region_count >= 1:
                # Son 10 çekilişin o bölgedeki yoğunluğuna bak
                reg_saturation = np.sum([p[region_idx] for p in all_patterns[:10]])
                if reg_saturation > 3: # Bölge zaten doygunsa (Senin 20'ler kuralın)
                    score -= 150 # İkinci ikilemi (21-27) koymaktan kaçın
        
        # SON 15 ÇEKİLİŞ DOYGUNLUK CEZASI
        if np.sum(draws[:15] == n) >= 3:
            score -= 300
            
        return score

    # 5. KOLON ÜRETİMİ
    def make_pro_col(p, rank_offset=0):
        res = []
        bins = [1, 11, 21, 31, 41, 51, 61, 71, 81, 91]
        for i, count in enumerate(p):
            if count > 0:
                # Bölgedeki adayları bul (Pozisyonel muhakemeye göre sırala)
                candidates = [n for n in range(bins[i], bins[i+1]) if n not in res]
                candidates.sort(key=lambda x: get_muhakeme_score(x, i if i<6 else 5, res), reverse=True)
                # Seçim
                selected = candidates[rank_offset : rank_offset + count]
                res.extend(selected)
        return sorted(res[:6])

    # --- ARAYÜZ TASARIMI ---
    st.divider()
    c1, c2 = st.columns([1, 2])

    with c1:
        st.subheader("🔮 Örüntü Tahmin Raporu")
        st.write(f"Son Çekiliş Dizilişi: **{'-'.join(map(str, [x for x in last_p if x>0]))}**")
        st.success(f"Tahmin Edilen Bir Sonraki Diziliş: **{'-'.join(map(str, [x for x in predicted_pattern if x>0]))}**")
        
        # En Çok Bekleyenler
        waiting = sorted(last_seen.items(), key=lambda x: x[1], reverse=True)[:3]
        st.warning(f"🚨 En Çok Bekleyenler: {', '.join([str(x[0]) for x in waiting])}")

    with c2:
        st.subheader("🎰 Stratejik Altın Kolonlar")
        k1 = make_pro_col(predicted_pattern, 0)
        k2 = make_pro_col(predicted_pattern, 1)
        st.markdown(f"### 🥇 1. Kolon (Maksimum Sinerji): `{k1}`")
        st.markdown(f"### 🥈 2. Kolon (Alternatif Güç): `{k2}`")
        st.info("💡 Bot bu kolonları üretirken; pozisyonel başarıyı, sayıların birbirini sevme oranını ve son 15 çekilişteki bölge doygunluğunu hesapladı.")

    # --- İKİLEMLER TABLOSU (ONDALIK DÜZELTİLMİŞ) ---
    st.divider()
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("📈 Popüler Dizilişler")
        p_counts = Counter(["-".join(map(str, [x for x in p if x>0])) for p in all_patterns])
        st.bar_chart(pd.DataFrame(p_counts.most_common(5), columns=['Diziliş', 'Adet']).set_index('Diziliş'))

    with g2:
        st.subheader("🔗 Birlikte Çıkmayı Seven İkililer")
        pairs = []
        for i in range(1, 91):
            for j in range(i+1, 91):
                if co_matrix[i][j] > 0:
                    pairs.append((f"{i} - {j}", int(co_matrix[i][j])))
        
        top_pairs = sorted(pairs, key=lambda x: x[1], reverse=True)[:10]
        st.table(pd.DataFrame(top_pairs, columns=['Sayı Çifti', 'Adet']))

