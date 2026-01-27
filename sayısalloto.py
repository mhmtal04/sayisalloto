import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter

st.set_page_config(page_title="Pattern Master AI", layout="wide")

st.title("🧩 Stratejik Örüntü Analizli Loto Botu")
st.markdown("Bu bot, dizilişleri birer 'zincir' olarak analiz eder ve bir sonrakini tahmin eder.")

uploaded_file = st.file_uploader("CSV Dosyasını Yükle", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    draws = df[cols].values

    # 1. HER ÇEKİLİŞİN DİZİLİŞİNİ (PATTERN) BUL
    def get_pattern(draw):
        # 10'luk gruplara göre (1-10, 11-20...) dağılımı bulur
        counts, _ = np.histogram(draw, bins=[1, 11, 21, 31, 41, 51, 61, 71, 81, 91])
        return tuple(counts)

    all_patterns = [get_pattern(d) for d in draws]
    
    # 2. ÖRÜNTÜ GEÇİŞ ANALİZİ (MARKOV CHAIN)
    # Son çekilişin dizilişini alalım (Örn: 1-2-1-1-1)
    last_p = all_patterns[0]
    
    # Geçmişte bu dizilişten sonra ne gelmiş?
    successors = []
    for i in range(len(all_patterns) - 1):
        if all_patterns[i+1] == last_p:
            successors.append(all_patterns[i])
            
    # Eğer geçmişte bu dizilişin örneği varsa en çok tekrarlananı seç, yoksa en popüler olanı seç
    if successors:
        predicted_pattern = Counter(successors).most_common(1)[0][0]
        prediction_method = "Örüntü Geçiş Analizi (Markov Chain)"
    else:
        predicted_pattern = Counter(all_patterns).most_common(1)[0][0]
        prediction_method = "Genel En Çok Çıkan Diziliş"

    # 3. SAYI PUANLAMA (SON 15 ÇEKİLİŞ FİLTRESİYLE)
    all_nums = draws.flatten()
    freq = Counter(all_nums)
    last_seen = {n: i for i, d in enumerate(draws) for n in d}

    def get_smart_score(n):
        # Tarihsel güç + Bekleme süresi bonusu
        score = (freq[n] * 0.4) + (last_seen.get(n, 100) * 0.6)
        # Son 15 çekiliş doygunluk cezası
        if np.sum(draws[:15] == n) >= 3: score -= 200 # 40 gibi sayılar elenir
        return score

    # 4. KOLON ÜRETİMİ
    def make_col(p, rank=0):
        res = []
        bins = [1, 11, 21, 31, 41, 51, 61, 71, 81, 91]
        for i, count in enumerate(p):
            if count > 0:
                candidates = [n for n in range(bins[i], bins[i+1])]
                candidates.sort(key=get_smart_score, reverse=True)
                res.extend(candidates[rank : rank + count])
        return sorted(res)

    # --- PANEL ---
    st.divider()
    c1, c2 = st.columns([1, 2])

    with c1:
        st.subheader("🔮 Tahmin Algoritması")
        st.write(f"Son Çekiliş Dizilişi: **{'-'.join(map(str, [x for x in last_p if x>0]))}**")
        st.success(f"Tahmin Edilen Bir Sonraki Diziliş: **{'-'.join(map(str, [x for x in predicted_pattern if x>0]))}**")
        st.info(f"Yöntem: {prediction_method}")

    with c2:
        st.subheader("🎰 Üretilen Altın Kolonlar")
        k1 = make_col(predicted_pattern, 0)
        k2 = make_col(predicted_pattern, 1)
        st.markdown(f"### 1. Kolon: `{k1}`")
        st.markdown(f"### 2. Kolon: `{k2}`")

    # Geçiş Haritası Görseli (Opsiyonel)
    st.divider()
    st.subheader("📈 En Sık Görülen 5 Diziliş Tipi")
    p_counts = Counter(["-".join(map(str, [x for x in p if x>0])) for p in all_patterns])
    st.bar_chart(pd.DataFrame(p_counts.most_common(5), columns=['Diziliş', 'Adet']).set_index('Diziliş'))
