import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from io import BytesIO

# ==================== 页面配置 ====================
st.set_page_config(layout="wide", page_title="教学楼狭管效应探究平台")

st.title("教学楼狭管效应数字化探究平台")
st.markdown(
    "本平台基于**连续性方程** $A_1V_1 = A_2V_2$ 与经验风洞模型，"
    "模拟两栋教学楼之间因通道变窄而出现的**风速放大现象（狭管效应）**。"
)
st.markdown("---")

# ==================== 侧边栏参数 ====================
with st.sidebar:
    st.header("⚙️ 参数设置")
    V_inf = st.slider("来流风速 V∞ (m/s)", 0.0, 20.0, 5.0, 0.5)
    T = st.slider("环境温度 T (°C)", -10.0, 40.0, 20.0, 0.5)
    H = st.slider("建筑高度 H (m)", 5.0, 60.0, 20.0, 1.0)
    d = st.slider("建筑间距 d (m)", 1.0, 40.0, 8.0, 0.5)
    w = st.slider("建筑宽度 w (m)", 10.0, 120.0, 40.0, 5.0)

    st.markdown("---")
    with st.expander("📚 点击展开：理论推导与代数过程", expanded=False):
      st.markdown("### 狭管效应风速与风压的代数推导")
    
      st.markdown("#### 第一步：由连续性方程推导速度关系")
      st.markdown("假设空气不可压缩，流量守恒：")
      st.latex(r"A_1 V_1 = A_2 V_2 \implies V_2 = \frac{A_1}{A_2} V_1")
      st.markdown("其中 $A_1$ 为开阔来流的有效迎风面积，$A_2$ 为教学楼通道的截面积。由于 $A_2 \ll A_1$，因此 $V_2 \gg V_1$。")
    
      st.markdown("#### 第二步：由伯努利方程推导风压差")
      st.markdown("忽略高度变化，水平气流的伯努利方程为：")
      st.latex(r"P_1 + \frac{1}{2}\rho V_1^2 = P_2 + \frac{1}{2}\rho V_2^2")
      st.markdown("移项可得静压差：")
      st.latex(r"\Delta P = P_1 - P_2 = \frac{1}{2}\rho (V_2^2 - V_1^2)")
      st.markdown("这说明：**通道内风速的平方增加，会导致通道内的静压远低于外部，从而产生强烈的吸附与推力。**")
    
      st.markdown("#### 第三步：动压计算与风级评估")
      st.markdown("风对行人的物理冲击力主要取决于动压 $q$：")
      st.latex(r"q = \frac{1}{2}\rho V^2")
      st.markdown("结合空气密度随温度变化的理想气体近似公式：")
      st.latex(r"\rho = \frac{353}{T + 273.15}")
      st.markdown("因此，狭管处的动压增加量为：")
      st.latex(r"\Delta q = q_{gap} - q_\infty = \frac{1}{2}\rho \left( V_{gap}^2 - V_\infty^2 \right)")
    
      st.markdown("#### 第四步：引入教学楼几何修正")
      st.markdown("理想流体模型忽略了建筑尺寸的摩擦与绕流。实际应用中，采用风洞实验拟合的半经验公式：")
      st.latex(r"V_{gap} = V_\infty \cdot \left(1 + 0.5\sqrt{\frac{H}{d}}\right)")
      st.markdown(r"其中 $H$ 为教学楼高度，$d$ 为楼间距。此公式表明：**楼越高（$H \uparrow$）、间距越窄（$d \downarrow$），狭管放大效应越强**。")
      st.caption("我们的平台正是将上述代数过程通过代码转化为可视化的3D流线与实时指标卡。")
    st.markdown("### 核心物理模型")
    st.markdown("狭管效应背后的流体力学逻辑：")
    
    st.markdown("**① 连续性方程（质量守恒）**")
    st.latex(r"A_1 V_1 = A_2 V_2")
    st.caption("气流挤进窄缝，面积减小，风速被迫增加。")
    
    st.markdown("**② 伯努利方程（能量守恒）**")
    st.latex(r"P_1 + \frac{1}{2}\rho V_1^2 = P_2 + \frac{1}{2}\rho V_2^2")
    st.caption("风速增加导致动压剧增，静压下降，形成强烈的向外推力。")
    
    st.markdown("**③ 经验放大系数**")
    st.latex(r"V_{gap} = V_\infty \cdot \left(1 + 0.5\sqrt{\frac{H}{d}}\right)")
    st.caption("结合教学楼高度 H 和间距 d 的半经验修正公式。")

# ==================== 核心计算 ====================
rho = 353.0 / (T + 273.15)
amplification = min(1 + 0.5 * np.sqrt(H / d), 3.0)
V_gap = V_inf * amplification
q_inf = 0.5 * rho * V_inf ** 2
q_gap = 0.5 * rho * V_gap ** 2

def wind_level(v):
    levels = [(0.3,"0级 无风"),(1.6,"1级 软风"),(3.4,"2级 轻风"),
              (5.5,"3级 微风"),(8.0,"4级 和风"),(10.8,"5级 清风"),
              (13.9,"6级 强风"),(17.2,"7级 疾风"),(20.8,"8级 大风"),
              (24.5,"9级 烈风"),(28.5,"10级 狂风"),(32.7,"11级 暴风")]
    for limit, name in levels:
        if v < limit:
            return name
    return "12级 台风以上"

# ==================== 实时指标卡 ====================
st.subheader("📊 实时计算结果")
c1, c2, c3, c4 = st.columns(4)
c1.metric("来流风速 V∞", f"{V_inf:.1f} m/s")
c2.metric("狭管风速 V_gap", f"{V_gap:.2f} m/s", delta=f"+{V_gap - V_inf:.2f} m/s")
c3.metric("放大系数", f"{amplification:.2f} ×")
c4.metric("空气密度 ρ", f"{rho:.3f} kg/m³")

c5, c6, c7, c8 = st.columns(4)
c5.metric("来流动压", f"{q_inf:.1f} Pa")
c6.metric("狭管动压", f"{q_gap:.1f} Pa", delta=f"+{q_gap - q_inf:.1f} Pa")
c7.metric("来流风级", wind_level(V_inf))
c8.metric("狭管风级", wind_level(V_gap))

st.markdown("---")

# ==================== 视图切换 ====================
view_mode = st.radio("🎥 视图模式", ["3D 立体视图", "2D 俯视视图"], horizontal=True)

# 公共参数定义
x_build_start = -25.0
x_build_end = x_build_start + w
half_gap = d / 2.0
half_width = w / 2.0

# ==================== 3D 立体视图 ====================
if view_mode == "3D 立体视图":
    st.subheader("3D 立体流场演示（鼠标拖动可旋转）")

    with st.expander("📐 点击展开：流线场“神秘小公式”推导过程", expanded=False):
        st.markdown("采用**分段平滑势流模型**，将流场视作连续介质，任何一点的速度与位置由以下解析式给出：")
        st.latex(r"S(x) = \begin{cases} 0, & x < x_{start} - L \\ 3t^2 - 2t^3, & x_{start} - L \le x \le x_{start} \\ 1, & x_{start} \le x \le x_{end} \\ 3t^2 - 2t^3, & x_{end} \le x \le x_{end} + L \\ 0, & x > x_{end} + L \end{cases}")
        st.markdown("其中 $t = (x - (x_{start}-L))/L$ 为归一化距离，$S(x)$ 为平滑影响因子。")
        st.markdown("**收缩区流线（楼缝内）**：")
        st.latex(r"y(x, y_0) = y_0 \cdot \left(1 - 0.35 S(x)\right)")
        st.markdown("**绕流区流线（撞击楼体）**：")
        st.latex(r"y(x, y_0) = y_0 + \text{sgn}(y_0) \cdot \left[ (y_{target} - |y_0|) \cdot S(x) \right]")
        st.markdown("**速度场叠加（用于颜色设色）**：")
        st.latex(r"V(x, y_0) = V_\infty \cdot \left[ 1 + \left(\frac{V_{gap}}{V_\infty} - 1\right) S_{gap} - 0.3 S_{outer} \right]")
        st.caption("$S(x)$ 为 0→1 的平滑过渡，确保流线在建筑主体内完全绕出，且在建筑前后 20m 内平滑恢复。")

    fig3d = go.Figure()

    def make_box(x0, x1, y0, y1, z0, z1, color, name):
        verts = np.array([
            [x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],
            [x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1],
        ])
        faces = [(0,1,2),(0,2,3),(4,5,6),(4,6,7),(0,1,5),(0,5,4),
                 (1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
        I = [f[0] for f in faces]; J=[f[1] for f in faces]; K=[f[2] for f in faces]
        return go.Mesh3d(x=verts[:,0], y=verts[:,1], z=verts[:,2],
                         i=I, j=J, k=K, color=color, opacity=0.35,
                         name=name, showlegend=True,
                         lighting=dict(ambient=0.6, diffuse=0.8, specular=0.3))

    fig3d.add_trace(make_box(x_build_start, x_build_end, half_gap, half_width, 0, H, "steelblue", "教学楼 A"))
    fig3d.add_trace(make_box(x_build_start, x_build_end, -half_width, -half_gap, 0, H, "steelblue", "教学楼 B"))

    def smoothstep(t):
        t = np.clip(t, 0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)

    n_lines_per_level = 31
    z_levels = [H * 0.2, H * 0.5, H * 0.8]
    transition_len = 20.0

    for z_val in z_levels:
        y_init_range = np.linspace(-half_width * 2.5, half_width * 2.5, n_lines_per_level)
        for y_init in y_init_range:
            x_vals = np.linspace(-70, 130, 120)
            y_vals = np.zeros_like(x_vals)
            speeds = np.zeros_like(x_vals)

            influence = np.ones_like(x_vals)
            mask_front = (x_vals >= x_build_start - transition_len) & (x_vals < x_build_start)
            if mask_front.any():
                t = (x_vals[mask_front] - (x_build_start - transition_len)) / transition_len
                influence[mask_front] = smoothstep(t)
            mask_back = (x_vals > x_build_end) & (x_vals <= x_build_end + transition_len)
            if mask_back.any():
                t = ((x_build_end + transition_len) - x_vals[mask_back]) / transition_len
                influence[mask_back] = smoothstep(t)
            influence[x_vals < x_build_start - transition_len] = 0.0
            influence[x_vals > x_build_end + transition_len] = 0.0

            if abs(y_init) < half_gap:
                y_vals = y_init * (1 - 0.35 * influence)
                speed_ratio = 1 + (V_gap / V_inf - 1) * influence if V_inf > 0 else np.ones_like(x_vals)
            elif abs(y_init) <= half_width:
                normalized_pos = (abs(y_init) - half_gap) / (half_width - half_gap + 1e-6)
                target_abs = half_width + 0.5 + normalized_pos * 2.0
                delta = (target_abs - abs(y_init)) * influence
                y_vals = y_init + np.sign(y_init) * delta
                speed_ratio = 1 - 0.3 * influence
            else:
                ratio = (abs(y_init) - half_width) / half_width
                delta = (half_width * 0.3) * (1 / (1 + ratio**2)) * influence
                y_vals = y_init + np.sign(y_init) * delta
                speed_ratio = 1 - 0.08 * influence

            speeds = V_inf * speed_ratio

            fig3d.add_trace(go.Scatter3d(
                x=x_vals, y=y_vals, z=np.full_like(x_vals, z_val),
                mode="lines",
                line=dict(color=speeds, colorscale="Jet", width=3.5,
                          cmin=0, cmax=max(V_gap, 1)),
                name=f"流线 z={z_val:.0f}m",
                showlegend=False,
                hoverinfo="skip"
            ))

    arrow_x = [x_build_start + (x_build_end - x_build_start) * 0.5]
    fig3d.add_trace(go.Cone(
        x=arrow_x, y=[0], z=[H * 0.5],
        u=[V_gap], v=[0], w=[0],
        colorscale="Reds", sizemode="absolute", sizeref=3,
        anchor="tail", showscale=False, name="狭管加速"))

    xx, yy = np.meshgrid([-70, 130], [-70, 70])
    fig3d.add_trace(go.Surface(
        x=xx, y=yy, z=np.full_like(xx, -0.5),
        colorscale=[[0, "rgba(200, 200, 200, 0.6)"], [1, "rgba(200, 200, 200, 0.6)"]],
        showscale=False, hoverinfo="skip", name="地面"))

    fig3d.update_layout(
        height=700,
        scene=dict(
            xaxis_title="沿气流方向 X (m)",
            yaxis_title="垂直方向 Y (m)",
            zaxis_title="高度 Z (m)",
            aspectmode="manual",
            aspectratio=dict(x=2, y=1.2, z=0.8),
            camera=dict(eye=dict(x=1.6, y=-1.6, z=1.2))
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(x=0.02, y=0.98)
    )

    st.plotly_chart(fig3d, use_container_width=True)
    st.caption("💡 提示：鼠标左键拖动旋转；滚轮缩放；右键平移。线条颜色越红代表风速越快。")
# ==================== 2D 俯视视图 ====================
    st.subheader("2D 俯视流场示意图")
    x_lin = np.linspace(-70, 130, 22)
    y_lin = np.linspace(-70, 70, 16)
    Xg, Yg = np.meshgrid(x_lin, y_lin)
    Ug = np.zeros_like(Xg); Vg_comp = np.zeros_like(Yg)

    for i in range(len(x_lin)):
        for j in range(len(y_lin)):
            xv, yv = x_lin[i], y_lin[j]
            u, v_comp = V_inf, 0.0
            in_building = (x_build_start <= xv <= x_build_end) and (half_gap <= abs(yv) <= half_width)
            if in_building: u = 0.0; v_comp = 0.0
            in_gap = (x_build_start <= xv <= x_build_end) and (abs(yv) < half_gap)
            if in_gap:
                u = V_gap
                if half_gap > 0: v_comp = -0.15 * (yv / half_gap) * V_gap
            if xv > x_build_end and (half_gap <= abs(yv) <= half_width): u = V_inf * 0.35
            Ug[j, i] = u; Vg_comp[j, i] = v_comp

    fig_flow = go.Figure()
    fig_flow.add_shape(type="rect", x0=x_build_start, x1=x_build_end, y0=half_gap, y1=half_width,
                       fillcolor="rgba(70,130,180,0.75)", line=dict(color="navy", width=2))
    fig_flow.add_shape(type="rect", x0=x_build_start, x1=x_build_end, y0=-half_width, y1=-half_gap,
                       fillcolor="rgba(70,130,180,0.75)", line=dict(color="navy", width=2))
    fig_flow.add_annotation(x=(x_build_start+x_build_end)/2, y=(half_gap+half_width)/2, text="教学楼 A", showarrow=False, font=dict(color="white", size=14))
    fig_flow.add_annotation(x=(x_build_start+x_build_end)/2, y=-(half_gap+half_width)/2, text="教学楼 B", showarrow=False, font=dict(color="white", size=14))

    scale = 0.6
    for j in range(len(y_lin)):
        for i in range(len(x_lin)):
            if Ug[j, i] > 0.05:
                fig_flow.add_annotation(x=x_lin[i]+Ug[j,i]*scale, y=y_lin[j]+Vg_comp[j,i]*scale,
                                        ax=x_lin[i], ay=y_lin[j], xref="x", yref="y", axref="x", ayref="y",
                                        showarrow=True, arrowhead=2, arrowsize=0.8, arrowwidth=1, arrowcolor="rgba(200,60,60,0.55)")

    fig_flow.add_shape(type="line", x0=x_build_start, x1=x_build_end, y0=0, y1=0, line=dict(color="red", width=2, dash="dash"))
    fig_flow.update_layout(
        xaxis=dict(title="沿气流方向 x (m)", range=[-70, 130]),
        yaxis=dict(title="垂直气流方向 y (m)", range=[-70, 70], scaleanchor="x", scaleratio=1),
        height=520, margin=dict(l=40, r=40, t=40, b=40), plot_bgcolor="rgba(240,248,255,0.6)", showlegend=False)
    st.plotly_chart(fig_flow, use_container_width=True)

st.markdown("---")

# ==================== 参数扫描图 ====================
st.subheader("📈 定量分析曲线")
colA, colB = st.columns(2)

with colA:
    d_range = np.linspace(1, 40, 80)
    amp_curve = np.minimum(1 + 0.5 * np.sqrt(H / d_range), 3.0)
    fig1 = px.line(x=d_range, y=amp_curve, labels={"x": "建筑间距 d (m)", "y": "放大系数"}, title=f"放大系数随间距变化（H = {H:.0f} m）")
    fig1.add_vline(x=d, line_dash="dash", line_color="red", annotation_text=f"当前 d = {d:.1f} m")
    fig1.update_layout(height=380)
    st.plotly_chart(fig1, use_container_width=True)

with colB:
    H_range = np.linspace(5, 60, 80)
    amp_curve2 = np.minimum(1 + 0.5 * np.sqrt(H_range / d), 3.0)
    fig2 = px.line(x=H_range, y=amp_curve2, labels={"x": "建筑高度 H (m)", "y": "放大系数"}, title=f"放大系数随高度变化（d = {d:.1f} m）")
    fig2.add_vline(x=H, line_dash="dash", line_color="red", annotation_text=f"当前 H = {H:.0f} m")
    fig2.update_layout(height=380)
    st.plotly_chart(fig2, use_container_width=True)

# ---- 图3：风速剖面（沿 y 方向） ----
st.subheader("📉 通道横截面风速剖面")
y_profile = np.linspace(-half_width * 1.5, half_width * 1.5, 200)
speed_profile = np.where(np.abs(y_profile) < half_gap, V_gap, np.where(np.abs(y_profile) <= half_width, 0.0, V_inf))

fig3 = px.area(x=y_profile, y=speed_profile, labels={"x": "横向位置 y (m)", "y": "风速 (m/s)"}, title="通道横截面风速分布（中央为狭管通道）")
fig3.add_vrect(x0=-half_gap, x1=half_gap, fillcolor="rgba(255,200,200,0.35)", annotation_text="狭管通道", annotation_position="top")
fig3.update_layout(height=400)
st.plotly_chart(fig3, use_container_width=True)

# ==================== CSV 导出 ====================
st.markdown("---")
st.subheader("💾 实验数据导出")

export_rows = []
for dd in np.linspace(1, 40, 40):
    amp = min(1 + 0.5 * np.sqrt(H / dd), 3.0)
    vg = V_inf * amp
    qg = 0.5 * rho * vg ** 2
    export_rows.append({
        "来流风速(m/s)": V_inf, "温度(°C)": T, "建筑高度(m)": H, "建筑间距(m)": round(dd, 2),
        "建筑宽度(m)": w, "狭管风速(m/s)": round(vg, 3), "放大系数": round(amp, 3),
        "狭管动压(Pa)": round(qg, 2), "狭管风级": wind_level(vg)})
df_export = pd.DataFrame(export_rows)

st.write("### 数据预览（前 10 行）")
st.write(df_export.head(10).to_html(index=False, classes="table table-striped"), unsafe_allow_html=True)
st.caption("上表显示前 10 行。点击下方按钮下载完整 CSV。")
csv_bytes = df_export.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="📥 下载 CSV 数据表",
    data=csv_bytes,
    file_name=f"狭管效应实验数据_H{H}_d{d}_V{V_inf}.csv",
    mime="text/csv")

# ==================== 教学解读 ====================
st.markdown("---")
st.subheader("📖 结果解读")
colX, colY = st.columns([2, 1])
with colX:
    st.markdown(f"""
    - **来流风速**为 **{V_inf:.1f} m/s**（{wind_level(V_inf)}）。
    - 通道宽度仅 **{d:.1f} m** 时，风速放大为 **{V_gap:.2f} m/s**，放大系数约 **{amplification:.2f} 倍**。
    - 对应风级从 **{wind_level(V_inf)}** 提升到 **{wind_level(V_gap)}**。
    - 动压从 **{q_inf:.1f} Pa** 增加到 **{q_gap:.1f} Pa**，增加约 **{q_gap - q_inf:.1f} Pa**。
    - 温度 **{T:.1f} °C** 对应空气密度 **{rho:.3f} kg/m³**。
    """)
with colY:
    st.info("**结论**：狭管效应会显著放大风速。若要减弱通道强风，可**增大建筑间距 d**，或在通道口设置**导流板、绿化带**。")

st.caption("© 海拉尔第二中学 · 高一（15）班 · 狭管效应探究小组 · 数字化演示平台")