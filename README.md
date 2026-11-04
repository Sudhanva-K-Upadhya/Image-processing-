# Image Processor

A desktop application for exploring and applying classical image processing techniques, built with Python and OpenCV.

![Image Processor](img1.png)
![Image Processor](img2.png)

---

## Installation

```
pip install opencv-contrib-python numpy pillow
```

`tkinter` comes built-in with Python. If it's missing, install it via your system package manager.

### [Click here to Download the software without any dependencies](https://github.com/Sudhanva-K-Upadhya/Image-processing-/releases/latest)
---

## Usage

```
python image_processor.py
```

Load an image, pick a technique from the sidebar, and hit Apply.

---

## Techniques

| Category | Techniques |
|---|---|
| Histogram Processing | Histogram Equalization, CLAHE / Specification |
| Gray Level Transformations | Linear, Logarithmic, Power Law, Piecewise, Contrast Stretching |
| Image Enhancement | Point Processing, Image Subtraction, Image Averaging |
| Spatial Filtering | Smoothing, Sharpening, Order-Statistic, Gradient, Laplacian |
| Edge & Line Detection | Canny, Sobel, Line Detection, Point Detection |
| Frequency Domain | Ideal LPF, Gaussian LPF, Homomorphic Filtering |
| Image Segmentation | Thresholding, Otsu's Method, Region Growing, Watershed |
| Morphological Operations | Erosion, Dilation, Opening, Closing, Thinning, Convex Hull |
| Boundary & Shape | Edge Linking, Boundary Detection, Polygon Fitting, Shape Detection |
| Color & Vision | Gaussian Blur, Color Conversion, Color Masking, Perspective Transform |
| Live Video & Detection | ArUco Marker Detection, Motion Detection, Anomaly Detection |

---

## Libraries

- [opencv-contrib-python](https://pypi.org/project/opencv-contrib-python/) — core image processing and computer vision
- [numpy](https://numpy.org/) — numerical operations and array manipulation
- [Pillow](https://python-pillow.org/) — image display integration with Tkinter
- tkinter — GUI framework (Python built-in)

---

## Features

- Load any image and apply 40+ processing techniques 
- Live webcam support for real-time detection tasks
- Save any output image 
- Side-by-side result panels

---

## Project Structure

```
image_processor.py   # Main application
img.jpg               # Sample image (optional)
README.md
```

---

## License

MIT License
