#!/usr/bin/env python3
"""
Image Processing Lab  -  v2
===========================
A PyQt5 + OpenCV playground for classic image-processing techniques.

Requirements:  pip install PyQt5 opencv-python numpy
Run:           python image_lab.py

Architecture
------------
* Every technique is a small function registered with ``@technique(...)``
  together with its parameter definitions.  The sidebar, the parameter panel
  and the dispatcher are all generated from that registry, so adding a new
  technique means writing ONE function - no other code needs to change.
* Processing runs on a worker thread (UI never freezes) and large images are
  downscaled for processing.
* Live-video techniques (ArUco / Motion / Anomaly) use a separate dialog.
"""
from __future__ import annotations

import os
import re
import sys
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import cv2
import numpy as np
from PyQt5.QtCore import QEvent, QSize, Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QImage, QKeySequence, QPalette, QPixmap
from PyQt5.QtWidgets import (
    QAbstractSpinBox, QApplication, QComboBox, QDialog, QDoubleSpinBox, QFileDialog,
    QFormLayout, QFrame, QGraphicsScene, QGraphicsView, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox, QProgressBar,
    QPushButton, QScrollArea, QShortcut, QSizePolicy, QSlider, QSpinBox,
    QSplitter, QStackedWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

MAX_PROC_DIM = 1280      # larger images are downscaled before processing
THUMB = 270              # output card thumbnail size (design pixels, scaled by UI_SCALE)

# ── resolution / DPI awareness ───────────────────────────────────────────────
# Qt's high-DPI scaling (enabled in __main__) makes every pixel value a *logical*
# pixel.  On top of that, UI_SCALE adapts the layout to the screen's logical
# resolution (compact on small laptops, roomier on QHD/4K) and UI_DPR keeps image
# pixmaps sharp on high-DPI screens.  Override with env IMAGE_LAB_SCALE=1.25.
UI_SCALE = 1.0
UI_DPR = 1.0
_PX = re.compile(r"(-?\d+(?:\.\d+)?)px")


def px(n: float) -> int:
    """Design pixels -> scaled logical pixels (never collapses a non-zero size to 0)."""
    v = round(n * UI_SCALE)
    return max(1, v) if n > 0 else int(v)


def scale_css(css: str) -> str:
    """Scale every ``NNpx`` in a style sheet by UI_SCALE."""
    return _PX.sub(lambda m: f"{round(float(m.group(1)) * UI_SCALE)}px", css)

# ═════════════════════════════════════════════════════════════════════════════
#  THEME  -  one neutral palette, one accent colour
# ═════════════════════════════════════════════════════════════════════════════
C = {
    "bg": "#0f1012", "panel": "#16171a", "sidebar": "#121315", "topbar": "#0f1012",
    "card": "#1a1b1f", "border": "#26282d", "accent": "#7c8cff", "accent2": "#7c8cff",
    "green": "#7c8cff", "red": "#ff6b81", "text": "#e6e7ea", "muted": "#7d818c",
    "selected": "#23263a", "hover": "#1c1d22", "input_bg": "#1b1c20",
}

STYLE_SHEET = f"""
QMainWindow, QDialog {{ background-color:{C["bg"]}; }}
QWidget {{ color:{C["text"]}; font-family:'Inter','Ubuntu','Segoe UI','Helvetica Neue',sans-serif; font-size:13px; font-weight:500; }}
QLabel {{ background:transparent; }}
QToolTip {{ background:{C["card"]}; color:{C["text"]}; border:1px solid {C["border"]}; padding:4px 6px; }}

QScrollArea {{ background:transparent; border:none; }}
QScrollArea > QWidget > QWidget {{ background:transparent; }}
QScrollBar:vertical {{ background:transparent; width:8px; margin:0; }}
QScrollBar::handle:vertical {{ background:{C["border"]}; border-radius:4px; min-height:28px; }}
QScrollBar::handle:vertical:hover {{ background:{C["muted"]}; }}
QScrollBar:horizontal {{ background:transparent; height:8px; margin:0; }}
QScrollBar::handle:horizontal {{ background:{C["border"]}; border-radius:4px; min-width:28px; }}
QScrollBar::handle:horizontal:hover {{ background:{C["muted"]}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width:0; height:0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background:transparent; }}

QFrame#top {{ background:{C["topbar"]}; border:none; border-bottom:1px solid {C["border"]}; }}
QFrame#sidebar {{ background:{C["sidebar"]}; border:none; border-right:1px solid {C["border"]}; }}
QFrame#panel {{ background:{C["panel"]}; border:none; border-radius:10px; }}
QFrame#card {{ background:{C["card"]}; border:1px solid transparent; border-radius:8px; }}
QFrame#card:hover {{ border-color:{C["accent"]}; }}
QSplitter::handle {{ background:transparent; }}

QTreeWidget {{ background:transparent; border:none; outline:none; }}
QTreeWidget::item {{ padding:6px 8px; border-radius:0; }}
QTreeWidget::item:hover {{ background:{C["hover"]}; }}
QTreeWidget::item:selected, QTreeWidget::item:selected:!active {{ background:{C["selected"]}; color:{C["text"]}; }}
QTreeWidget::branch {{ background:transparent; image:none; }}
QTreeWidget::branch:selected, QTreeWidget::branch:selected:!active {{ background:{C["selected"]}; }}
QTreeWidget::branch:hover {{ background:{C["hover"]}; }}

QPushButton {{ background:{C["card"]}; color:{C["text"]}; border:1px solid {C["border"]};
    border-radius:6px; padding:7px 14px; font-weight:600; }}
QPushButton:hover {{ border-color:{C["muted"]}; }}
QPushButton:pressed {{ background:{C["hover"]}; }}
QPushButton:disabled {{ color:{C["muted"]}; background:transparent; }}
QPushButton#primary {{ background:{C["accent"]}; color:#0f1012; border:none; font-weight:700; }}
QPushButton#primary:hover {{ background:#93a0ff; }}
QPushButton#primary:disabled {{ background:{C["border"]}; color:{C["muted"]}; }}
QPushButton#tool {{ background:{C["selected"]}; color:{C["accent"]}; border:1px solid #3a4272;
    font-weight:700; padding:7px 20px; }}
QPushButton#tool:hover {{ background:#2c3050; border-color:{C["accent"]}; color:#aab4ff; }}
QPushButton#step {{ background:{C["input_bg"]}; color:{C["text"]}; border:1px solid {C["border"]};
    border-radius:6px; padding:0; font-size:16px; font-weight:700; min-width:30px; max-width:30px; }}
QPushButton#step:hover {{ border-color:{C["accent"]}; color:{C["accent"]}; background:{C["selected"]}; }}
QPushButton#step:pressed {{ background:#2c3050; }}
QPushButton#ghost {{ background:transparent; border:none; color:{C["muted"]}; padding:6px 10px; }}
QPushButton#ghost:hover {{ color:{C["text"]}; }}

QDoubleSpinBox, QSpinBox, QLineEdit, QComboBox {{ background:{C["input_bg"]}; color:{C["text"]};
    border:1px solid {C["border"]}; border-radius:6px; padding:4px 10px; font-weight:600;
    selection-background-color:{C["accent"]}; selection-color:#0f1012; }}
QDoubleSpinBox:focus, QSpinBox:focus, QLineEdit:focus, QComboBox:focus {{ border-color:{C["accent"]}; }}
QComboBox QAbstractItemView {{ background:{C["card"]}; border:1px solid {C["border"]}; padding:4px;
    selection-background-color:{C["selected"]}; selection-color:{C["text"]}; outline:none; }}
QMenu {{ background:{C["card"]}; border:1px solid {C["border"]}; padding:4px; }}
QMenu::item {{ padding:6px 18px; border-radius:4px; }}
QMenu::item:selected {{ background:{C["selected"]}; }}

QSlider::groove:horizontal {{ height:3px; background:{C["border"]}; border-radius:1px; }}
QSlider::handle:horizontal {{ background:{C["accent"]}; width:12px; height:12px; margin:-5px 0; border-radius:6px; }}

QProgressBar {{ background:transparent; border:none; }}
QProgressBar::chunk {{ background:{C["accent"]}; }}
"""


# ═════════════════════════════════════════════════════════════════════════════
#  TECHNIQUE REGISTRY
# ═════════════════════════════════════════════════════════════════════════════
CATEGORIES = [
    "Histogram Processing", "Gray Level Transformations", "Image Enhancement",
    "Spatial Filtering", "Edge & Line Detection", "Frequency Domain",
    "Image Segmentation", "Morphological Operations", "Boundary & Shape",
    "Color & Vision", "Live Video & Detection",
]


@dataclass(frozen=True)
class Param:
    name: str
    kind: str                      # "float" | "int" | "odd" | "choice"
    default: object
    lo: float = 0
    hi: float = 100
    step: float = 1
    choices: Tuple[str, ...] = ()
    tip: str = ""

    @property
    def label(self) -> str:
        return self.name.replace("_", " ")


def FLOAT(name, default, lo, hi, step=0.1, tip=""):
    return Param(name, "float", default, lo, hi, step, (), tip)

def INT(name, default, lo, hi, step=1, tip=""):
    return Param(name, "int", default, lo, hi, step, (), tip)

def ODD(name, default, lo, hi, tip=""):
    return Param(name, "odd", default, lo, hi, 2, (), tip)

def CHOICE(name, default, choices, tip=""):
    return Param(name, "choice", default, choices=tuple(choices), tip=tip)


@dataclass
class Technique:
    name: str
    category: str
    desc: str
    params: Sequence[Param]
    func: Optional[Callable]
    live: bool = False


REGISTRY: Dict[str, Technique] = {}


def technique(category: str, name: str, desc: str = "", params: Sequence[Param] = ()):
    def deco(fn):
        REGISTRY[name] = Technique(name, category, desc, tuple(params), fn)
        return fn
    return deco


def register_live(name: str, desc: str):
    REGISTRY[name] = Technique(name, "Live Video & Detection", desc, (), None, live=True)


def sanitize(img: np.ndarray) -> np.ndarray:
    """Make sure every result is a displayable uint8 image."""
    if img.ndim == 3 and img.shape[2] == 1:
        img = img[:, :, 0]
    if img.dtype != np.uint8:
        img = np.clip(np.nan_to_num(img), 0, 255).astype(np.uint8)
    return np.ascontiguousarray(img)


def run_technique(name: str, img_bgr: np.ndarray, params: Optional[dict] = None):
    """Run a registered technique -> list of (title, image)."""
    t = REGISTRY[name]
    vals = {p.name: p.default for p in t.params}
    for k, v in (params or {}).items():
        if k in vals:
            vals[k] = v
    for p in t.params:
        if p.kind == "odd":
            v = int(vals[p.name])
            vals[p.name] = v if v % 2 else v + 1
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    return [(title, sanitize(im)) for title, im in t.func(img_bgr, gray, **vals)]


# ═════════════════════════════════════════════════════════════════════════════
#  IMAGE HELPERS
# ═════════════════════════════════════════════════════════════════════════════
SHAPES = ("Rect", "Ellipse", "Cross")
POLARITY = ("Auto", "Bright objects", "Dark objects")
CURVE_COLORS = [(255, 198, 0), (160, 255, 0), (106, 74, 255)]


def to_u8(x):
    return np.clip(np.rint(x), 0, 255).astype(np.uint8)

def norm_u8(x):
    return cv2.normalize(np.asarray(x, np.float32), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

def fit(img, max_dim):
    h, w = img.shape[:2]
    s = max_dim / max(h, w)
    if s >= 1:
        return img
    return cv2.resize(img, (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_AREA)

def hist_of(gray):
    return cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel()

def se(shape, k):
    kind = {"Rect": cv2.MORPH_RECT, "Ellipse": cv2.MORPH_ELLIPSE, "Cross": cv2.MORPH_CROSS}[shape]
    return cv2.getStructuringElement(kind, (k, k))

def contours_of(binary, mode=cv2.RETR_EXTERNAL):
    return cv2.findContours(binary, mode, cv2.CHAIN_APPROX_SIMPLE)[-2]

def overlay(img_bgr, mask, color=(0, 0, 255), alpha=0.55):
    out = img_bgr.copy()
    m = mask > 0
    out[m] = (out[m] * (1 - alpha) + np.array(color) * alpha).astype(np.uint8)
    return out

def binarize(gray, t=0, polarity="Auto"):
    """Binary image with objects = white. t == 0 -> Otsu."""
    if t <= 0:
        _, b = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        _, b = cv2.threshold(gray, t, 255, cv2.THRESH_BINARY)
    if polarity == "Dark objects":
        b = cv2.bitwise_not(b)
    elif polarity == "Auto":
        border = np.concatenate([b[0], b[-1], b[:, 0], b[:, -1]])
        if border.mean() > 127:          # bright background -> invert
            b = cv2.bitwise_not(b)
    return b

def hist_plot(values, title="", marker=None, color=(255, 160, 90)):
    W, H, top = 512, 300, 28
    img = np.full((H, W, 3), 24, np.uint8)
    v = np.asarray(values, np.float32).ravel()
    if v.max() > 0:
        v = v / v.max() * (H - top - 6)
    for i in range(256):
        cv2.rectangle(img, (i * 2, H - 1 - int(v[i])), (i * 2 + 1, H - 1), color, -1)
    if marker is not None:
        x = int(marker) * 2
        cv2.line(img, (x, top), (x, H - 1), (80, 80, 255), 2)
    cv2.putText(img, title, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (230, 230, 230), 1, cv2.LINE_AA)
    return img

def hist_img(gray, title="", marker=None):
    return hist_plot(hist_of(gray), title, marker)

def draw_curve(curves, title=""):
    if isinstance(curves, np.ndarray) and curves.ndim == 1:
        curves = [curves]
    S = 300
    img = np.full((S, S, 3), 24, np.uint8)
    for g in range(0, 256, 64):
        p = int(g * (S - 1) / 255)
        cv2.line(img, (p, 0), (p, S - 1), (50, 50, 60), 1)
        cv2.line(img, (0, S - 1 - p), (S - 1, S - 1 - p), (50, 50, 60), 1)
    cv2.line(img, (0, S - 1), (S - 1, 0), (90, 90, 100), 1)
    for c, col in zip(curves, CURVE_COLORS * 3):
        pts = np.array([[int(i * (S - 1) / 255), S - 1 - int(float(v) * (S - 1) / 255)]
                        for i, v in enumerate(c)], np.int32)
        cv2.polylines(img, [pts], False, col, 2, cv2.LINE_AA)
    if title:
        cv2.putText(img, title, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (230, 230, 230), 1, cv2.LINE_AA)
    return img

def heatmap(mask):
    m = (mask - mask.min()) / (mask.max() - mask.min() + 1e-9)
    return cv2.applyColorMap((m * 255).astype(np.uint8), cv2.COLORMAP_JET)

def freq_grid(shape):
    rows, cols = shape
    y, x = np.ogrid[:rows, :cols]
    return np.sqrt((x - cols // 2) ** 2 + (y - rows // 2) ** 2)

def apply_freq_filter(gray, H):
    F = np.fft.fftshift(np.fft.fft2(gray.astype(np.float32)))
    G = F * H
    out = np.real(np.fft.ifft2(np.fft.ifftshift(G)))
    return F, G, out

def spectrum(F):
    return norm_u8(np.log1p(np.abs(F)))

def zhang_suen(binary, max_iter=1000):
    """Vectorised Zhang-Suen thinning (white objects on black)."""
    img = binary > 0
    for _ in range(max_iter):
        changed = False
        for step in (0, 1):
            P = np.pad(img, 1)
            p2, p3, p4, p5 = P[:-2, 1:-1], P[:-2, 2:], P[1:-1, 2:], P[2:, 2:]
            p6, p7, p8, p9 = P[2:, 1:-1], P[2:, :-2], P[1:-1, :-2], P[:-2, :-2]
            nb = (p2.astype(np.uint8) + p3 + p4 + p5 + p6 + p7 + p8 + p9)
            seq = (p2, p3, p4, p5, p6, p7, p8, p9, p2)
            trans = sum((~seq[i] & seq[i + 1]).astype(np.uint8) for i in range(8))
            if step == 0:
                c = ~(p2 & p4 & p6) & ~(p4 & p6 & p8)
            else:
                c = ~(p2 & p4 & p8) & ~(p2 & p6 & p8)
            m = img & (nb >= 2) & (nb <= 6) & (trans == 1) & c
            if m.any():
                img = img & ~m
                changed = True
        if not changed:
            break
    return img.astype(np.uint8) * 255

def thin(binary, max_iter=1000):
    if max_iter >= 1000 and hasattr(cv2, "ximgproc") and hasattr(cv2.ximgproc, "thinning"):
        return cv2.ximgproc.thinning(binary)
    return zhang_suen(binary, max_iter)


# ═════════════════════════════════════════════════════════════════════════════
#  TECHNIQUES
# ═════════════════════════════════════════════════════════════════════════════
# ── Histogram Processing ────────────────────────────────────────────────────
@technique("Histogram Processing", "Histogram Processing",
           "Intensity histogram and cumulative distribution (CDF) of the image.")
def t_histogram(img, gray):
    cdf = np.cumsum(hist_of(gray))
    cdf = cdf / cdf[-1] * 255
    return [("Grayscale", gray), ("Histogram", hist_img(gray, "Histogram")),
            ("Cumulative distribution", draw_curve(cdf, "CDF"))]


@technique("Histogram Processing", "Histogram Equalization",
           "Spreads intensities so the histogram becomes approximately flat.")
def t_equalize(img, gray):
    eq = cv2.equalizeHist(gray)
    return [("Original", gray), ("Histogram before", hist_img(gray, "Before")),
            ("Equalized", eq), ("Histogram after", hist_img(eq, "After"))]


@technique("Histogram Processing", "Histogram Specification",
           "Matches the histogram to a Gaussian-shaped target (true histogram matching "
           "via CDF mapping).",
           [INT("target_mean", 128, 0, 255), INT("target_sigma", 40, 5, 120)])
def t_hist_spec(img, gray, target_mean, target_sigma):
    x = np.arange(256, dtype=np.float64)
    target = np.exp(-0.5 * ((x - target_mean) / target_sigma) ** 2)
    target /= target.sum()
    s = hist_of(gray).astype(np.float64)
    s_cdf = np.cumsum(s) / s.sum()
    t_cdf = np.cumsum(target)
    lut = np.clip(np.searchsorted(t_cdf, s_cdf), 0, 255).astype(np.uint8)
    out = cv2.LUT(gray, lut)
    return [("Original", gray),
            ("Target histogram", hist_plot(target, f"Target N({target_mean}, {target_sigma})", color=(120, 220, 120))),
            ("Specified result", out), ("Result histogram", hist_img(out, "Result")),
            ("Mapping function", draw_curve(lut, "Mapping"))]


@technique("Histogram Processing", "CLAHE",
           "Contrast-Limited Adaptive Histogram Equalization - local contrast boost.",
           [FLOAT("clip_limit", 2.0, 0.1, 10.0), INT("grid_size", 8, 2, 32)])
def t_clahe(img, gray, clip_limit, grid_size):
    out = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(grid_size, grid_size)).apply(gray)
    return [("Original", gray), ("Global equalization", cv2.equalizeHist(gray)),
            (f"CLAHE (clip={clip_limit})", out), ("CLAHE histogram", hist_img(out, "CLAHE"))]


# ── Gray Level Transformations ──────────────────────────────────────────────
@technique("Gray Level Transformations", "Linear Transformation",
           "s = α·r + β (contrast / brightness) and the negative s = 255 − r.",
           [FLOAT("alpha", 1.5, 0.1, 5.0), INT("beta", 30, -100, 100)])
def t_linear(img, gray, alpha, beta):
    return [("Original", gray), (f"Linear (α={alpha:.2f}, β={beta})", cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)),
            ("Negative", cv2.bitwise_not(gray))]


@technique("Gray Level Transformations", "Logarithmic Transformation",
           "s = c·log(1 + r) - expands dark values, compresses bright ones.",
           [FLOAT("gain", 1.0, 0.1, 3.0)])
def t_log(img, gray, gain):
    c = 255.0 / np.log1p(max(float(gray.max()), 1.0)) * gain
    out = to_u8(c * np.log1p(gray.astype(np.float32)))
    curve = c * np.log1p(np.arange(256))
    return [("Original", gray), ("Log transformed", out), ("Transfer curve", draw_curve(np.clip(curve, 0, 255), "Log")),
            ("Log histogram", hist_img(out, "Log"))]


@technique("Gray Level Transformations", "Power Law Transformation",
           "s = 255·(r/255)^γ - γ<1 brightens, γ>1 darkens.",
           [FLOAT("gamma1", 0.4, 0.05, 5.0, 0.05), FLOAT("gamma2", 1.0, 0.05, 5.0, 0.05),
            FLOAT("gamma3", 2.5, 0.05, 5.0, 0.05)])
def t_power(img, gray, gamma1, gamma2, gamma3):
    x = np.arange(256) / 255.0
    luts = [to_u8(255 * x ** g) for g in (gamma1, gamma2, gamma3)]
    steps = [("Original", gray)]
    steps += [(f"γ = {g}", cv2.LUT(gray, l)) for g, l in zip((gamma1, gamma2, gamma3), luts)]
    steps.append(("Transfer curves", draw_curve(luts, "gamma curves")))
    return steps


@technique("Gray Level Transformations", "Piecewise Linear Transformation",
           "Custom contrast curve through (0,0) → (r1,s1) → (r2,s2) → (255,255).",
           [INT("r1", 85, 0, 255), INT("s1", 42, 0, 255), INT("r2", 170, 0, 255), INT("s2", 212, 0, 255)])
def t_piecewise(img, gray, r1, s1, r2, s2):
    r2 = max(r2, r1 + 1)
    lut = to_u8(np.interp(np.arange(256), [0, r1, r2, 255], [0, s1, s2, 255]))
    return [("Original", gray), ("Piecewise linear", cv2.LUT(gray, lut)), ("LUT curve", draw_curve(lut, "LUT"))]


@technique("Gray Level Transformations", "Contrast Stretching",
           "Linearly maps the [low, high] percentile range onto the full 0-255 range.",
           [INT("min_percentile", 2, 0, 49), INT("max_percentile", 98, 51, 100)])
def t_stretch(img, gray, min_percentile, max_percentile):
    lo, hi = np.percentile(gray, [min_percentile, max_percentile])
    out = to_u8((gray.astype(np.float32) - lo) / max(hi - lo, 1e-5) * 255)
    return [("Original", gray), (f"Stretched (p{min_percentile}-p{max_percentile})", out),
            ("Histogram before", hist_img(gray, "Before")), ("Histogram after", hist_img(out, "After"))]


@technique("Gray Level Transformations", "Bit-Plane Slicing",
           "Splits the image into its 8 binary bit planes (MSB carries most structure).")
def t_bitplane(img, gray):
    return [(f"Bit plane {b}" + (" (MSB)" if b == 7 else " (LSB)" if b == 0 else ""),
             ((gray >> b) & 1) * 255) for b in range(7, -1, -1)]


# ── Image Enhancement ───────────────────────────────────────────────────────
@technique("Image Enhancement", "Point Processing",
           "Pixel-wise operations: global threshold and negative.",
           [INT("thresh_val", 127, 0, 255)])
def t_point(img, gray, thresh_val):
    return [("Original", gray), (f"Threshold (t={thresh_val})", cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)[1]),
            ("Negative", cv2.bitwise_not(gray))]


@technique("Image Enhancement", "Image Subtraction",
           "Subtracts a blurred copy (background estimate) to reveal detail.",
           [ODD("blur_k_size", 21, 3, 99)])
def t_subtract(img, gray, blur_k_size):
    blur = cv2.GaussianBlur(gray, (blur_k_size, blur_k_size), 0)
    diff = cv2.absdiff(gray, blur)
    return [("Original", gray), (f"Blurred reference (k={blur_k_size})", blur),
            ("|Original − Blurred|", norm_u8(diff)), ("Enhanced (orig + diff)", cv2.add(gray, diff))]


@technique("Image Enhancement", "Image Averaging",
           "Noise reduction by averaging many noisy frames of the same scene (σ of noise falls by √N).",
           [FLOAT("noise_sigma", 25.0, 1.0, 100.0, 1.0), INT("frames", 16, 2, 64)])
def t_average(img, gray, noise_sigma, frames):
    rng = np.random.default_rng(0)
    g = gray.astype(np.float32)
    acc = np.zeros_like(g)
    first = None
    for _ in range(frames):
        noisy = to_u8(g + rng.normal(0, noise_sigma, g.shape))
        first = noisy if first is None else first
        acc += noisy
    avg = to_u8(acc / frames)
    return [("Original", gray), (f"Single noisy frame (PSNR {cv2.PSNR(gray, first):.1f} dB)", first),
            (f"Average of {frames} frames (PSNR {cv2.PSNR(gray, avg):.1f} dB)", avg)]


# ── Spatial Filtering ───────────────────────────────────────────────────────
@technique("Spatial Filtering", "Smoothing Spatial Filters",
           "Box, Gaussian and median smoothing.", [ODD("k_size", 5, 3, 31)])
def t_smooth(img, gray, k_size):
    k = (k_size, k_size)
    return [("Original", gray), (f"Box ({k_size}×{k_size})", cv2.blur(gray, k)),
            (f"Gaussian ({k_size}×{k_size})", cv2.GaussianBlur(gray, k, 0)),
            (f"Median ({k_size}×{k_size})", cv2.medianBlur(gray, k_size))]


@technique("Spatial Filtering", "Sharpening Spatial Filters",
           "Laplacian-kernel sharpening, unsharp masking and high-boost filtering.",
           [ODD("blur_k", 5, 3, 31), FLOAT("boost", 2.5, 1.0, 6.0)])
def t_sharpen(img, gray, blur_k, boost):
    blur = cv2.GaussianBlur(gray, (blur_k, blur_k), 0)
    mask = gray.astype(np.float32) - blur
    kern = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], np.float32)
    return [("Original", gray), ("Laplacian-kernel sharpen", cv2.filter2D(gray, -1, kern)),
            ("Detail mask (+128)", to_u8(mask + 128)), ("Unsharp mask (k=1)", to_u8(gray + mask)),
            (f"High-boost (k={boost})", to_u8(gray + boost * mask))]


@technique("Spatial Filtering", "Order-Statistic Filters",
           "Median, minimum, maximum and midpoint filters.", [ODD("k_size", 5, 3, 31)])
def t_orderstat(img, gray, k_size):
    kern = np.ones((k_size, k_size), np.uint8)
    mn, mx = cv2.erode(gray, kern), cv2.dilate(gray, kern)
    return [("Original", gray), (f"Median (k={k_size})", cv2.medianBlur(gray, k_size)),
            ("Min filter", mn), ("Max filter", mx), ("Midpoint filter", to_u8((mn.astype(np.float32) + mx) / 2))]


@technique("Spatial Filtering", "Gradient Operator",
           "Sobel gradients and gradient magnitude.", [ODD("k_size", 3, 1, 7)])
def t_gradient(img, gray, k_size):
    g = gray.astype(np.float32)
    gx, gy = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=k_size), cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=k_size)
    return [("Original", gray), (f"|Sobel X| (k={k_size})", cv2.convertScaleAbs(gx)),
            (f"|Sobel Y| (k={k_size})", cv2.convertScaleAbs(gy)), ("Gradient magnitude", norm_u8(cv2.magnitude(gx, gy)))]


@technique("Spatial Filtering", "Laplacian Operator",
           "Second-derivative operator; sharpened = original − Laplacian.",
           [ODD("k_size", 1, 1, 7)])
def t_laplacian(img, gray, k_size):
    lap = cv2.Laplacian(gray.astype(np.float32), cv2.CV_32F, ksize=k_size)
    return [("Original", gray), ("|Laplacian|", norm_u8(np.abs(lap))), ("Sharpened (orig − lap)", to_u8(gray - lap))]


# ── Edge & Line Detection ───────────────────────────────────────────────────
@technique("Edge & Line Detection", "Edge Detection",
           "Compares Sobel, Prewitt, Roberts, Laplacian-of-Gaussian and auto-threshold Canny.",
           [FLOAT("sigma", 1.0, 0.0, 5.0)])
def t_edges(img, gray, sigma):
    g = cv2.GaussianBlur(gray, (0, 0), sigma) if sigma > 0 else gray
    gf = g.astype(np.float32)
    sob = cv2.magnitude(cv2.Sobel(gf, cv2.CV_32F, 1, 0), cv2.Sobel(gf, cv2.CV_32F, 0, 1))
    px = np.array([[-1, 0, 1]] * 3, np.float32)
    pre = cv2.magnitude(cv2.filter2D(gf, -1, px), cv2.filter2D(gf, -1, px.T))
    rx, ry = np.array([[1, 0], [0, -1]], np.float32), np.array([[0, 1], [-1, 0]], np.float32)
    rob = cv2.magnitude(cv2.filter2D(gf, -1, rx), cv2.filter2D(gf, -1, ry))
    log = np.abs(cv2.Laplacian(gf, cv2.CV_32F, ksize=1))
    med = float(np.median(g))
    lo, hi = int(max(0, 0.66 * med)), int(min(255, 1.33 * med))
    return [("Original", gray), ("Sobel", norm_u8(sob)), ("Prewitt", norm_u8(pre)), ("Roberts", norm_u8(rob)),
            ("Laplacian of Gaussian", norm_u8(log)), (f"Canny auto ({lo},{hi})", cv2.Canny(g, lo, hi))]


@technique("Edge & Line Detection", "Canny Edge Detection",
           "Canny with / without pre-blur and with two threshold pairs.",
           [INT("low", 50, 0, 500, 5), INT("high", 150, 0, 500, 5), ODD("blur_k", 5, 3, 31),
            INT("low2", 100, 0, 500, 5), INT("high2", 200, 0, 500, 5)])
def t_canny(img, gray, low, high, blur_k, low2, high2):
    blur = cv2.GaussianBlur(gray, (blur_k, blur_k), 0)
    return [("Original", gray), ("Gaussian blurred", blur), (f"Canny, no blur ({low},{high})", cv2.Canny(gray, low, high)),
            (f"Canny, blurred ({low},{high})", cv2.Canny(blur, low, high)),
            (f"Canny, blurred ({low2},{high2})", cv2.Canny(blur, low2, high2))]


@technique("Edge & Line Detection", "Line Detection",
           "Probabilistic Hough transform on Canny edges.",
           [INT("canny_low", 50, 0, 500, 5), INT("canny_high", 150, 0, 500, 5), INT("hough_thresh", 80, 10, 300, 5),
            INT("min_line_len", 50, 5, 300, 5), INT("max_line_gap", 10, 0, 100)])
def t_lines(img, gray, canny_low, canny_high, hough_thresh, min_line_len, max_line_gap):
    edges = cv2.Canny(gray, canny_low, canny_high)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, hough_thresh, minLineLength=min_line_len, maxLineGap=max_line_gap)
    lines = np.zeros((0, 4), int) if lines is None else lines.reshape(-1, 4)   # works for (N,1,4) and (N,4)
    out = img.copy()
    n = len(lines)
    for x1, y1, x2, y2 in lines:
        cv2.line(out, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
    return [("Original", gray), ("Canny edges", edges), (f"Hough lines ({n} found)", out)]


@technique("Edge & Line Detection", "Point Detection",
           "Isolated-point detector (8-neighbour Laplacian kernel); threshold is a fraction of the peak response.",
           [FLOAT("threshold", 0.6, 0.05, 1.0, 0.05)])
def t_points(img, gray, threshold):
    k = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]], np.float32)
    resp = np.abs(cv2.filter2D(gray.astype(np.float32), -1, k))
    mask = ((resp >= threshold * resp.max()) & (resp.max() > 0)).astype(np.uint8) * 255
    n = cv2.connectedComponents(mask)[0] - 1
    out = img.copy()
    out[cv2.dilate(mask, np.ones((5, 5), np.uint8)) > 0] = (0, 0, 255)
    return [("Original", gray), ("|Response|", norm_u8(resp)), (f"Detected points ({n})", mask), ("Overlay", out)]


# ── Frequency Domain ────────────────────────────────────────────────────────
@technique("Frequency Domain", "Ideal Low Pass Filtering",
           "Hard circular cut-off in the Fourier domain (causes ringing).", [INT("radius", 30, 1, 300)])
def t_ilpf(img, gray, radius):
    H = (freq_grid(gray.shape) <= radius).astype(np.float32)
    F, G, out = apply_freq_filter(gray, H)
    return [("Original", gray), ("Magnitude spectrum", spectrum(F)), (f"Ideal LPF mask (r={radius})", H * 255),
            ("Filtered spectrum", spectrum(G)), ("Filtered result", out)]


@technique("Frequency Domain", "Gaussian Low Pass Filtering",
           "Smooth Gaussian cut-off - no ringing.", [INT("sigma", 30, 1, 300)])
def t_glpf(img, gray, sigma):
    H = np.exp(-(freq_grid(gray.shape) ** 2) / (2.0 * sigma ** 2)).astype(np.float32)
    F, G, out = apply_freq_filter(gray, H)
    return [("Original", gray), ("Magnitude spectrum", spectrum(F)), (f"Gaussian mask (σ={sigma})", heatmap(H)),
            ("Filtered spectrum", spectrum(G)), ("Filtered result", out)]


@technique("Frequency Domain", "Homomorphic Filtering",
           "Separates illumination and reflectance in the log domain to even out lighting.",
           [FLOAT("gammaH", 1.8, 0.5, 5.0), FLOAT("gammaL", 0.5, 0.1, 1.0), FLOAT("c", 1.0, 0.1, 5.0), INT("D0", 30, 5, 300, 5)])
def t_homomorphic(img, gray, gammaH, gammaL, c, D0):
    log_img = np.log1p(gray.astype(np.float32) / 255.0)
    D = freq_grid(gray.shape)
    H = ((gammaH - gammaL) * (1 - np.exp(-c * (D ** 2 / D0 ** 2))) + gammaL).astype(np.float32)
    F, G, out = apply_freq_filter(log_img, H)
    return [("Original", gray), ("Log domain", norm_u8(log_img)), ("Homomorphic filter", heatmap(H)),
            ("Enhanced result", norm_u8(np.expm1(out)))]


# ── Image Segmentation ──────────────────────────────────────────────────────
@technique("Image Segmentation", "Thresholding",
           "Binary, inverse-binary and adaptive (Gaussian) thresholding.",
           [INT("t_val", 127, 0, 255), ODD("block_size", 11, 3, 99), INT("c_val", 2, 0, 20)])
def t_threshold(img, gray, t_val, block_size, c_val):
    return [("Original", gray), (f"Binary (t={t_val})", cv2.threshold(gray, t_val, 255, cv2.THRESH_BINARY)[1]),
            ("Inverse", cv2.threshold(gray, t_val, 255, cv2.THRESH_BINARY_INV)[1]),
            (f"Adaptive (block={block_size}, C={c_val})",
             cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, c_val))]


@technique("Image Segmentation", "Global Thresholding",
           "Iterative (isodata) global threshold selection.", [FLOAT("tolerance", 0.5, 0.01, 5.0, 0.01)])
def t_global(img, gray, tolerance):
    T = float(gray.mean())
    for _ in range(100):
        g1, g2 = gray[gray >= T], gray[gray < T]
        Tn = ((g1.mean() if g1.size else 0) + (g2.mean() if g2.size else 0)) / 2
        if abs(T - Tn) < tolerance:
            T = Tn
            break
        T = Tn
    return [("Original", gray), ("Histogram + threshold", hist_img(gray, f"T = {T:.1f}", T)),
            (f"Global (T={int(T)})", cv2.threshold(gray, int(T), 255, cv2.THRESH_BINARY)[1])]


@technique("Image Segmentation", "Otsu's Method",
           "Chooses the threshold that minimises intra-class variance.", [ODD("blur_k", 1, 1, 31, "1 = no pre-blur")])
def t_otsu(img, gray, blur_k):
    g = cv2.GaussianBlur(gray, (blur_k, blur_k), 0) if blur_k > 1 else gray
    t, out = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return [("Original", gray), ("Histogram + Otsu T", hist_img(g, f"Otsu T = {int(t)}", t)), (f"Otsu result (T={int(t)})", out)]


@technique("Image Segmentation", "Region Growing",
           "Seeded region growing: grows from the seed over pixels within ± tolerance of the seed value.",
           [INT("seed_x_pct", 50, 0, 100, 1, "Seed X position in % of width"),
            INT("seed_y_pct", 50, 0, 100, 1, "Seed Y position in % of height"), INT("tolerance", 20, 1, 128)])
def t_region_growing(img, gray, seed_x_pct, seed_y_pct, tolerance):
    h, w = gray.shape
    seed = (min(w - 1, int(w * seed_x_pct / 100)), min(h - 1, int(h * seed_y_pct / 100)))
    mask = np.zeros((h + 2, w + 2), np.uint8)
    flags = 4 | cv2.FLOODFILL_FIXED_RANGE | cv2.FLOODFILL_MASK_ONLY | (255 << 8)
    cv2.floodFill(gray.copy(), mask, seed, 255, loDiff=tolerance, upDiff=tolerance, flags=flags)
    region = mask[1:-1, 1:-1]
    marked = img.copy()
    cv2.circle(marked, seed, max(4, min(h, w) // 60), (0, 0, 255), -1)
    cv2.circle(marked, seed, max(6, min(h, w) // 60 + 2), (255, 255, 255), 2)
    pct = 100.0 * np.count_nonzero(region) / region.size
    return [("Seed", marked), (f"Grown region ({pct:.1f}% of image)", region), ("Overlay", overlay(img, region, (0, 255, 0)))]


@technique("Image Segmentation", "Region Splitting and Merging",
           "Quad-tree split on local standard deviation, then merge neighbouring regions with similar mean.",
           [INT("split_std", 12, 1, 80, 1, "Split a block while its std-dev exceeds this"),
            INT("min_block", 16, 4, 128, 4), INT("merge_diff", 12, 0, 80, 1, "Merge neighbours whose means differ less than this")])
def t_split_merge(img, gray, split_std, min_block, merge_diff):
    g = fit(gray, 640)
    H, W = g.shape
    leaves: List[Tuple[int, int, int, int]] = []

    def rec(x, y, w, h):
        if w <= min_block or h <= min_block or g[y:y + h, x:x + w].std() <= split_std:
            leaves.append((x, y, w, h))
            return
        w2, h2 = w // 2, h // 2
        rec(x, y, w2, h2); rec(x + w2, y, w - w2, h2)
        rec(x, y + h2, w2, h - h2); rec(x + w2, y + h2, w - w2, h - h2)

    rec(0, 0, W, H)
    n = len(leaves)
    lab = np.zeros((H, W), np.int32)
    means = np.zeros(n)
    areas = np.zeros(n)
    vis = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
    for i, (x, y, w, h) in enumerate(leaves):
        lab[y:y + h, x:x + w] = i
        means[i], areas[i] = g[y:y + h, x:x + w].mean(), w * h
        cv2.rectangle(vis, (x, y), (x + w - 1, y + h - 1), (0, 255, 0), 1)
    split_img = means[lab]

    # adjacency of leaves -> union-find merge
    hm, vm = lab[:, :-1] != lab[:, 1:], lab[:-1, :] != lab[1:, :]
    a = np.concatenate([lab[:, :-1][hm], lab[:-1, :][vm]])
    b = np.concatenate([lab[:, 1:][hm], lab[1:, :][vm]])
    pairs = np.unique(np.stack([np.minimum(a, b), np.maximum(a, b)], 1), axis=0)
    if len(pairs):
        pairs = pairs[np.argsort(np.abs(means[pairs[:, 0]] - means[pairs[:, 1]]))]
    parent = list(range(n))
    s, ar = (means * areas).tolist(), areas.tolist()

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, j in pairs.tolist():
        ri, rj = find(i), find(j)
        if ri != rj and abs(s[ri] / ar[ri] - s[rj] / ar[rj]) <= merge_diff:
            parent[rj] = ri
            s[ri] += s[rj]; ar[ri] += ar[rj]
    roots = [find(i) for i in range(n)]
    merged = np.array([s[r] / ar[r] for r in roots])[lab]
    return [("Original", g), (f"Split into {n} blocks", vis), ("Split (block means)", split_img),
            (f"Merged into {len(set(roots))} regions", merged)]


@technique("Image Segmentation", "Clustering-based Segmentation",
           "K-Means colour clustering for three values of K (image is downscaled to 480px for speed).",
           [INT("K1", 2, 2, 16), INT("K2", 4, 2, 16), INT("K3", 8, 2, 16), INT("attempts", 3, 1, 10)])
def t_kmeans(img, gray, K1, K2, K3, attempts):
    small = fit(img, 480)
    Z = small.reshape((-1, 3)).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    steps = [("Original", small)]
    for K in (K1, K2, K3):
        _, labels, centers = cv2.kmeans(Z, K, None, crit, attempts, cv2.KMEANS_PP_CENTERS)
        steps.append((f"K-Means (K={K})", np.uint8(centers)[labels.flatten()].reshape(small.shape)))
    return steps


@technique("Image Segmentation", "Watershed Algorithm",
           "Marker-based watershed on the distance transform (auto-detects dark / bright objects).",
           [FLOAT("fg_thresh", 0.7, 0.1, 0.99, 0.01, "Fraction of max distance kept as sure foreground")])
def t_watershed(img, gray, fg_thresh):
    thresh = binarize(gray, 0, "Auto")
    kern = np.ones((3, 3), np.uint8)
    opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kern, iterations=2)
    sure_bg = cv2.dilate(opened, kern, iterations=3)
    dist = cv2.distanceTransform(opened, cv2.DIST_L2, 5)
    sure_fg = np.uint8(cv2.threshold(dist, fg_thresh * dist.max(), 255, 0)[1])
    unknown = cv2.subtract(sure_bg, sure_fg)
    n, markers = cv2.connectedComponents(sure_fg)
    markers = markers + 1
    markers[unknown == 255] = 0
    cv2.watershed(img.copy(), markers)
    colors = np.random.default_rng(1).integers(60, 255, (n + 2, 3), dtype=np.uint8)
    segs = colors[np.clip(markers, 0, None)]
    segs[markers == -1] = (0, 0, 255)
    result = img.copy()
    result[markers == -1] = (0, 0, 255)
    edges = np.zeros(markers.shape, np.uint8)             # boundaries only: white lines on black
    edges[markers == -1] = 255
    edges[0, :] = edges[-1, :] = edges[:, 0] = edges[:, -1] = 0   # OpenCV flags the image border itself
    edges = cv2.dilate(edges, kern)                       # 1-px lines vanish in thumbnails
    return [("Original", img), ("Binary (objects white)", thresh), ("Sure foreground", sure_fg),
            ("Distance transform", norm_u8(dist)), ("Segments", segs), ("Watershed boundaries", result),
            ("Boundaries only", edges)]


# ── Morphological Operations ────────────────────────────────────────────────
def _make_morph(op, name):
    def run(img, gray, k_size, iterations, shape):
        out = cv2.morphologyEx(gray, op, se(shape, k_size), iterations=iterations)
        return [("Original", gray), (f"{name} ({shape} {k_size}×{k_size}, ×{iterations})", out),
                ("|Original − Result|", cv2.absdiff(gray, out))]
    return run

for _n, _op, _d in [
    ("Erosion", cv2.MORPH_ERODE, "Shrinks bright regions, removes small bright specks."),
    ("Dilation", cv2.MORPH_DILATE, "Grows bright regions, fills small dark gaps."),
    ("Opening", cv2.MORPH_OPEN, "Erosion then dilation - removes small bright objects."),
    ("Closing", cv2.MORPH_CLOSE, "Dilation then erosion - closes small dark holes."),
    ("Morphological Gradient", cv2.MORPH_GRADIENT, "Dilation − erosion: object outlines."),
    ("Top Hat", cv2.MORPH_TOPHAT, "Original − opening: small bright details."),
    ("Black Hat", cv2.MORPH_BLACKHAT, "Closing − original: small dark details."),
]:
    technique("Morphological Operations", _n, _d,
              [ODD("k_size", 5, 3, 31), INT("iterations", 1, 1, 10), CHOICE("shape", "Rect", SHAPES)])(_make_morph(_op, _n))

_BIN_PARAMS = [INT("thresh_val", 0, 0, 255, 1, "0 = automatic (Otsu)"), CHOICE("polarity", "Auto", POLARITY, "Which side counts as the object")]


@technique("Morphological Operations", "Thinning",
           "Zhang-Suen thinning reduces objects to 1-pixel skeletons.",
           _BIN_PARAMS + [INT("max_iter", 1000, 1, 1000, 1, "Limit iterations (1000 = until done)")])
def t_thinning(img, gray, thresh_val, polarity, max_iter):
    g = fit(gray, 640)
    b = binarize(g, thresh_val, polarity)
    sk = thin(b, max_iter)
    return [("Binary", b), ("Skeleton", sk), ("Skeleton overlay", overlay(cv2.cvtColor(g, cv2.COLOR_GRAY2BGR), cv2.dilate(sk, np.ones((2, 2), np.uint8)), (0, 0, 255), 1.0))]


@technique("Morphological Operations", "Thickening",
           "Morphological thickening = complement of thinning the background.",
           _BIN_PARAMS + [INT("iterations", 5, 1, 50)])
def t_thickening(img, gray, thresh_val, polarity, iterations):
    g = fit(gray, 640)
    b = binarize(g, thresh_val, polarity)
    thick = cv2.bitwise_not(thin(cv2.bitwise_not(b), iterations))
    return [("Binary", b), (f"Thickened (≤{iterations} iterations)", thick), ("Added pixels", cv2.subtract(thick, b))]


@technique("Morphological Operations", "Convex Hull",
           "Smallest convex polygon enclosing each object.", _BIN_PARAMS + [INT("min_area", 100, 0, 50000, 10)])
def t_hull(img, gray, thresh_val, polarity, min_area):
    b = binarize(gray, thresh_val, polarity)
    out, filled, n = img.copy(), np.zeros_like(b), 0
    for c in contours_of(b):
        if cv2.contourArea(c) < min_area:
            continue
        hull = cv2.convexHull(c)
        cv2.drawContours(out, [hull], -1, (0, 255, 0), 2)
        cv2.drawContours(filled, [hull], -1, 255, -1)
        n += 1
    return [("Original", img), ("Binary", b), (f"Convex hulls ({n})", out), ("Filled hulls", filled)]


_HM_PATTERNS = {
    "Isolated pixel": [[-1, -1, -1], [-1, 1, -1], [-1, -1, -1]],
    "Top-left corner": [[-1, -1, 0], [-1, 1, 1], [0, 1, 0]],
    "Line end (right)": [[0, -1, 0], [1, 1, -1], [0, -1, 0]],
}

@technique("Morphological Operations", "Hit-or-Miss Transform",
           "Finds exact foreground/background neighbourhood patterns (1 = must be object, -1 = must be background, 0 = ignore).",
           _BIN_PARAMS + [CHOICE("pattern", "Top-left corner", tuple(_HM_PATTERNS))])
def t_hitmiss(img, gray, thresh_val, polarity, pattern):
    b = binarize(gray, thresh_val, polarity)
    hm = cv2.morphologyEx(b, cv2.MORPH_HITMISS, np.array(_HM_PATTERNS[pattern], np.int32))
    n = cv2.connectedComponents(hm)[0] - 1
    out = img.copy()
    out[cv2.dilate(hm, np.ones((7, 7), np.uint8)) > 0] = (0, 0, 255)
    return [("Binary", b), (f"Matches: {pattern} ({n})", hm), ("Matches on image", out)]


@technique("Morphological Operations", "Hole Filling",
           "Fills holes inside objects by flood-filling the background from the border.", _BIN_PARAMS)
def t_holes(img, gray, thresh_val, polarity):
    b = binarize(gray, thresh_val, polarity)
    padded = cv2.copyMakeBorder(b, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)
    flood = padded.copy()
    mask = np.zeros((padded.shape[0] + 2, padded.shape[1] + 2), np.uint8)
    cv2.floodFill(flood, mask, (0, 0), 255)
    holes = cv2.bitwise_not(flood)[1:-1, 1:-1]
    return [("Original", gray), ("Binary", b), ("Holes", holes), ("Holes filled", cv2.bitwise_or(b, holes))]


# ── Boundary & Shape ────────────────────────────────────────────────────────
@technique("Boundary & Shape", "Edge Linking",
           "Hysteresis (weak edges kept only if connected to strong ones) plus gap-closing.",
           [INT("low", 50, 0, 500, 5), INT("high", 150, 0, 500, 5), ODD("gap", 3, 1, 15, "Closing kernel used to bridge small gaps")])
def t_linking(img, gray, low, high, gap):
    hyst = cv2.Canny(gray, low, high)
    linked = cv2.morphologyEx(hyst, cv2.MORPH_CLOSE, np.ones((gap, gap), np.uint8))
    return [("Original", gray), (f"Strong edges only (≥{high})", cv2.Canny(gray, high, high)),
            (f"All candidate edges (≥{low})", cv2.Canny(gray, low, low)), ("Hysteresis linked", hyst), (f"Gap-closed (k={gap})", linked)]


@technique("Boundary & Shape", "Boundary Detection",
           "Boundary = object − erosion(object); contours extracted from the binary image.",
           [ODD("k_size", 3, 3, 15)] + _BIN_PARAMS)
def t_boundary(img, gray, k_size, thresh_val, polarity):
    b = binarize(gray, thresh_val, polarity)
    boundary = cv2.subtract(b, cv2.erode(b, np.ones((k_size, k_size), np.uint8)))
    cnts = contours_of(b)
    out = img.copy()
    cv2.drawContours(out, cnts, -1, (0, 255, 0), 2)
    return [("Original", img), ("Binary", b), ("Morphological boundary", boundary), (f"Contours ({len(cnts)})", out)]


@technique("Boundary & Shape", "Polygon Fitting Algorithm",
           "Douglas-Peucker polygon approximation of contours (ε = eps_mult × perimeter).",
           [INT("low", 50, 0, 500, 5), INT("high", 150, 0, 500, 5), INT("min_area", 100, 10, 5000, 10),
            FLOAT("eps_mult", 0.02, 0.001, 0.2, 0.001)])
def t_polygon(img, gray, low, high, min_area, eps_mult):
    edges = cv2.morphologyEx(cv2.Canny(gray, low, high), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    out, n = img.copy(), 0
    for c in contours_of(edges):
        if cv2.contourArea(c) < min_area:
            continue
        ap = cv2.approxPolyDP(c, eps_mult * cv2.arcLength(c, True), True)
        cv2.drawContours(out, [ap], -1, (0, 255, 0), 2)
        for p in ap[:, 0]:
            cv2.circle(out, tuple(int(v) for v in p), 3, (0, 0, 255), -1)
        n += 1
    return [("Original", img), ("Edges", edges), (f"Polygons ({n}, ε={eps_mult})", out)]


@technique("Boundary & Shape", "Shape Detection",
           "Classifies contours by vertex count and circularity.",
           [INT("min_area", 200, 10, 5000, 10), FLOAT("eps_mult", 0.04, 0.001, 0.2, 0.001),
            CHOICE("polarity", "Auto", POLARITY)])
def t_shapes(img, gray, min_area, eps_mult, polarity):
    b = cv2.morphologyEx(binarize(gray, 0, polarity), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    out, n = img.copy(), 0
    for c in contours_of(b):
        area = cv2.contourArea(c)
        if area < min_area:
            continue
        per = cv2.arcLength(c, True)
        ap = cv2.approxPolyDP(c, eps_mult * per, True)
        v, circ = len(ap), 4 * np.pi * area / (per ** 2 + 1e-9)
        if v == 3: name = "Triangle"
        elif v == 4:
            _, _, w, h = cv2.boundingRect(ap)
            name = "Square" if 0.9 <= w / h <= 1.1 else "Rectangle"
        elif v == 5: name = "Pentagon"
        elif v == 6: name = "Hexagon"
        elif circ > 0.8: name = "Circle"
        else: name = f"Polygon({v})"
        color = {"Triangle": (0, 255, 0), "Square": (255, 128, 0), "Rectangle": (255, 0, 0),
                 "Circle": (0, 0, 255)}.get(name, (255, 255, 0))
        m = cv2.moments(c)
        if m["m00"]:
            cx, cy = int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"])
            cv2.putText(out, name, (cx - 30, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2, cv2.LINE_AA)
        cv2.drawContours(out, [ap], -1, color, 2)
        n += 1
    return [("Original", img), ("Binary mask", b), (f"Shapes detected ({n})", out)]


# ── Color & Vision ──────────────────────────────────────────────────────────
@technique("Color & Vision", "Gaussian Blurring",
           "Gaussian blur at three kernel sizes (σ = 0 → derived from kernel size).",
           [ODD("k1", 5, 3, 99), ODD("k2", 15, 3, 99), ODD("k3", 31, 3, 99), FLOAT("sigma", 0.0, 0.0, 30.0, 0.5)])
def t_gblur(img, gray, k1, k2, k3, sigma):
    return [("Original", img)] + [(f"Gaussian {k}×{k}", cv2.GaussianBlur(img, (k, k), sigma)) for k in (k1, k2, k3)]


_SPACES = {
    "HSV": (cv2.COLOR_BGR2HSV, ("H", "S", "V"), 0), "LAB": (cv2.COLOR_BGR2LAB, ("L", "a", "b"), None),
    "YCrCb": (cv2.COLOR_BGR2YCrCb, ("Y", "Cr", "Cb"), None), "HLS": (cv2.COLOR_BGR2HLS, ("H", "L", "S"), 0),
}

@technique("Color & Vision", "Color Conversion",
           "Splits the image into the channels of another colour space.", [CHOICE("space", "HSV", tuple(_SPACES))])
def t_colorconv(img, gray, space):
    code, names, hue_idx = _SPACES[space]
    conv = cv2.cvtColor(img, code)
    steps = [("Original BGR", img)]
    for i, nm in enumerate(names):
        ch = conv[:, :, i]
        if i == hue_idx:
            ch = to_u8(ch.astype(np.float32) * 255 / 179)      # OpenCV hue is 0-179
        steps.append((f"{space} - {nm} channel", ch))
    steps.append(("Grayscale", gray))
    return steps


@technique("Color & Vision", "Color Masking",
           "Isolates red / green / blue regions with HSV range masks.",
           [INT("sat_min", 70, 0, 255), INT("val_min", 70, 0, 255)])
def t_colormask(img, gray, sat_min, val_min):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lo = lambda h: np.array([h, sat_min, val_min])
    red = cv2.inRange(hsv, lo(0), np.array([10, 255, 255])) | cv2.inRange(hsv, lo(170), np.array([180, 255, 255]))
    green = cv2.inRange(hsv, lo(40), np.array([80, 255, 255]))
    blue = cv2.inRange(hsv, lo(100), np.array([130, 255, 255]))
    pick = lambda m: cv2.bitwise_and(img, img, mask=m)
    return [("Original", img), ("Hue channel", to_u8(hsv[:, :, 0].astype(np.float32) * 255 / 179)), ("Red", pick(red)), ("Green", pick(green)), ("Blue", pick(blue))]


@technique("Color & Vision", "Perspective Transformation",
           "Warps the marked quadrilateral to a full rectangle (4-point homography).",
           [FLOAT("margin_pct", 0.15, 0.01, 0.45, 0.01), FLOAT("tilt", 0.1, 0.0, 0.4, 0.01, "Narrows the top edge (keystone)")])
def t_perspective(img, gray, margin_pct, tilt):
    h, w = img.shape[:2]
    m, t = int(min(h, w) * margin_pct), int(w * tilt)
    src = np.float32([[m + t, m], [w - m - t, m], [w - m, h - m], [m, h - m]])
    dst = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    warped = cv2.warpPerspective(img, cv2.getPerspectiveTransform(src, dst), (w, h))
    marked = img.copy()
    cv2.polylines(marked, [src.astype(np.int32)], True, (0, 255, 0), 2)
    for p in src.astype(int):
        cv2.circle(marked, tuple(p), 8, (0, 0, 255), -1)
    return [("Source points", marked), ("Warped", warped)]


# ── Live ────────────────────────────────────────────────────────────────────
register_live("ArUco Marker Detection", "Real-time ArUco marker detection from the webcam.")
register_live("Motion Detection", "Background-subtraction (MOG2) motion detection with bounding boxes.")
register_live("Anomaly Detection", "Flags changes relative to a reference frame captured at start.")


# ═════════════════════════════════════════════════════════════════════════════
#  QT HELPERS
# ═════════════════════════════════════════════════════════════════════════════
def to_qpixmap(img, max_w=None, max_h=None) -> QPixmap:
    """max_w/max_h are *logical* pixels; on high-DPI screens the pixmap is rendered at
    device resolution (and tagged with the device pixel ratio) so it stays sharp."""
    dpr = 1.0
    if max_w and max_h:
        h, w = img.shape[:2]
        s_log = min(max_w / w, max_h / h, 1.0)            # fit inside the box, in logical pixels
        s_dev = min(s_log * UI_DPR, 1.0)                  # render at device resolution, never above the source
        if s_dev < 1.0:
            img = cv2.resize(img, (max(1, int(w * s_dev)), max(1, int(h * s_dev))), interpolation=cv2.INTER_AREA)
        dpr = img.shape[1] / (w * s_log)                  # tag so the logical size is exactly w * s_log
    rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB if img.ndim == 2 else cv2.COLOR_BGR2RGB)
    rgb = np.ascontiguousarray(rgb)
    h, w = rgb.shape[:2]
    pm = QPixmap.fromImage(QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGB888).copy())
    pm.setDevicePixelRatio(dpr)
    return pm


def read_image(path: str):
    try:
        return cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)   # unicode-path safe
    except Exception:
        return None


def write_image(path: str, img) -> None:
    ok, buf = cv2.imencode(os.path.splitext(path)[1] or ".png", img)
    if not ok:
        raise IOError("Could not encode image")
    buf.tofile(path)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "result"


class OddSpinBox(QSpinBox):
    """Spin box that only ever holds odd values (kernel sizes)."""
    def __init__(self):
        super().__init__()
        self.setSingleStep(2)
        self.editingFinished.connect(self._fix)

    def _fix(self):
        v = self.value()
        if v % 2 == 0:
            self.setValue(v + 1 if v < self.maximum() else v - 1)


class ProcessWorker(QThread):
    done = pyqtSignal(list, float)
    failed = pyqtSignal(str)

    def __init__(self, name, img, params):
        super().__init__()
        self._a = (name, img, params)

    def run(self):
        t0 = time.perf_counter()
        try:
            steps = run_technique(*self._a)
        except Exception as ex:                       # surface any OpenCV / numpy error
            self.failed.emit(f"{type(ex).__name__}: {ex}")
            return
        self.done.emit(steps, time.perf_counter() - t0)


# ═════════════════════════════════════════════════════════════════════════════
#  WIDGETS
# ═════════════════════════════════════════════════════════════════════════════
class ParamPanel(QWidget):
    """Auto-generated editor for the selected technique's parameters."""
    changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._form = QFormLayout(self)
        self._form.setContentsMargins(0, px(4), px(8), px(4))
        self._form.setHorizontalSpacing(px(14))
        self._form.setVerticalSpacing(px(10))
        self._form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self._widgets: Dict[str, QWidget] = {}
        self._cache: Dict[str, dict] = {}          # remembers edits per technique
        self._tech: Optional[Technique] = None

    def load(self, tech: Optional[Technique]):
        self._widgets.clear()
        while self._form.rowCount():
            self._form.removeRow(0)
        self._tech = tech
        if tech is None or not tech.params:
            lbl = QLabel("No adjustable parameters.")
            lbl.setStyleSheet(scale_css(f"color:{C['muted']};"))
            self._form.addRow(lbl)
            return
        saved = self._cache.get(tech.name, {})
        for p in tech.params:
            w = self._make(p, saved.get(p.name, p.default))
            w.setToolTip(p.tip or f"Default {p.default}" + ("" if p.kind == "choice" else f"  ·  range [{p.lo}, {p.hi}]"))
            text = p.label
            lab = QLabel(text[:1].upper() + text[1:])
            lab.setStyleSheet(scale_css(f"color:{C['muted']}; font-weight:600;"))
            lab.setToolTip(w.toolTip())
            self._form.addRow(lab, w if isinstance(w, QComboBox) else self._with_steppers(w))
            self._widgets[p.name] = w

    @staticmethod
    def _with_steppers(spin):
        """Wrap a spin box with − / + buttons (hold to repeat)."""
        box = QWidget()
        row = QHBoxLayout(box)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(px(6))
        row.addWidget(spin, 1)
        for text, slot in (("−", spin.stepDown), ("+", spin.stepUp)):
            b = QPushButton(text)
            b.setObjectName("step")
            b.setFixedHeight(px(30))
            b.setCursor(Qt.PointingHandCursor)
            b.setAutoRepeat(True)
            b.setAutoRepeatDelay(400)
            b.setAutoRepeatInterval(70)
            b.setFocusPolicy(Qt.NoFocus)
            b.clicked.connect(lambda _=False, f=slot: f())
            row.addWidget(b)
        return box

    def _make(self, p: Param, value):
        if p.kind == "choice":
            w = QComboBox()
            w.addItems(p.choices)
            w.setCurrentText(str(value))
            w.currentTextChanged.connect(self._on_change)
        else:
            if p.kind == "float":
                w = QDoubleSpinBox()
                w.setDecimals(max(2, len(str(p.step).split(".")[-1])))
            else:
                w = OddSpinBox() if p.kind == "odd" else QSpinBox()
            w.setRange(p.lo, p.hi)
            w.setSingleStep(p.step)
            w.setValue(value)
            w.setButtonSymbols(QAbstractSpinBox.NoButtons)   # type, scroll or use ↑/↓ keys
            w.valueChanged.connect(self._on_change)
            w.setKeyboardTracking(False)
        w.setFixedHeight(px(30))
        return w

    def get_params(self) -> dict:
        return {n: (w.currentText() if isinstance(w, QComboBox) else w.value()) for n, w in self._widgets.items()}

    def _on_change(self, *_):
        if self._tech:
            self._cache[self._tech.name] = self.get_params()
        self.changed.emit()

    def reset(self):
        if self._tech:
            self._cache.pop(self._tech.name, None)
            self.load(self._tech)
            self.changed.emit()


class ImageCard(QFrame):
    """Result thumbnail.  Click = enlarge, right-click = save."""
    view_requested = pyqtSignal(str, object)

    def __init__(self, title, img, thumb=None):
        super().__init__()
        thumb = thumb or px(THUMB)
        self.setObjectName("card")
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Click to enlarge  ·  right-click to save")
        self._title, self._img = title, img
        self.setFixedSize(thumb + px(20), thumb + px(76))
        lay = QVBoxLayout(self)
        lay.setContentsMargins(px(10), px(10), px(10), px(8))
        lay.setSpacing(px(6))

        pic = QLabel()
        pic.setFixedSize(thumb, thumb)
        pic.setAlignment(Qt.AlignCenter)
        pic.setPixmap(to_qpixmap(img, thumb, thumb))
        lay.addWidget(pic)

        t = QLabel(title)
        t.setStyleSheet(scale_css("font-size:12px; font-weight:700;"))
        t.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        t.setWordWrap(True)
        t.setFixedHeight(px(32))
        lay.addWidget(t)

        h, w = img.shape[:2]
        info = QLabel(f"{w}×{h}")
        info.setStyleSheet(scale_css(f"color:{C['muted']}; font-size:11px;"))
        lay.addWidget(info)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self.rect().contains(e.pos()):
            self.view_requested.emit(self._title, self._img)
        super().mouseReleaseEvent(e)

    def contextMenuEvent(self, e):
        menu = QMenu(self)
        menu.addAction("Enlarge", lambda: self.view_requested.emit(self._title, self._img))
        menu.addAction("Save as…", self._save)
        menu.exec_(e.globalPos())

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save image", f"{slug(self._title)}.png",
                                              "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp)")
        if path:
            try:
                write_image(path, self._img)
            except Exception as ex:
                QMessageBox.critical(self, "Save failed", str(ex))


class _ZoomView(QGraphicsView):
    def wheelEvent(self, e):
        f = 1.15 if e.angleDelta().y() > 0 else 1 / 1.15
        self.scale(f, f)


class ZoomViewer(QDialog):
    """Pan / zoom viewer (mouse wheel zooms, drag pans)."""
    def __init__(self, title, img, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle(title)
        self.resize(px(1000), px(720))
        self._img = img
        lay = QVBoxLayout(self)
        lay.setContentsMargins(px(12), px(12), px(12), px(10))
        lay.setSpacing(px(6))
        self.view = _ZoomView()
        self.view.setFrameShape(QFrame.NoFrame)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setStyleSheet(scale_css(f"background:{C['panel']}; border-radius:8px;"))
        self.view.setToolTip("Scroll to zoom  ·  drag to pan")
        scene = QGraphicsScene(self)
        self.item = scene.addPixmap(to_qpixmap(img))
        self.view.setScene(scene)
        lay.addWidget(self.view)
        row = QHBoxLayout()
        row.setSpacing(px(8))
        for text, slot, obj in (("Fit", self._fit, "tool"), ("100%", self._actual, "tool"),
                                ("Save", self._save, "primary")):
            b = QPushButton(text)
            b.setObjectName(obj)
            b.setMinimumWidth(px(84))
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, s=slot: s())
            row.addWidget(b)
        row.addStretch()
        lay.addLayout(row)

    def showEvent(self, e):
        super().showEvent(e)
        QTimer.singleShot(0, self._fit)

    def _fit(self):
        self.view.fitInView(self.item, Qt.KeepAspectRatio)

    def _actual(self):
        self.view.resetTransform()

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save image", "result.png", "PNG (*.png);;JPEG (*.jpg)")
        if path:
            write_image(path, self._img)


# ═════════════════════════════════════════════════════════════════════════════
#  LIVE VIDEO DIALOG
# ═════════════════════════════════════════════════════════════════════════════
def make_aruco_detector(dict_name):
    ar = cv2.aruco
    dictionary = ar.getPredefinedDictionary(getattr(ar, dict_name))
    if hasattr(ar, "ArucoDetector"):                       # OpenCV >= 4.7
        det = ar.ArucoDetector(dictionary, ar.DetectorParameters())
        return lambda g: det.detectMarkers(g)[:2]
    params = ar.DetectorParameters_create()                # legacy API
    return lambda g: ar.detectMarkers(g, dictionary, parameters=params)[:2]


class LivePanel(QWidget):
    """ArUco: one camera panel.  Motion / Anomaly: camera | threshold | masked.
    Lives inside the main window (no separate window); emits ``closed`` when the camera stops."""

    closed = pyqtSignal(str)

    def __init__(self, cap, technique, parent=None):
        super().__init__(parent)
        self._cap, self._tech, self._running = cap, technique, True
        self._ref = None
        self._last = None
        self._frames, self._t0, self._fps = 0, time.perf_counter(), 0.0
        self._mog2 = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=30, detectShadows=False)
        self._detect = None
        aruco = technique == "ArUco Marker Detection"

        root = QVBoxLayout(self)
        root.setContentsMargins(px(16), px(16), px(16), px(16))
        root.setSpacing(px(10))

        # ── controls
        top = QHBoxLayout()
        top.setSpacing(px(10))
        name_lbl = QLabel(technique)
        name_lbl.setStyleSheet(scale_css("font-size:15px; font-weight:700;"))
        top.addWidget(name_lbl)
        top.addSpacing(px(8))
        if aruco:
            self._dict_combo = QComboBox()
            self._dict_combo.addItems([d for d in ("DICT_4X4_50", "DICT_5X5_50", "DICT_6X6_50", "DICT_7X7_50",
                                                  "DICT_ARUCO_ORIGINAL") if hasattr(cv2.aruco, d)])
            self._dict_combo.currentTextChanged.connect(self._set_dict)
            top.addWidget(self._hint("Dictionary"))
            top.addWidget(self._dict_combo)
            self._set_dict(self._dict_combo.currentText())
        else:
            self._thr = QSlider(Qt.Horizontal)
            self._thr.setRange(5, 100)
            self._thr.setValue(30)
            self._thr.setFixedWidth(px(140))
            self._thr.valueChanged.connect(lambda v: self._mog2.setVarThreshold(float(v)))
            self._thr_lbl = self._hint("Threshold 30")
            self._thr_lbl.setMinimumWidth(px(86))
            self._thr.valueChanged.connect(lambda v: self._thr_lbl.setText(f"Threshold {v}"))
            self._area = QSpinBox()
            self._area.setRange(0, 100000)
            self._area.setValue(500)
            self._area.setSingleStep(100)
            self._area.setButtonSymbols(QAbstractSpinBox.NoButtons)
            self._area.setFixedWidth(px(72))
            top.addWidget(self._thr_lbl)
            top.addWidget(self._thr)
            top.addWidget(self._hint("Min area"))
            top.addWidget(self._area)
            reset = QPushButton("Reset reference" if technique == "Anomaly Detection" else "Reset background")
            reset.clicked.connect(self._reset_ref)
            top.addWidget(reset)
        top.addStretch()
        snap = QPushButton("Save frame")
        snap.clicked.connect(self._snapshot)
        top.addWidget(snap)
        stop = QPushButton("Stop camera")
        stop.setObjectName("primary")
        stop.setCursor(Qt.PointingHandCursor)
        stop.clicked.connect(lambda _=False: self._stop())
        top.addWidget(stop)
        root.addLayout(top)

        # ── panels
        panels = QHBoxLayout()
        panels.setSpacing(px(10))
        self._lbl_cam = self._panel(None if aruco else "Camera", panels)
        if aruco:
            self._lbl_thr = self._lbl_masked = None
        else:
            self._lbl_thr = self._panel("Threshold", panels)
            self._lbl_masked = self._panel("Masked", panels)
        root.addLayout(panels, 1)

        self._status = QLabel("Starting…")
        self._status.setStyleSheet(scale_css(f"color:{C['muted']};"))
        root.addWidget(self._status)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_frame)
        self._timer.start(30)
        QShortcut(QKeySequence("Esc"), self, activated=self._stop)       # Esc stops the camera

    @staticmethod
    def _hint(text):
        lbl = QLabel(text)
        lbl.setStyleSheet(scale_css(f"color:{C['muted']};"))
        return lbl

    def _panel(self, header, layout):
        frame = QFrame()
        frame.setObjectName("panel")
        v = QVBoxLayout(frame)
        v.setContentsMargins(px(8), px(8), px(8), px(8))
        v.setSpacing(px(4))
        if header:
            hdr = QLabel(header)
            hdr.setStyleSheet(scale_css(f"color:{C['muted']}; font-size:11px;"))
            v.addWidget(hdr)
        img = QLabel()
        img.setAlignment(Qt.AlignCenter)
        img.setMinimumSize(1, 1)
        img.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)     # prevents pixmap-driven growth
        v.addWidget(img, 1)
        layout.addWidget(frame)
        return img

    def _set_dict(self, name):
        self._detect = make_aruco_detector(name)

    def _reset_ref(self):
        self._ref = None
        self._mog2 = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=float(self._thr.value()), detectShadows=False)

    def _show(self, lbl, img):
        pm = to_qpixmap(img).scaled(max(1, int(lbl.width() * UI_DPR)), max(1, int(lbl.height() * UI_DPR)),
                                    Qt.KeepAspectRatio, Qt.FastTransformation)
        pm.setDevicePixelRatio(UI_DPR)
        lbl.setPixmap(pm)

    def _snapshot(self):
        if self._last is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save snapshot", "snapshot.png", "PNG (*.png);;JPEG (*.jpg)")
        if path:
            write_image(path, self._last)

    def _next_frame(self):
        if not self._running:
            return
        ok, frame = self._cap.read()
        if not ok:
            self._stop("Camera stopped delivering frames.")
            return
        self._last = frame
        self._frames += 1
        if self._frames % 15 == 0:
            now = time.perf_counter()
            self._fps, self._t0 = 15 / (now - self._t0), now

        if self._tech == "ArUco Marker Detection":
            corners, ids = self._detect(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
            disp = frame.copy()
            if ids is not None and len(ids):
                cv2.aruco.drawDetectedMarkers(disp, corners, ids)
                lst = ids.flatten().tolist()
                self._status.setText(f"Detected {len(lst)} marker(s) — IDs: {', '.join(map(str, lst))}   |   {self._fps:.0f} FPS")
            else:
                self._status.setText(f"No markers detected   |   {self._fps:.0f} FPS")
            self._show(self._lbl_cam, disp)
            return

        blurred = cv2.GaussianBlur(frame, (15, 15), 0)
        if self._tech == "Anomaly Detection":
            if self._ref is None:
                self._ref = blurred.copy()
            gray_diff = cv2.cvtColor(cv2.absdiff(self._ref, blurred), cv2.COLOR_BGR2GRAY)
            thresh = cv2.dilate(cv2.threshold(gray_diff, self._thr.value(), 255, cv2.THRESH_BINARY)[1], None, iterations=1)
            label = "Anomalies"
        else:
            k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            thresh = cv2.morphologyEx(self._mog2.apply(blurred), cv2.MORPH_OPEN, k)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, k, iterations=2)
            label = "Motion"
        disp, n = frame.copy(), 0
        for c in contours_of(thresh):
            if cv2.contourArea(c) >= self._area.value():
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(disp, (x, y), (x + w, y + h), (0, 255, 0), 2)
                n += 1
        self._status.setText(f"{label}: {n} region(s)   |   {self._fps:.0f} FPS")
        self._show(self._lbl_cam, disp)
        self._show(self._lbl_thr, thresh)
        self._show(self._lbl_masked, cv2.bitwise_and(frame, frame, mask=thresh))

    def _stop(self, reason=""):
        if not self._running:
            return
        self._running = False
        self._timer.stop()
        self._cap.release()
        self.closed.emit(reason)

    def closeEvent(self, e):
        self._stop()
        super().closeEvent(e)


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═════════════════════════════════════════════════════════════════════════════
class ImageProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Processing Lab")
        self.resize(px(1440), px(900))
        self.setStyleSheet(scale_css(STYLE_SHEET))
        self.setAcceptDrops(True)

        self._img_full = None          # as loaded
        self._img = None               # downscaled for processing
        self._img_name = ""
        self._tech: Optional[Technique] = None
        self._worker: Optional[ProcessWorker] = None
        self._live: Optional[LivePanel] = None
        self._pending = False
        self._cards: List[ImageCard] = []
        self._last_steps: List[Tuple[str, np.ndarray]] = []

        self._auto_timer = QTimer(self, singleShot=True, interval=250)
        self._auto_timer.timeout.connect(lambda: self._request_process(silent=True))
        self._reflow_timer = QTimer(self, singleShot=True, interval=80)
        self._reflow_timer.timeout.connect(self._reflow)
        self._preview_timer = QTimer(self, singleShot=True, interval=80)
        self._preview_timer.timeout.connect(self._refresh_input)

        self._build_ui()
        for key, slot in (("Ctrl+O", self._upload_image), ("F5", self._request_process),
                          ("Ctrl+Return", self._request_process), ("Ctrl+S", self._export_all),
                          ("Ctrl+F", lambda: self._search.setFocus())):
            QShortcut(QKeySequence(key), self, activated=slot)

    # ── UI construction ─────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # top bar: title + the two things you actually do with files
        top = QFrame()
        top.setObjectName("top")
        top.setFixedHeight(px(52))
        tl = QHBoxLayout(top)
        tl.setContentsMargins(px(20), 0, px(16), 0)
        tl.setSpacing(px(8))
        title = QLabel("Image Lab")
        title.setStyleSheet(scale_css("font-size:22px; font-weight:800;"))
        tl.addWidget(title)
        tl.addStretch()
        self._btn(tl, "Open image", "primary", self._upload_image, "Ctrl+O")
        self._export_btn = self._btn(tl, "Export all", None, self._export_all, "Ctrl+S")
        self._export_btn.setEnabled(False)
        root.addWidget(top)

        # hairline progress strip - only animates while processing
        self._busy = QProgressBar()
        self._busy.setTextVisible(False)
        self._busy.setFixedHeight(px(2))
        self._busy.setRange(0, 1)
        self._busy.setValue(0)
        root.addWidget(self._busy)

        split = QSplitter(Qt.Horizontal)
        split.setHandleWidth(1)
        root.addWidget(split, 1)

        # ── sidebar
        side = QFrame()
        side.setObjectName("sidebar")
        side.setMinimumWidth(px(230))
        side.setMaximumWidth(px(360))
        sl = QVBoxLayout(side)
        sl.setContentsMargins(px(12), px(12), px(8), px(8))
        sl.setSpacing(px(8))
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search techniques")
        self._search.textChanged.connect(self._filter_tree)
        sl.addWidget(self._search)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(px(10))
        self._tree.setRootIsDecorated(False)
        self._tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._tree.setFocusPolicy(Qt.NoFocus)
        cat_font = QFont(self._tree.font())
        cat_font.setWeight(QFont.ExtraBold)
        cat_font.setPixelSize(px(10))
        cat_font.setLetterSpacing(QFont.AbsoluteSpacing, 0.6 * UI_SCALE)
        for cat in CATEGORIES:
            techs = [t for t in REGISTRY.values() if t.category == cat]
            if not techs:
                continue
            ci = QTreeWidgetItem([cat.upper()])           # headers: small caps in the accent colour
            ci.setFont(0, cat_font)
            ci.setForeground(0, QColor(C["accent"]))
            ci.setSizeHint(0, QSize(0, px(38)))               # extra air above each group
            ci.setTextAlignment(0, Qt.AlignLeft | Qt.AlignBottom)
            ci.setFlags(Qt.ItemIsEnabled)                 # headers: not selectable, click toggles
            self._tree.addTopLevelItem(ci)
            for t in techs:
                it = QTreeWidgetItem([t.name])
                it.setData(0, Qt.UserRole, t.name)
                it.setToolTip(0, t.desc)
                ci.addChild(it)
            ci.setExpanded(True)
        self._tree.currentItemChanged.connect(self._on_tech_changed)
        self._tree.itemClicked.connect(lambda it, _c: it.setExpanded(not it.isExpanded()) if it.childCount() else None)
        sl.addWidget(self._tree, 1)
        split.addWidget(side)

        # ── right side
        right = QSplitter(Qt.Vertical)
        right.setHandleWidth(1)

        top_right = QWidget()
        tr = QHBoxLayout(top_right)
        tr.setContentsMargins(px(16), px(16), px(16), px(8))
        tr.setSpacing(px(16))

        # input image
        inp = QFrame()
        inp.setObjectName("panel")
        il = QVBoxLayout(inp)
        il.setContentsMargins(px(14), px(10), px(14), px(12))
        il.setSpacing(px(6))
        self._input_info = self._muted("")
        self._input_info.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        il.addWidget(self._input_info)
        self._input_label = QLabel("Drop an image here, or click to open")
        self._input_label.setAlignment(Qt.AlignCenter)
        self._input_label.setMinimumSize(1, 1)
        self._input_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self._input_label.setStyleSheet(scale_css(f"color:{C['muted']};"))
        self._input_label.setCursor(Qt.PointingHandCursor)
        self._input_label.installEventFilter(self)
        il.addWidget(self._input_label, 1)
        self._input_panel = inp
        tr.addWidget(inp, 3)

        # settings for the selected technique
        pc = QFrame()
        pc.setObjectName("panel")
        pc.setFixedWidth(px(310))
        pl = QVBoxLayout(pc)
        pl.setContentsMargins(px(18), px(16), px(18), px(12))
        pl.setSpacing(px(8))
        self._tech_name = QLabel("Select a technique")
        self._tech_name.setStyleSheet(scale_css(f"color:{C['muted']}; font-size:15px; font-weight:700;"))
        self._tech_name.setWordWrap(True)
        pl.addWidget(self._tech_name)
        self._tech_desc = self._muted("")
        self._tech_desc.setWordWrap(True)
        pl.addWidget(self._tech_desc)
        pl.addSpacing(px(6))
        self._param_panel = ParamPanel()
        self._param_panel.changed.connect(self._on_param_changed)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.NoFrame)
        sc.setWidget(self._param_panel)
        pl.addWidget(sc, 1)

        # live-video techniques only: camera + start (everything else runs automatically)
        self._live_box = QWidget()
        lb = QHBoxLayout(self._live_box)
        lb.setContentsMargins(0, 0, 0, 0)
        lb.setSpacing(px(8))
        self._cam_combo = QComboBox()
        self._cam_combo.addItems([f"Camera {i}" for i in range(5)])
        lb.addWidget(self._cam_combo)
        self._start_btn = self._btn(lb, "Start camera", "primary", self._request_process, "F5")
        self._live_box.hide()
        pl.addWidget(self._live_box)

        self._reset_btn = self._btn(pl, "Reset to defaults", "ghost", self._param_panel.reset)
        self._reset_btn.hide()
        tr.addWidget(pc)
        right.addWidget(top_right)

        # results
        out = QWidget()
        ol = QVBoxLayout(out)
        ol.setContentsMargins(px(16), px(8), px(16), px(16))
        ol.setSpacing(px(8))
        oh = QHBoxLayout()
        oh.addWidget(self._section("Results"))
        oh.addStretch()
        self._status = self._muted("Select a technique to begin")
        oh.addWidget(self._status)
        ol.addLayout(oh)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.viewport().installEventFilter(self)
        holder = QWidget()
        self._out_layout = QGridLayout(holder)
        self._out_layout.setContentsMargins(0, 0, 0, 0)
        self._out_layout.setSpacing(px(14))
        self._scroll.setWidget(holder)
        ol.addWidget(self._scroll)
        right.addWidget(out)
        right.setSizes([px(360), px(540)])
        right.setStretchFactor(0, 0)
        right.setStretchFactor(1, 1)
        self._stack = QStackedWidget()          # page 0 = normal view, page 1 = live camera view
        self._stack.addWidget(right)
        split.addWidget(self._stack)
        split.setSizes([px(260), px(1180)])
        split.setStretchFactor(1, 1)

    def _muted(self, text):
        l = QLabel(text)
        l.setStyleSheet(scale_css(f"color:{C['muted']}; font-size:12px;"))
        return l

    def _section(self, text):
        l = QLabel(text)
        l.setStyleSheet(scale_css("font-size:13px; font-weight:700;"))
        return l

    def _btn(self, layout, text, obj, slot, shortcut=None):
        b = QPushButton(text)
        if obj:
            b.setObjectName(obj)
        b.setCursor(Qt.PointingHandCursor)
        if shortcut:
            b.setToolTip(shortcut)
        b.clicked.connect(lambda _=False: slot())
        layout.addWidget(b)
        return b

    # ── events ──────────────────────────────────────────────────────────────
    def eventFilter(self, obj, ev):
        if ev.type() == QEvent.Resize:
            if obj is self._scroll.viewport():
                self._reflow_timer.start()
            elif obj is self._input_label:
                self._preview_timer.start()
        elif (ev.type() == QEvent.MouseButtonRelease and obj is self._input_label
              and self._img is None and ev.button() == Qt.LeftButton):
            self._upload_image()
        return super().eventFilter(obj, ev)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        if urls:
            self._load_image(urls[0].toLocalFile())

    def closeEvent(self, e):
        self._stop_live()
        if self._worker and self._worker.isRunning():
            self._worker.wait(3000)
        super().closeEvent(e)

    # ── sidebar ─────────────────────────────────────────────────────────────
    def _filter_tree(self, text):
        text = text.strip().lower()
        for i in range(self._tree.topLevelItemCount()):
            cat = self._tree.topLevelItem(i)
            cat_hit = text in cat.text(0).lower()
            visible = False
            for j in range(cat.childCount()):
                ch = cat.child(j)
                show = not text or cat_hit or text in ch.data(0, Qt.UserRole).lower()
                ch.setHidden(not show)
                visible |= show
            cat.setHidden(not visible)
            if text:
                cat.setExpanded(True)

    def _on_tech_changed(self, cur, _prev):
        name = cur.data(0, Qt.UserRole) if cur else None
        if not name:
            return
        self._stop_live()                        # picking another technique leaves the camera view
        self._tech = REGISTRY[name]
        self._tech_name.setText(name)
        self._input_panel.setVisible(not self._tech.live)      # live techniques use the camera, not the opened image
        if self._tech.live:
            self._clear_results()
            self._status.setText("Choose a camera and press Start camera")
        self._tech_name.setStyleSheet(scale_css("font-size:15px; font-weight:700;"))
        self._tech_desc.setText(self._tech.desc)
        self._param_panel.load(self._tech)
        self._live_box.setVisible(self._tech.live)
        self._reset_btn.setVisible(bool(self._tech.params))
        self._on_param_changed()

    def _on_param_changed(self):
        if self._tech and not self._tech.live and self._img is not None:
            self._auto_timer.start()

    # ── image loading ───────────────────────────────────────────────────────
    def _upload_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open image", "",
                                              "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp);;All files (*.*)")
        if path:
            self._load_image(path)

    def _load_image(self, path):
        img = read_image(path)
        if img is None:
            QMessageBox.critical(self, "Error", f"Could not read the image:\n{path}")
            return
        self._img_full, self._img_name = img, os.path.basename(path)
        self._img = fit(img, MAX_PROC_DIM)
        h, w = img.shape[:2]
        note = "  (downscaled for processing)" if self._img.shape != img.shape else ""
        self._input_info.setText(f"{self._img_name}  ·  {w}×{h}{note}")
        self._input_label.setCursor(Qt.ArrowCursor)
        self._refresh_input()
        if self._tech and not self._tech.live:
            self._request_process(silent=True)

    def _refresh_input(self):
        if self._img is None:
            return
        self._input_label.setText("")
        self._input_label.setPixmap(to_qpixmap(self._img, max(1, self._input_label.width() - 6),
                                               max(1, self._input_label.height() - 6)))

    # ── processing ──────────────────────────────────────────────────────────
    def _request_process(self, silent=False):
        t = self._tech
        if t is None:
            if not silent:
                QMessageBox.warning(self, "No technique", "Please select a technique from the sidebar.")
            return
        if t.live:
            if not silent:
                self._open_live(t)
            return
        if self._img is None:
            if not silent:
                QMessageBox.warning(self, "No image", "Please upload an image first.")
            return
        if self._worker and self._worker.isRunning():
            self._pending = True               # re-run with the newest parameters afterwards
            return
        self._pending = False
        self._set_busy(True)
        w = ProcessWorker(t.name, self._img, self._param_panel.get_params())
        w.done.connect(self._on_done)
        w.failed.connect(self._on_failed)
        w.finished.connect(self._on_worker_finished)
        self._worker = w
        w.start()

    def _set_busy(self, busy):
        if busy:
            self._busy.setRange(0, 0)              # indeterminate
        else:
            self._busy.setRange(0, 1)
            self._busy.setValue(0)

    def _on_done(self, steps, secs):
        if self._tech and self._tech.live:           # a late result from the previous technique
            return
        self._render_output(steps)
        self._status.setText(f"{len(steps)} result{'s' if len(steps) != 1 else ''}  ·  {secs * 1000:.0f} ms")

    def _on_failed(self, msg):
        self._status.setText("Processing failed")
        QMessageBox.critical(self, "Processing error", msg)

    def _on_worker_finished(self):
        self._set_busy(False)
        if self._pending:
            QTimer.singleShot(0, lambda: self._request_process(silent=True))

    # ── output grid ─────────────────────────────────────────────────────────
    def _clear_results(self):
        for i in reversed(range(self._out_layout.count())):
            self._out_layout.takeAt(i)
        for c in self._cards:
            c.setParent(None)
            c.deleteLater()
        self._cards, self._last_steps = [], []
        self._export_btn.setEnabled(False)

    def _render_output(self, steps):
        lay = self._out_layout
        for i in reversed(range(lay.count())):
            lay.takeAt(i)
        for c in self._cards:
            c.setParent(None)
            c.deleteLater()
        self._cards = []
        for title, img in steps:
            card = ImageCard(title, img)
            card.view_requested.connect(lambda t, im: ZoomViewer(t, im, self).show())
            self._cards.append(card)
        self._last_steps = steps
        self._export_btn.setEnabled(bool(steps))
        self._reflow()

    def _reflow(self):
        lay = self._out_layout
        for i in reversed(range(lay.count())):
            lay.takeAt(i)
        for r in range(lay.rowCount() + 1):
            lay.setRowStretch(r, 0)
        for c in range(lay.columnCount() + 1):
            lay.setColumnStretch(c, 0)
        if not self._cards:
            return
        cw = self._cards[0].width() + lay.spacing()
        cols = max(1, (self._scroll.viewport().width() - 4) // cw)
        r = 0
        for i, card in enumerate(self._cards):
            r, c = divmod(i, cols)
            lay.addWidget(card, r, c, Qt.AlignTop | Qt.AlignLeft)
        lay.setRowStretch(r + 1, 1)
        lay.setColumnStretch(cols, 1)

    def _export_all(self):
        if not self._last_steps:
            return
        folder = QFileDialog.getExistingDirectory(self, "Export all results to…")
        if not folder:
            return
        base = slug(self._tech.name if self._tech else "result")
        try:
            for i, (title, img) in enumerate(self._last_steps, 1):
                write_image(os.path.join(folder, f"{base}_{i:02d}_{slug(title)[:40]}.png"), img)
        except Exception as ex:
            QMessageBox.critical(self, "Export failed", str(ex))
            return
        self._status.setText(f"Exported {len(self._last_steps)} images to {folder}")

    def _reset_params(self):
        self._param_panel.reset()

    # ── live video ──────────────────────────────────────────────────────────
    def _open_live(self, t):
        if t.name == "ArUco Marker Detection" and not hasattr(cv2, "aruco"):
            QMessageBox.critical(self, "ArUco unavailable",
                                 "Your OpenCV build has no aruco module.\nInstall:  pip install opencv-contrib-python")
            return
        if self._live is not None:
            return
        idx = self._cam_combo.currentIndex()
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW) if sys.platform == "win32" else cv2.VideoCapture(idx)
        if not cap.isOpened():
            QMessageBox.critical(self, "Webcam error", f"Could not open camera {idx}.")
            return
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self._live = LivePanel(cap, t.name)
        self._live.closed.connect(self._close_live)
        self._stack.addWidget(self._live)
        self._stack.setCurrentWidget(self._live)
        self._status.setText(f"{t.name} running")

    def _stop_live(self):
        if self._live is not None:
            self._live._stop()

    def _close_live(self, msg=""):
        panel, self._live = self._live, None
        if panel is not None:
            self._stack.setCurrentIndex(0)
            self._stack.removeWidget(panel)
            panel.deleteLater()
        self._status.setText(msg or "Camera stopped")


# ═════════════════════════════════════════════════════════════════════════════
#  STARTUP HELPERS  (display scale)
# ═════════════════════════════════════════════════════════════════════════════
def init_display(app):
    """Measure the screen once: device pixel ratio + a layout scale from its logical height."""
    global UI_SCALE, UI_DPR
    scr = app.primaryScreen()
    UI_DPR = max(1.0, float(scr.devicePixelRatio()))
    env = os.environ.get("IMAGE_LAB_SCALE")
    try:
        UI_SCALE = float(env) if env else max(0.85, min(1.35, scr.size().height() / 1080.0))
    except ValueError:
        UI_SCALE = 1.0
    UI_SCALE = round(UI_SCALE, 2)


# ═════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    if hasattr(Qt, "PassThrough") and hasattr(QApplication, "setHighDpiScaleFactorRoundingPolicy"):
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.PassThrough)    # true fractional scaling (125 %, 150 %…)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    init_display(app)
    pal = QPalette()
    for role, col in ((QPalette.Window, C["bg"]), (QPalette.WindowText, C["text"]), (QPalette.Base, C["input_bg"]),
                      (QPalette.AlternateBase, C["panel"]), (QPalette.Text, C["text"]), (QPalette.Button, C["card"]),
                      (QPalette.ButtonText, C["text"]), (QPalette.Highlight, C["accent"]), (QPalette.HighlightedText, "white")):
        pal.setColor(role, QColor(col))
    app.setPalette(pal)
    win = ImageProcessorApp()
    win.showMaximized()
    sys.exit(app.exec_())
