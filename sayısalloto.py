import streamlit as st
import pandas as pd
import random
from collections import Counter, defaultdict
from itertools import combinations

# -------------------------------------------------
# Sayfa Ayarları
# -------------------------------------------------
st.set_page_config(
    page_title="🎯 Sayısal Loto Düşünen Bot",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Sayısal Loto Örüntü & Diziliş Botu")
st.caption("Ondalık diziliş • örüntü • sıcak/soğuk • favori kolon")
st.divider()

# -------------------------------------------------
# Yardımcı Fonksiyonlar
# -------------------------------------------------
def get_decade(n: int) -> int:
    return n // 10

def determine_pattern(numbers):
    """Verilen kolonun diziliş patternini çıkarır (1-2-1-1 gibi)"""
    decades = [get_decade(n) for n in numbers]
    pattern = []
    i = 0
    while i < len(decades):
        count = 1
        for j in range(i+1, len(decades)):
            if decades[j] == decades[i]:
                count += 1
            else:
                break
        pattern.append(count)
        i += count
    return pattern

def analyze_patterns(df):
    """Tüm kolonların patternlerini analiz eder"""
    patterns = [tuple(determine_pattern(row)) for row in df.values]
    counter = Counter(patterns)
    return counter

def frequency_analysis(df):
    freq = Counter(df.values.flatten())
    avg = sum(freq.values()) / len(freq)
    hot = [n for n, f in freq.items() if f > avg * 1.3]
    cold = [n for n, f in freq.items() if f < avg * 0.7]
    neutral = [n for n in freq if n not in hot and n not in cold]
    return hot, neutral, cold, freq

def pair_analysis(df):
    pair_counter = Counter()
    for row in df.values:
        for a, b in combinations(sorted(row), 2):
            pair_counter[(a, b)] += 1
    return pair_counter

def generate_column_for_pattern(pattern, hot, neutral, cold, pair_stats, t_history):
    """
    Pattern'e uygun kolon üretir.
    - pattern: ör. [1,2,1,1,1]
    - t_history: geçmiş T kolonları verisi
    """
    column = []
    used_decades = []
    for idx, group_size in enumerate(pattern):
        # Pozisyona göre sayı havuzu
        possible = list(range(1, 91))
        # Önceki T ile ilişkili seçimi dikkate al
        if idx > 0 and len(column) > 0:
            prev = column[-1]
            # Aynı ondalık gerekirse
            if group_size > 1:
                dec = get_decade(prev)
                possible = [n for n in possible if get_decade(n) == dec]
        # Onluk grubuna göre kullanılacak sayı
        possible = [n for n in possible if n not in column]
        # Öncelik: hot -> neutral -> cold
        choices = [n for n in possible if n in hot] or \
                  [n for n in possible if n in neutral] or \
                  [n for n in possible if n in cold] or \
                  possible
        if len(choices) >= group_size:
            picks = random.sample(choices, group_size)
        else:
            picks = choices
        column.extend(picks)
    return sorted(column)[:6]

def score_column(col, hot, cold, pair_stats):
    score = 0
    for n in col:
        if n in hot:
            score += 2
        elif n in cold:
            score += 0.5
        else:
            score += 1
    for a, b in combinations(col, 2):
        score += pair_stats.get((a, b), 0) * 0.05
    return round(score, 2)

# -------------------------------------------------
# CSV Yükleme
# -------------------------------------------------
uploaded_file = st.file_uploader(
    "📂 CSV dosyasını yükle (T1–T6 veya S1–S6)",
    type="csv"
)

if uploaded_file:
    df_raw = pd.read_csv(uploaded_file)
    df_raw.columns = [c.strip().upper() for c in df_raw.columns]

    s_cols = ["S1","S2","S3","S4","S5","S6"]
    t_cols = ["T1","T2","T3","T4","T5","T6"]

    if all(c in df_raw.columns for c in t_cols):
        df = df_raw[t_cols].copy()
    elif all(c in df_raw.columns for c in s_cols):
        df = df_raw[s_cols].copy()
    else:
        df = df_raw.iloc[:,1:7].copy()
    df = df.apply(pd.to_numeric, errors="coerce").dropna().astype(int)

    st.write(f"✅ {len(df)} çekiliş başarıyla işlendi")

    # -------------------------------------------------
    # Analizler
    # -------------------------------------------------
    pattern_counts = analyze_patterns(df)
    st.subheader("📊 En Çok Çıkan 3 Pattern")
    for pat, cnt in pattern_counts.most_common(3):
        st.write(f"{'-'.join(map(str, pat))} → {cnt} kez")

    hot, neutral, cold, freq = frequency_analysis(df)
    pair_stats = pair_analysis(df)

    st.subheader("🌡️ Sayı Davranışları")
    st.write(f"🔥 Sıcak: {hot}")
    st.write(f"⚖️ Nötr: {neutral}")
    st.write(f"❄️ Soğuk: {cold}")

    # -------------------------------------------------
    # Kolon Üretimi
    # -------------------------------------------------
    st.subheader("🎯 Önerilen Kolonlar (En Çok Çıkan 3 Pattern)")
    results = []
    for pat, _ in pattern_counts.most_common(3):
        col = generate_column_for_pattern(pat, hot, neutral, cold, pair_stats, df)
        score = score_column(col, hot, cold, pair_stats)
        results.append((pat, col, score))
        st.write(f"{'-'.join(map(str, pat))} → {col} | Puan: {score}")

    # -------------------------------------------------
    # Favori Kolon (Tahmini Sonraki Çekiliş Pattern)
    # -------------------------------------------------
    st.subheader("⭐ FAVORİ KOLON (Örüntüye Dayalı Tahmin)")
    last_pattern = determine_pattern(df.iloc[-1].values)
    # Basit örüntü tahmini: son pattern'in en çok çıkan devamı
    next_pattern_candidates = [pat for pat in pattern_counts if pat != tuple(last_pattern)]
    if next_pattern_candidates:
        next_pattern = max(next_pattern_candidates, key=lambda p: pattern_counts[p])
    else:
        next_pattern = tuple(last_pattern)
    fav_col = generate_column_for_pattern(next_pattern, hot, neutral, cold, pair_stats, df)
    fav_score = score_column(fav_col, hot, cold, pair_stats)
    st.success(f"{fav_col} | Pattern: {'-'.join(map(str,next_pattern))} | Puan: {fav_score}")

else:
    st.info("👆 Başlamak için CSV dosyasını yükle")
