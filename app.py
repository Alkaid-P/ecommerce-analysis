import sys
from pathlib import Path

# 将当前目录添加到系统路径，解决云端部署找不到 src 模块的问题
sys.path.append(str(Path(__file__).parent.resolve()))
# app.py
import importlib.util
import sys

import streamlit as st

from config import (
    BASE_DIR, RAW_DATA_FILE, CLEANED_DATA_FILE, USER_FEATURE_FILE, MODEL_DIR
)
from src.auth import create_user, init_db, verify_login
from src.logger import log_operation
from src.utils import ensure_dirs

# 1. 页面全局配置
st.set_page_config(
    page_title="电商用户行为分析系统",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

ensure_dirs()
init_db()

# 定义所有页面及权限
PAGES = {
    "📥 数据接入与预处理": {"file": "1_数据接入与预处理.py", "roles": {"admin", "analyst"}},
    "📊 用户行为分析": {"file": "2_用户行为分析.py", "roles": {"admin", "analyst", "operator"}},
    "💎 RFM价值分析": {"file": "3_RFM价值分析.py", "roles": {"admin", "analyst", "operator"}},
    "🎯 用户聚类": {"file": "4_用户聚类.py", "roles": {"admin", "analyst"}},
    "🤖 行为预测": {"file": "5_行为预测.py", "roles": {"admin", "analyst", "operator"}},
    "⚙️ 系统管理": {"file": "6_系统管理.py", "roles": {"admin"}},
}

def load_page_render(filename: str):
    path = BASE_DIR / "pages" / filename
    if not path.exists():
        raise FileNotFoundError(f"页面文件不存在: {path}")
    module_name = f"page_module_{path.stem}"
    if module_name in sys.modules:
        module = sys.modules[module_name]
    else:
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    return module.render

# 初始化 session state
if "user" not in st.session_state:
    st.session_state["user"] = None

# ==========================================
# 状态 A：未登录（居中显示表单，隐藏侧边栏）
# ==========================================
if st.session_state["user"] is None:
    # 注入 CSS 隐藏左侧边栏
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] { display: none; }
            [data-testid="collapsedControl"] { display: none; }
            .stApp { background-color: #f8f9fa; }
        </style>
        """,
        unsafe_allow_html=True
    )

    # 使用空列实现居中布局
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.write("") # 占位，往下推一点
        st.write("")
        st.markdown("<h2 style='text-align: center;'>🛒 电商用户行为分析系统</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>基于机器学习的数据驱动决策平台</p>", unsafe_allow_html=True)
        st.write("")
        
        tab1, tab2 = st.tabs(["🔒 账号登录", "📝 注册新账号"])
        
        with tab1:
            with st.form("login_form"):
                user_name = st.text_input("用户名", placeholder="请输入用户名")
                password = st.text_input("密码", type="password", placeholder="请输入密码")
                submitted = st.form_submit_button("登 录", width="stretch", type="primary")
                
            if submitted:
                user = verify_login(user_name, password)
                if user:
                    st.session_state["user"] = user
                    log_operation(int(user["user_id"]), "登录", f"用户 {user['user_name']} 登录系统")
                    st.rerun()
                else:
                    st.error("❌ 用户名或密码错误，或账号被禁用")
                    
            st.caption("💡 默认管理员账号：`admin` / `admin123`")

        with tab2:
            with st.form("register_form"):
                new_user = st.text_input("设置用户名")
                new_password = st.text_input("设置密码", type="password")
                confirm_password = st.text_input("确认密码", type="password")
                real_name = st.text_input("真实姓名")
                role = st.selectbox("申请角色", ["analyst (数据分析师)", "operator (运营)", "admin (管理员)"])
                phone = st.text_input("手机号")
                submitted_reg = st.form_submit_button("注 册", width="stretch")
                
            if submitted_reg:
                role_val = role.split(" ")[0]
                if new_password != confirm_password:
                    st.error("❌ 两次输入的密码不一致")
                elif not new_user or not new_password:
                    st.error("❌ 用户名和密码不能为空")
                else:
                    ok, msg = create_user(new_user, new_password, real_name, role_val, phone)
                    if ok:
                        st.success(f"✅ {msg}，请前往左侧登录")
                    else:
                        st.error(f"❌ {msg}")

# ==========================================
# 状态 B：已登录（显示侧边栏、概览和导航）
# ==========================================
else:
    user = st.session_state["user"]
    
    # 侧边栏用户信息
    st.sidebar.title("🛒 电商分析系统")
    st.sidebar.markdown("---")
    st.sidebar.success(f"👤 **{user.get('real_name') or user['user_name']}**")
    st.sidebar.caption(f"角色：{user['role']}")
    
    if st.sidebar.button("🚪 退出登录", width="stretch"):
        log_operation(int(user["user_id"]), "退出", f"用户 {user['user_name']} 退出系统")
        st.session_state["user"] = None
        st.rerun()
        
    st.sidebar.markdown("---")
    
    # 构建菜单
    menu_options = ["🏠 系统概览"] + [
        label for label, info in PAGES.items() if user["role"] in info["roles"]
    ]
    
    selected_page = st.sidebar.radio("功能导航", menu_options)
    
    # ---- 渲染：系统概览 ----
    if selected_page == "🏠 系统概览":
        st.title(f"欢迎回来，{user.get('real_name') or user['user_name']} 👋")
        st.markdown("这里是系统的运行状态概览。请根据下方的步骤指引，完成数据分析与模型训练。")
        
        st.divider()
        
        # 状态检测
        has_raw = RAW_DATA_FILE.exists()
        has_cleaned = CLEANED_DATA_FILE.exists()
        has_features = USER_FEATURE_FILE.exists()
        has_models = len(list(MODEL_DIR.glob("*.pkl"))) > 0
        
        # 进度步骤提示
        st.subheader("📋 核心工作流状态")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="1. 原始数据", value="已就绪 ✅" if has_raw else "未上传 ❌")
        with col2:
            st.metric(label="2. 清洗数据", value="已处理 ✅" if has_cleaned else "未处理 ❌")
        with col3:
            st.metric(label="3. 用户特征", value="已生成 ✅" if has_features else "未生成 ❌")
        with col4:
            st.metric(label="4. 机器学习模型", value="已训练 ✅" if has_models else "未训练 ❌")
            
        st.divider()
        
        # 智能指导
        st.subheader("💡 下一步操作建议")
        
        if not has_raw:
            st.warning("**请先上传数据**：你还没有原始数据集。请准备好 `online_retail.csv`，然后前往【数据接入与预处理】页面。")
            if "📥 数据接入与预处理" in menu_options:
                st.info("👉 请点击左侧导航栏的【📥 数据接入与预处理】开始。")
        elif not has_cleaned or not has_features:
            st.info("**数据已接入，等待预处理**：请前往【数据接入与预处理】页面，点击“开始预处理”按钮，生成清洗数据和用户特征。")
        elif not has_models:
            st.success("**数据准备完毕！** 你可以开始进行【用户行为分析】和【RFM价值分析】。若想进行预测，请前往【用户聚类】或【行为预测】页面训练模型。")
        else:
            st.success("🎉 **系统各项数据均已就绪！** 你可以随意使用所有的分析与预测功能。")
            
        st.divider()
        st.caption("📌 提示：所有分析图表均支持交互式缩放与下载。如果有疑问，请查阅左侧的各个功能模块。")

    # ---- 渲染：其他功能页面 ----
    else:
        page_file = PAGES[selected_page]["file"]
        try:
            render = load_page_render(page_file)
            st.markdown(f"### {selected_page}")
            render()
        except Exception as exc:
            st.error(f"页面加载失败: {exc}")
            import traceback
            with st.expander("查看详细错误信息"):
                st.code(traceback.format_exc())
