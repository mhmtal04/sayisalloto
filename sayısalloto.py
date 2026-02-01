import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter

st.set_page_config(page_title="Loto AI - v32 Dinamik Analist", layout="wide")

# Tasarım CSS
st.markdown("""
    <style>
    .result-row { display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0 25px 0; }
    .result-item {
        padding: 12px 18px; border-radius: 8px; font-weight: 600; font-size: 15px;
        display: flex; align-items: center; justify-content: center; min-width: 110px;
    }
    .ana-sayi { background-color: rgba(28, 131, 225, 0.1); color: rgb(0, 104, 201); border-left: 4px solid rgb(0, 104, 201); }
    .super-sayi { background-color: rgba(255, 75, 75, 0.1); color: rgb(255, 75, 75); border-left: 4px solid rgb(255, 75, 75); }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ v32 - Dinamik Fren & Serbest Muhakeme Motoru")

uploaded_file = st.file_uploader("CSV Dosyasını Yükle", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    
    # 1. SON ÇEKİLİŞ PANELİ
    last_draw = df.iloc[0]
    st.subheader(f"📅 Son Çekiliş: {last_draw['Tarih'] if 'Tarih' in df.columns else 'Bilinmiyor'}")
    res_html = '<div class="result-row">'
    for c in cols: res_html += f'<div class="result-item ana-sayi">{c}: {int(last_draw[c])}</div>'
    if 'Super' in df.columns: res_html += f'<div class="result-item super-sayi">Super: {int(last_draw["Super"])}</div>'
    res_html += '</div>'
    st.markdown(res_html, unsafe_allow_html=True)

    # 2. VERİ HAZIRLIĞI (1-9, 10-19... Blok Yapısı)
    custom_bins = [1, 10, 20, 30, 40, 50, 60, 70, 80, 91]
    draws_raw = df[cols].values
    draws = np.array([[int(x) for x in row if pd.notnull(x)] for row in draws_raw if len(row) >= 6])

    last_seen = {n: i for i, d in enumerate(draws) for n in d if n not in last_seen} # Basitleştirilmiş bekleme
    last_seen = {}
    for i, d in enumerate(draws):
        for n in d:
            if n not in last_seen: last_seen[n] = i

    co_matrix_global = np.zeros((91, 91))
    for idx, d in enumerate(draws):
        for i in range(len(d)):
            for j in range(i + 1, len(d)):
                n1, n2 = sorted([d[i], d[j]])
                if n2 < 91: co_matrix_global[n1][n2] += 1

    pos_freq = {c: Counter(df[c]) for c in cols}
    
    # Diziliş Analizi (Sadece Bloklara Odaklı)
    def get_pattern(draw): return tuple(np.histogram(draw, bins=custom_bins)[0])
    all_patterns = [get_pattern(d) for d in draws]

    def predict_next_pattern(history):
        last_s = history[0]
        succs = [history[i] for i in range(len(history)-1) if history[i+1] == last_s]
        return Counter(succs).most_common(1)[0][0] if succs else Counter(history).most_common(1)[0][0]

    predicted_pattern = predict_next_pattern(all_patterns)

    # 3. YENİ NESİL MUHAKEME MOTORU (Dinamik Fren)
    def get_dynamic_score(n, pos_idx, current_res):
        region_idx = np.digitize(n, custom_bins) - 1
        
        # Temel Puan (Sıklık + Bekleme)
        score = (pos_freq[cols[pos_idx]][n] * 0.5) + (last_seen.get(n, 0) * 0.2)
        
        # Sinerji (Global İkililer)
        if current_res:
            for prev in current_res:
                n1, n2 = sorted([n, prev])
                score += (co_matrix_global[n1][n2] * 2.0)
        
        # --- YÜZDESEL FRENLEME (Ceza Yerine Olasılık Düşürme) ---
        # Sayı son 15 çekilişte kaç kere çıktı?
        count_last_15 = np.sum(draws[:15] == n)
        if count_last_15 >= 3:
            score *= 0.3 # Puanı %70 oranında kır (Tamamen silme!)
        elif count_last_15 >= 1:
            score *= 0.7 # Puanı %30 oranında kır
            
        # Bölgesel Doygunluk Freni (Yüzdesel)
        if current_res:
            same_reg = sum(1 for s in current_res if (np.digitize(s, custom_bins)-1) == region_idx)
            if same_reg >= 1:
                score *= 0.5 # Aynı bölgeden sayı seçme isteğini yarı yarıya düşür
                
        return score

    # 4. KOLON ÜRETİMİ (Sadece Dizilişe Sadık)
    def make_col(pattern, offset=0):
        res = []
        req_regions = []
        for i, count in enumerate(pattern):
            for _ in range(count): req_regions.append(i)
        
        for i, reg_idx in enumerate(req_regions):
            start, end = custom_bins[reg_idx], custom_bins[reg_idx+1]
            cands = [n for n in range(start, end) if n not in res]
            cands.sort(key=lambda x: get_dynamic_score(x, i, res), reverse=True)
            
            if cands:
                res.append(cands[min(offset, len(cands)-1)])
        return sorted(res)

    # 5. ARAYÜZ
    st.divider()
    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.subheader("🔮 Dinamik Öngörü")
        st.write(f"Tahmin Edilen Blok Yapısı: **{'-'.join(map(str, [x for x in predicted_pattern if x>0]))}**")
        
        st.success(f"🥇 Master Kolon: `{make_col(predicted_pattern, 0)}`")
        st.info(f"🥈 Alternatif Kolon: `{make_col(predicted_pattern, 1)}`")

    with c2:
        st.subheader("📈 Popüler Blok Dizilişleri")
        p_labels = ["-".join(map(str, [x for x in p if x>0])) for p in all_patterns]
        st.bar_chart(pd.DataFrame(Counter(p_labels).most_common(5), columns=['Diziliş', 'Adet']).set_index('Diziliş'))

    # ANALİZ TABLOLARI (V26 Standartları)
    st.divider()
    t1, t2, t3 = st.columns(3)
    with t1:
        st.subheader("🔥 Moda (Top 10)")
        tp = [(f"{i}-{j}", int(co_matrix_global[i][j])) for i in range(1,91) for j in range(i+1,91) if co_matrix_global[i][j] > 10]
        st.table(pd.DataFrame(sorted(tp, key=lambda x: x[1], reverse=True)[:10], columns=['İkili', 'Sıklık']))
    with t2:
        st.subheader("📍 Pozisyonel Liderler")
        pos_data = {c: [num for num, count in pos_freq[c].most_common(5)] for c in cols}
        st.table(pd.DataFrame(pos_data))
    with t3:
        st.subheader("💤 Pusu (Bekleyenler)")
        pl = [(n, last_seen.get(n, 0)) for n in range(1, 91) if last_seen.get(n, 0) > 20]
        st.table(pd.DataFrame(sorted(pl, key=lambda x: x[1], reverse=True)[:10], columns=['Sayı', 'Bekleme']))
