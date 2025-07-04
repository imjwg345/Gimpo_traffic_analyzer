import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- 한글 폰트 설정 (윈도우용) ---
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# --- 데이터 업로드 및 전처리 함수 ---
def load_and_preprocess_data(uploaded_file):
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
            st.success(f"✅ 데이터 업로드 완료: {len(df)}개 지역")
            return df
        except Exception as e:
            st.error(f"❌ 파일 업로드 실패: {e}")
            return pd.DataFrame()
    else:
        st.info("⬆ 좌측 사이드바에서 CSV 파일을 업로드해주세요.")
        return pd.DataFrame()

# --- 교통 환경 점수 계산 ---
def calculate_traffic_score(df):
    weights = {
        '평균_통행_속도': 0.4,
        '대중교통_노선_수': 0.3,
        '교통사고_건수_10만명당': 0.3
    }

    df['정규화_평균_통행_속도'] = (df['평균_통행_속도'] - df['평균_통행_속도'].min()) / (df['평균_통행_속도'].max() - df['평균_통행_속도'].min()) * 100
    df['정규화_대중교통_노선_수'] = (df['대중교통_노선_수'] - df['대중교통_노선_수'].min()) / (df['대중교통_노선_수'].max() - df['대중교통_노선_수'].min()) * 100
    df['정규화_교통사고_건수'] = (df['교통사고_건수_10만명당'].max() - df['교통사고_건수_10만명당']) / (df['교통사고_건수_10만명당'].max() - df['교통사고_건수_10만명당'].min()) * 100

    df['교통_환경_점수'] = (
        df['정규화_평균_통행_속도'] * weights['평균_통행_속도'] +
        df['정규화_대중교통_노선_수'] * weights['대중교통_노선_수'] +
        df['정규화_교통사고_건수'] * weights['교통사고_건수_10만명당']
    )

    return df

# --- Streamlit UI 시작 ---
st.set_page_config(layout="wide")
st.title("🚦 김포시 교통 환경 분석 시스템")
st.markdown("---")

# --- 파일 업로더 ---
uploaded_file = st.sidebar.file_uploader("📁 교통 데이터 CSV 업로드", type=["csv"])

# --- 데이터 로드 ---
df = load_and_preprocess_data(uploaded_file)

if not df.empty:
    df = calculate_traffic_score(df)

    st.subheader("📊 김포시 지역별 교통 환경 요약")
    display_df = df[['지역', '평균_통행_속도', '대중교통_노선_수', '교통사고_건수_10만명당', '교통_환경_점수']] \
        .sort_values(by='교통_환경_점수', ascending=False).reset_index(drop=True)
    display_df.insert(1, '순위', np.arange(1, len(display_df) + 1))
    st.dataframe(display_df.style.format({'평균_통행_속도': "{:.1f}", '교통사고_건수_10만명당': "{:.1f}", '교통_환경_점수': "{:.2f}"}),
                 use_container_width=True, hide_index=True)

    # --- 그래프 시각화 ---
    st.markdown("### 📈 지역별 교통 지표 시각화")
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))

    sns.barplot(x='지역', y='교통_환경_점수', data=df.sort_values(by='교통_환경_점수', ascending=False),
                palette='viridis', ax=axes[0, 0])
    axes[0, 0].set_title('종합 교통 환경 점수')
    axes[0, 0].tick_params(axis='x', rotation=45)

    sns.barplot(x='지역', y='평균_통행_속도', data=df.sort_values(by='평균_통행_속도', ascending=False),
                palette='Blues_d', ax=axes[0, 1])
    axes[0, 1].set_title('평균 통행 속도')
    axes[0, 1].tick_params(axis='x', rotation=45)

    sns.barplot(x='지역', y='대중교통_노선_수', data=df.sort_values(by='대중교통_노선_수', ascending=False),
                palette='Greens_d', ax=axes[1, 0])
    axes[1, 0].set_title('대중교통 노선 수')
    axes[1, 0].tick_params(axis='x', rotation=45)

    sns.barplot(x='지역', y='교통사고_건수_10만명당', data=df.sort_values(by='교통사고_건수_10만명당', ascending=True),
                palette='Reds_d', ax=axes[1, 1])
    axes[1, 1].set_title('10만명당 교통사고 건수')
    axes[1, 1].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    st.pyplot(fig)

    # --- 사용자 선택 지역 비교 ---
    st.markdown("---")
    st.subheader("🏠 내 거주 지역 비교")

    all_locations = ['선택'] + df['지역'].tolist()
    user_location = st.selectbox("📍 거주 지역을 선택하세요:", options=all_locations)

    if user_location != '선택':
        user_data = df[df['지역'] == user_location].iloc[0]
        gimpo_avg = df.mean(numeric_only=True)

        st.markdown(f"### ✅ **{user_location}** 지역 분석 결과")
        st.markdown(f"**교통 환경 점수**: {user_data['교통_환경_점수']:.2f} (평균: {gimpo_avg['교통_환경_점수']:.2f})")

        # 비교 상세
        for col, desc in {
            '평균_통행_속도': 'km/h',
            '대중교통_노선_수': '개',
            '교통사고_건수_10만명당': '건'
        }.items():
            user_val = user_data[col]
            avg_val = gimpo_avg[col]
            diff = user_val - avg_val
            direction = "높습니다" if diff > 0 else "낮습니다" if diff < 0 else "같습니다"

            st.write(f"- **{col}**: {user_val:.2f} {desc} (평균: {avg_val:.2f} {desc}) → 평균보다 {abs(diff):.2f} {desc} **{direction}**")

else:
    st.warning("⚠ CSV 파일을 업로드하면 분석 결과가 여기에 표시됩니다.")


