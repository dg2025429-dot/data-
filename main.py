import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="서울 기온 데이터 마스터 대시보드", layout="wide", page_icon="☀️")

st.title("☀️ 서울 기온 데이터 분석 마스터 대시보드")
st.markdown("업로드된 기상 데이터를 분석하여 다양한 기온 정보와 역사적 통계를 제공합니다.")

# 2. 데이터 로드 및 전처리 함수 (캐싱 적용 및 인코딩/날짜 에러 완벽 방지)
@st.cache_data
def load_data():
    file_name = "ta_20260601093156.csv"
    
    # UnicodeDecodeError 방지를 위해 'utf-8-sig' 인코딩 적용
    df = pd.read_csv(file_name, encoding='utf-8-sig')
    
    # 컬럼명 앞뒤 공백 제거
    df.columns = df.columns.str.strip()
    
    # 날짜 데이터 내부의 쌍따옴표("), 탭 문자(\t), 공백을 완벽하게 제거
    df['날짜'] = df['날짜'].astype(str).str.replace(r'[\"\t\s]', '', regex=True)
    
    # 날짜 데이터 타입 변환 및 연/월 추출
    df['날짜'] = pd.to_datetime(df['날짜'])
    df['연도'] = df['날짜'].dt.year
    df['월'] = df['날짜'].dt.month
    
    return df


# 3. 데이터 로딩 실행 및 파일 존재 여부 예외 처리
try:
    df = load_data()
    file_exists = True
except FileNotFoundError:
    st.error("❌ `ta_20260601093156.csv` 파일을 찾을 수 없습니다. 파일명을 확인하고 main.py와 동일한 위치(GitHub 최상위 루트 경로)에 업로드해 주세요.")
    file_exists = False


# 4. 파일이상 없이 로드된 경우 대시보드 화면 생성
if file_exists:
    
    # ==========================================
    # 사이드바 영역: 데이터 필터 및 추가 기능
    # ==========================================
    st.sidebar.header("🔍 데이터 필터")
    
    # 연도 선택 (가장 최신 연도가 먼저 나오도록 정렬)
    years = sorted(df['연도'].unique(), reverse=True)
    selected_year = st.sidebar.selectbox("연도 선택", years, index=0)
    
    # 월 선택
    months = sorted(df['월'].unique())
    selected_month = st.sidebar.selectbox("월 선택", months, index=0)
    
    # [추가 기능 1] 🎂 과거 날씨 검색기
    st.sidebar.markdown("---")
    st.sidebar.header("🎂 과거 날씨 검색기")
    search_date = st.sidebar.date_input("궁금한 날짜를 선택하세요", value=pd.to_datetime("2002-06-18"))

    if st.sidebar.button("날씨 확인하기"):
        search_result = df[df['날짜'] == pd.to_datetime(search_date)]
        
        if not search_result.empty:
            st.sidebar.balloons()  # 성공 시 풍선 애니메이션 효과
            row = search_result.iloc[0]
            st.sidebar.info(f"📅 **{search_date}** 서울 날씨")
            st.sidebar.write(f"• 평균 기온: {row['평균기온(℃)']} ℃")
            st.sidebar.write(f"• 최저 기온: {row['최저기온(℃)']} ℃")
            st.sidebar.write(f"• 최고 기온: {row['최고기온(℃)']} ℃")
        else:
            st.sidebar.error("⚠️ 해당 날짜의 데이터가 존재하지 않습니다.")

    # ==========================================
    # 메인 화면 영역
    # ==========================================
    
    # 사용자가 선택한 연도/월로 데이터 필터링
    filtered_df = df[(df['연도'] == selected_year) & (df['월'] == selected_month)]
    
    if filtered_df.empty:
        st.warning(f"⚠️ {selected_year}년 {selected_month}월에 해당하는 데이터가 없습니다.")
    else:
        # 주요 통계 카드 (Metric 지표 표시)
        st.subheader(f"📊 {selected_year}년 {selected_month}월 요약 정보")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("최고 기온", f"{filtered_df['최고기온(℃)'].max()} ℃")
        with col2:
            st.metric("최저 기온", f"{filtered_df['최저기온(℃)'].min()} ℃")
        with col3:
            st.metric("평균 기온", f"{filtered_df['평균기온(℃)'].mean():.1f} ℃")
            
        st.markdown("---")
        
        # 기본 그래프: 선택한 연도/월의 일별 기온 추이
        st.subheader("📈 기온 변화 추이 (스트림릿 기본 라인 차트)")
        chart_data = filtered_df.set_index('날짜')[['평균기온(℃)', '최저기온(℃)', '최고기온(℃)']]
        st.line_chart(chart_data)
        
        # [추가 기능 2] 🔄 전년도 동월 기온 비교 그래프
        prev_year = selected_year - 1
        prev_filtered_df = df[(df['연도'] == prev_year) & (df['월'] == selected_month)]
        
        if not prev_filtered_df.empty:
            st.markdown("---")
            st.subheader(f"🔄 {prev_year}년 vs {selected_year}년 {selected_month}월 평균 기온 비교")
            
            df_current = filtered_df.copy()
            df_current['일'] = df_current['날짜'].dt.day
            
            df_prev = prev_filtered_df.copy()
            df_prev['일'] = df_prev['날짜'].dt.day
            
            compare_df = pd.merge(
                df_current[['일', '평균기온(℃)']], 
                df_prev[['일', '평균기온(℃)']], 
                on='일', 
                suffixes=(f'_{selected_year}년', f'_{prev_year}년')
            ).set_index('일')
            
            st.line_chart(compare_df)

        st.markdown("---")

        # [추가 기능 3] 🏆 역대 극값 기온 랭킹 보드 (선택한 월 전체 데이터 기준)
        st.subheader(f"🏆 역대 {selected_month}월의 극값 기온 TOP 5 (전체 역사 기준)")
        monthly_all_years = df[df['월'] == selected_month]
        
        col_hot, col_cold = st.columns(2)
        with col_hot:
            st.markdown("🔥 **가장 더웠던 날 TOP 5**")
            hot_top5 = monthly_all_years.sort_values(by='최고기온(℃)', ascending=False).head(5)
            hot_top5_display = hot_top5[['날짜', '최고기온(℃)']].copy()
            hot_top5_display['날짜'] = hot_top5_display['날짜'].dt.strftime('%Y-%m-%d')
            st.dataframe(hot_top5_display, use_container_width=True, hide_index=True)
            
        with col_cold:
            st.markdown("❄️ **가장 추웠던 날 TOP 5**")
            cold_top5 = monthly_all_years.sort_values(by='최저기온(℃)', ascending=True).head(5)
            cold_top5_display = cold_top5[['날짜', '최저기온(℃)']].copy()
            cold_top5_display['날짜'] = cold_top5_display['날짜'].dt.strftime('%Y-%m-%d')
            st.dataframe(cold_top5_display, use_container_width=True, hide_index=True)

        st.markdown("---")

        # 데이터 원본 확인 및 다운로드 기능
        with st.expander("👀 선택한 기간의 원본 데이터 보기 및 다운로드"):
            display_df = filtered_df[['날짜', '평균기온(℃)', '최저기온(℃)', '최고기온(℃)']].copy()
            display_df['날짜'] = display_df['날짜'].dt.strftime('%Y-%m-%d')
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # [추가 기능 4] 📥 CSV 데이터 다운로드 버튼
            csv_data = display_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 필터링된 데이터 다운로드 (CSV)",
                data=csv_data,
                file_name=f"seoul_weather_{selected_year}_{selected_month}.csv",
                mime="text/csv"
            )
