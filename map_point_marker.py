"""Map Point Marker Application.

This module provides a GUI application for marking points on a campus map.
Points can be numeric (right-click) or alphanumeric (left-click) and are
saved to a JSON file for persistence.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tkinter import Canvas, Tk, messagebox, simpledialog
    from PIL import Image, ImageTk
except ImportError as e:
    print(f"Required libraries not installed: {e}")
    print("Please install: pip install pillow")
    raise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
IMAGE_PATH = Path("campus_colored.png")
JSON_PATH = Path("map_points.json")
POINT_RADIUS = 5
POINT_COLOR_NUMERIC = "red"
POINT_COLOR_ALPHANUMERIC = "blue"
TEXT_OFFSET = 10


class MapPointMarker:
    """Application for marking and managing points on a map image.

    This class handles the GUI, point management, and JSON persistence
    for marking points on a campus map.
    """

    def __init__(self, image_path: Path, json_path: Path) -> None:
        """Initialize the MapPointMarker application.

        Args:
            image_path: Path to the map image file.
            json_path: Path to the JSON file for storing points.
        """
        self.image_path = image_path
        self.json_path = json_path
        self.points: List[Dict[str, Any]] = []
        self.numeric_counter = 0
        self.alphanumeric_counter = 0
        self.delete_mode = False

        # Initialize GUI
        self.root = Tk()
        self.root.title("Map Point Marker")
        self.canvas: Optional[Canvas] = None
        self.image: Optional[Image.Image] = None
        self.original_image: Optional[Image.Image] = None
        self.photo: Optional[ImageTk.PhotoImage] = None
        self.scale_factor = 1.0
        self.original_width = 0
        self.original_height = 0

        self._setup_gui()
        self._load_points()
        self._display_points()

    def _setup_gui(self) -> None:
        """Set up the GUI components and bind event handlers."""
        if not self.image_path.exists():
            messagebox.showerror(
                "Error",
                f"Image file not found: {self.image_path}",
            )
            self.root.destroy()
            return

        # Load and display image
        try:
            # Load original image
            self.original_image = Image.open(self.image_path)
            self.original_width = self.original_image.width
            self.original_height = self.original_image.height

            # Calculate scale factor to fit screen (with 95% of screen size as max)
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            max_width = int(screen_width * 0.95)
            max_height = int(screen_height * 0.95)

            # Calculate scale factor maintaining aspect ratio
            scale_x = max_width / self.original_width
            scale_y = max_height / self.original_height
            self.scale_factor = min(scale_x, scale_y)

            # Resize image for display
            display_width = int(self.original_width * self.scale_factor)
            display_height = int(self.original_height * self.scale_factor)
            self.image = self.original_image.resize(
                (display_width, display_height),
                Image.Resampling.LANCZOS,
            )
            self.photo = ImageTk.PhotoImage(self.image)

            # Create canvas with scaled dimensions
            self.canvas = Canvas(
                self.root,
                width=display_width,
                height=display_height,
            )
            self.canvas.pack()

            # Display image
            self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

            # Bind mouse events
            self.canvas.bind("<Button-1>", self._on_left_click)
            self.canvas.bind("<Button-3>", self._on_right_click)

            # Bind keyboard events
            self.root.bind("<KeyPress-x>", self._toggle_delete_mode)
            self.root.bind("<KeyPress-X>", self._toggle_delete_mode)
            self.root.focus_set()  # Allow keyboard focus

            logger.info(
                f"GUI setup completed. Original size: {self.original_width}x{self.original_height}, "
                f"Display size: {display_width}x{display_height}, Scale: {self.scale_factor:.3f}",
            )
        except Exception as e:
            logger.error(f"Error setting up GUI: {e}")
            messagebox.showerror("Error", f"Failed to load image: {e}")
            self.root.destroy()

    def _on_left_click(self, event: Any) -> None:
        """Handle left mouse button click (alphanumeric point or delete).

        Args:
            event: Mouse event containing click coordinates.
        """
        # Convert scaled coordinates to original image coordinates
        x_original = int(event.x / self.scale_factor)
        y_original = int(event.y / self.scale_factor)

        if self.delete_mode:
            # Delete mode: find and delete the nearest point
            self._delete_nearest_point(x_original, y_original)
        else:
            # Normal mode: add alphanumeric point
            self.alphanumeric_counter += 1
            point_id = f"C{self.alphanumeric_counter}"

            point = {
                "id": point_id,
                "type": "alphanumeric",
                "x": x_original,
                "y": y_original,
            }

            self.points.append(point)
            self._draw_point(point)
            self._save_points()
            logger.info(
                f"Added alphanumeric point {point_id} at original ({x_original}, {y_original})",
            )

    def _on_right_click(self, event: Any) -> None:
        """Handle right mouse button click (numeric point).

        Args:
            event: Mouse event containing click coordinates.
        """
        # Convert scaled coordinates to original image coordinates
        x_original = int(event.x / self.scale_factor)
        y_original = int(event.y / self.scale_factor)
        
        # Request demand value from user
        demand_str = simpledialog.askstring(
            "Demanda do Ponto",
            "Digite a demanda do ponto numérico:",
            parent=self.root,
        )
        
        # If user cancels, don't create the point
        if demand_str is None:
            logger.info("Point creation cancelled by user")
            return
        
        # Validate and convert demand to number
        try:
            demand = float(demand_str)
        except ValueError:
            messagebox.showerror(
                "Erro",
                "A demanda deve ser um número válido. Ponto não criado.",
            )
            logger.warning(f"Invalid demand value entered: {demand_str}")
            return
        
        self.numeric_counter += 1
        point_id = str(self.numeric_counter)

        point = {
            "id": point_id,
            "type": "numeric",
            "x": x_original,
            "y": y_original,
            "demand": demand,
        }

        self.points.append(point)
        self._draw_point(point)
        self._save_points()
        logger.info(
            f"Added numeric point {point_id} at original ({x_original}, {y_original}) with demand {demand}",
        )

    def _draw_point(
        self,
        point: Dict[str, Any],
    ) -> None:
        """Draw a point on the canvas.

        Args:
            point: Dictionary containing point information (id, type, x, y, demand).
        """
        if self.canvas is None:
            return

        # Convert original coordinates to scaled display coordinates
        x_original = point["x"]
        y_original = point["y"]
        x = int(x_original * self.scale_factor)
        y = int(y_original * self.scale_factor)
        point_id = point["id"]
        point_type = point["type"]

        # Choose color based on point type
        color = (
            POINT_COLOR_NUMERIC
            if point_type == "numeric"
            else POINT_COLOR_ALPHANUMERIC
        )

        # Draw circle for the point
        self.canvas.create_oval(
            x - POINT_RADIUS,
            y - POINT_RADIUS,
            x + POINT_RADIUS,
            y + POINT_RADIUS,
            fill=color,
            outline="black",
            width=2,
        )

        # Draw label with ID
        self.canvas.create_text(
            x,
            y - TEXT_OFFSET - POINT_RADIUS,
            text=point_id,
            fill="black",
            font=("Arial", 10, "bold"),
        )
        
        # Draw demand label for numeric points (below the point)
        if point_type == "numeric" and "demand" in point:
            demand_text = f"D: {point['demand']}"
            self.canvas.create_text(
                x,
                y + TEXT_OFFSET + POINT_RADIUS,
                text=demand_text,
                fill="darkred",
                font=("Arial", 9),
            )

    def _load_points(self) -> None:
        """Load points from JSON file if it exists."""
        if not self.json_path.exists():
            logger.info(f"JSON file not found: {self.json_path}. Starting fresh.")
            return

        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Support both new format (separate arrays) and old format (single array)
            if "numeric_points" in data or "alpha_points" in data:
                # New format: separate arrays
                numeric_points = data.get("numeric_points", [])
                alpha_points = data.get("alpha_points", [])
                self.points = numeric_points + alpha_points

                # Update counters based on existing points
                for point in numeric_points:
                    try:
                        num = int(point["id"])
                        if num > self.numeric_counter:
                            self.numeric_counter = num
                    except ValueError:
                        pass

                for point in alpha_points:
                    # Extract number from alphanumeric ID (e.g., "C1" -> 1)
                    try:
                        num_str = point["id"][1:]  # Remove first character
                        num = int(num_str)
                        if num > self.alphanumeric_counter:
                            self.alphanumeric_counter = num
                    except (ValueError, IndexError):
                        pass
            else:
                # Old format: single "points" array (backward compatibility)
                self.points = data.get("points", [])

                # Update counters based on existing points
                for point in self.points:
                    if point.get("type") == "numeric":
                        try:
                            num = int(point["id"])
                            if num > self.numeric_counter:
                                self.numeric_counter = num
                        except ValueError:
                            pass
                    elif point.get("type") == "alphanumeric":
                        # Extract number from alphanumeric ID (e.g., "C1" -> 1)
                        try:
                            num_str = point["id"][1:]  # Remove first character
                            num = int(num_str)
                            if num > self.alphanumeric_counter:
                                self.alphanumeric_counter = num
                        except (ValueError, IndexError):
                            pass

            logger.info(f"Loaded {len(self.points)} points from {self.json_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON file: {e}")
            messagebox.showerror("Error", f"Invalid JSON file: {e}")
        except Exception as e:
            logger.error(f"Error loading points: {e}")
            messagebox.showerror("Error", f"Failed to load points: {e}")

    def _toggle_delete_mode(self, event: Any) -> None:
        """Toggle delete mode on/off.

        Args:
            event: Keyboard event (not used, but required by tkinter).
        """
        self.delete_mode = not self.delete_mode
        if self.delete_mode:
            self.root.title("Map Point Marker - DELETE MODE (Press X to toggle)")
            logger.info("Delete mode enabled")
        else:
            self.root.title("Map Point Marker")
            logger.info("Delete mode disabled")

    def _find_nearest_point(
        self,
        x: int,
        y: int,
        threshold: int = 20,
    ) -> Optional[int]:
        """Find the index of the nearest point to the given coordinates.

        Args:
            x: X coordinate in original image space.
            y: Y coordinate in original image space.
            threshold: Maximum distance to consider a point (in original pixels).

        Returns:
            Index of the nearest point if within threshold, None otherwise.
        """
        if not self.points:
            return None

        min_distance = float("inf")
        nearest_index = None

        for i, point in enumerate(self.points):
            px = point["x"]
            py = point["y"]
            distance = ((x - px) ** 2 + (y - py) ** 2) ** 0.5

            if distance < min_distance and distance <= threshold:
                min_distance = distance
                nearest_index = i

        return nearest_index

    def _delete_nearest_point(self, x: int, y: int) -> None:
        """Delete the nearest point to the given coordinates and reindex remaining points.

        Args:
            x: X coordinate in original image space.
            y: Y coordinate in original image space.
        """
        nearest_index = self._find_nearest_point(x, y)
        if nearest_index is not None:
            deleted_point = self.points.pop(nearest_index)
            deleted_type = deleted_point.get("type", "alphanumeric")
            
            # Reindex all points of the same type
            self._reindex_points(deleted_type)
            
            self._redraw_all_points()
            self._save_points()
            logger.info(
                f"Deleted point {deleted_point['id']} at ({deleted_point['x']}, {deleted_point['y']})",
            )
        else:
            logger.debug(f"No point found near ({x}, {y})")

    def _reindex_points(self, point_type: str) -> None:
        """Reindex all points of a given type to have consecutive indices.

        Args:
            point_type: Type of points to reindex ("numeric" or "alphanumeric").
        """
        # Get all points of the specified type
        points_to_reindex = [
            (i, point) for i, point in enumerate(self.points) if point.get("type") == point_type
        ]
        
        if not points_to_reindex:
            # No points of this type, reset counter
            if point_type == "numeric":
                self.numeric_counter = 0
            else:
                self.alphanumeric_counter = 0
            return
        
        # Sort points by their current ID to maintain relative order
        def get_id_number(point: Dict[str, Any]) -> int:
            """Extract numeric part from point ID."""
            point_id = point["id"]
            if point_type == "numeric":
                try:
                    return int(point_id)
                except ValueError:
                    return 0
            else:
                # Alphanumeric: extract number after first character
                try:
                    return int(point_id[1:])
                except (ValueError, IndexError):
                    return 0
        
        points_to_reindex.sort(key=lambda x: get_id_number(x[1]))
        
        # Reindex points starting from 1
        new_counter = 0
        for original_index, point in points_to_reindex:
            new_counter += 1
            if point_type == "numeric":
                point["id"] = str(new_counter)
            else:
                point["id"] = f"C{new_counter}"
        
        # Update the counter for this type
        if point_type == "numeric":
            self.numeric_counter = new_counter
        else:
            self.alphanumeric_counter = new_counter
        
        logger.info(f"Reindexed {new_counter} {point_type} points")

    def _redraw_all_points(self) -> None:
        """Clear canvas and redraw all points."""
        if self.canvas is None:
            return

        # Clear all canvas items except the image
        self.canvas.delete("all")

        # Redraw the image
        if self.photo is not None:
            self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

        # Redraw all points
        for point in self.points:
            self._draw_point(point)

    def _display_points(self) -> None:
        """Display all loaded points on the canvas."""
        for point in self.points:
            self._draw_point(point)
        logger.info(f"Displayed {len(self.points)} points on the map")

    def _save_points(self) -> None:
        """Save all points to JSON file, separated into numeric and alpha arrays."""
        try:
            # Separate points into numeric and alphanumeric arrays
            numeric_points: List[Dict[str, Any]] = []
            alpha_points: List[Dict[str, Any]] = []

            for point in self.points:
                if point.get("type") == "numeric":
                    numeric_points.append(point)
                else:
                    # Alphanumeric or any other type
                    alpha_points.append(point)

            data = {
                "numeric_points": numeric_points,
                "alpha_points": alpha_points,
            }
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(
                f"Saved {len(numeric_points)} numeric and {len(alpha_points)} alpha points to {self.json_path}",
            )
        except Exception as e:
            logger.error(f"Error saving points: {e}")
            messagebox.showerror("Error", f"Failed to save points: {e}")

    def run(self) -> None:
        """Start the application main loop."""
        logger.info("Starting Map Point Marker application")
        self.root.mainloop()


def main() -> None:
    """Main entry point for the Map Point Marker application."""
    app = MapPointMarker(IMAGE_PATH, JSON_PATH)
    app.run()


if __name__ == "__main__":
    main()

