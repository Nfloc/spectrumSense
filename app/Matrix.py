from config import *
import numpy as np
from colour import XYZ_to_Lab, XYZ_to_sRGB
import datetime, subprocess, json
from scipy.optimize import minimize
from PIL import ImageColor

PATCH_HEX = [
    "#735244", "#c29682", "#627a9d", "#576c43", "#8580b1",
    "#67bdaa", "#d67e2c", "#505ba6", "#c15a63", "#5e3c6c",
    "#9dbc40", "#e0a32e", "#383d96", "#469449", "#af262c",
    "#e7c71f", "#bb5695", "#0885a1", "#ffffff", "#f3f3f3",
    "#c8c8c8", "#a0a0a0", "#7a7a7a", "#555555", "#343434",
    "#000000"
]

# Convert hex → integer RGB tuples
patch_rgb_int = [ ImageColor.getrgb(h) for h in PATCH_HEX ]  # list of (R,G,B) 0–255

def normalize_rows(matrix):
    """L2-normalize rows of a matrix (each spectrum)."""
    return matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-8)

# Load baseline and Macbeth reference XYZ values
with open(BASELINE_RAW_JSON) as f:
    baseline = json.load(f)

with open(MACBETH_D65_PATH) as p:
    macbeth_xyz = json.load(p)

baseline_data = np.array(baseline, dtype=float)
macbeth_xyz = np.array(macbeth_xyz, dtype=float)
baseline_data = normalize_rows(baseline_data)

# === Optimize M using ΔE minimization ===
def deltaE_loss(flat_matrix):
    M = flat_matrix.reshape((3, 8))
    total_loss = 0
    for i in range(26):
        R = baseline_data[i]
        pred_XYZ = M @ R
        ref_XYZ = macbeth_xyz[i]

        # Normalize both predicted and reference XYZ to remove luminance
        pred_XYZ /= (np.sum(pred_XYZ) + 1e-6)
        ref_XYZ /= (np.sum(ref_XYZ) + 1e-6)

        pred_Lab = XYZ_to_Lab(pred_XYZ)
        ref_Lab = XYZ_to_Lab(ref_XYZ)

        deltaE = np.linalg.norm(pred_Lab - ref_Lab)
        total_loss += deltaE

    # === Add Tikhonov (L2) regularization to discourage extreme matrix values ===
    regularization_strength = 1 # You can tune this (start small)
    reg_term = regularization_strength * np.linalg.norm(M)
    total_loss += reg_term
    return total_loss

# Initial M from least-squares
X = macbeth_xyz.T
R = baseline_data.T
M_init = X @ R.T @ np.linalg.inv(R @ R.T)

# Optimize
result = minimize(deltaE_loss, M_init.flatten(), method='L-BFGS-B')
M = result.x.reshape((3, 8))
print("Final ΔE loss:", result.fun)

# === Compute Baseline XYZ Data ===
XYZ_baseline = []
for i in range(26):
    r = np.array(baseline[i], dtype=float)
    r_norm = r / (np.linalg.norm(r) + 1e-8)
    XYZ = M @ r_norm
    XYZ_baseline.append(XYZ.tolist())

with open(XYZ_BASELINE, "w") as f:
    json.dump(XYZ_baseline, f, indent=2)

# === Convert Monitor Data to XYZ ===
with open(MONITOR_RAW_JSON) as f:
    monitor_raw = json.load(f)

XYZ_monitor = []
for i in range(26):
    r = np.array(monitor_raw[i], dtype=float)
    r_norm = r / (np.linalg.norm(r) + 1e-8)
    XYZ = M @ r_norm
    XYZ_monitor.append(XYZ.tolist())

with open(XYZ_MONITOR, "w") as f:
    json.dump(XYZ_monitor, f, indent=2)

# === Compute Correction Matrix ===
XYZ_correction = []

# patches 0–17
for i in range(0, 18):
    delta = np.array(XYZ_monitor[i]) - np.array(XYZ_baseline[i])
    XYZ_correction.append(delta.tolist())

# white anchor at idx 18 → zero correction
XYZ_correction.append([0.0, 0.0, 0.0])

# patches 18–23 now live at monitor idx 19–24
for i in range(19, 25):
    delta = np.array(XYZ_monitor[i]) - np.array(XYZ_baseline[i-1])
    # note: baseline index is i-1, since baseline[18] corresponds to monitor[19]
    XYZ_correction.append(delta.tolist())

# black anchor at idx 25 → zero correction
XYZ_correction.append([0.0, 0.0, 0.0])

with open(COLOR_MATRIX_PATH, "w") as f:
    json.dump(XYZ_correction, f, indent=2)


# === Convert XYZ to sRGB ===
sRGB_list = []
white_patch_Y = XYZ_monitor[18][1]  # normalize relative to white patch
for xyz in XYZ_monitor:
    xyz = np.array(xyz)
    xyz_scaled = xyz / (white_patch_Y + 1e-6)
    rgb = XYZ_to_sRGB(xyz_scaled)
    rgb_clamped = np.clip(rgb, 0, 1)
    sRGB_list.append(rgb_clamped)

    # if np.any(rgb < 0) or np.any(rgb > 1):
    #     print(f"⚠️ Out-of-range RGB: {rgb} from XYZ: {xyz}")

# === Generate TI3 file ===
baseline_Lab = [XYZ_to_Lab(np.array(xyz)) for xyz in XYZ_baseline]

with open(TI3_OUTPUT,"w", newline="\n", encoding="ascii") as f:
    f.write("CTI3\n")
    f.write("DEVICE_CLASS DISPLAY\n")
    f.write("ORIGINATOR \"DIY Colorimeter\"\n")
    f.write("DESCRIPTOR \"Final Monitor ICC Profile\"\n")
    f.write(f"CREATED \"{datetime.datetime.now().isoformat()}\"\n")
    f.write("KEYWORD \"XYZ\"\n")
    f.write("COLOR_REP RGB_LAB\n\n")

    f.write("NUMBER_OF_FIELDS 9\n")
    f.write("NUMBER_OF_SETS 26\n")
    f.write("BEGIN_DATA_FORMAT\n")
    f.write("RGB_R RGB_G RGB_B XYZ_X XYZ_Y XYZ_Z LAB_L LAB_A LAB_B\n")
    f.write("END_DATA_FORMAT\n")
    f.write("BEGIN_DATA\n")

    for (r_int, g_int, b_int), xyz, lab in zip(patch_rgb_int, XYZ_baseline, baseline_Lab):
        # Convert to percent scale 0–100:
        r_pct = round(r_int   / 255 * 100, 2)
        g_pct = round(g_int   / 255 * 100, 2)
        b_pct = round(b_int   / 255 * 100, 2)

        line = (
            f"{r_pct} {g_pct} {b_pct} "
            f"{xyz[0]:.6f} {xyz[1]:.6f} {xyz[2]:.6f} "
            f"{lab[0]:.4f} {lab[1]:.4f} {lab[2]:.4f}\n"
        )
        f.write(line)

    f.write("END_DATA\n")

#Generate ICC profile
if not TI3_OUTPUT.exists():
    raise FileNotFoundError(f"TI3 file not found: {TI3_OUTPUT}")

# Generate unique name using timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
output_name = f"monitor_profile_{timestamp}"

colprof_cmd = [
    "colprof", "-v",
    "-A", "DIYColorimeter",
    "-M", "AS7341",
    "-D", output_name,
    "-C", "MIT",
    "-qm", "-al",
    TI3_OUTPUT.stem
]

print("🛠 Running colprof...")
subprocess.run(colprof_cmd, check=True, cwd=TI3_OUTPUT.parent)

# Move output .icc to models/ with unique name
generated_profile = TI3_OUTPUT.with_suffix(".icm")
new_profile_path = ICC_PROFILE_PATH.parent / f"{output_name}.icc"
generated_profile.rename(new_profile_path)

print(f"✅ ICC profile moved to: {new_profile_path}")