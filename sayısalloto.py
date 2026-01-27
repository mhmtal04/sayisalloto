import streamlit as st
import pandas as pd
import random
from collections import Counter, defaultdict
from itertools import combinations

st.set_page_config(page_title="Sayısal Loto Diziliş & Örüntü Botu", layout="wide")
st.title("🎯 Sayısal Loto Diziliş & Örüntü Botu")

# -----------------------------
# Yardımcı Fonksiyonlar
# -----------------------------

def decade(n):
    return n // 10

def generate_pattern(numbers):
    decades = [decade(n) for n in numbers]
    counts = Counter(decades)
    return "-".join(map(str, sorted(counts.values(), reverse=True)))

def analyze_patterns(df):
    patterns = df.apply(lambda r: generate_pattern(r.values), axis=1)
    return Counter(patterns), patterns.tolist()

def t_position_stats(df):
    return {f"T{i+1}": Counter(df.iloc[:, i]) for i in range(6)}

def pair_analysis(df):
    pair_counter = Counter()
    for row in df.values:
        for a, b in combinations(sorted(row), 2):
            pair_counter[(a, b)] += 1
    return pair_counter

def frequency_analysis(df):
    freq = Counter(df.values.flatten())
    avg = sum(freq.values()) / len(freq)

    hot = [n for n, f in freq.items() if f > avg * 1.3]
    cold = [n for n, f in freq.items() if f < avg * 0.7]
    neutral = [n for n in freq if n not in hot and n not in cold]

    return hot, neutral, cold, freq

def pattern_transition(patterns):
    transitions = defaultdict(Counter)
    for i in range(len(patterns) - 1):
        transitions[patterns[i]][patterns[i+1]] += 1
    return transitions

def predict_next_pattern(transitions, last_pattern):
    if last_pattern in transitions:
        return transitions[last_pattern].most_common(1)[0][0]
    return None

def generate_column(pattern, hot, neutral, cold, pair_stats):
    column = []
    used_decades = set()

    for size in map(int, pattern.split("-")):
        d = random.choice([x for x in range(0, 9) if x not in used_decades])
        used_decades.add(d)

        pool = list(range(d * 10, d * 10 + 10))
        pool = [n for n in pool if 1 <= n <= 90]

        choices = (
            random.sample([n for n in pool if n in neutral], min(size, len(pool)))
            if random.random() < 0.6 else
            random.sample(pool, size)
        )

        column.extend(choices)

    # soğuk ekleme şansı
    if cold and random.random() < 0.4:
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

# -----------------------------
# Streamlit
# -----------------------------

uploaded_file = st.file_uploader("CSV dosyanı yükle (HER çekiliş = 6 sayı)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = df.iloc[:, :6].dropna().astype(int)

    st.success(f"{len(df)} çekiliş yüklendi")

    # 1️⃣ Dizilişler
    pattern_counts, pattern_list = analyze_patterns(df)
    top_patterns = pattern_counts.most_common(3)

    st.subheader("📊 En Çok Çıkan 3 Diziliş")
    for p, c in top_patterns:
        st.write(f"{p} → {c} kez")

    # 2️⃣ T Bölgeleri
    st.subheader("📍 T1–T6 Baskıları")
    t_stats = t_position_stats(df)
    for t, c in t_stats.items():
        st.write(f"{t}:", c.most_common(5))

    # 3️⃣ Birlikte Çıkanlar
    pair_stats = pair_analysis(df)
    st.subheader("🤝 Birlikte Çıkmayı Seven Sayılar")
    for pair, c in pair_stats.most_common(5):
        st.write(pair, "→", c)

    # 4️⃣ Sıcak / Nötr / Soğuk
    hot, neutral, cold, freq = frequency_analysis(df)
    st.subheader("🌡️ Sayı Davranışları")
    st.write("🔥 Sıcak:", sorted(hot))
    st.write("⚖️ Nötr (örnek):", sorted(neutral)[:15])
    st.write("❄️ Soğuk:", sorted(cold))

    # 5️⃣ Örüntü Geçişi
    transitions = pattern_transition(pattern_list)
    last_pattern = pattern_list[-1]
    predicted_pattern = predict_next_pattern(transitions, last_pattern)

    st.subheader("🔮 Örüntü Tahmini")
    st.write("Son diziliş:", last_pattern)
    st.write("Tahmin edilen sonraki diziliş:", predicted_pattern)

    # 6️⃣ Kolon Üretimi + Puanlama
    st.subheader("🎯 Önerilen Kolonlar")

    results = []
    for pattern, _ in top_patterns:
        col = generate_column(pattern, hot, neutral, cold, pair_stats)
        score = score_column(col, hot, cold, pair_stats)
        results.append((pattern, col, score))

    for p, col, s in results:
        st.write(f"**{p} dizilişi** → {col} | Puan: {s}")

    # 7️⃣ Favori Kolon
    favorite = max(results, key=lambda x: x[2])
    st.subheader("⭐ FAVORİ KOLON")
    st.success(f"{favorite[1]}  |  Puan: {favorite[2]}")
