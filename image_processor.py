<<<<<<< HEAD
import sys
import cv2
import numpy as np
from PIL import Image
import os
import math

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QFileDialog, QMessageBox,
    QSizePolicy, QGridLayout, QComboBox, QDoubleSpinBox, QSpinBox,
    QSplitter, QTreeWidget, QTreeWidgetItem, QGroupBox, QFormLayout,
    QSlider, QLineEdit, QAbstractScrollArea
)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import (
    QPixmap, QImage, QFont, QColor, QPalette, QFontDatabase, QIcon, QPainter
)

# ─────────────────────────────────────────────
#  COLOUR PALETTE
# ─────────────────────────────────────────────
C = {
    "bg":       "#0d0f14",
    "panel":    "#13161e",
    "sidebar":  "#10131a",
    "topbar":   "#090b10",
    "card":     "#181b25",
    "border":   "#1e2235",
    "accent":   "#635bff",      # purple-blue accent (like the reference UI)
    "accent2":  "#00c6ff",      # cyan secondary
    "accent3":  "#7b2fff",
    "green":    "#00e5a0",
    "red":      "#ff4a6a",
    "text":     "#dde1f0",
    "muted":    "#4a5070",
    "selected": "#1a1840",
    "hover":    "#1c1f2e",
    "cat_bg":   "#161926",
    "input_bg": "#1a1d2b",
}

STYLE_SHEET = f"""
QMainWindow, QWidget {{
    background-color: {C["bg"]};
    color: {C["text"]};
    font-family: 'Segoe UI', 'Ubuntu', sans-serif;
    font-size: 13px;
}}

/* ── Scrollbars ─────────────────────── */
QScrollBar:vertical {{
    background: {C["panel"]};
    width: 6px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {C["border"]};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {C["accent"]};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: {C["panel"]};
    height: 6px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {C["border"]};
    border-radius: 3px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {C["accent"]};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ── Tree (sidebar) ─────────────────── */
QTreeWidget {{
    background: {C["sidebar"]};
    border: none;
    outline: none;
    color: {C["text"]};
    font-size: 12px;
}}
QTreeWidget::item {{
    padding: 5px 4px;
    border-radius: 4px;
}}
QTreeWidget::item:hover {{
    background: {C["hover"]};
    color: {C["accent2"]};
}}
QTreeWidget::item:selected {{
    background: {C["selected"]};
    color: white;
    border-left: 2px solid {C["accent"]};
}}
QTreeWidget::branch {{
    background: {C["sidebar"]};
}}
QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {{
    image: none;
    border: none;
}}
QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {{
    image: none;
    border: none;
}}

/* ── Buttons ────────────────────────── */
QPushButton {{
    background: {C["card"]};
    color: {C["text"]};
    border: 1px solid {C["border"]};
    border-radius: 6px;
    padding: 7px 18px;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: {C["hover"]};
    border-color: {C["accent"]};
    color: white;
}}
QPushButton:pressed {{
    background: {C["selected"]};
}}
QPushButton#accentBtn {{
    background: {C["accent"]};
    color: white;
    border: none;
}}
QPushButton#accentBtn:hover {{
    background: #7b72ff;
}}
QPushButton#greenBtn {{
    background: #0d2e22;
    color: {C["green"]};
    border: 1px solid #1a4535;
}}
QPushButton#greenBtn:hover {{
    background: #0e3a2b;
    border-color: {C["green"]};
}}
QPushButton#redBtn {{
    background: #2a0d14;
    color: {C["red"]};
    border: 1px solid #4a1525;
}}
QPushButton#redBtn:hover {{
    background: #350e18;
}}

/* ── Spinboxes / inputs ─────────────── */
QDoubleSpinBox, QSpinBox, QLineEdit, QComboBox {{
    background: {C["input_bg"]};
    color: {C["text"]};
    border: 1px solid {C["border"]};
    border-radius: 5px;
    padding: 4px 8px;
    font-size: 12px;
    selection-background-color: {C["accent"]};
}}
QDoubleSpinBox:focus, QSpinBox:focus, QLineEdit:focus {{
    border-color: {C["accent"]};
}}
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
QSpinBox::up-button, QSpinBox::down-button {{
    background: {C["border"]};
    border: none;
    width: 16px;
}}
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover,
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background: {C["accent"]};
}}

/* ── ComboBox ───────────────────────── */
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background: {C["card"]};
    border: 1px solid {C["border"]};
    selection-background-color: {C["accent"]};
    color: {C["text"]};
    outline: none;
}}

/* ── Group box (params panel) ───────── */
QGroupBox {{
    background: {C["card"]};
    border: 1px solid {C["border"]};
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 8px;
    font-size: 11px;
    font-weight: 700;
    color: {C["muted"]};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    top: -5px;
    padding: 0 6px;
    background: {C["card"]};
    color: {C["accent2"]};
    font-size: 10px;
    letter-spacing: 1px;
}}

/* ── Labels ─────────────────────────── */
QLabel#sectionLabel {{
    color: {C["muted"]};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
}}
QLabel#titleLabel {{
    color: {C["accent2"]};
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QLabel#selectedTech {{
    color: {C["accent"]};
    font-size: 12px;
    font-weight: 600;
}}

/* ── Splitter ───────────────────────── */
QSplitter::handle {{
    background: {C["border"]};
    width: 1px;
}}
"""

=======
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import os
import math

>>>>>>> 2dabd6ecc6a2d4835ffb2320c056b617d7a8ce9f
# ─────────────────────────────────────────────
#  TECHNIQUES REGISTRY
# ─────────────────────────────────────────────
TECHNIQUES = {
    "Histogram Processing": [
        "Histogram Processing",
        "Histogram Equalization",
        "Histogram Specification",
    ],
    "Gray Level Transformations": [
        "Linear Transformation",
        "Logarithmic Transformation",
        "Power Law Transformation",
        "Piecewise Linear Transformation",
        "Contrast Stretching",
    ],
    "Image Enhancement": [
        "Point Processing",
        "Image Subtraction",
        "Image Averaging",
    ],
    "Spatial Filtering": [
        "Smoothing Spatial Filters",
        "Sharpening Spatial Filters",
        "Order-Statistic Filters",
        "Gradient Operator",
        "Laplacian Operator",
    ],
    "Edge & Line Detection": [
        "Edge Detection",
        "Line Detection",
        "Point Detection",
        "Canny Edge Detection",
    ],
    "Frequency Domain": [
        "Ideal Low Pass Filtering",
        "Gaussian Low Pass Filtering",
        "Homomorphic Filtering",
    ],
    "Image Segmentation": [
        "Thresholding",
        "Global Thresholding",
        "Otsu's Method",
        "Region Growing",
        "Region Splitting and Merging",
        "Clustering-based Segmentation",
        "Watershed Algorithm",
    ],
    "Morphological Operations": [
        "Erosion",
        "Dilation",
        "Opening",
        "Closing",
        "Thinning",
        "Thickening",
        "Convex Hull",
        "Hit-or-Miss Transform",
        "Hole Filling",
    ],
    "Boundary & Shape": [
        "Edge Linking",
        "Boundary Detection",
        "Polygon Fitting Algorithm",
        "Shape Detection",
    ],
    "Color & Vision": [
        "Gaussian Blurring",
        "Color Conversion",
        "Color Masking",
        "Perspective Transformation",
    ],
    "Live Video & Detection": [
        "ArUco Marker Detection",
        "Motion Detection",
        "Anomaly Detection",
    ],
}

# ─────────────────────────────────────────────
<<<<<<< HEAD
#  PARAMETER DEFINITIONS  (name, type, default, min, max, step)
#  type: "float" | "int" | "int_odd"  (int_odd = must be odd, for kernel sizes)
# ─────────────────────────────────────────────
PARAM_DEFS = {
    "Histogram Specification": [
        ("clip_limit",  "float", 2.0,  0.1, 10.0, 0.1),
        ("grid_size",   "int",   8,    2,   32,   1),
    ],
    "Linear Transformation": [
        ("alpha",  "float", 1.5,  0.1, 5.0,  0.1),
        ("beta",   "int",   30,   -100, 100, 1),
    ],
    "Power Law Transformation": [
        ("gamma1", "float", 0.4,  0.05, 5.0, 0.05),
        ("gamma2", "float", 1.0,  0.05, 5.0, 0.05),
        ("gamma3", "float", 2.5,  0.05, 5.0, 0.05),
    ],
    "Piecewise Linear Transformation": [
        ("r1", "int", 85,  0, 255, 1),
        ("s1", "int", 42,  0, 255, 1),
        ("r2", "int", 170, 0, 255, 1),
        ("s2", "int", 212, 0, 255, 1),
    ],
    "Contrast Stretching": [
        ("min_percentile", "int", 2,  0, 49, 1),
        ("max_percentile", "int", 98, 51, 100, 1),
    ],
    "Point Processing": [
        ("thresh_val", "int", 127, 0, 255, 1),
    ],
    "Image Subtraction": [
        ("blur_k_size", "int_odd", 21, 3, 99, 2),
    ],
    "Image Averaging": [
        ("k1", "int_odd", 5,  3, 99, 2),
        ("k2", "int_odd", 15, 3, 99, 2),
        ("k3", "int_odd", 31, 3, 99, 2),
    ],
    "Smoothing Spatial Filters": [
        ("k_size", "int_odd", 5, 3, 31, 2),
    ],
    "Sharpening Spatial Filters": [
        ("weight_orig", "float", 1.5,  0.5, 3.0, 0.1),
        ("weight_blur", "float", -0.5, -2.0, 0.0, 0.1),
    ],
    "Order-Statistic Filters": [
        ("k_size", "int_odd", 5, 3, 31, 2),
    ],
    "Gradient Operator": [
        ("k_size", "int", 3, 1, 7, 2),
    ],
    "Canny Edge Detection": [
        ("t1", "int", 50,  0, 500, 5),
        ("t2", "int", 150, 0, 500, 5),
        ("t3", "int", 100, 0, 500, 5),
        ("t4", "int", 200, 0, 500, 5),
    ],
    "Line Detection": [
        ("hough_thresh",  "int", 80,  10, 300, 5),
        ("min_line_len",  "int", 50,  5,  300, 5),
        ("max_line_gap",  "int", 10,  0,  100, 1),
    ],
    "Point Detection": [
        ("pt_thresh", "int", 200, 50, 255, 5),
    ],
    "Ideal Low Pass Filtering": [
        ("radius", "int", 30, 1, 200, 1),
    ],
    "Gaussian Low Pass Filtering": [
        ("sigma", "int", 30, 1, 200, 1),
    ],
    "Homomorphic Filtering": [
        ("gammaH", "float", 1.8, 0.5, 5.0, 0.1),
        ("gammaL", "float", 0.5, 0.1, 1.0, 0.1),
        ("c",      "float", 1.0, 0.1, 5.0, 0.1),
        ("D0",     "int",   30,  5,   200, 5),
    ],
    "Thresholding": [
        ("t_val",      "int",     127, 0, 255, 1),
        ("block_size", "int_odd", 11,  3, 99,  2),
        ("c_val",      "int",     2,   0, 20,  1),
    ],
    "Global Thresholding": [
        ("tolerance", "float", 0.5, 0.01, 5.0, 0.01),
    ],
    "Region Growing": [
        ("dilate_iter", "int", 3, 1, 20, 1),
    ],
    "Clustering-based Segmentation": [
        ("K1",       "int", 2,  2, 16, 1),
        ("K2",       "int", 4,  2, 16, 1),
        ("K3",       "int", 8,  2, 16, 1),
        ("attempts", "int", 10, 1, 30, 1),
    ],
    "Watershed Algorithm": [
        ("fg_thresh", "float", 0.7, 0.1, 0.99, 0.01),
    ],
    "Erosion":  [("k_size", "int_odd", 5, 3, 31, 2)],
    "Dilation": [("k_size", "int_odd", 5, 3, 31, 2)],
    "Opening":  [("k_size", "int_odd", 5, 3, 31, 2)],
    "Closing":  [("k_size", "int_odd", 5, 3, 31, 2)],
    "Thinning":  [("thresh_val", "int", 127, 0, 255, 1)],
    "Thickening": [
        ("thresh_val",   "int",     127, 0, 255, 1),
        ("dilate_iters", "int",     2,   1, 20,  1),
    ],
    "Convex Hull":       [("thresh_val", "int", 127, 0, 255, 1)],
    "Hit-or-Miss Transform": [("thresh_val", "int", 127, 0, 255, 1)],
    "Hole Filling":      [("thresh_val", "int", 127, 0, 255, 1)],
    "Edge Linking": [
        ("t1", "int", 50,  0, 500, 5),
        ("t2", "int", 150, 0, 500, 5),
    ],
    "Boundary Detection": [("k_size", "int_odd", 3, 3, 15, 2)],
    "Polygon Fitting Algorithm": [
        ("t1",        "int",   50,   0, 500, 5),
        ("t2",        "int",   150,  0, 500, 5),
        ("min_area",  "int",   100,  10, 5000, 10),
        ("eps_mult",  "float", 0.02, 0.001, 0.2, 0.001),
    ],
    "Shape Detection": [
        ("min_area",  "int",   200,  10, 5000, 10),
        ("eps_mult",  "float", 0.04, 0.001, 0.2, 0.001),
    ],
    "Perspective Transformation": [
        ("margin_pct", "float", 0.15, 0.01, 0.45, 0.01),
    ],
}


# ─────────────────────────────────────────────
#  PROCESSING ENGINE
# ─────────────────────────────────────────────
def process_image(technique, img_bgr, params=None):
    """Returns list of (title, image_bgr) tuples."""
    if params is None:
        params = {}
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    steps = []

    def p(key, default):
        return params.get(key, default)

    # ── Histogram Processing ─────────────────
    if technique == "Histogram Processing":
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Histogram Plot", draw_histogram(hist, "Histogram")))

    elif technique == "Histogram Equalization":
        equ = cv2.equalizeHist(gray)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Histogram Before", draw_histogram(cv2.calcHist([gray],[0],None,[256],[0,256]),"Before")))
        steps.append(("Equalized Image",   cv2.cvtColor(equ, cv2.COLOR_GRAY2BGR)))
        steps.append(("Histogram After",   draw_histogram(cv2.calcHist([equ],[0],None,[256],[0,256]),"After")))

    elif technique == "Histogram Specification":
        clip_limit = p("clip_limit", 2.0)
        gs         = p("grid_size",  8)
        equ  = cv2.equalizeHist(gray)
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(gs, gs))
        clahe_img = clahe.apply(gray)
        steps.append(("Original Grayscale",    cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Equalized (Reference)", cv2.cvtColor(equ,  cv2.COLOR_GRAY2BGR)))
        steps.append((f"CLAHE (clip={clip_limit})", cv2.cvtColor(clahe_img, cv2.COLOR_GRAY2BGR)))
        steps.append(("Result Histogram", draw_histogram(cv2.calcHist([clahe_img],[0],None,[256],[0,256]),"Specified")))

    # ── Gray Level Transformations ───────────
    elif technique == "Linear Transformation":
        alpha = p("alpha", 1.5)
        beta  = p("beta",  30)
        linear = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
        neg    = cv2.bitwise_not(gray)
        steps.append(("Original Grayscale",      cv2.cvtColor(gray,   cv2.COLOR_GRAY2BGR)))
        steps.append((f"Linear (α={alpha}, β={beta})", cv2.cvtColor(linear, cv2.COLOR_GRAY2BGR)))
        steps.append(("Negative Image",           cv2.cvtColor(neg,    cv2.COLOR_GRAY2BGR)))
=======
#  PROCESSING ENGINE (STATIC IMAGES)
# ─────────────────────────────────────────────
def process_image(technique, img_bgr):
    """Returns list of (title, image_bgr) tuples."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    steps = []

    # ── Histogram Processing ─────────────────
    if technique == "Histogram Processing":
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_img = draw_histogram(hist, "Histogram")
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Histogram Plot", hist_img))

    elif technique == "Histogram Equalization":
        equ = cv2.equalizeHist(gray)
        hist_before = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_after = cv2.calcHist([equ], [0], None, [256], [0, 256])
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Histogram Before", draw_histogram(hist_before, "Before")))
        steps.append(("Equalized Image", cv2.cvtColor(equ, cv2.COLOR_GRAY2BGR)))
        steps.append(("Histogram After", draw_histogram(hist_after, "After")))

    elif technique == "Histogram Specification":
        clip_limit = 2.0  # Parameter
        grid_size = (8, 8)  # Parameter
        equ = cv2.equalizeHist(gray)
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)
        clahe_img = clahe.apply(gray)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Equalized (Reference)", cv2.cvtColor(equ, cv2.COLOR_GRAY2BGR)))
        steps.append((f"CLAHE (clip={clip_limit})", cv2.cvtColor(clahe_img, cv2.COLOR_GRAY2BGR)))
        steps.append(("Result Histogram", draw_histogram(cv2.calcHist([clahe_img], [0], None, [256], [0, 256]), "Specified")))

    # ── Gray Level Transformations ───────────
    elif technique == "Linear Transformation":
        alpha = 1.5  # Contrast control (1.0-3.0)
        beta = 30    # Brightness control (0-100)
        linear = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Linear (α={alpha}, β={beta})", cv2.cvtColor(linear, cv2.COLOR_GRAY2BGR)))
        neg = cv2.bitwise_not(gray)
        steps.append(("Negative Image", cv2.cvtColor(neg, cv2.COLOR_GRAY2BGR)))
>>>>>>> 2dabd6ecc6a2d4835ffb2320c056b617d7a8ce9f

    elif technique == "Logarithmic Transformation":
        c = 255 / np.log(1 + np.max(gray))
        log_img = (c * np.log(1 + gray.astype(np.float32))).astype(np.uint8)
<<<<<<< HEAD
        steps.append(("Original Grayscale", cv2.cvtColor(gray,    cv2.COLOR_GRAY2BGR)))
        steps.append(("Log Transformed",    cv2.cvtColor(log_img, cv2.COLOR_GRAY2BGR)))
        steps.append(("Log Histogram",      draw_histogram(cv2.calcHist([log_img],[0],None,[256],[0,256]),"Log")))

    elif technique == "Power Law Transformation":
        gammas = [p("gamma1", 0.4), p("gamma2", 1.0), p("gamma3", 2.5)]
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        for g in gammas:
            out = np.array(255 * (gray/255.0)**g, dtype=np.uint8)
            steps.append((f"Gamma = {g}", cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)))

    elif technique == "Piecewise Linear Transformation":
        r1, s1 = p("r1",85), p("s1",42)
        r2, s2 = p("r2",170), p("s2",212)
        lut = np.zeros(256, dtype=np.uint8)
        for i in range(256):
            if i < r1:   lut[i] = int((s1/r1)*i) if r1>0 else 0
            elif i < r2: lut[i] = int(((s2-s1)/(r2-r1+1e-5))*(i-r1)+s1)
            else:        lut[i] = min(255, int(((255-s2)/(255-r2+1e-5))*(i-r2)+s2))
        pwl = cv2.LUT(gray, lut)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Piecewise Linear",   cv2.cvtColor(pwl,  cv2.COLOR_GRAY2BGR)))
        steps.append(("LUT Curve",          draw_lut(lut)))

    elif technique == "Contrast Stretching":
        mn_p = p("min_percentile", 2)
        mx_p = p("max_percentile", 98)
        mn, mx = np.percentile(gray, mn_p), np.percentile(gray, mx_p)
        stretched = np.clip((gray.astype(np.float32)-mn)/(mx-mn+1e-5)*255,0,255).astype(np.uint8)
        steps.append(("Original Grayscale",     cv2.cvtColor(gray,      cv2.COLOR_GRAY2BGR)))
        steps.append((f"Stretched (p{mn_p}-p{mx_p})", cv2.cvtColor(stretched, cv2.COLOR_GRAY2BGR)))
        steps.append(("Histogram Before", draw_histogram(cv2.calcHist([gray],[0],None,[256],[0,256]),"Before")))
        steps.append(("Histogram After",  draw_histogram(cv2.calcHist([stretched],[0],None,[256],[0,256]),"After")))

    # ── Image Enhancement ────────────────────
    elif technique == "Point Processing":
        tv = p("thresh_val", 127)
        thresh = cv2.threshold(gray, tv, 255, cv2.THRESH_BINARY)[1]
        neg    = cv2.bitwise_not(gray)
        steps.append(("Original Grayscale",   cv2.cvtColor(gray,   cv2.COLOR_GRAY2BGR)))
        steps.append((f"Thresholded (t={tv})", cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)))
        steps.append(("Negative",             cv2.cvtColor(neg,    cv2.COLOR_GRAY2BGR)))

    elif technique == "Image Subtraction":
        k = p("blur_k_size", 21)
        if k % 2 == 0: k += 1
        blurred  = cv2.GaussianBlur(gray, (k,k), 0)
        diff     = cv2.absdiff(gray, blurred)
        enhanced = cv2.add(gray, diff)
        steps.append(("Original Grayscale",        cv2.cvtColor(gray,     cv2.COLOR_GRAY2BGR)))
        steps.append((f"Blurred Ref (k={k})",      cv2.cvtColor(blurred,  cv2.COLOR_GRAY2BGR)))
        steps.append(("Subtracted Result",         cv2.cvtColor(diff,     cv2.COLOR_GRAY2BGR)))
        steps.append(("Enhanced (orig + diff)",    cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)))

    elif technique == "Image Averaging":
        ks = [p("k1",5), p("k2",15), p("k3",31)]
        ks = [k if k%2==1 else k+1 for k in ks]
        avgs = [cv2.GaussianBlur(gray, (k,k), 0) for k in ks]
        result = (sum([gray.astype(np.float32)] + [a.astype(np.float32) for a in avgs]) / 4).astype(np.uint8)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        for a,k in zip(avgs,ks):
            steps.append((f"Blur (k={k})", cv2.cvtColor(a, cv2.COLOR_GRAY2BGR)))
=======
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Log Transformed", cv2.cvtColor(log_img, cv2.COLOR_GRAY2BGR)))
        steps.append(("Log Histogram", draw_histogram(cv2.calcHist([log_img], [0], None, [256], [0, 256]), "Log")))

    elif technique == "Power Law Transformation":
        gammas = [0.4, 1.0, 2.5]  # Parameters
        results = []
        for gamma in gammas:
            g = np.array(255 * (gray / 255.0) ** gamma, dtype=np.uint8)
            results.append((f"Gamma = {gamma}", cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)))
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.extend(results)

    elif technique == "Piecewise Linear Transformation":
        r1, s1 = 85, 42   # Point 1
        r2, s2 = 170, 212 # Point 2
        lut = np.zeros(256, dtype=np.uint8)
        for i in range(256):
            if i < r1:
                lut[i] = int((s1 / r1) * i)
            elif i < r2:
                lut[i] = int(((s2 - s1) / (r2 - r1)) * (i - r1) + s1)
            else:
                lut[i] = min(255, int(((255 - s2) / (255 - r2)) * (i - r2) + s2))
        pwl = cv2.LUT(gray, lut)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Piecewise Linear", cv2.cvtColor(pwl, cv2.COLOR_GRAY2BGR)))
        steps.append(("LUT Curve", draw_lut(lut)))

    elif technique == "Contrast Stretching":
        min_percentile = 2  # Parameter
        max_percentile = 98 # Parameter
        mn, mx = np.percentile(gray, min_percentile), np.percentile(gray, max_percentile)
        stretched = np.clip((gray.astype(np.float32) - mn) / (mx - mn + 1e-5) * 255, 0, 255).astype(np.uint8)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Stretched (p{min_percentile}-p{max_percentile})", cv2.cvtColor(stretched, cv2.COLOR_GRAY2BGR)))
        steps.append(("Histogram Before", draw_histogram(cv2.calcHist([gray], [0], None, [256], [0, 256]), "Before")))
        steps.append(("Histogram After", draw_histogram(cv2.calcHist([stretched], [0], None, [256], [0, 256]), "After")))

    # ── Image Enhancement ────────────────────
    elif technique == "Point Processing":
        thresh_val = 127 # Parameter
        thresh = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)[1]
        neg = cv2.bitwise_not(gray)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Thresholded (t={thresh_val})", cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)))
        steps.append(("Negative", cv2.cvtColor(neg, cv2.COLOR_GRAY2BGR)))

    elif technique == "Image Subtraction":
        k_size = (21, 21) # Blur parameter for background simulation
        blurred = cv2.GaussianBlur(gray, k_size, 0)
        diff = cv2.absdiff(gray, blurred)
        enhanced = cv2.add(gray, diff)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Blurred Ref (k={k_size[0]})", cv2.cvtColor(blurred, cv2.COLOR_GRAY2BGR)))
        steps.append(("Subtracted Result", cv2.cvtColor(diff, cv2.COLOR_GRAY2BGR)))
        steps.append(("Enhanced (orig + diff)", cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)))

    elif technique == "Image Averaging":
        kernels = [(5, 5), (15, 15), (31, 31)] # Parameters
        avg1 = cv2.GaussianBlur(gray, kernels[0], 0)
        avg2 = cv2.GaussianBlur(gray, kernels[1], 0)
        avg3 = cv2.GaussianBlur(gray, kernels[2], 0)
        result = ((gray.astype(np.float32) + avg1 + avg2 + avg3) / 4).astype(np.uint8)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Noisy (k={kernels[0][0]})", cv2.cvtColor(avg1, cv2.COLOR_GRAY2BGR)))
        steps.append((f"More Noisy (k={kernels[1][0]})", cv2.cvtColor(avg2, cv2.COLOR_GRAY2BGR)))
>>>>>>> 2dabd6ecc6a2d4835ffb2320c056b617d7a8ce9f
        steps.append(("Averaged Result", cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)))

    # ── Spatial Filtering ────────────────────
    elif technique == "Smoothing Spatial Filters":
<<<<<<< HEAD
        k = p("k_size", 5)
        if k%2==0: k+=1
        box    = cv2.blur(gray, (k,k))
        gauss  = cv2.GaussianBlur(gray, (k,k), 0)
        median = cv2.medianBlur(gray, k)
        steps.append(("Original Grayscale",        cv2.cvtColor(gray,   cv2.COLOR_GRAY2BGR)))
        steps.append((f"Box Filter ({k}×{k})",     cv2.cvtColor(box,    cv2.COLOR_GRAY2BGR)))
        steps.append((f"Gaussian Filter ({k}×{k})",cv2.cvtColor(gauss,  cv2.COLOR_GRAY2BGR)))
        steps.append((f"Median Filter ({k}×{k})",  cv2.cvtColor(median, cv2.COLOR_GRAY2BGR)))

    elif technique == "Sharpening Spatial Filters":
        wo = p("weight_orig", 1.5)
        wb = p("weight_blur", -0.5)
        k_sharp   = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
        k_unsharp = np.array([[-1,-1,-1],[-1,9,-1],[-1,-1,-1]])
        blurred   = cv2.GaussianBlur(gray,(5,5),0)
        steps.append(("Original Grayscale",        cv2.cvtColor(gray,                                cv2.COLOR_GRAY2BGR)))
        steps.append(("Sharpened (Laplacian)",      cv2.cvtColor(cv2.filter2D(gray,-1,k_sharp),      cv2.COLOR_GRAY2BGR)))
        steps.append(("High Boost Filter",          cv2.cvtColor(cv2.filter2D(gray,-1,k_unsharp),    cv2.COLOR_GRAY2BGR)))
        steps.append((f"Unsharp Masking (w={wo})",  cv2.cvtColor(cv2.addWeighted(gray,wo,blurred,wb,0), cv2.COLOR_GRAY2BGR)))

    elif technique == "Order-Statistic Filters":
        k = p("k_size", 5)
        if k%2==0: k+=1
        kernel = np.ones((k,k), np.uint8)
        steps.append(("Original Grayscale",   cv2.cvtColor(gray,                     cv2.COLOR_GRAY2BGR)))
        steps.append((f"Median Filter (k={k})", cv2.cvtColor(cv2.medianBlur(gray,k), cv2.COLOR_GRAY2BGR)))
        steps.append((f"Min Filter (k={k})",  cv2.cvtColor(cv2.erode(gray,kernel),   cv2.COLOR_GRAY2BGR)))
        steps.append((f"Max Filter (k={k})",  cv2.cvtColor(cv2.dilate(gray,kernel),  cv2.COLOR_GRAY2BGR)))

    elif technique == "Gradient Operator":
        k = p("k_size", 3)
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=k)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=k)
        mag    = np.clip(cv2.magnitude(sobelx,sobely),0,255).astype(np.uint8)
        steps.append(("Original Grayscale", cv2.cvtColor(gray,                        cv2.COLOR_GRAY2BGR)))
        steps.append((f"Sobel X (k={k})",   cv2.cvtColor(cv2.convertScaleAbs(sobelx), cv2.COLOR_GRAY2BGR)))
        steps.append((f"Sobel Y (k={k})",   cv2.cvtColor(cv2.convertScaleAbs(sobely), cv2.COLOR_GRAY2BGR)))
        steps.append(("Gradient Magnitude", cv2.cvtColor(mag,                         cv2.COLOR_GRAY2BGR)))

    elif technique == "Laplacian Operator":
        lap     = cv2.Laplacian(gray, cv2.CV_64F)
        lap_abs = cv2.convertScaleAbs(lap)
        steps.append(("Original Grayscale",    cv2.cvtColor(gray,              cv2.COLOR_GRAY2BGR)))
        steps.append(("Laplacian Response",    cv2.cvtColor(lap_abs,           cv2.COLOR_GRAY2BGR)))
        steps.append(("Sharpened (orig+lap)",  cv2.cvtColor(cv2.add(gray,lap_abs), cv2.COLOR_GRAY2BGR)))

    # ── Edge & Line Detection ────────────────
    elif technique == "Edge Detection":
        sx  = cv2.convertScaleAbs(cv2.Sobel(gray, cv2.CV_64F, 1, 0))
        sy  = cv2.convertScaleAbs(cv2.Sobel(gray, cv2.CV_64F, 0, 1))
        px  = cv2.filter2D(gray,-1,np.array([[-1,0,1],[-1,0,1],[-1,0,1]]))
        py  = cv2.filter2D(gray,-1,np.array([[-1,-1,-1],[0,0,0],[1,1,1]]))
        can = cv2.Canny(gray,100,200)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Sobel X",   cv2.cvtColor(sx,  cv2.COLOR_GRAY2BGR)))
        steps.append(("Sobel Y",   cv2.cvtColor(sy,  cv2.COLOR_GRAY2BGR)))
        steps.append(("Prewitt X", cv2.cvtColor(px,  cv2.COLOR_GRAY2BGR)))
        steps.append(("Prewitt Y", cv2.cvtColor(py,  cv2.COLOR_GRAY2BGR)))
        steps.append(("Canny (100,200)", cv2.cvtColor(can, cv2.COLOR_GRAY2BGR)))

    elif technique == "Canny Edge Detection":
        t1,t2,t3,t4 = p("t1",50),p("t2",150),p("t3",100),p("t4",200)
        blur = cv2.GaussianBlur(gray,(5,5),0)
        steps.append(("Original Grayscale",          cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Gaussian Blurred",            cv2.cvtColor(blur, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Canny (No Blur, {t1},{t2})", cv2.cvtColor(cv2.Canny(gray,t1,t2), cv2.COLOR_GRAY2BGR)))
        steps.append((f"Canny (Blur, {t1},{t2})",   cv2.cvtColor(cv2.Canny(blur,t1,t2), cv2.COLOR_GRAY2BGR)))
        steps.append((f"Canny (Blur, {t3},{t4})",   cv2.cvtColor(cv2.Canny(blur,t3,t4), cv2.COLOR_GRAY2BGR)))

    elif technique == "Line Detection":
        ht  = p("hough_thresh", 80)
        mll = p("min_line_len", 50)
        mlg = p("max_line_gap", 10)
        edges     = cv2.Canny(gray, 50, 150)
        lines_img = cv2.cvtColor(edges.copy(), cv2.COLOR_GRAY2BGR)
        lines = cv2.HoughLinesP(edges,1,np.pi/180, ht, minLineLength=mll, maxLineGap=mlg)
        if lines is not None:
            for l in lines:
                x1,y1,x2,y2 = l[0]
                cv2.line(lines_img,(x1,y1),(x2,y2),(0,255,0),2)
        steps.append(("Original Grayscale", cv2.cvtColor(gray,  cv2.COLOR_GRAY2BGR)))
        steps.append(("Canny Edges",         cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Hough Lines (thresh={ht})", lines_img))

    elif technique == "Point Detection":
        pt = p("pt_thresh", 200)
        kernel   = np.array([[-1,-1,-1],[-1,8,-1],[-1,-1,-1]], dtype=np.float32)
        response = np.clip(cv2.filter2D(gray.astype(np.float32),-1,kernel),0,255).astype(np.uint8)
        _, points = cv2.threshold(response, pt, 255, cv2.THRESH_BINARY)
        disp  = img_bgr.copy()
        for y,x in np.argwhere(points>0)[:500]:
            cv2.circle(disp,(x,y),3,(0,0,255),-1)
        steps.append(("Original Grayscale",  cv2.cvtColor(gray,     cv2.COLOR_GRAY2BGR)))
        steps.append(("Laplacian Response",  cv2.cvtColor(response,  cv2.COLOR_GRAY2BGR)))
        steps.append((f"Points (t>{pt})",    cv2.cvtColor(points,    cv2.COLOR_GRAY2BGR)))
        steps.append(("Points on Original",  disp))

    # ── Frequency Domain ─────────────────────
    elif technique == "Ideal Low Pass Filtering":
        r = p("radius", 30)
        f      = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        mag    = np.log(1+np.abs(fshift))
        mag_n  = (mag/mag.max()*255).astype(np.uint8)
        rows,cols = gray.shape
        mask = np.zeros((rows,cols), np.float32)
        cv2.circle(mask,(cols//2,rows//2), r, 1, -1)
        filtered = np.clip(np.abs(np.fft.ifft2(np.fft.ifftshift(fshift*mask))),0,255).astype(np.uint8)
        steps.append(("Original Grayscale",    cv2.cvtColor(gray,     cv2.COLOR_GRAY2BGR)))
        steps.append(("Magnitude Spectrum",    cv2.cvtColor(mag_n,    cv2.COLOR_GRAY2BGR)))
        steps.append((f"Ideal LPF (r={r})",   draw_mask(mask)))
        steps.append(("Filtered Result",       cv2.cvtColor(filtered, cv2.COLOR_GRAY2BGR)))

    elif technique == "Gaussian Low Pass Filtering":
        sigma = p("sigma", 30)
        f      = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        rows,cols = gray.shape
        x = np.arange(cols)-cols//2
        y = np.arange(rows)-rows//2
        X,Y = np.meshgrid(x,y)
        H = np.exp(-(X**2+Y**2)/(2*sigma**2))
        filtered = np.abs(np.fft.ifft2(np.fft.ifftshift(fshift*H))).astype(np.uint8)
        mag = np.log(1+np.abs(fshift))
        mag_n = (mag/mag.max()*255).astype(np.uint8)
        steps.append(("Original Grayscale",      cv2.cvtColor(gray,     cv2.COLOR_GRAY2BGR)))
        steps.append(("Magnitude Spectrum",      cv2.cvtColor(mag_n,    cv2.COLOR_GRAY2BGR)))
        steps.append((f"Gaussian Mask (σ={sigma})", draw_mask(H)))
        steps.append(("Filtered Result",         cv2.cvtColor(filtered, cv2.COLOR_GRAY2BGR)))

    elif technique == "Homomorphic Filtering":
        gammaH = p("gammaH", 1.8)
        gammaL = p("gammaL", 0.5)
        c      = p("c",      1.0)
        D0     = p("D0",     30)
        img_f  = np.float32(gray)/255.0
        log_img = np.log1p(img_f)
        F      = np.fft.fft2(log_img)
        Fshift = np.fft.fftshift(F)
        rows,cols = gray.shape
        x = np.arange(cols)-cols//2
        y = np.arange(rows)-rows//2
        X,Y = np.meshgrid(x,y)
        D = np.sqrt(X**2+Y**2)
        H = (gammaH-gammaL)*(1-np.exp(-c*(D**2/D0**2)))+gammaL
        filtered = np.real(np.fft.ifft2(np.fft.ifftshift(Fshift*H)))
        out = np.expm1(filtered)
        out = (out-out.min())/(out.max()-out.min()+1e-5)
        out = (out*255).astype(np.uint8)
        steps.append(("Original Grayscale",  cv2.cvtColor(gray,                      cv2.COLOR_GRAY2BGR)))
        steps.append(("Log Domain",          cv2.cvtColor((log_img*255).astype(np.uint8), cv2.COLOR_GRAY2BGR)))
        steps.append(("Homomorphic Filter",  draw_mask(H/H.max())))
        steps.append(("Enhanced Result",     cv2.cvtColor(out,                        cv2.COLOR_GRAY2BGR)))

    # ── Image Segmentation ───────────────────
    elif technique == "Thresholding":
        tv   = p("t_val", 127)
        bs   = p("block_size", 11)
        cv   = p("c_val", 2)
        if bs%2==0: bs+=1
        _, tb = cv2.threshold(gray, tv, 255, cv2.THRESH_BINARY)
        _, ti = cv2.threshold(gray, tv, 255, cv2.THRESH_BINARY_INV)
        ta    = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,bs,cv)
        steps.append(("Original Grayscale",      cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Binary Thresh (t={tv})", cv2.cvtColor(tb,   cv2.COLOR_GRAY2BGR)))
        steps.append(("Inverse Threshold",        cv2.cvtColor(ti,   cv2.COLOR_GRAY2BGR)))
        steps.append((f"Adaptive (bs={bs},c={cv})", cv2.cvtColor(ta, cv2.COLOR_GRAY2BGR)))

    elif technique == "Global Thresholding":
        tol = p("tolerance", 0.5)
        T   = float(gray.mean())
        for _ in range(100):
            g1 = gray[gray>=T]; g2 = gray[gray<T]
            m1 = g1.mean() if len(g1) else 0
            m2 = g2.mean() if len(g2) else 0
            Tn = (m1+m2)/2
            if abs(T-Tn) < tol: break
            T = Tn
        _, tg = cv2.threshold(gray, int(T), 255, cv2.THRESH_BINARY)
        steps.append(("Original Grayscale",   cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Histogram",            draw_histogram(cv2.calcHist([gray],[0],None,[256],[0,256]),f"T={int(T)}")))
        steps.append((f"Global (T={int(T)})", cv2.cvtColor(tg,   cv2.COLOR_GRAY2BGR)))

    elif technique == "Otsu's Method":
        tv, totsu = cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        hist = cv2.calcHist([gray],[0],None,[256],[0,256])
        steps.append(("Original Grayscale",      cv2.cvtColor(gray,  cv2.COLOR_GRAY2BGR)))
        steps.append(("Histogram",               draw_histogram(hist,f"Otsu T={int(tv)}")))
        steps.append((f"Otsu Thresh (T={int(tv)})", cv2.cvtColor(totsu, cv2.COLOR_GRAY2BGR)))

    elif technique == "Region Growing":
        di = p("dilate_iter", 3)
        _, seeds = cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        kernel   = np.ones((3,3),np.uint8)
        grown    = cv2.dilate(seeds, kernel, iterations=di)
        steps.append(("Original Grayscale",       cv2.cvtColor(gray,  cv2.COLOR_GRAY2BGR)))
        steps.append(("Seed Points (Otsu)",       cv2.cvtColor(seeds, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Region Grown (iter={di})", cv2.cvtColor(grown, cv2.COLOR_GRAY2BGR)))

    elif technique == "Region Splitting and Merging":
        h,w   = gray.shape
        display = img_bgr.copy()
        cv2.rectangle(display,(0,0),(w,h),(0,255,0),2)
        cv2.line(display,(w//2,0),(w//2,h),(0,255,0),1)
        cv2.line(display,(0,h//2),(w,h//2),(0,255,0),1)
        merged = cv2.pyrUp(cv2.pyrDown(gray), dstsize=(w,h))
        steps.append(("Original",            img_bgr))
        steps.append(("Split Regions (L1)",  display))
        steps.append(("Merged (Pyramid)",    cv2.cvtColor(merged, cv2.COLOR_GRAY2BGR)))

    elif technique == "Clustering-based Segmentation":
        K1       = p("K1", 2)
        K2       = p("K2", 4)
        K3       = p("K3", 8)
        attempts = p("attempts", 10)
        Z = img_bgr.reshape((-1,3)).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        steps.append(("Original", img_bgr))
        for K in [K1, K2, K3]:
            _, labels, centers = cv2.kmeans(Z, K, None, criteria, attempts, cv2.KMEANS_RANDOM_CENTERS)
            seg = np.uint8(centers)[labels.flatten()].reshape(img_bgr.shape)
            steps.append((f"K-Means (K={K})", seg))

    elif technique == "Watershed Algorithm":
        fgt = p("fg_thresh", 0.7)
        _, thresh = cv2.threshold(gray,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        kernel    = np.ones((3,3),np.uint8)
        sure_bg   = cv2.dilate(thresh, kernel, iterations=3)
        dist      = cv2.distanceTransform(thresh, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist, fgt*dist.max(), 255, 0)
        sure_fg    = np.uint8(sure_fg)
        unknown    = cv2.subtract(sure_bg, sure_fg)
        _, markers = cv2.connectedComponents(sure_fg)
        markers   += 1
        markers[unknown==255] = 0
        result = img_bgr.copy()
        cv2.watershed(result, markers)
        result[markers==-1] = [0,0,255]
        dist_disp = cv2.normalize(dist,None,0,255,cv2.NORM_MINMAX).astype(np.uint8)
        steps.append(("Original",           img_bgr))
        steps.append(("Thresholded",        cv2.cvtColor(thresh,    cv2.COLOR_GRAY2BGR)))
        steps.append(("Sure Foreground",    cv2.cvtColor(sure_fg,   cv2.COLOR_GRAY2BGR)))
        steps.append(("Distance Transform", cv2.cvtColor(dist_disp, cv2.COLOR_GRAY2BGR)))
        steps.append(("Watershed Result",   result))

    # ── Morphological ────────────────────────
    elif technique in ("Erosion","Dilation","Opening","Closing"):
        k = p("k_size", 5)
        if k%2==0: k+=1
        kernel = np.ones((k,k),np.uint8)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        for i in range(1,4):
            if technique=="Erosion":
                out = cv2.erode(gray,kernel,iterations=i)
                lbl = f"Erosion (iter={i})"
            elif technique=="Dilation":
                out = cv2.dilate(gray,kernel,iterations=i)
                lbl = f"Dilation (iter={i})"
            elif technique=="Opening":
                out = cv2.morphologyEx(gray,cv2.MORPH_OPEN,kernel)
                lbl = "Opening"
            else:
                out = cv2.morphologyEx(gray,cv2.MORPH_CLOSE,kernel)
                lbl = "Closing"
            steps.append((lbl, cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)))
            if technique in ("Opening","Closing"):
                break

    elif technique=="Thinning":
        tv = p("thresh_val",127)
        _, binary = cv2.threshold(gray,tv,255,cv2.THRESH_BINARY)
        thinned   = cv2.ximgproc.thinning(binary) if hasattr(cv2,'ximgproc') else cv2.erode(binary,np.ones((3,3),np.uint8),iterations=3)
        steps.append(("Original Binary", cv2.cvtColor(binary,  cv2.COLOR_GRAY2BGR)))
        steps.append(("Thinned",         cv2.cvtColor(thinned, cv2.COLOR_GRAY2BGR)))

    elif technique=="Thickening":
        tv = p("thresh_val",127)
        di = p("dilate_iters",2)
        _, binary = cv2.threshold(gray,tv,255,cv2.THRESH_BINARY)
        thick = cv2.dilate(binary,np.ones((5,5),np.uint8),iterations=di)
        steps.append(("Original Binary",       cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Thickened (i={di})",   cv2.cvtColor(thick,  cv2.COLOR_GRAY2BGR)))

    elif technique=="Convex Hull":
        tv = p("thresh_val",127)
        _, binary = cv2.threshold(gray,tv,255,cv2.THRESH_BINARY)
        contours,_ = cv2.findContours(binary,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        hull_img   = img_bgr.copy()
        for cnt in contours:
            cv2.drawContours(hull_img,[cv2.convexHull(cnt)],-1,(0,255,0),2)
        steps.append(("Original",    img_bgr))
        steps.append(("Binary",      cv2.cvtColor(binary,   cv2.COLOR_GRAY2BGR)))
        steps.append(("Convex Hulls",hull_img))

    elif technique=="Hit-or-Miss Transform":
        tv = p("thresh_val",127)
        _, binary = cv2.threshold(gray,tv,255,cv2.THRESH_BINARY)
        k1 = np.array([[0,1,0],[1,1,1],[0,1,0]],np.uint8)
        k2 = np.array([[1,0,1],[0,0,0],[1,0,1]],np.uint8)
        hit  = cv2.morphologyEx(binary,cv2.MORPH_ERODE,k1)
        miss = cv2.morphologyEx(cv2.bitwise_not(binary),cv2.MORPH_ERODE,k2)
        steps.append(("Original Binary",    cv2.cvtColor(binary,          cv2.COLOR_GRAY2BGR)))
        steps.append(("Hit (K1 Erode)",    cv2.cvtColor(hit,             cv2.COLOR_GRAY2BGR)))
        steps.append(("Miss (K2 Erode)",   cv2.cvtColor(miss,            cv2.COLOR_GRAY2BGR)))
        steps.append(("Hit-or-Miss",       cv2.cvtColor(cv2.bitwise_and(hit,miss), cv2.COLOR_GRAY2BGR)))

    elif technique=="Hole Filling":
        tv = p("thresh_val",127)
        _, binary = cv2.threshold(gray,tv,255,cv2.THRESH_BINARY_INV)
        flood  = binary.copy()
        mask   = np.zeros((binary.shape[0]+2,binary.shape[1]+2),np.uint8)
        cv2.floodFill(flood,mask,(0,0),255)
        result = cv2.bitwise_or(binary, cv2.bitwise_not(flood))
        steps.append(("Original Grayscale", cv2.cvtColor(gray,   cv2.COLOR_GRAY2BGR)))
        steps.append(("Binary (Inverted)",  cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)))
        steps.append(("Flood Border",       cv2.cvtColor(cv2.bitwise_not(flood), cv2.COLOR_GRAY2BGR)))
        steps.append(("Holes Filled",       cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)))

    # ── Boundary & Shape ─────────────────────
    elif technique=="Edge Linking":
        t1,t2 = p("t1",50),p("t2",150)
        edges  = cv2.Canny(gray,t1,t2)
        kernel = np.ones((3,3),np.uint8)
        linked = cv2.erode(cv2.dilate(edges,kernel,iterations=1),kernel,iterations=1)
        steps.append(("Original Grayscale",  cv2.cvtColor(gray,   cv2.COLOR_GRAY2BGR)))
        steps.append((f"Canny ({t1},{t2})", cv2.cvtColor(edges,  cv2.COLOR_GRAY2BGR)))
        steps.append(("Edge Linked (Morph)", cv2.cvtColor(linked, cv2.COLOR_GRAY2BGR)))

    elif technique=="Boundary Detection":
        k = p("k_size",3)
        if k%2==0: k+=1
        kernel     = np.ones((k,k),np.uint8)
        _,binary   = cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        boundary   = cv2.subtract(binary,cv2.erode(binary,kernel))
        contours,_ = cv2.findContours(boundary,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        cnt_img    = img_bgr.copy()
        cv2.drawContours(cnt_img,contours,-1,(0,255,0),2)
        steps.append(("Original",        img_bgr))
        steps.append(("Binary",          cv2.cvtColor(binary,   cv2.COLOR_GRAY2BGR)))
        steps.append(("Boundary",        cv2.cvtColor(boundary, cv2.COLOR_GRAY2BGR)))
        steps.append(("Contours Drawn",  cnt_img))

    elif technique=="Polygon Fitting Algorithm":
        t1,t2    = p("t1",50),p("t2",150)
        min_area = p("min_area",100)
        eps_mult = p("eps_mult",0.02)
        edges    = cv2.Canny(gray,t1,t2)
        contours,_ = cv2.findContours(edges,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        poly_img = img_bgr.copy()
        for cnt in contours:
            if cv2.contourArea(cnt)<min_area: continue
            approx = cv2.approxPolyDP(cnt, eps_mult*cv2.arcLength(cnt,True), True)
            cv2.drawContours(poly_img,[approx],-1,(0,255,0),2)
        steps.append(("Original",            img_bgr))
        steps.append(("Edges",               cv2.cvtColor(edges,    cv2.COLOR_GRAY2BGR)))
        steps.append((f"Polygon (eps={eps_mult})", poly_img))

    elif technique=="Shape Detection":
        min_area = p("min_area",200)
        eps_mult = p("eps_mult",0.04)
        edges    = cv2.Canny(gray,50,150)
        contours,_ = cv2.findContours(edges,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        shape_img  = img_bgr.copy()
        for cnt in contours:
            if cv2.contourArea(cnt)<min_area: continue
            approx = cv2.approxPolyDP(cnt, eps_mult*cv2.arcLength(cnt,True), True)
            n = len(approx)
            shape = "Triangle" if n==3 else "Rectangle" if n==4 else "Circle" if n>8 else f"Poly({n})"
            color = (0,255,0) if n==3 else (255,0,0) if n==4 else (0,0,255) if n>8 else (255,255,0)
            M = cv2.moments(cnt)
            if M["m00"]!=0:
                cx,cy = int(M["m10"]/M["m00"]),int(M["m01"]/M["m00"])
                cv2.putText(shape_img,shape,(cx-20,cy),cv2.FONT_HERSHEY_SIMPLEX,0.5,color,2)
            cv2.drawContours(shape_img,[approx],-1,color,2)
        steps.append(("Original",        img_bgr))
        steps.append(("Edges",           cv2.cvtColor(edges,     cv2.COLOR_GRAY2BGR)))
        steps.append(("Shapes Detected", shape_img))

    # ── Color & Vision ───────────────────────
    elif technique=="Gaussian Blurring":
        steps.append(("Original",             img_bgr))
        steps.append(("Blur (5×5)",  cv2.GaussianBlur(img_bgr,(5,5),0)))
        steps.append(("Blur (15×15)",cv2.GaussianBlur(img_bgr,(15,15),0)))
        steps.append(("Blur (31×31)",cv2.GaussianBlur(img_bgr,(31,31),0)))

    elif technique=="Color Conversion":
        steps.append(("Original BGR",  img_bgr))
        steps.append(("Grayscale",     cv2.cvtColor(gray,cv2.COLOR_GRAY2BGR)))
        steps.append(("HSV Space",     cv2.cvtColor(img_bgr,cv2.COLOR_BGR2HSV)))
        steps.append(("LAB Space",     cv2.cvtColor(img_bgr,cv2.COLOR_BGR2LAB)))
        steps.append(("YCrCb Space",   cv2.cvtColor(img_bgr,cv2.COLOR_BGR2YCrCb)))

    elif technique=="Color Masking":
        hsv = cv2.cvtColor(img_bgr,cv2.COLOR_BGR2HSV)
        red_mask   = cv2.bitwise_or(
            cv2.inRange(hsv,np.array([0,70,70]),np.array([10,255,255])),
            cv2.inRange(hsv,np.array([170,70,70]),np.array([180,255,255])))
        green_mask = cv2.inRange(hsv,np.array([40,40,40]),np.array([80,255,255]))
        blue_mask  = cv2.inRange(hsv,np.array([100,40,40]),np.array([130,255,255]))
        steps.append(("Original",    img_bgr))
        steps.append(("HSV",         hsv))
        steps.append(("Red Mask",    cv2.bitwise_and(img_bgr,img_bgr,mask=red_mask)))
        steps.append(("Green Mask",  cv2.bitwise_and(img_bgr,img_bgr,mask=green_mask)))
        steps.append(("Blue Mask",   cv2.bitwise_and(img_bgr,img_bgr,mask=blue_mask)))

    elif technique=="Perspective Transformation":
        mp  = p("margin_pct",0.15)
        h,w = img_bgr.shape[:2]
        m   = int(min(h,w)*mp)
        src = np.float32([[m,m],[w-m,m],[w-m,h-m],[m,h-m]])
        dst = np.float32([[0,0],[w,0],[w,h],[0,h]])
        M   = cv2.getPerspectiveTransform(src,dst)
        warped = cv2.warpPerspective(img_bgr,M,(w,h))
        disp   = img_bgr.copy()
        for pt in src.astype(int): cv2.circle(disp,tuple(pt),8,(0,0,255),-1)
        steps.append(("Source Points", disp))
        steps.append(("Warped",        warped))
=======
        k_size = 5 # Parameter
        box = cv2.blur(gray, (k_size, k_size))
        gauss = cv2.GaussianBlur(gray, (k_size, k_size), 0)
        median = cv2.medianBlur(gray, k_size)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Box Filter ({k_size}x{k_size})", cv2.cvtColor(box, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Gaussian Filter ({k_size}x{k_size})", cv2.cvtColor(gauss, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Median Filter ({k_size}x{k_size})", cv2.cvtColor(median, cv2.COLOR_GRAY2BGR)))

    elif technique == "Sharpening Spatial Filters":
        weight_orig = 1.5 # Parameter for unsharp mask
        weight_blur = -0.5
        kernel_sharp = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        kernel_unsharp = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharp = cv2.filter2D(gray, -1, kernel_sharp)
        unsharp = cv2.filter2D(gray, -1, kernel_unsharp)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        usm = cv2.addWeighted(gray, weight_orig, blurred, weight_blur, 0)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Sharpened (Laplacian Mask)", cv2.cvtColor(sharp, cv2.COLOR_GRAY2BGR)))
        steps.append(("High Boost Filter", cv2.cvtColor(unsharp, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Unsharp Masking (w={weight_orig})", cv2.cvtColor(usm, cv2.COLOR_GRAY2BGR)))

    elif technique == "Order-Statistic Filters":
        k_size = 5 # Parameter
        median = cv2.medianBlur(gray, k_size)
        kernel = np.ones((k_size, k_size), np.uint8)
        min_f = cv2.erode(gray, kernel)
        max_f = cv2.dilate(gray, kernel)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Median Filter (k={k_size})", cv2.cvtColor(median, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Min Filter (k={k_size})", cv2.cvtColor(min_f, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Max Filter (k={k_size})", cv2.cvtColor(max_f, cv2.COLOR_GRAY2BGR)))

    elif technique == "Gradient Operator":
        k_size = 3 # Parameter
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=k_size)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=k_size)
        mag = cv2.magnitude(sobelx, sobely)
        mag = np.clip(mag, 0, 255).astype(np.uint8)
        sx = cv2.convertScaleAbs(sobelx)
        sy = cv2.convertScaleAbs(sobely)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Sobel X (k={k_size})", cv2.cvtColor(sx, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Sobel Y (k={k_size})", cv2.cvtColor(sy, cv2.COLOR_GRAY2BGR)))
        steps.append(("Gradient Magnitude", cv2.cvtColor(mag, cv2.COLOR_GRAY2BGR)))

    elif technique == "Laplacian Operator":
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        lap_abs = cv2.convertScaleAbs(lap)
        sharpened = cv2.add(gray, lap_abs)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Laplacian Response", cv2.cvtColor(lap_abs, cv2.COLOR_GRAY2BGR)))
        steps.append(("Sharpened (orig + lap)", cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)))

    # ── Edge & Line Detection ────────────────
    elif technique == "Edge Detection":
        sobelx = cv2.convertScaleAbs(cv2.Sobel(gray, cv2.CV_64F, 1, 0))
        sobely = cv2.convertScaleAbs(cv2.Sobel(gray, cv2.CV_64F, 0, 1))
        prewittx = cv2.filter2D(gray, -1, np.array([[-1,0,1],[-1,0,1],[-1,0,1]]))
        prewitty = cv2.filter2D(gray, -1, np.array([[-1,-1,-1],[0,0,0],[1,1,1]]))
        canny = cv2.Canny(gray, 100, 200)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Sobel X", cv2.cvtColor(sobelx, cv2.COLOR_GRAY2BGR)))
        steps.append(("Sobel Y", cv2.cvtColor(sobely, cv2.COLOR_GRAY2BGR)))
        steps.append(("Prewitt X", cv2.cvtColor(prewittx, cv2.COLOR_GRAY2BGR)))
        steps.append(("Prewitt Y", cv2.cvtColor(prewitty, cv2.COLOR_GRAY2BGR)))
        steps.append(("Canny Edge (100,200)", cv2.cvtColor(canny, cv2.COLOR_GRAY2BGR)))

    elif technique == "Canny Edge Detection":
        t1, t2 = 50, 150 # Parameters
        t3, t4 = 100, 200 # Parameters
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        c1 = cv2.Canny(gray, t1, t2)
        c2 = cv2.Canny(blur, t1, t2)
        c3 = cv2.Canny(blur, t3, t4)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Gaussian Blurred", cv2.cvtColor(blur, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Canny (No Blur, t={t1},{t2})", cv2.cvtColor(c1, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Canny (Blur, t={t1},{t2})", cv2.cvtColor(c2, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Canny (Blur, t={t3},{t4})", cv2.cvtColor(c3, cv2.COLOR_GRAY2BGR)))

    elif technique == "Line Detection":
        hough_thresh = 80 # Parameter
        min_line_len = 50 # Parameter
        max_line_gap = 10 # Parameter
        edges = cv2.Canny(gray, 50, 150)
        lines_img = cv2.cvtColor(edges.copy(), cv2.COLOR_GRAY2BGR)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, hough_thresh, minLineLength=min_line_len, maxLineGap=max_line_gap)
        if lines is not None:
            for l in lines:
                x1,y1,x2,y2 = l[0]
                cv2.line(lines_img, (x1,y1), (x2,y2), (0,255,0), 2)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Canny Edges", cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Hough Lines (thresh={hough_thresh})", lines_img))

    elif technique == "Point Detection":
        pt_thresh = 200 # Parameter
        kernel = np.array([[-1,-1,-1],[-1,8,-1],[-1,-1,-1]], dtype=np.float32)
        response = cv2.filter2D(gray.astype(np.float32), -1, kernel)
        response = np.clip(response, 0, 255).astype(np.uint8)
        _, points = cv2.threshold(response, pt_thresh, 255, cv2.THRESH_BINARY)
        disp = img_bgr.copy()
        coords = np.argwhere(points > 0)
        for y, x in coords[:500]:
            cv2.circle(disp, (x, y), 3, (0, 0, 255), -1)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Laplacian Response", cv2.cvtColor(response, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Isolated Points (t>{pt_thresh})", cv2.cvtColor(points, cv2.COLOR_GRAY2BGR)))
        steps.append(("Points on Original", disp))

    # ── Frequency Domain ─────────────────────
    elif technique == "Ideal Low Pass Filtering":
        r = 30 # Radius parameter
        f = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        mag_spectrum = np.log(1 + np.abs(fshift))
        mag_norm = (mag_spectrum / mag_spectrum.max() * 255).astype(np.uint8)

        rows, cols = gray.shape
        crow, ccol = rows//2, cols//2
        mask = np.zeros((rows, cols), np.float32)
        cv2.circle(mask, (ccol, crow), r, 1, -1)
        filtered = np.fft.ifft2(np.fft.ifftshift(fshift * mask))
        filtered = np.clip(np.abs(filtered), 0, 255).astype(np.uint8)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Magnitude Spectrum", cv2.cvtColor(mag_norm, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Ideal LPF Mask (r={r})", draw_mask(mask)))
        steps.append(("Filtered Result", cv2.cvtColor(filtered, cv2.COLOR_GRAY2BGR)))

    elif technique == "Gaussian Low Pass Filtering":
        sigma = 30 # Spread parameter
        f = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        rows, cols = gray.shape
        crow, ccol = rows//2, cols//2
        x = np.arange(cols) - ccol
        y = np.arange(rows) - crow
        X, Y = np.meshgrid(x, y)
        D = np.sqrt(X**2 + Y**2)
        H = np.exp(-D**2 / (2 * sigma**2))
        filtered = np.abs(np.fft.ifft2(np.fft.ifftshift(fshift * H))).astype(np.uint8)
        mag_spectrum = np.log(1 + np.abs(fshift))
        mag_norm = (mag_spectrum / mag_spectrum.max() * 255).astype(np.uint8)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Magnitude Spectrum", cv2.cvtColor(mag_norm, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Gaussian Mask (σ={sigma})", draw_mask(H)))
        steps.append(("Filtered Result", cv2.cvtColor(filtered, cv2.COLOR_GRAY2BGR)))

    elif technique == "Homomorphic Filtering":
        gammaH, gammaL, c, D0 = 1.8, 0.5, 1.0, 30 # Parameters
        img_f = np.float32(gray) / 255.0
        log_img = np.log1p(img_f)
        F = np.fft.fft2(log_img)
        Fshift = np.fft.fftshift(F)
        rows, cols = gray.shape
        crow, ccol = rows//2, cols//2
        x = np.arange(cols) - ccol
        y = np.arange(rows) - crow
        X, Y = np.meshgrid(x, y)
        D = np.sqrt(X**2 + Y**2)
        H = (gammaH - gammaL) * (1 - np.exp(-c * (D**2 / D0**2))) + gammaL
        filtered = np.real(np.fft.ifft2(np.fft.ifftshift(Fshift * H)))
        out = np.expm1(filtered)
        out = (out - out.min()) / (out.max() - out.min() + 1e-5)
        out = (out * 255).astype(np.uint8)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Log Domain", cv2.cvtColor((log_img*255).astype(np.uint8), cv2.COLOR_GRAY2BGR)))
        steps.append(("Homomorphic Filter", draw_mask(H / H.max())))
        steps.append(("Enhanced Result", cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)))

    # ── Image Segmentation ───────────────────
    elif technique == "Thresholding":
        t_val = 127 # Parameter
        block_size = 11 # Parameter for Adaptive
        c_val = 2 # Parameter for Adaptive
        _, t_binary = cv2.threshold(gray, t_val, 255, cv2.THRESH_BINARY)
        _, t_inv = cv2.threshold(gray, t_val, 255, cv2.THRESH_BINARY_INV)
        t_adapt = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         cv2.THRESH_BINARY, block_size, c_val)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Binary Threshold (t={t_val})", cv2.cvtColor(t_binary, cv2.COLOR_GRAY2BGR)))
        steps.append(("Inverse Threshold", cv2.cvtColor(t_inv, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Adaptive (bs={block_size}, c={c_val})", cv2.cvtColor(t_adapt, cv2.COLOR_GRAY2BGR)))

    elif technique == "Global Thresholding":
        tolerance = 0.5 # Parameter
        T = gray.mean()
        for _ in range(100):
            g1 = gray[gray >= T]
            g2 = gray[gray < T]
            m1 = g1.mean() if len(g1) else 0
            m2 = g2.mean() if len(g2) else 0
            T_new = (m1 + m2) / 2
            if abs(T - T_new) < tolerance:
                break
            T = T_new
        _, t_global = cv2.threshold(gray, int(T), 255, cv2.THRESH_BINARY)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Histogram", draw_histogram(cv2.calcHist([gray], [0], None, [256], [0, 256]), f"T={int(T)}")))
        steps.append((f"Iterative Global (T={int(T)})", cv2.cvtColor(t_global, cv2.COLOR_GRAY2BGR)))

    elif technique == "Otsu's Method":
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
        t_val, t_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Histogram", draw_histogram(hist.reshape(-1, 1), f"Otsu T={int(t_val)}")))
        steps.append((f"Otsu Thresholded (T={int(t_val)})", cv2.cvtColor(t_otsu, cv2.COLOR_GRAY2BGR)))

    elif technique == "Region Growing":
        dilate_iter = 3 # Parameter
        _, seeds = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = np.ones((3, 3), np.uint8)
        grown = cv2.dilate(seeds, kernel, iterations=dilate_iter)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Seed Points (Otsu)", cv2.cvtColor(seeds, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Region Grown (iter={dilate_iter})", cv2.cvtColor(grown, cv2.COLOR_GRAY2BGR)))

    elif technique == "Region Splitting and Merging":
        h, w = gray.shape
        h2, w2 = h//2, w//2
        display = img_bgr.copy()
        cv2.rectangle(display, (0,0), (w,h), (0,255,0), 2)
        cv2.line(display, (w2,0), (w2,h), (0,255,0), 1)
        cv2.line(display, (0,h2), (w,h2), (0,255,0), 1)
        merged = cv2.pyrDown(gray)
        merged = cv2.pyrUp(merged, dstsize=(w, h))
        steps.append(("Original", img_bgr))
        steps.append(("Split Regions (Level 1)", display))
        steps.append(("Merged Result (Pyramid)", cv2.cvtColor(merged, cv2.COLOR_GRAY2BGR)))

    elif technique == "Clustering-based Segmentation":
        Z = img_bgr.reshape((-1, 3)).astype(np.float32)
        attempts = 10 # Parameter
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        results_k = []
        for K in [2, 4, 8]: # Parameters
            _, labels, centers = cv2.kmeans(Z, K, None, criteria, attempts, cv2.KMEANS_RANDOM_CENTERS)
            centers = np.uint8(centers)
            segmented = centers[labels.flatten()].reshape(img_bgr.shape)
            results_k.append((f"K-Means (K={K})", segmented))
        steps.append(("Original", img_bgr))
        steps.extend(results_k)

    elif technique == "Watershed Algorithm":
        fg_thresh = 0.7 # Parameter
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        kernel = np.ones((3, 3), np.uint8)
        sure_bg = cv2.dilate(thresh, kernel, iterations=3)
        dist_transform = cv2.distanceTransform(thresh, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist_transform, fg_thresh * dist_transform.max(), 255, 0)
        sure_fg = np.uint8(sure_fg)
        unknown = cv2.subtract(sure_bg, sure_fg)
        _, markers = cv2.connectedComponents(sure_fg)
        markers += 1
        markers[unknown == 255] = 0
        result = img_bgr.copy()
        cv2.watershed(result, markers)
        result[markers == -1] = [0, 0, 255]
        steps.append(("Original", img_bgr))
        steps.append(("Thresholded", cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Sure Foreground (>{fg_thresh} max)", cv2.cvtColor(sure_fg, cv2.COLOR_GRAY2BGR)))
        steps.append(("Distance Transform", cv2.cvtColor(cv2.normalize(dist_transform, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8), cv2.COLOR_GRAY2BGR)))
        steps.append(("Watershed Result", result))

    # ── Morphological Operations ─────────────
    elif technique == "Erosion":
        k_size = 5 # Parameter
        kernel = np.ones((k_size, k_size), np.uint8)
        e1 = cv2.erode(gray, kernel, iterations=1)
        e2 = cv2.erode(gray, kernel, iterations=2)
        e3 = cv2.erode(gray, kernel, iterations=3)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Erosion (iter=1)", cv2.cvtColor(e1, cv2.COLOR_GRAY2BGR)))
        steps.append(("Erosion (iter=2)", cv2.cvtColor(e2, cv2.COLOR_GRAY2BGR)))
        steps.append(("Erosion (iter=3)", cv2.cvtColor(e3, cv2.COLOR_GRAY2BGR)))

    elif technique == "Dilation":
        k_size = 5 # Parameter
        kernel = np.ones((k_size, k_size), np.uint8)
        d1 = cv2.dilate(gray, kernel, iterations=1)
        d2 = cv2.dilate(gray, kernel, iterations=2)
        d3 = cv2.dilate(gray, kernel, iterations=3)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Dilation (iter=1)", cv2.cvtColor(d1, cv2.COLOR_GRAY2BGR)))
        steps.append(("Dilation (iter=2)", cv2.cvtColor(d2, cv2.COLOR_GRAY2BGR)))
        steps.append(("Dilation (iter=3)", cv2.cvtColor(d3, cv2.COLOR_GRAY2BGR)))

    elif technique == "Opening":
        k_size = 5 # Parameter
        kernel = np.ones((k_size, k_size), np.uint8)
        opened = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
        eroded = cv2.erode(gray, kernel)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Step 1: Erosion", cv2.cvtColor(eroded, cv2.COLOR_GRAY2BGR)))
        steps.append(("Step 2: Dilation (Opening)", cv2.cvtColor(opened, cv2.COLOR_GRAY2BGR)))

    elif technique == "Closing":
        k_size = 5 # Parameter
        kernel = np.ones((k_size, k_size), np.uint8)
        closed = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        dilated = cv2.dilate(gray, kernel)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Step 1: Dilation", cv2.cvtColor(dilated, cv2.COLOR_GRAY2BGR)))
        steps.append(("Step 2: Erosion (Closing)", cv2.cvtColor(closed, cv2.COLOR_GRAY2BGR)))

    elif technique == "Thinning":
        thresh_val = 127 # Parameter
        _, binary = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)
        thinned = cv2.ximgproc.thinning(binary) if hasattr(cv2, 'ximgproc') else binary
        if not hasattr(cv2, 'ximgproc'):
            kernel = np.ones((3,3), np.uint8)
            thinned = cv2.erode(binary, kernel, iterations=3)
        steps.append(("Original Binary", cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)))
        steps.append(("Thinned (Skeleton)", cv2.cvtColor(thinned, cv2.COLOR_GRAY2BGR)))

    elif technique == "Thickening":
        thresh_val = 127 # Parameter
        dilate_iters = 2 # Parameter
        _, binary = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)
        kernel = np.ones((5,5), np.uint8)
        thick = cv2.dilate(binary, kernel, iterations=dilate_iters)
        steps.append(("Original Binary", cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Thickened (iters={dilate_iters})", cv2.cvtColor(thick, cv2.COLOR_GRAY2BGR)))

    elif technique == "Convex Hull":
        thresh_val = 127 # Parameter
        _, binary = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        hull_img = img_bgr.copy()
        for cnt in contours:
            hull = cv2.convexHull(cnt)
            cv2.drawContours(hull_img, [hull], -1, (0, 255, 0), 2)
        steps.append(("Original", img_bgr))
        steps.append(("Contours", cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)))
        steps.append(("Convex Hulls", hull_img))

    elif technique == "Hit-or-Miss Transform":
        thresh_val = 127 # Parameter
        _, binary = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)
        kernel1 = np.array([[0,1,0],[1,1,1],[0,1,0]], np.uint8)
        kernel2 = np.array([[1,0,1],[0,0,0],[1,0,1]], np.uint8)
        hit = cv2.morphologyEx(binary, cv2.MORPH_ERODE, kernel1)
        miss = cv2.morphologyEx(cv2.bitwise_not(binary), cv2.MORPH_ERODE, kernel2)
        result = cv2.bitwise_and(hit, miss)
        steps.append(("Original Binary", cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)))
        steps.append(("Hit (Erosion with K1)", cv2.cvtColor(hit, cv2.COLOR_GRAY2BGR)))
        steps.append(("Miss (Comp Erosion K2)", cv2.cvtColor(miss, cv2.COLOR_GRAY2BGR)))
        steps.append(("Hit-or-Miss Result", cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)))

    elif technique == "Hole Filling":
        thresh_val = 127 # Parameter
        _, binary = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY_INV)
        flood = binary.copy()
        mask = np.zeros((binary.shape[0]+2, binary.shape[1]+2), np.uint8)
        cv2.floodFill(flood, mask, (0,0), 255)
        flood_inv = cv2.bitwise_not(flood)
        result = cv2.bitwise_or(binary, flood_inv)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("Binary (Inverted)", cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)))
        steps.append(("Flood Fill from Border", cv2.cvtColor(flood_inv, cv2.COLOR_GRAY2BGR)))
        steps.append(("Holes Filled", cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)))

    # ── Boundary & Shape ─────────────────────
    elif technique == "Edge Linking":
        t1, t2 = 50, 150 # Parameters
        edges = cv2.Canny(gray, t1, t2)
        kernel = np.ones((3,3), np.uint8)
        linked = cv2.dilate(edges, kernel, iterations=1)
        linked = cv2.erode(linked, kernel, iterations=1)
        steps.append(("Original Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Canny Edges ({t1},{t2})", cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)))
        steps.append(("Edge Linked (Morph)", cv2.cvtColor(linked, cv2.COLOR_GRAY2BGR)))

    elif technique == "Boundary Detection":
        k_size = 3 # Parameter
        kernel = np.ones((k_size, k_size), np.uint8)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        eroded = cv2.erode(binary, kernel)
        boundary = cv2.subtract(binary, eroded)
        contours, _ = cv2.findContours(boundary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnt_img = img_bgr.copy()
        cv2.drawContours(cnt_img, contours, -1, (0, 255, 0), 2)
        steps.append(("Original", img_bgr))
        steps.append(("Binary", cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)))
        steps.append(("Boundary (Morph)", cv2.cvtColor(boundary, cv2.COLOR_GRAY2BGR)))
        steps.append(("Contours Drawn", cnt_img))

    elif technique == "Polygon Fitting Algorithm":
        t1, t2 = 50, 150 # Canny Parameters
        min_area = 100 # Parameter
        eps_mult = 0.02 # Parameter
        edges = cv2.Canny(gray, t1, t2)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        poly_img = img_bgr.copy()
        for cnt in contours:
            if cv2.contourArea(cnt) < min_area:
                continue
            epsilon = eps_mult * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            cv2.drawContours(poly_img, [approx], -1, (0, 255, 0), 2)
        steps.append(("Original", img_bgr))
        steps.append(("Edges", cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)))
        steps.append((f"Polygon Fit (eps={eps_mult})", poly_img))

    elif technique == "Shape Detection":
        min_area = 200 # Parameter
        eps_mult = 0.04 # Parameter
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        shape_img = img_bgr.copy()
        for cnt in contours:
            if cv2.contourArea(cnt) < min_area:
                continue
            epsilon = eps_mult * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            n = len(approx)
            if n == 3:
                shape = "Triangle"
                color = (0, 255, 0)
            elif n == 4:
                shape = "Rectangle"
                color = (255, 0, 0)
            elif n > 8:
                shape = "Circle"
                color = (0, 0, 255)
            else:
                shape = f"Poly({n})"
                color = (255, 255, 0)
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"]/M["m00"])
                cy = int(M["m01"]/M["m00"])
                cv2.putText(shape_img, shape, (cx-20, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            cv2.drawContours(shape_img, [approx], -1, color, 2)
        steps.append(("Original", img_bgr))
        steps.append(("Edges", cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)))
        steps.append(("Shapes Detected", shape_img))

    # ── Color & Vision ───────────────────────
    elif technique == "Gaussian Blurring":
        b5 = cv2.GaussianBlur(img_bgr, (5,5), 0)
        b15 = cv2.GaussianBlur(img_bgr, (15,15), 0)
        b31 = cv2.GaussianBlur(img_bgr, (31,31), 0)
        steps.append(("Original", img_bgr))
        steps.append(("Gaussian Blur (5×5)", b5))
        steps.append(("Gaussian Blur (15×15)", b15))
        steps.append(("Gaussian Blur (31×31)", b31))

    elif technique == "Color Conversion":
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
        ycrcb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YCrCb)
        steps.append(("Original BGR", img_bgr))
        steps.append(("Grayscale", cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)))
        steps.append(("HSV Space", hsv))
        steps.append(("LAB Space", lab))
        steps.append(("YCrCb Space", ycrcb))

    elif technique == "Color Masking":
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        mask_r1 = cv2.inRange(hsv, np.array([0,70,70]), np.array([10,255,255]))
        mask_r2 = cv2.inRange(hsv, np.array([170,70,70]), np.array([180,255,255]))
        red_mask = cv2.bitwise_or(mask_r1, mask_r2)
        red_result = cv2.bitwise_and(img_bgr, img_bgr, mask=red_mask)
        green_mask = cv2.inRange(hsv, np.array([40,40,40]), np.array([80,255,255]))
        green_result = cv2.bitwise_and(img_bgr, img_bgr, mask=green_mask)
        blue_mask = cv2.inRange(hsv, np.array([100,40,40]), np.array([130,255,255]))
        blue_result = cv2.bitwise_and(img_bgr, img_bgr, mask=blue_mask)
        steps.append(("Original", img_bgr))
        steps.append(("HSV", hsv))
        steps.append(("Red Mask", red_result))
        steps.append(("Green Mask", green_result))
        steps.append(("Blue Mask", blue_result))

    elif technique == "Perspective Transformation":
        margin_pct = 0.15 # Parameter
        h, w = img_bgr.shape[:2]
        margin = int(min(h, w) * margin_pct)
        src = np.float32([[margin, margin],[w-margin, margin],[w-margin, h-margin],[margin, h-margin]])
        dst = np.float32([[0, 0],[w, 0],[w, h],[0, h]])
        M = cv2.getPerspectiveTransform(src, dst)
        warped = cv2.warpPerspective(img_bgr, M, (w, h))
        src_disp = img_bgr.copy()
        for pt in src.astype(int):
            cv2.circle(src_disp, tuple(pt), 8, (0,0,255), -1)
        steps.append(("Original with Source Points", src_disp))
        steps.append(("Perspective Warped", warped))
>>>>>>> 2dabd6ecc6a2d4835ffb2320c056b617d7a8ce9f

    else:
        steps.append(("Original", img_bgr))
        note = np.zeros_like(img_bgr)
<<<<<<< HEAD
        cv2.putText(note,technique,(20,60),cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,255,255),2)
        cv2.putText(note,"Processing applied",(20,100),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,255,0),2)
=======
        cv2.putText(note, f"{technique}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        cv2.putText(note, "Processing applied", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
>>>>>>> 2dabd6ecc6a2d4835ffb2320c056b617d7a8ce9f
        steps.append((f"{technique} Result", note))

    return steps


# ─────────────────────────────────────────────
#  HELPER DRAW FUNCTIONS
# ─────────────────────────────────────────────
def draw_histogram(hist, title=""):
<<<<<<< HEAD
    h,w = 256,400
    img = np.zeros((h,w,3),np.uint8)+30
    hist_flat = hist.flatten()
    if hist_flat.max()>0:
        hist_norm = (hist_flat/hist_flat.max()*(h-20)).astype(np.int32)
    else:
        hist_norm = hist_flat.astype(np.int32)
    for i in range(256):
        cv2.rectangle(img,(i*(w//256),h-hist_norm[i]),((i+1)*(w//256),h),(100,200,255),-1)
    cv2.putText(img,title,(10,20),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,255),1)
    return img

def draw_lut(lut):
    img = np.zeros((256,256,3),np.uint8)+20
    pts = [(i,int(255-lut[i])) for i in range(256)]
    for i in range(len(pts)-1):
        cv2.line(img,pts[i],pts[i+1],(0,230,255),2)
    return img

def draw_mask(mask):
    m = (mask-mask.min())/(mask.max()-mask.min()+1e-5)
    return cv2.applyColorMap((m*255).astype(np.uint8),cv2.COLORMAP_JET)

def cv_to_qpixmap(img_bgr, max_w, max_h):
    h,w = img_bgr.shape[:2]
    scale = min(max_w/w, max_h/h, 1.0)
    nw,nh = max(1,int(w*scale)), max(1,int(h*scale))
    resized = cv2.resize(img_bgr,(nw,nh),interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    qi  = QImage(rgb.data, rgb.shape[1], rgb.shape[0], rgb.strides[0], QImage.Format_RGB888)
    return QPixmap.fromImage(qi)


# ─────────────────────────────────────────────
#  PARAMETER PANEL
# ─────────────────────────────────────────────
class ParamPanel(QWidget):
    """Shows editable spinboxes for the selected technique's parameters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QFormLayout(self)
        self._layout.setContentsMargins(12, 16, 12, 12)
        self._layout.setSpacing(8)
        self._layout.setLabelAlignment(Qt.AlignLeft)
        self._widgets = {}  # name -> spinbox widget

    def load(self, technique: str):
        """Rebuild widgets for the given technique."""
        # Clear old
        while self._layout.rowCount() > 0:
            self._layout.removeRow(0)
        self._widgets.clear()

        defs = PARAM_DEFS.get(technique, [])
        if not defs:
            lbl = QLabel("No editable parameters\nfor this technique.")
            lbl.setStyleSheet(f"color: {C['muted']}; font-size: 11px;")
            lbl.setAlignment(Qt.AlignCenter)
            self._layout.addRow(lbl)
            return

        for (name, typ, default, mn, mx, step) in defs:
            label = QLabel(name.replace("_", " "))
            label.setStyleSheet(f"color: {C['text']}; font-size: 11px;")

            if typ == "float":
                w = QDoubleSpinBox()
                w.setRange(mn, mx)
                w.setSingleStep(step)
                w.setValue(default)
                w.setDecimals(3)
            else:  # int or int_odd
                w = QSpinBox()
                w.setRange(mn, mx)
                w.setSingleStep(step)
                w.setValue(default)

            w.setFixedHeight(28)
            w.setToolTip(f"Default: {default}  |  Range: [{mn}, {mx}]")
            self._layout.addRow(label, w)
            self._widgets[name] = w

    def get_params(self) -> dict:
        out = {}
        for name, w in self._widgets.items():
            out[name] = w.value()
        return out


# ─────────────────────────────────────────────
#  OUTPUT CARD WIDGET
# ─────────────────────────────────────────────
class ImageCard(QFrame):
    def __init__(self, title, img_bgr, thumb_size=260, parent=None):
        super().__init__(parent)
        self._img_bgr = img_bgr
        self.setFixedHeight(thumb_size + 80)   
        self.setStyleSheet(f"""
            QFrame {{
                background: {C["card"]};
                border: 1px solid {C["border"]};
                border-radius: 8px;
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8,8,8,8)
        lay.setSpacing(6)

        img_lbl = QLabel()
        pix = cv_to_qpixmap(img_bgr, thumb_size, thumb_size)
        img_lbl.setPixmap(pix)
        img_lbl.setAlignment(Qt.AlignCenter)
        img_lbl.setStyleSheet("border: none;")
        lay.addWidget(img_lbl)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color: {C['accent2']}; font-size: 11px; font-weight: 600; border: none;")
        t_lbl.setAlignment(Qt.AlignCenter)
        t_lbl.setWordWrap(True)
        lay.addWidget(t_lbl)

        save_btn = QPushButton("⬇  Save")
        save_btn.setObjectName("greenBtn")
        save_btn.setFixedHeight(26)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: #0d2820;
                color: {C["green"]};
                border: 1px solid #1a4535;
                border-radius: 5px;
                font-size: 11px; font-weight: 600;
                padding: 0 10px;
            }}
            QPushButton:hover {{ background: #0e3a2b; border-color: {C["green"]}; }}
        """)
        save_btn.clicked.connect(self._save)
        lay.addWidget(save_btn)

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Image", "",
            "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp);;All (*.*)")
        if path:
            cv2.imwrite(path, self._img_bgr)
            QMessageBox.information(self, "Saved", f"Image saved to:\n{path}")


# ─────────────────────────────────────────────
#  MAIN APPLICATION WINDOW
# ─────────────────────────────────────────────
class ImageProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Processing Lab")
        self.resize(1440, 900)
        self.showMaximized()
        self.setStyleSheet(STYLE_SHEET)

        self._img_bgr = None
        self._selected_tech = ""

        self._build_ui()
        # self._params_container = QWidget()
        
    # ── Build UI ────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_lay = QVBoxLayout(central)
        root_lay.setContentsMargins(0,0,0,0)
        root_lay.setSpacing(0)

        # ── Top bar ──────────────────────────
        topbar = QFrame()
        topbar.setFixedHeight(56)
        topbar.setStyleSheet(f"background: {C['topbar']}; border-bottom: 1px solid {C['border']};")
        tb_lay = QHBoxLayout(topbar)
        tb_lay.setContentsMargins(20,0,16,0)
        tb_lay.setSpacing(12)

        logo = QLabel("⬡  IMAGE PROCESSING LAB")
        logo.setObjectName("titleLabel")
        logo.setStyleSheet(f"color: {C['accent2']}; font-size: 15px; font-weight: 700; letter-spacing: 1px;")
        tb_lay.addWidget(logo)
        tb_lay.addStretch()

        # Camera
        cam_lbl = QLabel("Camera:")
        cam_lbl.setStyleSheet(f"color: {C['muted']}; font-size: 11px;")
        tb_lay.addWidget(cam_lbl)
        self._cam_combo = QComboBox()
        self._cam_combo.addItems(["Cam 0","Cam 1","Cam 2"])
        self._cam_combo.setFixedWidth(90)
        self._cam_combo.setCursor(Qt.PointingHandCursor)
        tb_lay.addWidget(self._cam_combo)

        upload_btn = QPushButton("↑  Upload Image")
        upload_btn.setObjectName("greenBtn")
        upload_btn.setCursor(Qt.PointingHandCursor)
        upload_btn.clicked.connect(self._upload_image)
        tb_lay.addWidget(upload_btn)

        process_btn = QPushButton("▶  Process")
        process_btn.setObjectName("accentBtn")
        process_btn.setCursor(Qt.PointingHandCursor)
        process_btn.clicked.connect(self._run_process)
        tb_lay.addWidget(process_btn)

        exit_btn = QPushButton("✕  Exit")
        exit_btn.setObjectName("redBtn")
        exit_btn.setCursor(Qt.PointingHandCursor)
        exit_btn.clicked.connect(self.close)
        tb_lay.addWidget(exit_btn)

        root_lay.addWidget(topbar)

        # ── Main area ────────────────────────
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setHandleWidth(1)
        main_splitter.setStyleSheet(f"QSplitter::handle {{ background: {C['border']}; }}")
        root_lay.addWidget(main_splitter)

        # ─ Sidebar ───────────────────────────
        sidebar_widget = QWidget()
        sidebar_widget.setFixedWidth(268)
        sidebar_widget.setStyleSheet(f"background: {C['sidebar']};")
        sb_lay = QVBoxLayout(sidebar_widget)
        sb_lay.setContentsMargins(0,8,0,0)
        sb_lay.setSpacing(0)

        tech_lbl = QLabel("  TECHNIQUES")
        tech_lbl.setObjectName("sectionLabel")
        tech_lbl.setStyleSheet(f"color: {C['muted']}; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; padding: 4px 14px 8px;")
        sb_lay.addWidget(tech_lbl)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(14)
        self._tree.setAnimated(True)
        self._tree.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        for cat, techs in TECHNIQUES.items():
            cat_item = QTreeWidgetItem([f"  {cat}"])
            cat_item.setFont(0, QFont("Segoe UI", 11, QFont.Bold))
            cat_item.setForeground(0, QColor(C["accent"]))
            self._tree.addTopLevelItem(cat_item)
            for t in techs:
                child = QTreeWidgetItem([f"   {t}"])
                child.setFont(0, QFont("Segoe UI", 11))
                child.setData(0, Qt.UserRole, t)
                cat_item.addChild(child)
            cat_item.setExpanded(True)

        self._tree.itemClicked.connect(self._on_tree_click)
        sb_lay.addWidget(self._tree)
        main_splitter.addWidget(sidebar_widget)

        # ─ Right side ────────────────────────
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.setHandleWidth(1)

        # ─ Top right: input + params side by side ─
        top_right = QWidget()
        top_right.setStyleSheet(f"background: {C['bg']};")
        top_right.setMinimumHeight(300)
        top_right.setMaximumHeight(380)
        tr_lay = QHBoxLayout(top_right)
        tr_lay.setContentsMargins(10,10,10,8)
        tr_lay.setSpacing(10)

        # Input image panel
        input_panel = QFrame()
        input_panel.setStyleSheet(f"""
            QFrame {{
                background: {C["panel"]};
                border: 1px solid {C["border"]};
                border-radius: 10px;
            }}
        """)
        ip_lay = QVBoxLayout(input_panel)
        ip_lay.setContentsMargins(10,8,10,10)
        ip_lay.setSpacing(4)

        input_header = QLabel("INPUT IMAGE")
        input_header.setObjectName("sectionLabel")
        input_header.setStyleSheet(f"color: {C['muted']}; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; border: none;")
        ip_lay.addWidget(input_header)

        self._input_label = QLabel("No image uploaded\n\nClick  ↑ Upload Image  to begin")
        self._input_label.setAlignment(Qt.AlignCenter)
        self._input_label.setStyleSheet(f"color: {C['muted']}; font-size: 12px; border: none;")
        self._input_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        ip_lay.addWidget(self._input_label)
        tr_lay.addWidget(input_panel, stretch=3)

        # Params panel (right of input)
        self._params_container = QWidget()
        self._params_container.setFixedWidth(280)
        self._params_container.setStyleSheet(f"background: {C['bg']};")
        pc_lay = QVBoxLayout(self._params_container)
        pc_lay.setContentsMargins(0,0,0,0)
        pc_lay.setSpacing(8)

        self._tech_name_lbl = QLabel("Select a technique →")
        self._tech_name_lbl.setObjectName("selectedTech")
        self._tech_name_lbl.setStyleSheet(f"color: {C['muted']}; font-size: 12px; font-weight: 600;")
        self._tech_name_lbl.setWordWrap(True)
        pc_lay.addWidget(self._tech_name_lbl)

        self._param_panel = ParamPanel()
        self._param_panel.setMinimumHeight(120)
        scroll_params = QScrollArea()
        scroll_params.setWidget(self._param_panel)
        scroll_params.viewport().setStyleSheet(f"background: {C['bg']};")
        scroll_params.setWidgetResizable(True)
        scroll_params.setWindowFlags(Qt.Widget)
        scroll_params.setStyleSheet(f"background: {C['bg']}; border: none;")
        scroll_params.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        pc_lay.addWidget(scroll_params)

        reset_btn = QPushButton("↺  Reset to Defaults")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C["card"]};
                color: {C["muted"]};
                border: 1px solid {C["border"]};
                border-radius: 5px;
                font-size: 11px;
            }}
            QPushButton:hover {{ color: {C["text"]}; border-color: {C["accent2"]}; }}
        """)
        reset_btn.clicked.connect(self._reset_params)
        pc_lay.addWidget(reset_btn)

        tr_lay.addWidget(self._params_container, stretch=0)
        right_splitter.addWidget(top_right)

        # ─ Bottom right: output grid ─────────
        out_container = QWidget()
        out_container.setStyleSheet(f"background: {C['bg']};")
        oc_lay = QVBoxLayout(out_container)
        oc_lay.setContentsMargins(10,4,10,10)
        oc_lay.setSpacing(4)

        out_header_row = QHBoxLayout()
        self._out_header = QLabel("OUTPUT")
        self._out_header.setObjectName("sectionLabel")
        self._out_header.setStyleSheet(f"color: {C['muted']}; font-size: 10px; font-weight: 700; letter-spacing: 1.5px;")
        out_header_row.addWidget(self._out_header)
        out_header_row.addStretch()
        self._out_count = QLabel("")
        self._out_count.setStyleSheet(f"color: {C['muted']}; font-size: 11px;")
        out_header_row.addWidget(self._out_count)
        oc_lay.addLayout(out_header_row)

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setStyleSheet(f"background: {C['bg']}; border: none;")
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self._output_widget = QWidget()
        self._output_widget.setStyleSheet(f"background: {C['bg']};")
        self._output_layout = QGridLayout(self._output_widget)
        self._output_layout.setContentsMargins(0,0,0,0)
        self._output_layout.setSpacing(12)
        self._scroll_area.setWidget(self._output_widget)
        oc_lay.addWidget(self._scroll_area)

        right_splitter.addWidget(out_container)
        right_splitter.setStretchFactor(0, 0)
        right_splitter.setStretchFactor(1, 1)
        main_splitter.addWidget(right_splitter)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)

    # ── Sidebar interaction ──────────────────
    def _on_tree_click(self, item, col):
        tech = item.data(0, Qt.UserRole)
        if not tech:
            item.setExpanded(not item.isExpanded())
            return
        self._selected_tech = tech
        self._tech_name_lbl.setText(f"⬡  {tech}")
        self._tech_name_lbl.setStyleSheet(f"color: {C['accent']}; font-size: 12px; font-weight: 600;")
        self._param_panel.load(tech)
        self._params_container.show()

    # ── Upload image ────────────────────────
    def _upload_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp);;All (*.*)")
=======
    h, w = 256, 400
    img = np.zeros((h, w, 3), np.uint8) + 30
    hist_flat = hist.flatten()
    if hist_flat.max() > 0:
        hist_norm = (hist_flat / hist_flat.max() * (h - 20)).astype(np.int32)
    else:
        hist_norm = hist_flat.astype(np.int32)
    bin_w = w // 256
    for i in range(256):
        cv2.rectangle(img, (i*bin_w, h-hist_norm[i]), ((i+1)*bin_w, h), (100, 200, 255), -1)
    cv2.putText(img, title, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
    return img

def draw_lut(lut):
    h, w = 256, 256
    img = np.zeros((h, w, 3), np.uint8) + 20
    pts = [(i, int(h - lut[i])) for i in range(256)]
    for i in range(len(pts)-1):
        cv2.line(img, pts[i], pts[i+1], (0, 230, 255), 2)
    cv2.putText(img, "LUT Curve", (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)
    return img

def draw_mask(mask):
    m = (mask - mask.min()) / (mask.max() - mask.min() + 1e-5)
    return cv2.applyColorMap((m * 255).astype(np.uint8), cv2.COLORMAP_JET)


# ─────────────────────────────────────────────
#  GUI APPLICATION
# ─────────────────────────────────────────────
class ImageProcessorApp:
    BG = "#0d0f14"
    PANEL_BG = "#13161e"
    ACCENT = "#00c6ff"
    ACCENT2 = "#7b2fff"
    TEXT = "#e8eaf0"
    MUTED = "#5a5f72"
    BTN_BG = "#1c2030"
    BTN_SEL = "#1a1040"
    CAT_BG = "#1a1d28"

    def __init__(self, root):
        self.root = root
        self.root.title("Image Processing Lab")
        self.root.configure(bg=self.BG)
        self.root.state("zoomed")

        self.img_bgr = None
        self.selected_technique = tk.StringVar(value="")
        self.camera_var = tk.StringVar(value="Cam 0")
        self.output_images = []
        self.photo_refs = []
        self.technique_btns = {}

        self._build_ui()

    def _build_ui(self):
        # Top bar
        topbar = tk.Frame(self.root, bg="#090b10", height=55)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        tk.Label(topbar, text="⬡  IMAGE PROCESSING LAB", font=("Consolas", 15, "bold"),
                 bg="#090b10", fg=self.ACCENT).pack(side="left", padx=20, pady=12)

        btn_style = dict(font=("Consolas", 10, "bold"), bd=0, cursor="hand2", padx=16, pady=8, relief="flat")

        tk.Button(topbar, text="✕  EXIT", bg="#2a0a0a", fg="#ff4a4a",
                  activebackground="#3a1010", activeforeground="#ff6a6a",
                  command=self.root.destroy, **btn_style).pack(side="right", padx=10, pady=8)

        tk.Button(topbar, text="⬡  PROCESS", bg=self.ACCENT2, fg="white",
                  activebackground="#9a4fff",
                  command=self.run_process, **btn_style).pack(side="right", padx=4, pady=8)

        # Camera selection dropdown
        cam_combo = ttk.Combobox(topbar, textvariable=self.camera_var, values=["Cam 0", "Cam 1", "Cam 2"], width=8, state="readonly", font=("Consolas", 10))
        cam_combo.pack(side="right", padx=(2, 15), pady=12)
        tk.Label(topbar, text="Camera:", bg="#090b10", fg="white", font=("Consolas", 10, "bold")).pack(side="right")

        tk.Button(topbar, text="↑  UPLOAD IMAGE", bg="#0a2a1a", fg="#00ffaa",
                  activebackground="#0a3a2a", activeforeground="#00ffcc",
                  command=self.upload_image, **btn_style).pack(side="right", padx=10, pady=8)

        # Main layout
        main = tk.Frame(self.root, bg=self.BG)
        main.pack(fill="both", expand=True)

        # Sidebar
        sidebar_frame = tk.Frame(main, bg=self.PANEL_BG, width=280)
        sidebar_frame.pack(side="left", fill="y")
        sidebar_frame.pack_propagate(False)

        tk.Label(sidebar_frame, text="TECHNIQUES", font=("Consolas", 9, "bold"),
                 bg=self.PANEL_BG, fg=self.MUTED).pack(anchor="w", padx=14, pady=(12,4))

        sb_canvas = tk.Canvas(sidebar_frame, bg=self.PANEL_BG, highlightthickness=0, bd=0)
        sb_scroll = tk.Scrollbar(sidebar_frame, orient="vertical", command=sb_canvas.yview)
        sb_canvas.configure(yscrollcommand=sb_scroll.set)
        sb_scroll.pack(side="right", fill="y")
        sb_canvas.pack(side="left", fill="both", expand=True)

        self.sb_inner = tk.Frame(sb_canvas, bg=self.PANEL_BG)
        sb_window = sb_canvas.create_window((0, 0), window=self.sb_inner, anchor="nw")

        def on_configure(e):
            sb_canvas.configure(scrollregion=sb_canvas.bbox("all"))
            sb_canvas.itemconfig(sb_window, width=sb_canvas.winfo_width())

        self.sb_inner.bind("<Configure>", on_configure)
        sb_canvas.bind("<Configure>", on_configure)
        sb_canvas.bind_all("<MouseWheel>", lambda e: sb_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._populate_sidebar()

        # Right side
        right = tk.Frame(main, bg=self.BG)
        right.pack(side="left", fill="both", expand=True)

        # Input image row
        input_row = tk.Frame(right, bg=self.PANEL_BG, height=350)
        input_row.pack(fill="x", padx=10, pady=(10,0))
        input_row.pack_propagate(False)

        tk.Label(input_row, text="INPUT IMAGE", font=("Consolas", 8, "bold"),
                 bg=self.PANEL_BG, fg=self.MUTED).pack(anchor="w", padx=12, pady=(6,2))

        self.input_label = tk.Label(input_row, bg=self.PANEL_BG,
                                    text="No image uploaded", fg=self.MUTED,
                                    font=("Consolas", 10))
        self.input_label.pack(expand=True)

        self.tech_label = tk.Label(right, text="Select a technique →", font=("Consolas", 9),
                                   bg=self.BG, fg=self.MUTED)
        self.tech_label.pack(anchor="w", padx=14, pady=(8,2))

        # Output scroll area
        out_frame = tk.Frame(right, bg=self.BG)
        out_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))

        self.out_canvas = tk.Canvas(out_frame, bg=self.BG, highlightthickness=0)
        out_scroll_y = tk.Scrollbar(out_frame, orient="vertical", command=self.out_canvas.yview)
        out_scroll_x = tk.Scrollbar(out_frame, orient="horizontal", command=self.out_canvas.xview)
        self.out_canvas.configure(yscrollcommand=out_scroll_y.set, xscrollcommand=out_scroll_x.set)
        out_scroll_x.pack(side="bottom", fill="x")
        out_scroll_y.pack(side="right", fill="y")
        self.out_canvas.pack(side="left", fill="both", expand=True)

        self.out_inner = tk.Frame(self.out_canvas, bg=self.BG)
        self.out_window = self.out_canvas.create_window((0, 0), window=self.out_inner, anchor="nw")

        def out_configure(e):
            self.out_canvas.configure(scrollregion=self.out_canvas.bbox("all"))

        self.out_inner.bind("<Configure>", out_configure)

    def _populate_sidebar(self):
        for cat, techs in TECHNIQUES.items():
            # Section wrapper prevents items falling to the bottom when toggled
            section_frame = tk.Frame(self.sb_inner, bg=self.PANEL_BG)
            section_frame.pack(fill="x", pady=(2, 0))

            cat_frame = tk.Frame(section_frame, bg=self.CAT_BG)
            cat_frame.pack(fill="x", padx=6, pady=(6,0))

            cat_label = tk.Label(cat_frame, text=f"⏷ {cat}", font=("Consolas", 8, "bold"),
                                  bg=self.CAT_BG, fg=self.ACCENT, cursor="hand2", anchor="w")
            cat_label.pack(fill="x", pady=4, padx=5)

            tech_container = tk.Frame(section_frame, bg=self.PANEL_BG)
            tech_container.pack(fill="x", padx=6)

            cat_label.bind("<Button-1>", lambda e, tc=tech_container, cl=cat_label: self._toggle_menu(tc, cl))

            for t in techs:
                btn = tk.Label(tech_container, text=f"  {t}", font=("Consolas", 8),
                               bg=self.PANEL_BG, fg=self.TEXT, cursor="hand2", anchor="w",
                               pady=4)
                btn.pack(fill="x", padx=4)
                btn.bind("<Button-1>", lambda e, name=t, b=btn: self._select_technique(name, b))
                btn.bind("<Enter>", lambda e, b=btn: b.configure(fg=self.ACCENT) if b.cget("fg") != "white" else None)
                btn.bind("<Leave>", lambda e, b=btn, name=t: b.configure(fg=self.TEXT) if self.selected_technique.get() != name else None)
                self.technique_btns[t] = btn

    def _toggle_menu(self, container, label):
        if container.winfo_viewable():
            container.pack_forget()
            label.configure(text=label.cget("text").replace("⏷", "⏵"))
        else:
            container.pack(fill="x", padx=6)
            label.configure(text=label.cget("text").replace("⏵", "⏷"))

    def _select_technique(self, name, btn):
        prev = self.selected_technique.get()
        if prev and prev in self.technique_btns:
            self.technique_btns[prev].configure(bg=self.PANEL_BG, fg=self.TEXT)

        self.selected_technique.set(name)
        btn.configure(bg=self.BTN_SEL, fg="white")
        self.tech_label.configure(text=f"Selected: {name}", fg=self.ACCENT)

    def upload_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp"), ("All", "*.*")]
        )
>>>>>>> 2dabd6ecc6a2d4835ffb2320c056b617d7a8ce9f
        if not path:
            return
        img = cv2.imread(path)
        if img is None:
<<<<<<< HEAD
            QMessageBox.critical(self, "Error", "Could not read the image.")
            return
        self._img_bgr = img
        self._show_input(img)

    def _show_input(self, img):
        w = self._input_label.width() or 600
        h = self._input_label.height() or 280
        pix = cv_to_qpixmap(img, w-20, h-20)
        self._input_label.setPixmap(pix)
        self._input_label.setText("")

    # ── Run process ─────────────────────────
    def _run_process(self):
        tech = self._selected_tech
        if not tech:
            QMessageBox.warning(self, "No Technique", "Please select a processing technique from the sidebar.")
            return

        if tech in ("ArUco Marker Detection","Motion Detection","Anomaly Detection"):
            self._run_video_stream(tech)
            return

        if self._img_bgr is None:
            QMessageBox.warning(self, "No Image", "Please upload an image first.")
            return

        params = self._param_panel.get_params()
        try:
            steps = process_image(tech, self._img_bgr, params)
        except Exception as ex:
            QMessageBox.critical(self, "Processing Error", str(ex))
            return

        self._render_output(steps)

    # ── Render output cards ──────────────────
    def _render_output(self, steps):
        # Clear
        while self._output_layout.count():
            item = self._output_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        THUMB = 270
        avail_w = self._scroll_area.width() or 900
        cols = max(1, avail_w // (THUMB + 20))

        for idx, (title, img) in enumerate(steps):
            card = ImageCard(title, img, thumb_size=THUMB)
            row, col = divmod(idx, cols)
            self._output_layout.addWidget(card, row, col, Qt.AlignTop)
            self._output_layout.setRowStretch(self._output_layout.rowCount(), 1)

        self._out_count.setText(f"{len(steps)} result{'s' if len(steps)!=1 else ''}")
        self._out_header.setStyleSheet(f"color: {C['accent2']}; font-size: 10px; font-weight: 700; letter-spacing: 1.5px;")

    # ── Reset params ─────────────────────────
    def _reset_params(self):
        if self._selected_tech:
            self._param_panel.load(self._selected_tech)

    # ── Video stream ─────────────────────────
    def _run_video_stream(self, technique):
        try:
            cam_idx = int(self._cam_combo.currentText().replace("Cam ",""))
        except ValueError:
            cam_idx = 0
        cap = cv2.VideoCapture(cam_idx)
        if not cap.isOpened():
            QMessageBox.critical(self,"Webcam Error",f"Could not open webcam {cam_idx}.")
            return

        QMessageBox.information(self,"Webcam Activated",f"Starting {technique}.\n\nPress 'q' in the video window to exit.")

        if technique == "ArUco Marker Detection":
            arucoDict   = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
            arucoParams = cv2.aruco.DetectorParameters()
            arucoParams.adaptiveThreshConstant   = 11
            arucoParams.adaptiveThreshWinSizeStep = 1
            arucoParams.adaptiveThreshWinSizeMin  = 4
            detector = cv2.aruco.ArucoDetector(arucoDict, arucoParams)
        elif technique == "Anomaly Detection":
            isFirst = True; firstFrame = None
        elif technique == "Motion Detection":
            isPre = False; preFrame = None

        while True:
            ret, frame = cap.read()
            if not ret: break
            disp = frame.copy()

            if technique == "ArUco Marker Detection":
                gray_f = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                corners, ids, _ = detector.detectMarkers(gray_f)
                if corners and len(corners)>0:
                    for (mc, mid) in zip(corners, ids.flatten()):
                        mc = mc.reshape((4,2))
                        tl,tr,br,bl = mc.astype(int)
                        cv2.line(disp,tuple(tl),tuple(tr),(0,255,0),2)
                        cv2.line(disp,tuple(tr),tuple(br),(0,255,0),2)
                        cv2.line(disp,tuple(br),tuple(bl),(0,255,0),2)
                        cv2.line(disp,tuple(bl),tuple(tl),(0,255,0),2)
                        cv2.putText(disp,f"ID:{mid}",tuple(tl),cv2.FONT_HERSHEY_COMPLEX,0.5,(255,0,255),1)
                cv2.imshow("ArUco (q to stop)", disp)

            elif technique == "Anomaly Detection":
                blur = cv2.GaussianBlur(frame,(15,15),0)
                if isFirst:
                    firstFrame = blur.copy(); isFirst = False
                diff   = cv2.absdiff(firstFrame,blur)
                thresh = cv2.threshold(cv2.cvtColor(diff,cv2.COLOR_BGR2GRAY),30,255,cv2.THRESH_BINARY)[1]
                thresh = cv2.dilate(thresh,None,iterations=1)
                cv2.imshow("Anomaly - Thresh (q to exit)", thresh)
                cv2.imshow("Anomaly - Masked (q to exit)", cv2.bitwise_and(frame,frame,mask=thresh))

            elif technique == "Motion Detection":
                blur = cv2.GaussianBlur(frame,(15,15),0)
                if not isPre:
                    preFrame = blur.copy(); isPre = True
                diff   = cv2.absdiff(preFrame,blur)
                thresh = cv2.threshold(cv2.cvtColor(diff,cv2.COLOR_BGR2GRAY),5,255,cv2.THRESH_BINARY)[1]
                thresh = cv2.dilate(thresh,None,iterations=4)
                preFrame = blur.copy()
                cv2.imshow("Motion - Thresh (q to exit)", thresh)
                cv2.imshow("Motion - Masked (q to exit)", cv2.bitwise_and(frame,frame,mask=thresh))

=======
            messagebox.showerror("Error", "Could not read the image.")
            return
        self.img_bgr = img
        self._show_input(img)

    def _show_input(self, img):
        disp = self._fit_image(img, 800, 330)
        photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(disp, cv2.COLOR_BGR2RGB)))
        self.input_label.configure(image=photo, text="")
        self.input_label.image = photo

    def run_process(self):
        tech = self.selected_technique.get()
        if not tech:
            messagebox.showwarning("No Technique", "Please select a processing technique.")
            return

        # Divert to webcam stream for specific techniques
        if tech in ["ArUco Marker Detection", "Motion Detection", "Anomaly Detection"]:
            self.run_video_stream(tech)
            return

        # Static image processing
        if self.img_bgr is None:
            messagebox.showwarning("No Image", "Please upload an image first for static processing.")
            return

        for w in self.out_inner.winfo_children():
            w.destroy()
        self.photo_refs.clear()
        self.output_images.clear()

        try:
            steps = process_image(tech, self.img_bgr)
        except Exception as ex:
            messagebox.showerror("Processing Error", str(ex))
            return

        self.output_images = steps
        self._render_output(steps)

    def run_video_stream(self, technique):
        cam_idx_str = self.camera_var.get().replace("Cam ", "")
        try:
            cam_idx = int(cam_idx_str)
        except ValueError:
            cam_idx = 0

        cap = cv2.VideoCapture(cam_idx)
        if not cap.isOpened():
            messagebox.showerror("Webcam Error", f"Could not open webcam {cam_idx}.")
            return

        messagebox.showinfo("Webcam Activated", f"Starting {technique}.\n\nPress 'q' on your keyboard while the video window is selected to exit.")
        
        # Initialization based on technique from PDF
        if technique == "ArUco Marker Detection":
            arucoDict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
            arucoParams = cv2.aruco.DetectorParameters()
            # Fine-tuning parameters based on PDF
            arucoParams.adaptiveThreshConstant = 11
            arucoParams.adaptiveThreshWinSizeStep = 1
            arucoParams.adaptiveThreshWinSizeMin = 4
            detector = cv2.aruco.ArucoDetector(arucoDict, arucoParams)
            
        elif technique == "Anomaly Detection":
            isFirstFrame = True
            firstFrame = None
            
        elif technique == "Motion Detection":
            isPreFrame = False
            preFrame = None

        while True:
            ret, frame = cap.read()
            if not ret: 
                break

            display_frame = frame.copy()

            if technique == "ArUco Marker Detection":
                grayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                corners, ids, rejected = detector.detectMarkers(grayFrame)
                
                if corners and len(corners) > 0:
                    ids = ids.flatten()
                    for (markCorner, markID) in zip(corners, ids):
                        markCorner = markCorner.reshape((4, 2))
                        (tl, tr, br, bl) = markCorner
                        
                        # Finding center and orientation as per PDF logic
                        center_coordinate = (tl + tr + br + bl).astype(float) / 4
                        center_coordinate_int = center_coordinate.astype(int)
                        
                        dxdy = tr - tl + br - bl
                        z_rotation = np.arctan2(dxdy[1], dxdy[0]).astype(float)
                        
                        tl = tl.astype(int)
                        tr = tr.astype(int)
                        br = br.astype(int)
                        bl = bl.astype(int)
                        
                        cv2.line(display_frame, tuple(tl), tuple(tr), (0, 255, 0), 2)
                        cv2.line(display_frame, tuple(tr), tuple(br), (0, 255, 0), 2)
                        cv2.line(display_frame, tuple(br), tuple(bl), (0, 255, 0), 2)
                        cv2.line(display_frame, tuple(bl), tuple(tl), (0, 255, 0), 2)
                        
                        cv2.putText(display_frame, f"ID: {str(markID)}", tuple(tl), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 255), 1)

                cv2.imshow("ArUco Detection (Press 'q' to stop)", display_frame)

            elif technique == "Anomaly Detection":
                # PDF: Apply Gaussian blur to reduce noise and details
                imageFrame_blur = cv2.GaussianBlur(frame, (15, 15), 0)
                
                if isFirstFrame:
                    firstFrame = imageFrame_blur.copy()
                    isFirstFrame = False
                
                # PDF: absolute difference between current and first frame
                deff_frame = cv2.absdiff(firstFrame, imageFrame_blur)
                thresh_frame = cv2.cvtColor(deff_frame, cv2.COLOR_BGR2GRAY)
                
                # PDF: binary thresholding
                thresh_frame = cv2.threshold(thresh_frame, 30, 255, cv2.THRESH_BINARY)[1]
                
                # PDF: dilate
                thresh_frame = cv2.dilate(thresh_frame, None, iterations=1)
                
                # PDF: apply threshold mask to original image
                masked = cv2.bitwise_and(frame, frame, mask=thresh_frame)
                
                cv2.imshow("Anomaly - Thresholded (Press 'q' to exit)", thresh_frame)
                cv2.imshow("Anomaly - Masked (Press 'q' to exit)", masked)

            elif technique == "Motion Detection":
                # PDF: Apply Gaussian blur
                imageFrame_blur = cv2.GaussianBlur(frame, (15, 15), 0)
                
                if not isPreFrame:
                    preFrame = imageFrame_blur.copy()
                    isPreFrame = True
                
                # PDF: absolute difference between current and previous frame
                deff_frame = cv2.absdiff(preFrame, imageFrame_blur)
                thresh_frame = cv2.cvtColor(deff_frame, cv2.COLOR_BGR2GRAY)
                
                # PDF: binary thresholding
                thresh_frame = cv2.threshold(thresh_frame, 5, 255, cv2.THRESH_BINARY)[1]
                
                # PDF: dilate
                thresh_frame = cv2.dilate(thresh_frame, None, iterations=4)
                
                # PDF: create mask to extract moving regions
                masked = cv2.bitwise_and(frame, frame, mask=thresh_frame)
                
                # Update previous frame
                preFrame = imageFrame_blur.copy()
                
                cv2.imshow("Motion - Thresholded (Press 'q' to exit)", thresh_frame)
                cv2.imshow("Motion - Masked (Press 'q' to exit)", masked)

            # Wait for 'q' to exit
>>>>>>> 2dabd6ecc6a2d4835ffb2320c056b617d7a8ce9f
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

<<<<<<< HEAD
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-render input preview on resize (guard against early calls before __init__ completes)
        if getattr(self, "_img_bgr", None) is not None:
            self._show_input(self._img_bgr)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(C["bg"]))
    palette.setColor(QPalette.WindowText, QColor(C["text"]))
    palette.setColor(QPalette.Base, QColor(C["input_bg"]))
    palette.setColor(QPalette.AlternateBase, QColor(C["panel"]))
    palette.setColor(QPalette.Text, QColor(C["text"]))
    palette.setColor(QPalette.Button, QColor(C["card"]))
    palette.setColor(QPalette.ButtonText, QColor(C["text"]))
    palette.setColor(QPalette.Highlight, QColor(C["accent"]))
    palette.setColor(QPalette.HighlightedText, QColor("white"))
    app.setPalette(palette)

    win = ImageProcessorApp()
    win.show()
    sys.exit(app.exec_())
=======

    def _render_output(self, steps):
        THUMB = 280
        cols = max(1, self.out_canvas.winfo_width() // (THUMB + 20)) or 3

        for idx, (title, img) in enumerate(steps):
            col = idx % cols
            row = idx // cols

            card = tk.Frame(self.out_inner, bg=self.PANEL_BG, padx=4, pady=4)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="n")

            thumb = self._fit_image(img, THUMB, THUMB)
            photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB)))
            self.photo_refs.append(photo)

            img_lbl = tk.Label(card, image=photo, bg=self.PANEL_BG)
            img_lbl.pack()

            tk.Label(card, text=title, font=("Consolas", 8, "bold"),
                     bg=self.PANEL_BG, fg=self.ACCENT, wraplength=THUMB).pack(pady=(4,2))

            save_btn = tk.Button(card, text="⬇ Save", font=("Consolas", 8),
                                  bg="#0a2a1a", fg="#00ffaa", bd=0, cursor="hand2",
                                  padx=8, pady=3, relief="flat",
                                  command=lambda i=img, t=title: self._save_image(i, t))
            save_btn.pack(pady=(0,4))

    def _save_image(self, img, title):
        safe_title = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in title)
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile=safe_title,
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp"), ("All", "*.*")]
        )
        if path:
            cv2.imwrite(path, img)
            messagebox.showinfo("Saved", f"Image saved to:\n{path}")

    def _fit_image(self, img, max_w, max_h):
        h, w = img.shape[:2]
        scale = min(max_w / w, max_h / h, 1.0)
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        return cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageProcessorApp(root)
    root.mainloop()
>>>>>>> 2dabd6ecc6a2d4835ffb2320c056b617d7a8ce9f
