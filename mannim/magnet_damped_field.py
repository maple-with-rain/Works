# 文件: magnet_inside_coil.py
from manim import *
import numpy as np

# ---------- 参数（可调） ----------
L_coil = 4.0           # 线圈总长
R_coil_inner = 0.25    # 线圈内腔半径（磁铁必须小于此）
coil_thickness = 0.08  # 线圈厚度（外半径 = inner + thickness）
m_mag = 0.5            # 磁铁质量 (用于物理量)
k_spring = 20.0        # 弹簧劲度
c_damp = 0.6           # 阻尼系数
A0 = 0.6               # 初始振幅（m）
phi0 = 0.0
z_eq = 0.0             # 平衡位置（线圈中心）
t_total = 8.0
dipole_magnitude = 1.0

# 箭头采样密度（越高越慢）
NX, NY, NZ = 5, 5, 5
ARROW_SCALE = 0.35
MIN_ARROW_LEN = 0.02

# 磁铁几何（必须小于 R_coil_inner）
mag_radius = 0.18
mag_height = 0.5

# ---------- 物理与限制 ----------
omega0 = np.sqrt(k_spring / m_mag)
zeta = c_damp / (2 * np.sqrt(k_spring * m_mag))
if zeta < 1:
    omega_d = omega0 * np.sqrt(1 - zeta**2)
else:
    omega_d = 0.0

# 允许磁铁运动范围（在内腔内沿轴运动）
z_min = - (L_coil/2 - mag_height/2 - 0.02)  # 留点余量防止碰壁
z_max =   (L_coil/2 - mag_height/2 - 0.02)

def z_of_t_raw(t):
    """欠阻尼解析解（不做边界限制）"""
    if zeta < 1:
        return A0 * np.exp(-zeta * omega0 * t) * np.cos(omega_d * t + phi0) + z_eq
    else:
        return A0 * np.exp(-c_damp / (2*m_mag) * t) + z_eq

def z_of_t(t):
    """在边界内强制约束位置，避免穿墙（优先安全性）"""
    zt = z_of_t_raw(t)
    # 如果超出边界，限制到边界（你也可以选择反射或缩小振幅）
    return float(np.clip(zt, z_min, z_max))

# 偶极子近似磁场（用于可视化）
mu0_4pi = 1.0
def dipole_B_field_at_point(r_vec, r0_vec, m_vec):
    r = r_vec - r0_vec
    r_norm = np.linalg.norm(r)
    if r_norm < 1e-6:
        return np.array([0.0, 0.0, 0.0])
    r_hat = r / r_norm
    m_dot_r = np.dot(m_vec, r_hat)
    B = mu0_4pi * (3 * r_hat * m_dot_r / (r_norm**3) - m_vec / (r_norm**3))
    return B

# ---------- Manim Scene ----------
class MagnetInsideCoil(ThreeDScene):
    def construct(self):
        # 坐标轴与相机
        axes = ThreeDAxes(x_range=[-1,1,1], y_range=[-1,1,1],
                          z_range=[-L_coil/2 - 0.5, L_coil/2 + 0.5, 1])
        self.add(axes)
        self.set_camera_orientation(phi=65*DEGREES, theta=-30*DEGREES)

        # 线圈：构造为两个同心圆柱相减得到空心
        coil_outer = Cylinder(radius=R_coil_inner + coil_thickness, height=L_coil,
                              direction=UP, fill_opacity=0.25, color=BLUE)
        coil_inner = Cylinder(radius=R_coil_inner, height=L_coil+0.01, direction=UP,
                              fill_opacity=1.0, color=BLACK)
        coil_inner.move_to([0,0,0])
        coil_outer.move_to([0,0,0])
        # 使用差集（若 manim 版本不支持 BooleanSurface，可直接用透明外壳表示）
        try:
            coil_shell = Difference(coil_outer, coil_inner)
            self.add(coil_shell)
        except Exception:
            # 回退：只添加半透明外壳（视觉上也可行）
            self.add(coil_outer)

        # 弹簧固定端（上端）标记
        fixed_dot = Dot3D(point=[0,0,L_coil/2], radius=0.03, color=GREY)
        fixed_label = Text("弹簧固定端", font_size=20).next_to(fixed_dot, RIGHT)
        self.add(fixed_dot, fixed_label)

        # 磁铁（圆柱），初始放在 z_of_t(0)，并保证在内腔内
        magnet = Cylinder(radius=mag_radius, height=mag_height, direction=UP,
                          color=RED, fill_opacity=0.95)
        z0 = z_of_t(0)
        magnet.move_to([0, 0, z0])
        self.add(magnet)

        # 箭头网格：只在内腔与外部合理位置放置，避免放在线圈实体或磁铁内部
        arrow_meta = []
        xs = np.linspace(- (R_coil_inner + coil_thickness)*1.1, (R_coil_inner + coil_thickness)*1.1, NX)
        ys = np.linspace(- (R_coil_inner + coil_thickness)*1.1, (R_coil_inner + coil_thickness)*1.1, NY)
        zs = np.linspace(-L_coil/2 - 0.2, L_coil/2 + 0.2, NZ)

        for xi in xs:
            for yi in ys:
                # 排除位于线圈实体壁（即 r between inner and outer within thickness region）
                radial = np.hypot(xi, yi)
                # 我们允许箭头位于内腔内（radial < R_coil_inner - small), 或者外部 (radial > R_coil_inner+coil_thickness + small)
                # 但排除恰好在线圈材质区域内
                if R_coil_inner - 0.02 < radial < (R_coil_inner + coil_thickness) + 0.02:
                    continue
                for zi in zs:
                    base = np.array([xi, yi, zi])
                    # 排除在磁铁内部（动态的，注意初始 z0 做近似）
                    if np.linalg.norm(base - np.array([0.0, 0.0, z0])) < max(mag_radius, mag_height/2) + 0.03:
                        continue
                    arrow = Arrow(start=base, end=base + np.array([0.0,0.0,0.0001]), buff=0)
                    self.add(arrow)
                    arrow_meta.append((base, arrow))

        # scene-level updater：只接受 dt
        def scene_update(dt):
            t = self.time
            zt = z_of_t(t)
            # 保证磁铁永远在内腔内（防止用户设置超大 A0）
            zt = float(np.clip(zt, z_min, z_max))
            magnet.move_to([0,0,zt])

            m_vec = np.array([0.0, 0.0, dipole_magnitude])

            for base, arrow in arrow_meta:
                # 如果箭头点位随磁铁接近而进入磁铁内部，则缩短（避免可视化错误）
                if np.linalg.norm(base - np.array([0.0,0.0,zt])) < mag_radius + 0.02:
                    arrow.put_start_and_end_on(base, base + np.array([0.0,0.0,0.0001]))
                    arrow.set_color(GREY)
                    continue
                B = dipole_B_field_at_point(base, np.array([0.0,0.0,zt]), m_vec)
                B_norm = np.linalg.norm(B)
                if B_norm < 1e-6:
                    new_end = base + np.array([0.0,0.0,0.0001])
                else:
                    scale_len = ARROW_SCALE * (B_norm ** (1/3))
                    scale_len = max(scale_len, MIN_ARROW_LEN)
                    vec = (B / B_norm) * scale_len
                    new_end = base + vec
                arrow.put_start_and_end_on(base, new_end)
                cval = np.clip(min(1.0, B_norm/5.0), 0.0, 1.0)
                arrow.set_color(interpolate_color(BLUE, RED, cval))

        # 注册 scene-level updater（保存引用便于移除）
        self.add_updater(scene_update)

        # magnet 的 mobject-updater（可用也可不用，这里用 scene_update 已直接 move_to）
        def magnet_updater(mobj, dt):
            # 直接把位置设定到解析解（确保与 scene_update 一致）
            zt = z_of_t(self.time)
            zt = float(np.clip(zt, z_min, z_max))
            mobj.move_to([0,0,zt])
        magnet.add_updater(magnet_updater)

        # 小提示：把相机做一点慢旋转利于观察
        self.begin_ambient_camera_rotation(rate=0.12)
        self.wait(t_total)

        # 渲染结束前移除 updaters
        self.remove_updater(scene_update)
        magnet.remove_updater(magnet_updater)
