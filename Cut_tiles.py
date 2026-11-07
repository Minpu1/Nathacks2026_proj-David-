import cv2
import numpy as np

def split_into_grid(image_path, rows, cols):
    """Open an image and cut all of it into rows x cols pieces."""
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not open image: {image_path}")

    height, width = image.shape[:2]
    y_edges = np.linspace(0, height, rows + 1).astype(int)
    x_edges = np.linspace(0, width, cols + 1).astype(int)

    grid = []
    for r in range(rows):
        row_pieces = []
        for c in range(cols):
            piece = image[y_edges[r]:y_edges[r + 1], x_edges[c]:x_edges[c + 1]]
            row_pieces.append(piece)
        grid.append(row_pieces)
    return grid

def show_grid(grid, gap=4):
    rows, cols = len(grid), len(grid[0])
    heights = [grid[r][0].shape[0] for r in range(rows)]
    widths = [grid[0][c].shape[1] for c in range(cols)]

    canvas = np.full(
        (sum(heights) + (rows - 1) * gap, sum(widths) + (cols - 1) * gap, 3),
        255,
        dtype=np.uint8,
    )

    y = 0
    for r in range(rows):
        x = 0
        for c in range(cols):
            canvas[y:y + heights[r], x:x + widths[c]] = grid[r][c]
            x += widths[c] + gap
        y += heights[r] + gap

    cv2.namedWindow("Grid", cv2.WINDOW_NORMAL)
    cv2.imshow("Grid", canvas)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    row = int(input("Enter the number of rows: "))
    col = int(input("Enter the number of columns: "))
    path = r"C:\Users\LENOVO\OneDrive\Desktop\Github\Nathacks2026_proj\a.png"
    grid = split_into_grid(path, row, col)
    show_grid(grid)