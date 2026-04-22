"""
Vitis-AI Streamlit Interface
Интерфейс для оценки пригодности земель для виноделия

Запуск: streamlit run app.py
"""

import streamlit as st
import requests
import json
import os
from datetime import datetime
import folium
from streamlit_folium import st_folium

# ============================================
# Configuration
# ============================================

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3000")
st.set_page_config(
    page_title="Vitis-AI — Оценка земель для виноделия",
    page_icon="🍇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# Custom CSS
# ============================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4CAF50;
        text-align: center;
        margin-bottom: 1rem;
    }
    .score-high {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        color: #155724;
    }
    .score-medium {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        color: #856404;
    }
    .score-low {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        color: #721c24;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# Session State
# ============================================

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None
if 'evaluation_result' not in st.session_state:
    st.session_state.evaluation_result = None

# ============================================
# Helper Functions
# ============================================

def make_request(method, endpoint, data=None, headers=None):
    """Make HTTP request to backend API"""
    url = f"{BACKEND_URL}{endpoint}"
    
    if headers is None:
        headers = {}
    
    if st.session_state.token:
        headers['Authorization'] = f'Bearer {st.session_state.token}'
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response.status_code, response.json()
    except requests.exceptions.RequestException as e:
        return 500, {"error": str(e)}

def login(email, password):
    """Authenticate user"""
    status_code, response = make_request('POST', '/api/auth/login', {
        'email': email,
        'password': password
    })
    
    if status_code == 200 and response.get('success'):
        st.session_state.token = response['data']['token']
        st.session_state.user = response['data']['user']
        st.session_state.authenticated = True
        return True, "Вход выполнен успешно"
    return False, response.get('message', 'Ошибка входа')

def register(username, email, password, full_name=None):
    """Register new user"""
    data = {
        'username': username,
        'email': email,
        'password': password
    }
    if full_name:
        data['fullName'] = full_name
    
    status_code, response = make_request('POST', '/api/auth/register', data)
    
    if status_code == 201 and response.get('success'):
        st.session_state.token = response['data']['token']
        st.session_state.user = response['data']['user']
        st.session_state.authenticated = True
        return True, "Регистрация успешна"
    return False, response.get('message', 'Ошибка регистрации')

def evaluate_location(latitude, longitude, region=None):
    """Evaluate location for viticulture suitability"""
    data = {
        'latitude': latitude,
        'longitude': longitude
    }
    if region:
        data['region'] = region
    
    status_code, response = make_request('POST', '/api/evaluate', data)
    
    if status_code == 200 and response.get('success'):
        return True, response['data']
    return False, response.get('message', 'Ошибка оценки')

def get_evaluation_history():
    """Get user's evaluation history"""
    status_code, response = make_request('GET', '/api/user/history')
    
    if status_code == 200 and response.get('success'):
        return True, response['data']
    return False, response.get('message', 'Ошибка получения истории')

def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.evaluation_result = None

# ============================================
# Authentication UI
# ============================================

def show_auth_page():
    """Show authentication page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<p class="main-header">🍇 Vitis-AI</p>', unsafe_allow_html=True)
        st.markdown("### Система оценки пригодности земель для виноделия")
        st.markdown("---")
        
        tab_login, tab_register = st.tabs(["🔐 Вход", "📝 Регистрация"])
        
        with tab_login:
            st.subheader("Вход в систему")
            login_email = st.text_input("Email", key="login_email")
            login_password = st.text_input("Пароль", type="password", key="login_password")
            
            if st.button("Войти", use_container_width=True):
                if login_email and login_password:
                    success, message = login(login_email, login_password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Заполните все поля")
        
        with tab_register:
            st.subheader("Регистрация")
            reg_username = st.text_input("Имя пользователя", key="reg_username")
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Пароль", type="password", key="reg_password")
            reg_fullname = st.text_input("ФИО (необязательно)", key="reg_fullname")
            
            if st.button("Зарегистрироваться", use_container_width=True):
                if reg_username and reg_email and reg_password:
                    success, message = register(reg_username, reg_email, reg_password, reg_fullname)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Заполните обязательные поля")

# ============================================
# Main Application UI
# ============================================

def show_main_app():
    """Show main application interface"""
    # Sidebar
    with st.sidebar:
        st.markdown("### 👤 Профиль")
        if st.session_state.user:
            st.write(f"**{st.session_state.user.get('username', 'User')}**")
            st.write(f"Роль: {st.session_state.user.get('role', 'user')}")
            st.write(f"Оценок: {st.session_state.user.get('evaluationCount', 0)}")
        
        st.markdown("---")
        
        if st.button("🚪 Выйти", use_container_width=True):
            logout()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Навигация")
        page = st.radio(
            "Страницы",
            ["🗺️ Оценка участка", "📜 История оценок", "ℹ️ О системе"],
            label_visibility="collapsed"
        )
    
    # Main content
    if page == "🗺️ Оценка участка":
        show_evaluation_page()
    elif page == "📜 История оценок":
        show_history_page()
    else:
        show_about_page()

def show_evaluation_page():
    """Show evaluation page with map and form"""
    st.markdown('<p class="main-header">🗺️ Оценка участка</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 📍 Выберите местоположение")
        
        # Default coordinates (Krasnodar region)
        default_lat = 45.0456
        default_lon = 38.9765
        
        # Interactive map
        m = folium.Map(location=[default_lat, default_lon], zoom_start=10)
        
        # Add marker that can be dragged (using Folium)
        marker = folium.Marker(
            location=[default_lat, default_lon],
            popup="Выбранная точка",
            draggable=True
        )
        marker.add_to(m)
        
        # Display map
        map_data = st_folium(m, width=700, height=500, returned_objects=["last_clicked"])
        
        # Update coordinates if user clicked on map
        if map_data and map_data.get("last_clicked"):
            default_lat = map_data["last_clicked"]["lat"]
            default_lon = map_data["last_clicked"]["lng"]
        
        st.info("💡 Кликните на карту для выбора координат или введите вручную ниже")
    
    with col2:
        st.markdown("#### 📝 Параметры участка")
        
        latitude = st.number_input(
            "Широта",
            min_value=-90.0,
            max_value=90.0,
            value=default_lat,
            format="%.6f"
        )
        
        longitude = st.number_input(
            "Долгота",
            min_value=-180.0,
            max_value=180.0,
            value=default_lon,
            format="%.6f"
        )
        
        region = st.selectbox(
            "Регион",
            ["Краснодарский край", "Ставропольский край", "Ростовская область", 
             "Республика Крым", "Дагестан", "Другое"]
        )
        
        st.markdown("---")
        
        if st.button("🚀 Оценить участок", use_container_width=True, type="primary"):
            with st.spinner("Выполняется оценка... Это может занять до 30 секунд"):
                success, result = evaluate_location(latitude, longitude, region)
                
                if success:
                    st.session_state.evaluation_result = result
                    st.success("Оценка завершена!")
                    st.rerun()
                else:
                    st.error(f"Ошибка: {result}")
    
    # Show results if available
    if st.session_state.evaluation_result:
        display_evaluation_results(st.session_state.evaluation_result)

def display_evaluation_results(result):
    """Display evaluation results"""
    st.markdown("---")
    st.markdown("### 📊 Результаты оценки")
    
    score = result.get('data', {}).get('prediction', {}).get('suitability_score', 0)
    category = result.get('data', {}).get('prediction', {}).get('category', 'low')
    
    # Score display
    if category == 'high':
        score_class = "score-high"
        emoji = "✅"
    elif category == 'medium':
        score_class = "score-medium"
        emoji = "⚠️"
    else:
        score_class = "score-low"
        emoji = "❌"
    
    st.markdown(f'<div class="{score_class}">{emoji} Пригодность: {score}%</div>', unsafe_allow_html=True)
    
    # Details
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("##### 🌡️ Климат")
        features = result.get('data', {}).get('features', {})
        climate = features.get('climate', {})
        st.metric("GDD (Winkler)", climate.get('growing_degree_days', 'N/A'))
        st.metric("Осадки (год)", f"{climate.get('rainfall_year', 'N/A')} мм")
        st.metric("Средняя температура", f"{climate.get('avg_temp_year', 'N/A')}°C")
    
    with col2:
        st.markdown("##### ⛰️ Рельеф")
        relief = features.get('relief', {})
        st.metric("Высота", f"{relief.get('elevation', 'N/A')} м")
        st.metric("Уклон", f"{relief.get('slope', 'N/A')}°")
        st.metric("Экспозиция", f"{relief.get('aspect', 'N/A')}°")
    
    with col3:
        st.markdown("##### 🌱 Почва")
        soil = features.get('soil', {})
        st.metric("Тип", soil.get('soil_type', 'N/A'))
        st.metric("pH", soil.get('soil_ph', 'N/A'))
        st.metric("Органика", f"{soil.get('organic_matter', 'N/A')}%")
    
    # Top factors
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🔍 Факторы влияния")
        top_factors = result.get('data', {}).get('top_factors', [])
        for factor in top_factors:
            direction = "↗️" if factor.get('direction') == '+' else "↘️"
            st.write(f"{direction} **{factor.get('factor')}**: {factor.get('influence'):.2f}")
    
    with col2:
        st.markdown("##### ⚠️ Риски")
        risks = result.get('data', {}).get('risks', {})
        for risk_name, risk_data in risks.items():
            level_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(risk_data.get('level'), "⚪")
            st.write(f"{level_emoji} **{risk_name.replace('_', ' ').title()}**: {risk_data.get('description', 'N/A')}")
    
    # Recommendations
    st.markdown("---")
    st.markdown("##### 💡 Рекомендации")
    recommendations = result.get('data', {}).get('recommendations', {})
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Подходящие сорта:**")
        varieties = recommendations.get('suitable_varieties', [])
        for variety in varieties:
            st.write(f"🍇 {variety}")
    
    with col2:
        st.write("**Советы по посадке:**")
        st.write(recommendations.get('planting_advice', 'N/A'))
        st.write("\n**Полив:**")
        st.write(recommendations.get('irrigation_needs', 'N/A'))

def show_history_page():
    """Show evaluation history"""
    st.markdown('<p class="main-header">📜 История оценок</p>', unsafe_allow_html=True)
    
    success, result = get_evaluation_history()
    
    if success:
        evaluations = result.get('evaluations', [])
        pagination = result.get('pagination', {})
        
        if not evaluations:
            st.info("У вас пока нет оценок. Начните с оценки первого участка!")
        else:
            st.write(f"Всего оценок: {pagination.get('total_items', 0)}")
            
            for eval_item in evaluations:
                with st.expander(f"📍 {eval_item.get('region', 'Unknown')} - {eval_item.get('prediction', {}).get('suitability_score', 0)}%"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Координаты:** {eval_item.get('location', {}).get('coordinates', 'N/A')}")
                        st.write(f"**Дата:** {eval_item.get('createdAt', 'N/A')}")
                    with col2:
                        st.write(f"**Категория:** {eval_item.get('prediction', {}).get('category', 'N/A')}")
                        st.write(f"**Модель:** v{eval_item.get('prediction', {}).get('model_version', 'N/A')}")
    else:
        st.error(f"Ошибка загрузки истории: {result}")

def show_about_page():
    """Show about page"""
    st.markdown('<p class="main-header">ℹ️ О системе Vitis-AI</p>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 🎯 Назначение системы
    
    Vitis-AI — это система оценки пригодности земельных участков для виноделия на основе геопространственного машинного обучения.
    
    ### 🔧 Используемые технологии
    
    - **Backend:** Node.js + Express
    - **Database:** MongoDB (GeoJSON support)
    - **Frontend:** Streamlit
    - **ML Model:** CatBoost с SHAP интерпретацией
    - **Data Sources:** 
      - ERA5 (климат)
      - SRTM DEM (рельеф)
      - SoilGrids (почвы)
      - Sentinel-2 (спутниковые данные)
    
    ### 📊 Критерии оценки
    
    1. **Климатические факторы:**
       - Growing Degree Days (GDD)
       - Осадки
       - Температура
       - Риск заморозков
    
    2. **Рельеф:**
       - Высота над уровнем моря
       - Уклон и экспозиция склонов
       - Инсоляция
    
    3. **Почвенные характеристики:**
       - Тип почвы
       - pH
       - Органическое вещество
    
    ### 📈 Интерпретация результатов
    
    - **🟢 Высокая пригодность (>70%)**: Отличные условия для коммерческого виноградарства
    - **🟡 Средняя пригодность (40-70%)**: Требуется дополнительный анализ и уход
    - **🔴 Низкая пригодность (<40%)**: Высокий риск неудачи
    
    ---
    
    *Версия системы: 1.0.0*
    
    *Разработано командой Vitis-AI в рамках проектного практикура УрФУ*
    """)

# ============================================
# Main Application Flow
# ============================================

def main():
    """Main application entry point"""
    if not st.session_state.authenticated:
        show_auth_page()
    else:
        show_main_app()

if __name__ == "__main__":
    main()
