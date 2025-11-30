"""Solution Visualization for CFLP Problem.

This module provides a GUI application for visualizing the CFLP solution,
showing only the facilities that are actually opened in the solution.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tkinter import Canvas, Tk, messagebox
    from PIL import Image, ImageTk
except ImportError as e:
    print(f"Required libraries not installed: {e}")
    print("Please install: pip install pillow")
    raise

# Ensure UTF-8 encoding for output
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")

from src.cflp.config import JSON_PATH
from src.cflp.data_loader import load_points
from src.cflp.distance import calculate_distance_matrix
from src.cflp.solvers import (
    GurobiSolver,
    HeuristicSolver,
    SCIPSolver,
    is_gurobi_available,
    is_scip_available,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
IMAGE_PATH = Path("campus_colored.png")
POINT_RADIUS = 8
FACILITY_POINT_COLOR_SMALL = "green"
FACILITY_POINT_COLOR_MEDIUM = "blue"
FACILITY_POINT_COLOR_LARGE = "purple"
TEXT_OFFSET = 12


class SolutionVisualizer:
    """Application for visualizing CFLP solution on map.

    This class handles the GUI and visualization of the solution,
    showing only the opened facilities (cantinas).
    """

    def __init__(
        self,
        image_path: Path,
        solution: Dict[str, Any],
        demand_points: List[Dict[str, Any]],
        solver_name: str = "Solver",
    ) -> None:
        """Initialize the SolutionVisualizer application.

        Args:
            image_path: Path to the map image file.
            solution: Solution dictionary from solver.
            demand_points: List of demand points (not used in visualization).
            solver_name: Name of the solver used.
        """
        self.image_path = image_path
        self.solution = solution
        self.solver_name = solver_name
        self.facilities_opened = solution.get("facilities_opened", [])

        # Initialize GUI
        self.root = Tk()
        self.root.title(f"Solucao CFLP - {solver_name}")
        self.canvas: Optional[Canvas] = None
        self.image: Optional[Image.Image] = None
        self.original_image: Optional[Image.Image] = None
        self.photo: Optional[ImageTk.PhotoImage] = None
        self.scale_factor = 1.0
        self.original_width = 0
        self.original_height = 0
        self.display_width = 0
        self.display_height = 0

        self._setup_gui()
        self._display_solution()

    def _setup_gui(self) -> None:
        """Set up the GUI components."""
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
            self.display_width = int(self.original_width * self.scale_factor)
            self.display_height = int(self.original_height * self.scale_factor)
            self.image = self.original_image.resize(
                (self.display_width, self.display_height),
                Image.Resampling.LANCZOS,
            )
            self.photo = ImageTk.PhotoImage(self.image)

            # Create canvas with scaled dimensions
            self.canvas = Canvas(
                self.root,
                width=self.display_width,
                height=self.display_height,
            )
            self.canvas.pack()

            # Display image
            self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

            # Draw legend
            self._draw_legend()

            logger.info(
                f"GUI setup completed. Original size: {self.original_width}x{self.original_height}, "
                f"Display size: {self.display_width}x{self.display_height}, Scale: {self.scale_factor:.3f}",
            )
        except Exception as e:
            logger.error(f"Error setting up GUI: {e}")
            messagebox.showerror("Error", f"Failed to load image: {e}")
            self.root.destroy()

    def _get_facility_color(self, facility_type: str) -> str:
        """Get color for facility based on type.

        Args:
            facility_type: Type of facility (pequena, media, grande).

        Returns:
            Color string for the facility.
        """
        color_map = {
            "pequena": FACILITY_POINT_COLOR_SMALL,
            "media": FACILITY_POINT_COLOR_MEDIUM,
            "grande": FACILITY_POINT_COLOR_LARGE,
        }
        return color_map.get(facility_type, "blue")

    def _draw_point(
        self,
        x: int,
        y: int,
        label: str,
        color: str,
        is_facility: bool = False,
        facility_type: Optional[str] = None,
    ) -> None:
        """Draw a point on the canvas.

        Args:
            x: X coordinate in original image space.
            y: Y coordinate in original image space.
            label: Label text for the point.
            color: Color of the point.
            is_facility: Whether this is a facility point.
            facility_type: Type of facility (if is_facility is True).
        """
        if self.canvas is None:
            return

        # Convert original coordinates to scaled display coordinates
        x_scaled = int(x * self.scale_factor)
        y_scaled = int(y * self.scale_factor)

        # Draw circle for the point
        radius = POINT_RADIUS + 2 if is_facility else POINT_RADIUS
        self.canvas.create_oval(
            x_scaled - radius,
            y_scaled - radius,
            x_scaled + radius,
            y_scaled + radius,
            fill=color,
            outline="black",
            width=2 if is_facility else 1,
        )

        # Draw label with ID
        label_y = y_scaled - TEXT_OFFSET - radius
        self.canvas.create_text(
            x_scaled,
            label_y,
            text=label,
            fill="black",
            font=("Arial", 10, "bold"),
        )

        # Draw facility type label for facilities
        if is_facility and facility_type:
            type_label = facility_type.upper()[:1]  # First letter
            type_y = y_scaled + TEXT_OFFSET + radius
            # Draw white background for type label
            self.canvas.create_rectangle(
                x_scaled - 8,
                type_y - 8,
                x_scaled + 8,
                type_y + 8,
                fill="white",
                outline="black",
                width=1,
            )
            self.canvas.create_text(
                x_scaled,
                type_y,
                text=type_label,
                fill="black",
                font=("Arial", 8, "bold"),
            )

    def _display_solution(self) -> None:
        """Display the solution on the map."""
        if self.canvas is None:
            return

        # Draw only opened facilities
        for facility in self.facilities_opened:
            x, y = facility["coordinates"]
            facility_id = facility["location"]
            facility_type = facility["type"]
            color = self._get_facility_color(facility_type)

            self._draw_point(
                x,
                y,
                facility_id,
                color,
                is_facility=True,
                facility_type=facility_type,
            )

        # Redraw legend on top
        self._draw_legend()

        logger.info(
            f"Displayed {len(self.facilities_opened)} opened facilities",
        )

    def _draw_legend(self) -> None:
        """Draw color legend on the canvas."""
        if self.canvas is None:
            return

        # Use display width for legend positioning
        canvas_width = (
            self.display_width if self.display_width > 0 else self.canvas.winfo_width()
        )

        # Legend position (top-right corner with margin)
        margin = 10
        legend_width = 200
        legend_x = canvas_width - legend_width - margin
        legend_y = margin
        legend_spacing = 25

        # Background rectangle for legend
        legend_height = 100
        self.canvas.create_rectangle(
            legend_x - 5,
            legend_y - 5,
            legend_x + legend_width,
            legend_y + legend_height,
            fill="white",
            outline="black",
            width=2,
        )

        # Title
        self.canvas.create_text(
            legend_x + legend_width // 2,
            legend_y + 10,
            text="Legenda - Cantinas",
            fill="black",
            font=("Arial", 10, "bold"),
        )

        # Facility types
        facility_types = [
            ("pequena", FACILITY_POINT_COLOR_SMALL, "Cantina pequena"),
            ("media", FACILITY_POINT_COLOR_MEDIUM, "Cantina media"),
            ("grande", FACILITY_POINT_COLOR_LARGE, "Cantina grande"),
        ]

        legend_point_y = legend_y + 30
        for facility_type, color, label in facility_types:
            self.canvas.create_oval(
                legend_x + 10 - POINT_RADIUS - 2,
                legend_point_y - POINT_RADIUS - 2,
                legend_x + 10 + POINT_RADIUS + 2,
                legend_point_y + POINT_RADIUS + 2,
                fill=color,
                outline="black",
                width=2,
            )
            self.canvas.create_text(
                legend_x + 30,
                legend_point_y,
                text=label,
                fill="black",
                font=("Arial", 9),
                anchor="w",
            )
            legend_point_y += legend_spacing

    def run(self) -> None:
        """Start the application main loop."""
        logger.info("Starting Solution Visualizer application")
        self.root.mainloop()


def get_solution(solver_name: str = "gurobi") -> Optional[Dict[str, Any]]:
    """Get solution from specified solver.

    Args:
        solver_name: Name of solver to use ("gurobi", "scip", or "heuristic").

    Returns:
        Solution dictionary or None if solver unavailable or error.
    """
    try:
        # Load data
        demand_points, facility_points = load_points(JSON_PATH)

        if not demand_points:
            print("Erro: Nenhum ponto de demanda encontrado.")
            return None

        if not facility_points:
            print("Erro: Nenhum ponto de instalacao encontrado.")
            return None

        # Calculate distance matrix
        distance_matrix = calculate_distance_matrix(demand_points, facility_points)

        # Solve with specified solver
        if solver_name.lower() == "gurobi":
            if not is_gurobi_available():
                print("Gurobi nao esta disponivel.")
                return None
            solver = GurobiSolver(demand_points, facility_points, distance_matrix)
            solution = solver.solve()
            if solution:
                solution["solver_name"] = "Gurobi"
            return solution

        elif solver_name.lower() == "scip":
            if not is_scip_available():
                print("SCIP nao esta disponivel.")
                return None
            solver = SCIPSolver(demand_points, facility_points, distance_matrix)
            solution = solver.solve()
            if solution:
                solution["solver_name"] = "SCIP"
            return solution

        elif solver_name.lower() == "heuristic":
            solver = HeuristicSolver(demand_points, facility_points, distance_matrix)
            solution = solver.solve()
            if solution:
                solution["solver_name"] = "Heuristica"
            return solution

        else:
            print(f"Solver desconhecido: {solver_name}")
            return None

    except Exception as e:
        logger.error(f"Error getting solution: {e}")
        print(f"Erro ao obter solucao: {e}")
        return None


def main() -> None:
    """Main entry point for solution visualization."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Visualize CFLP solution on map",
    )
    parser.add_argument(
        "--solver",
        type=str,
        default="gurobi",
        choices=["gurobi", "scip", "heuristic"],
        help="Solver to use (default: gurobi)",
    )

    args = parser.parse_args()

    # Get solution
    print(f"Obtendo solucao com {args.solver}...")
    solution = get_solution(args.solver)

    if solution is None:
        print("Nao foi possivel obter uma solucao.")
        return

    # Load demand points for visualization
    demand_points, _ = load_points(JSON_PATH)

    # Create and run visualizer
    solver_name = solution.get("solver_name", args.solver)
    visualizer = SolutionVisualizer(
        IMAGE_PATH,
        solution,
        demand_points,
        solver_name=solver_name,
    )
    visualizer.run()


if __name__ == "__main__":
    main()

