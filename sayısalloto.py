import streamlit as st
import pandas as pd
import random
from collections import Counter
from itertools import combinations

# -------------------------------------------------
# Sayfa Ayarları
# -------------------------------------------------
st.set_page_config(
    page_title="Sayısal Loto Diziliş & Örüntü Botu",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Sayısal Loto Diziliş & Örüntü Botu")
st.caption("Ondalık diziliş • örüntü • sıcak / soğuk • favori kolon")
st.divider()

# -------------------------------------------------
# Yardımcı Fonksiyonlar
# -------------------------------------------------

def decade(n: int) -> int:
    return n // 10

def generate_pattern(numbers):
    decades = [decade(n) for n in numbers]
    counts = Counter(decades)
    return "-".join(map(str, sorted(counts.values(), reverse=True)))

def analyze_patterns(df):
    pattern_list = df.apply(lambda r: generate_pattern(r.values), axis=1)
    return Counter(pattern_list), pattern_list.tolist()

def frequency_analysis(df):
    freq = Counter(df.values.flatten())
    avg = sum(freq.values()) / len(freq)

    hot = [n for n, f in freq.items() if f > avg * 1.30]
    cold = [n for n, f in freq.items() if f < avg * 0.70]
    neutral = [n for n in freq if n not in hot and n not in cold]

    return hot, neutral, cold, freq

def pair_analysis(df):
    pair_counter = Counter()
    for row in df.values:
        for a, b in combinations(sorted(row), 2):
            pair_counter[(a, b)] += 1
    return pair_counter

def generate_column(pattern, hot, neutral, cold):
    column = []
    used_decades = set()

    for size in map(int, pattern.split("-")):
        possible_decades = [d for d in range(0, 9) if d not in used_decades]
        d = random.choice(possible_decades)
        used_decades.add(d)

        pool = [n for n in range(d * 10, d * 10 + 10) if 1 <= n <= 90]

        preferred = [n for n in pool if n in neutral]
        picks = random.sample(preferred, size) if len(preferred) >= size else random.sample(pool, size)

        column.extend(picks)

    if cold and random.random() < 0.35:
        column[random.randint(0, 5)] = random.choice(cold)

    return sorted(set(column))[:6]

def score_column(col, hot, cold, pair_stats):
    score = 0
    for n in col:
        if n in hot:
            score += 2
        if n in cold:
            score += 1
    for a, b in combinations(col, 2):
        score += pair_stats.get((a, b), 0) * 0.05
    return round(score, 2)

# -------------------------------------------------
# CSV Yükleme
# -------------------------------------------------

uploaded_file = st.file_uploader(
    "📂 CSV dosyasını yükle (T1–T6 veya S1–S6 desteklenir)",
    type="csv"
)

if uploaded_file:
    st.subheader("📥 Veri Okuma & Temizleme")

    df_raw = pd.read_csv(uploaded_file)
    total_rows = len(df_raw)
    st.write(f"📄 CSV okundu → **{total_rows} satır bulundu**")

    # Kolon isimlerini temizle
    df_raw.columns = [c.strip().upper() for c in df_raw.columns]

    s_cols = ["S1", "S2", "S3", "S4", "S5", "S6"]
    t_cols = ["T1", "T2", "T3", "T4", "T5", "T6"]

    if all(c in df_raw.columns for c in s_cols):
        df = df_raw[s_cols].copy()
        st.write("✅ S1–S6 kolonları kullanıldı")
    elif all(c in df_raw.columns for c in t_cols):
        df = df_raw[t_cols].copy()
        st.write("✅ T1–T6 kolonları kullanıldı")
    else:
        df = df_raw.iloc[:, 1:7].copy()
        st.write("⚠️ Kolon isimleri bulunamadı → 2–7. kolonlar alındı")

    df = df.apply(pd.to_numeric, errors="coerce")

    before = len(df)
    df = df.dropna()
    after = len(df)
    dropped = before - after

    df = df.astype(int)

    st.write(f"🧹 Hatalı satırlar elendi → **{dropped} satır atıldı**")
    st.success(f"✅ **{after} çekiliş başarıyla işlendi**")
    st.divider()

    # -------------------------------------------------
    # Analizler
    # -------------------------------------------------

    st.subheader("📊 En Çok Çıkan Dizilişler")
    pattern_counts, pattern_list = analyze_patterns(df)

    for p, c in pattern_counts.most_common(3):
        st.write(f"🔹 **{p}** → {c} kez")

    st.divider()

    st.subheader("🌡️ Sayı Davranışları")
    hot, neutral, cold, _ = frequency_analysis(df)

    c1, c2, c3 = st.columns(3)
    c1.metric("🔥 Sıcak", len(hot))
    c2.metric("⚖️ Nötr", len(neutral))
    c3.metric("❄️ Soğuk", len(cold))

    st.divider()

    st.subheader("🤝 Birlikte Çıkmayı Sevenler")
    pair_stats = pair_analysis(df)
    for pair, c in pair_stats.most_common(5):
        st.write(f"{pair} → {c} kez")

    st.divider()

    # -------------------------------------------------
    # Kolon Üretimi
    # -------------------------------------------------

    st.subheader("🎯 Önerilen Kolonlar")

    results = []
    for pattern, _ in pattern_counts.most_common(3):
        col = generate_column(pattern, hot, neutral, cold)
        score = score_column(col, hot, cold, pair_stats)
        results.append((pattern, col, score))

    for p, col, s in results:
        st.write(f"**{p} dizilişi** → {col} | Puan: **{s}**")

    fav = max(results, key=lambda x: x[2])
    st.divider()
    st.subheader("⭐ FAVORİ KOLON")
    st.success(f"{fav[1]}  |  Puan: {fav[2]}")

else:
    st.info("👆 Başlamak için CSV dosyasını yükle")
