import cv2
import numpy as np

def split_into_grid(image_path, rows=10, cols=10):
    """Open an image and cut it into a grid of equal squares."""
    image = cv2.imread(r"C:\Users\LENOVO\OneDrive\Desktop\Github\Nathacks2026_proj\a.png")
    if image is None:
        raise FileNotFoundError(f"Could not open image: {image_path}")

    height, width = image.shape[:2]
    tile = min(height // rows, width // cols)

    top = (height - tile * rows) // 2
    left = (width - tile * cols) // 2

    grid = []
    for r in range(rows):
        row_tiles = []
        for c in range(cols):
            y = top + r * tile
            x = left + c * tile
            row_tiles.append(image[y:y + tile, x:x + tile])
        grid.append(row_tiles)
    return grid

def show_grid(grid, gap=4):
    rows, cols = len(grid), len(grid[0])
    tile_h, tile_w = grid[0][0].shape[:2]

    canvas = np.full(
        (rows * tile_h + (rows - 1) * gap, cols * tile_w + (cols - 1) * gap, 3),
        255,
        dtype=np.uint8,
    )

    for r in range(rows):
        for c in range(cols):
            y = r * (tile_h + gap)
            x = c * (tile_w + gap)
            canvas[y:y + tile_h, x:x + tile_w] = grid[r][c]

    cv2.namedWindow("Grid", cv2.WINDOW_NORMAL)
    cv2.imshow("Grid", canvas)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    grid = split_into_grid("photo.jpg", rows=10, cols=10)
    show_grid(grid)


