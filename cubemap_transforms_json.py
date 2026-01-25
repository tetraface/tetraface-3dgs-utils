import os
import sys
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import numpy as np
import cv2
from PIL import Image

example_text = '''Example:
  python cubemap_transforms_json.py .
  python cubemap_transforms_json.py . ./cubic --yaw 45 --stitch 2.5'''

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help()
        sys.stderr.write(f'\n{message}\n')
        sys.exit(1)

parser = MyParser(description="Convert transform.json from equirectanglar to cubemap.", formatter_class=argparse.RawDescriptionHelpFormatter, epilog=example_text)
parser.add_argument("input_dir", help="Input directory contains 'transforms.json' file and 'images' directory")
parser.add_argument("output_dir", nargs="?", help="Output directory for cubified data (default='./cubic')")
parser.add_argument("--mask_dir", help="Input mask images directory (default='./masks')")
parser.add_argument("--yaw", type=float, default=45.0, help="Shift the horizontal angle (default=45.0 degrees)")
parser.add_argument("--stitch", type=float, default=0.0, help="Angle to avoid stitching areas (default=0.0 degrees)")
parser.add_argument("--fov", type=float, default=90.0, help="Field of view for cubemap faces (default=90.0 degrees)")
parser.add_argument("--no_image", action="store_true", help="Without cube-map conversion of images & masks")
parser.add_argument("--no_transform", action="store_true", help="No transformation of coordinates for LichtFeld Studio")
args = parser.parse_args()

INPUT_DIR = args.input_dir
OUTPUT_DIR = args.output_dir if args.output_dir else f"{INPUT_DIR}/cubic"
IMAGE_DIR = INPUT_DIR
MASK_DIR = args.mask_dir if args.mask_dir else f"{INPUT_DIR}/masks"
OUTPUT_IMAGE_DIR = f"{OUTPUT_DIR}/images"
OUTPUT_MASK_DIR = f"{OUTPUT_DIR}/masks"
YAW = args.yaw if args.yaw else 45.0
STITCH = args.stitch if args.stitch else 0.0
FOV = args.fov if args.fov else 90.0
NO_IMAGE  = args.no_image
NO_TRANSFORM = args.no_transform
_WORKER_REMAP_TABLES = None


def rot4(R3):
    R4 = np.eye(4)
    R4[:3, :3] = R3
    return R4

# cubemap rotation
R_faces = [
    ("px", 90-YAW-STITCH, 0), 
    ("nx", -90-YAW-STITCH, 0),
    ("py", 0-YAW, -90),
    ("ny", 0-YAW, 90),
    ("pz", 0-YAW+STITCH, 0),
    ("nz", 180-YAW+STITCH, 0)
]

# ==========================
# Get rotation matrix from yaw/pitch
# ==========================
def rotation_matrix(yaw, pitch, forward):
    yaw   = np.deg2rad(yaw)
    pitch = np.deg2rad(pitch)

    Ry = np.array([
        [ np.cos(yaw), 0, np.sin(yaw)],
        [ 0,           1, 0          ],
        [-np.sin(yaw), 0, np.cos(yaw)]
    ])

    Rx = np.array([
        [1, 0,               0              ],
        [0, np.cos(pitch),  -np.sin(pitch)],
        [0, np.sin(pitch),   np.cos(pitch)]
    ])

    if forward:
        R = Rx @ Ry
    else:
        R = Ry @ Rx
    for i in range(3):
        for j in range(3):
            if abs(R[i,j]) < 1e-10:
                R[i,j] = 0.0
    return R


# ==========================
# create remap tables (once)
# ==========================
def build_remap(input_size, fov, yaw, pitch, output_size):
    xs, ys = np.meshgrid(
        np.arange(output_size),
        np.arange(output_size)
    )

    cx = xs - output_size / 2
    cy = ys - output_size / 2

    f = 0.5 * output_size / np.tan(np.deg2rad(fov) / 2)

    rays = np.stack([cx, -cy, np.full_like(cx, f)], axis=-1)
    rays /= np.linalg.norm(rays, axis=-1, keepdims=True)

    R = rotation_matrix(yaw, pitch, False)
    rays = rays @ R.T

    dx, dy, dz = rays[..., 0], rays[..., 1], rays[..., 2]

    lon = np.arctan2(dx, dz)
    lat = np.arcsin(dy)

    map_x = (lon / np.pi + 1) * 0.5 * input_size[0]
    map_y = (0.5 - lat / np.pi) * input_size[1]

    return map_x.astype(np.float32), map_y.astype(np.float32)

def remap_image(input_file, output_dir, REMAP_TABLES):
    basename, ext = os.path.splitext(os.path.basename(input_file))
    if basename.endswith(".jpg") or basename.endswith(".png"):
        basename, ext2 = os.path.splitext(basename)
    else:
        ext2 = ""

    print(f"Processing: {input_file}")
    img = Image.open(input_file)

    if img.mode == "L":
        equi = np.array(img)
        is_gray = True
    else:
        equi = np.array(img.convert("RGB"))
        is_gray = False

    for face, _, _ in R_faces:
        map_x, map_y = REMAP_TABLES[face]

        view = cv2.remap(
            equi,
            map_x,
            map_y,
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_WRAP
        )

        if is_gray:
            _, view = cv2.threshold(view, 127, 255, cv2.THRESH_BINARY)

        out_path = os.path.join(output_dir, basename+f"_{face}{ext2}{ext}")
        Image.fromarray(view).save(out_path)
        

def transform_json():
    # Open transforms.json
    path = os.path.join(INPUT_DIR, "transforms.json")
    if not os.path.exists(path):
        print(f"Error: {path} not found")
        return [], [], 0
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ---- Check camera model ----
    if data["camera_model"] != "EQUIRECTANGULAR":
        print("Error: camera_model is not EQUIRECTANGULAR")
        return [], [], 0

    # ---- Check input size (by the first image) ----
    INPUT_SIZE = [7840, 3920]
    OUTPUT_SIZE = 1920
    basefile = os.path.join(IMAGE_DIR, data["frames"][0]["file_path"])
    if os.path.exists(basefile):
        first_img = Image.open(basefile)
        INPUT_SIZE[0], INPUT_SIZE[1] = first_img.size
        OUTPUT_SIZE = INPUT_SIZE[1] // 2

    # ---- Convert json ----
    if NO_TRANSFORM:
        A = np.eye(4) # for LichtFeld Studio
    else:
        A = rot4(np.array([[0,0,-1],[1,0,0],[0,-1,0]])) # for Postshot/Brush

    new_frames = []
    image_files = []
    for frame in data["frames"]:    
        T = np.array(frame["transform_matrix"])
        T_world = A @ T  # apply transformation

        image_files.append(frame["file_path"])

        for face, yaw, pitch in R_faces:
            f2 = {}
            if frame["file_path"].endswith(".png"):
                f2["file_path"] = frame["file_path"].replace(
                    ".png", f"_{face}.png"
                )
            elif frame["file_path"].endswith(".jpg"):
                f2["file_path"] = frame["file_path"].replace(
                    ".jpg", f"_{face}.jpg"
                )

            R = rotation_matrix(yaw, pitch, True)
            T_face = T_world @ rot4(R.T)
            
            f2["transform_matrix"] = T_face.tolist()

            # camera parameters for each image
            """
            f2["w"] = OUTPUT_SIZE
            f2["h"] = OUTPUT_SIZE
            f2["fl_x"] = OUTPUT_SIZE / 2 / np.tan(np.deg2rad(FOV) / 2)
            f2["fl_y"] = OUTPUT_SIZE / 2 / np.tan(np.deg2rad(FOV) / 2)
            f2["cx"] = OUTPUT_SIZE / 2
            f2["cy"] = OUTPUT_SIZE / 2
            """

            new_frames.append(f2)

    out = {
        #"camera_model": "PERSPECTIVE",
        "camera_model": "SIMPLE_PINHOLE",
        "w": OUTPUT_SIZE,
        "h": OUTPUT_SIZE,
        "fl_x": OUTPUT_SIZE / 2 / np.tan(np.deg2rad(FOV) / 2),
        "fl_y": OUTPUT_SIZE / 2 / np.tan(np.deg2rad(FOV) / 2),
        "cx": OUTPUT_SIZE / 2,
        "cy": OUTPUT_SIZE / 2,
        "frames": new_frames
    }
    #out["applied_transform"] = data["applied_transform"]
    if data.get("ply_file_path"):
        out["ply_file_path"] = data["ply_file_path"]

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "transforms.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Saved transforms.json in {OUTPUT_DIR}")

    return image_files, INPUT_SIZE, OUTPUT_SIZE

def proc_convert_images(file):
    global _WORKER_REMAP_TABLES

    # ---- 4. Image & mask conversion ----
    #for file in image_files:
    image = os.path.join(IMAGE_DIR, file)
    if os.path.exists(image):
        remap_image(image, OUTPUT_IMAGE_DIR, _WORKER_REMAP_TABLES)
    masks = [
        os.path.join(MASK_DIR, os.path.basename(file)),
        os.path.join(MASK_DIR, os.path.basename(file)+".png"),
        os.path.join(MASK_DIR, os.path.basename(file)).replace(".jpg", ".png")
    ]
    for mask in masks:
        if os.path.exists(mask):
            remap_image(mask, OUTPUT_MASK_DIR, _WORKER_REMAP_TABLES)
            break

def worker_init(input_size, fov, output_size):
    global _WORKER_REMAP_TABLES

    _WORKER_REMAP_TABLES = {}
    for face, yaw, pitch in R_faces:
        _WORKER_REMAP_TABLES[face] = build_remap(
            input_size, fov, yaw, pitch, output_size
        )

def convert_images(image_files, input_size, output_size):
    print("Convert images...")

    max_workers = min(16, os.cpu_count())

    # Precompute remap tables
    """
    print("Precomputing remap tables...")
    REMAP_TABLES = {}
    for face, yaw, pitch in R_faces:
        REMAP_TABLES[face] = build_remap(
            input_size, FOV, yaw, pitch, output_size
        )
    """

    os.makedirs(OUTPUT_IMAGE_DIR, exist_ok=True)
    os.makedirs(OUTPUT_MASK_DIR, exist_ok=True)

    # Convert images in parallel
    with ProcessPoolExecutor(
        max_workers=max_workers,
              initializer=worker_init,
        initargs=(input_size, FOV, output_size)
    ) as executor:
        futures = [
            executor.submit(proc_convert_images, file)
            for file in image_files
        ]

        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print("Worker failed:", e)

if __name__ == "__main__":
    for face, yaw, pitch in R_faces:
        print(f"{face}: yaw={yaw},pitch={pitch}")

    image_files, INPUT_SIZE, OUTPUT_SIZE = transform_json()
    if len(image_files) == 0:
        sys.exit(1)
    if not NO_IMAGE:
        convert_images(image_files, INPUT_SIZE, OUTPUT_SIZE)

