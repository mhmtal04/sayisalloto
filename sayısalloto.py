import streamlit as st
import pandas as pd
import random
from collections import Counter, defaultdict
from itertools import combinations

# --------------------------
# Sayfa Ayarları
# --------------------------
st.set_page_config(
    page_title="🎯 Sayısal Loto Örüntü & Diziliş Botu",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Sayısal Loto Örüntü & Diziliş Botu")
st.caption("Ondalık diziliş • örüntü • sıcak/soğuk • favori kolon")
st.divider()

# --------------------------
# Yardımcı Fonksiyonlar
# --------------------------

def get_decade(n):
    """Sayının ondalık grubunu döndürür (0-9,10-19,...,80-90)"""
    return n // 10

def pattern_from_numbers(numbers):
    """Verilen kolonun pattern kodunu çıkarır"""
    decades = [get_decade(n) for n in numbers]
    pattern = []
    i = 0
    while i < len(decades):
        cnt = 1
        for j in range(i+1, len(decades)):
            if decades[j] == decades[i]:
                cnt += 1
            else:
                break
        pattern.append(cnt)
        i += cnt
    return "-".join(map(str, pattern))

def analyze_patterns(df):
    """Tüm kolonlar için pattern çıkar ve say"""
    pattern_list = df.apply(lambda r: pattern_from_numbers(r.values), axis=1)
    counts = Counter(pattern_list)
    return counts, pattern_list.tolist()

def frequency_analysis(df):
    """Sayıların sıcak/soğuk/nötr durumunu döndür"""
    freq = Counter(df.values.flatten())
    avg = sum(freq.values()) / len(freq)
    hot = [n for n,f in freq.items() if f > avg*1.3]
    cold = [n for n,f in freq.items() if f < avg*0.7]
    neutral = [n for n in freq if n not in hot and n not in cold]
    return hot, neutral, cold, freq

def pair_analysis(df):
    """Birlikte çıkma istatistikleri"""
    pair_counter = Counter()
    for row in df.values:
        for a,b in combinations(sorted(row),2):
            pair_counter[(a,b)] +=1
    return pair_counter

# --------------------------
# Kolon Üretme Fonksiyonu
# --------------------------

def generate_column(pattern, hot, neutral, cold, pair_stats, last_pattern=None):
    """Pattern’e uygun kolon üretir"""
    column = []
    used_numbers = set()
    pattern_sizes = list(map(int, pattern.split("-")))

    # Ondalıkları rastgele seçmek yerine mümkün olduğunca hot/neutral/cold ile destekle
    available_numbers = list(range(1,91))

    for idx, size in enumerate(pattern_sizes):
        # Belirli ondalık grubunu seç
        decades_pool = [d for d in range(0,9)]
        random.shuffle(decades_pool)
        for d in decades_pool:
            # Bu ondalıkta kullanılmamış sayılar
            pool = [n for n in range(d*10, d*10+10) if n not in used_numbers and n<=90]
            # Önce hot veya neutral sayılardan seç
            preferred = [n for n in pool if n in hot or n in neutral]
            if len(preferred) >= size:
                picks = random.sample(preferred, size)
            elif len(pool) >= size:
                picks = random.sample(pool, size)
            else:
                continue
            column.extend(picks)
            used_numbers.update(picks)
            break

    column = sorted(column)
    return column[:6]

def score_column(col, hot, cold, pair_stats):
    """Kolona puan verir"""
    score = 0
    for n in col:
        if n in hot: score +=2
        if n in cold: score +=1
    for a,b in combinations(col,2):
        score += pair_stats.get((a,b),0)*0.05
    return round(score,2)

# --------------------------
# CSV Yükleme
# --------------------------
uploaded_file = st.file_uploader("📂 CSV dosyasını yükle (T1–T6 veya S1–S6)", type="csv")

if uploaded_file:
    st.subheader("📥 Veri Okuma & Temizleme")
    df_raw = pd.read_csv(uploaded_file)
    df_raw.columns = [c.strip().upper() for c in df_raw.columns]

    s_cols = ["S1","S2","S3","S4","S5","S6"]
    t_cols = ["T1","T2","T3","T4","T5","T6"]

    if all(c in df_raw.columns for c in t_cols):
        df = df_raw[t_cols].copy()
        st.write("✅ T1–T6 kolonları kullanıldı")
    elif all(c in df_raw.columns for c in s_cols):
        df = df_raw[s_cols].copy()
        st.write("✅ S1–S6 kolonları kullanıldı")
    else:
        df = df_raw.iloc[:,1:7].copy()
        st.write("⚠️ Kolon isimleri bulunamadı → 2–7. kolonlar alındı")

    df = df.apply(pd.to_numeric, errors="coerce").dropna().astype(int)
    st.write(f"✅ {len(df)} çekiliş başarıyla işlendi")
    st.divider()

    # --------------------------
    # Analizler
    # --------------------------
    st.subheader("📊 En Çok Çıkan Dizilişler")
    pattern_counts, pattern_list = analyze_patterns(df)
    for p,c in pattern_counts.most_common(3):
        st.write(f"🔹 {p} → {c} kez")

    st.divider()
    st.subheader("🌡️ Sayı Davranışları")
    hot, neutral, cold, freq = frequency_analysis(df)
    c1,c2,c3 = st.columns(3)
    c1.metric("🔥 Sıcak", len(hot))
    c2.metric("⚖️ Nötr", len(neutral))
    c3.metric("❄️ Soğuk", len(cold))

    st.divider()
    st.subheader("🤝 Birlikte Çıkmayı Sevenler")
    pair_stats = pair_analysis(df)
    for pair,c in pair_stats.most_common(5):
        st.write(f"{pair} → {c} kez")

    st.divider()
    # --------------------------
    # Kolon Üretimi
    # --------------------------
    st.subheader("🎯 Önerilen Kolonlar (En Çok Çıkan 3 Pattern)")
    results = []
    for pattern,_ in pattern_counts.most_common(3):
        col = generate_column(pattern, hot, neutral, cold, pair_stats)
        score = score_column(col, hot, cold, pair_stats)
        results.append((pattern,col,score))
        st.write(f"{pattern} dizilişi → {col} | Puan: {score}")

    # Favori kolon (örüntüye dayalı tahmin)
    last_pattern = pattern_list[-1]
    next_pattern = random.choice(list(pattern_counts.keys()))  # Basit tahmin örneği
    fav_col = generate_column(next_pattern, hot, neutral, cold, pair_stats)
    fav_score = score_column(fav_col, hot, cold, pair_stats)
    st.divider()
    st.subheader("⭐ FAVORİ KOLON")
    st.success(f"{fav_col} | Pattern: {next_pattern} | Puan: {fav_score}")

else:
    st.info("👆 Başlamak için CSV dosyasını yükle")
