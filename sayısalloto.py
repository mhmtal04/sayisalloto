import streamlit as st
import pandas as pd
import random
from collections import Counter, defaultdict
from itertools import combinations

# -------------------------------------------------
# Sayfa Ayarları
# -------------------------------------------------
st.set_page_config(
    page_title="🎯 Sayısal Loto Örüntü & Diziliş Botu",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Sayısal Loto Örüntü & Diziliş Botu")
st.caption("Ondalık diziliş • örüntü • sıcak/soğuk • favori kolon")
st.divider()

# -------------------------------------------------
# Yardımcı Fonksiyonlar
# -------------------------------------------------

def decade(n):
    """Sayıyı onluk gruba dönüştürür"""
    return n // 10

def get_pattern(numbers):
    """T kolonlarını alır ve pattern çıkarır"""
    numbers_sorted = sorted(numbers)
    groups = []
    i = 0
    while i < len(numbers_sorted):
        cnt = 1
        d = decade(numbers_sorted[i])
        for j in range(i+1, len(numbers_sorted)):
            if decade(numbers_sorted[j]) == d:
                cnt += 1
            else:
                break
        groups.append(cnt)
        i += cnt
    return "-".join(map(str, groups))

def analyze_patterns(df):
    patterns = df.apply(lambda row: get_pattern(row.values), axis=1)
    return Counter(patterns)

def frequency_analysis(df):
    freq = Counter(df.values.flatten())
    avg = sum(freq.values()) / len(freq)
    hot = [n for n, f in freq.items() if f > avg * 1.3]
    cold = [n for n, f in freq.items() if f < avg * 0.7]
    neutral = [n for n in freq if n not in hot and n not in cold]
    return hot, neutral, cold, freq

def pair_analysis(df):
    pairs = Counter()
    for row in df.values:
        for a, b in combinations(sorted(row), 2):
            pairs[(a, b)] += 1
    return pairs

def select_number(pool, preferred=None):
    """Tercihli havuzdan rastgele sayı seçer, yoksa pooldan"""
    if preferred:
        choices = [n for n in pool if n in preferred]
        if choices:
            return random.choice(choices)
    return random.choice(pool)

def generate_column_for_pattern(pattern, hot, neutral, cold, pair_stats, last_numbers=None):
    """
    Pattern'e uygun kolon üretir.
    T2-T6 seçimleri bir önceki T'ye göre yapılır
    """
    column = []
    used_decades = set()
    sizes = list(map(int, pattern.split("-")))

    for idx, size in enumerate(sizes):
        # Kullanılabilecek onluklar
        possible_decades = [d for d in range(0, 9) if d not in used_decades]
        # T1 veya bir önceki grup
        if idx == 0:
            d = random.choice(possible_decades)
        else:
            # Son eklenen sayı ile aynı onluk
            d = decade(column[-1])
        used_decades.add(d)

        pool = [n for n in range(d*10+1, d*10+10) if 1 <= n <= 90]

        # Öncelik sıralaması: birlikte çıkmayı sevenler, sıcak, nötr, soğuk
        preferred = []
        if last_numbers:
            for n in pool:
                for ln in last_numbers:
                    if (min(n, ln), max(n, ln)) in pair_stats:
                        preferred.append(n)
        preferred += [n for n in pool if n in hot or n in neutral]

        picks = []
        needed = size
        while needed > 0 and pool:
            num = select_number(pool, preferred)
            if num not in picks:
                picks.append(num)
                needed -= 1
            pool.remove(num)
        column.extend(picks)

    # Küçükten büyüğe sırala
    column = sorted(column)
    return column

def score_column(col, hot, cold, pair_stats):
    score = 0
    for n in col:
        if n in hot:
            score += 2
        if n in cold:
            score += 1
    for a, b in combinations(col, 2):
        score += pair_stats.get((a, b), 0) * 0.05
    return round(score,2)

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
    st.success(f"✅ {len(df)} çekiliş başarıyla işlendi")
    st.divider()

    # -------------------------------------------------
    # Analizler
    # -------------------------------------------------
    st.subheader("📊 En Çok Çıkan Dizilişler")
    pattern_counts = analyze_patterns(df)
    for p, c in pattern_counts.most_common(3):
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
    for pair, c in pair_stats.most_common(5):
        st.write(f"{pair} → {c} kez")

    st.divider()

    # -------------------------------------------------
    # Kolon Üretimi
    # -------------------------------------------------
    st.subheader("🎯 Önerilen Kolonlar (En Çok Çıkan 3 Pattern)")

    results = []
    for pattern, _ in pattern_counts.most_common(3):
        col = generate_column_for_pattern(pattern, hot, neutral, cold, pair_stats)
        score = score_column(col, hot, cold, pair_stats)
        results.append((pattern, col, score))
        st.write(f"{pattern} dizilişi → {col} | Puan: {score}")

    # -------------------------------------------------
    # Favori Kolon (Son pattern’den tahmin)
    st.divider()
    st.subheader("⭐ FAVORİ KOLON (Örüntüye Dayalı Tahmin)")

    last_pattern = get_pattern(df.values[-1])
    fav_pattern_counts = defaultdict(int)

    # Basit geçiş tahmini: son pattern’den sonra hangi pattern daha çok çıkmış
    for i in range(len(df)-1):
        cur = get_pattern(df.values[i])
        nxt = get_pattern(df.values[i+1])
        if cur == last_pattern:
            fav_pattern_counts[nxt] += 1

    if fav_pattern_counts:
        fav_pattern = max(fav_pattern_counts, key=fav_pattern_counts.get)
    else:
        fav_pattern = pattern_counts.most_common(1)[0][0]

    fav_col = generate_column_for_pattern(fav_pattern, hot, neutral, cold, pair_stats)
    fav_score = score_column(fav_col, hot, cold, pair_stats)
    st.success(f"{fav_col} | Pattern: {fav_pattern} | Puan: {fav_score}")

else:
    st.info("👆 Başlamak için CSV dosyasını yükle")
