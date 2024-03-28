import h3
import folium
import os
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import glob
from PIL import Image

def gradient_color(value: float, min_value: float = 0, max_value: float = 2, greyscale=False):
    """
    Return a color hex value from a value between 0-1, based on the range of values in the dictionary.
    """
    if value < min_value:
        value = min_value
    elif value > max_value:
        value = max_value

    # Normalize the value within the range
    normalized_value = (value - min_value) / (max_value - min_value)

    if not greyscale:
        r = int(255 * normalized_value)
        b = int(255 * (1 - normalized_value))
        g = 0  # You can adjust the green component as needed
    else:
        r = int(255 * (1 - normalized_value))
        b = int(255 * (1 - normalized_value))
        g = int(255 * (1 - normalized_value))

    hex_string = "#{:02x}{:02x}{:02x}".format(r, g, b)
    return hex_string

def visualise_hex_dict_to_map(hexagon_values: dict, m: folium.Map, casualty_locations: set):
    """
    Visualise the probability map.

    Parameters:
    - hexagon_values: dictionary of hex_idx and probability values
    - m: folium map

    Returns:
    """
    keys = list(hexagon_values.keys())
    num_keys = len(keys)

    # Calculate min and max values from hexagon_values dictionary
    min_value = min(hexagon_values.values())
    max_value = max(hexagon_values.values())

    for i, hexagon_id in enumerate(hexagon_values):
        vertices = h3.h3_to_geo_boundary(hexagon_id)
        # color = color = gradient_color(hexagon_values[hexagon_id])
        # Update the function call in your visualise_hex_dict_to_map function
        color = gradient_color(
            hexagon_values[hexagon_id], min_value, max_value)
        if hexagon_id in casualty_locations:
            # Mark casualty
            folium.Polygon(locations=vertices, color="#FF0000",
                           fill=True).add_to(m)
        else:
            folium.Polygon(locations=vertices, color=color,
                           fill=True, fill_opacity=0.005).add_to(m)

def generate_gif(directory):
    """Generate gif based on a list of numbered png"""
    # Ensure the directory path ends with a slash
    if not directory.endswith('/'): directory += '/'

    # Gather all PNG images in the directory
    png_files = sorted(glob.glob(f"{directory}*.png"))

    # Debug print to check if PNG files are found
    print(f'PNG Files: {png_files}')

    if not png_files:
        print("No PNG files found in the directory.")
        return

    # Create a list to hold the images
    images = []

    # Open each image and append to the list
    for filename in png_files:
        img = Image.open(filename).convert('RGBA')
        images.append(img)

    # Debug print to check the images list
    print(f'Images: {images}, Length: {len(images)}')

    # Define the output path for the GIF
    output_gif_path = f"{directory}animated.gif"

    # Save the images as a GIF
    images[0].save(output_gif_path, save_all=True, append_images=images[1:], optimize=False, duration=200, loop=0)

    print(f"Generated GIF saved at {output_gif_path}")


def create_gif(output_filename: str, hexagon_map: dict, hexagon_values: list[dict],
               
               casualty_locations: set, casualty_detected: dict, dpi: int):
    """
    Create a GIF visualization of hexagon values and detected casualties.

    Parameters:
    - output_filename (str): The filename for the resulting GIF.
    - hexagon_map (dict): Mapping of hexagon indices to values.
    - hexagon_values (list): List of hexagon values and indices.
    - casualty_locations (set): Set of locations with casualties.
    - casualty_detected (dict): Mapping of hexagon indices to bool indicating if a casualty was detected.
    """
    import geopandas as gpd
    import matplotlib.pyplot as plt
    from shapely.geometry import Polygon
    import imageio
    from PIL import Image, ImageDraw

    filenames = []

    def create_base_map_image(hex_map_shapes: list[tuple[str, Polygon]],
                              global_xlim: tuple[float, float],
                              global_ylim: tuple[float, float],
                              casualty_locations: set,
                              dpi: int) -> str:
        """
        Create a base map image showing hexagons and casualty locations.
        """
        fig, ax = plt.subplots(figsize=(10, 10))

        ax.set_xlim(global_xlim)
        ax.set_ylim(global_ylim)
        ax.axis('off')

        # Plot the entire hexagon map with no fill
        # for hex_idx, hex_shape in (pbar := tqdm(hex_map_shapes)):
        #     pbar.set_description(f"Processing hex index: {hex_idx}")
        #     gdf_map = gpd.GeoDataFrame([{'geometry': hex_shape}])
        #     gdf_map.plot(ax=ax, color="none", edgecolor="k")
        #     if hex_idx in casualty_locations:
        #         gdf_map = gpd.GeoDataFrame([{"geometry": hex_shape}])
        #         gdf_map.plot(ax=ax, color="#FF0000", edgecolor="k")
        #     else:
        #         gdf_map = gpd.GeoDataFrame([{"geometry": hex_shape}])
        #         gdf_map.plot(ax=ax, color="none", edgecolor="k")

        def create_geodataframe(hex_shape, hex_idx, casualty_locations):
            color = "#FF0000" if hex_idx in casualty_locations else "none"
            return gpd.GeoDataFrame([{'geometry': hex_shape}]), color

        # Pre-generate GeoDataFrames in parallel
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(create_geodataframe, hex_shape, hex_idx, casualty_locations)
                    for hex_idx, hex_shape in hex_map_shapes]

        geodataframes = [future.result() for future in futures]

        # Now, in the main thread, do the plotting
        idx = 0
        for gdf, color in (pbar :=tqdm(geodataframes)):
            pbar.set_description(f"Ploting {idx+1}th image on map")
            gdf.plot(ax=ax, color=color, edgecolor="k")
            idx += 1

        base_filename = os.path.join(os.getcwd(), "base_map.png")
        plt.savefig(base_filename, dpi=dpi, bbox_inches="tight")
        plt.close()
        print("Generate base map done!")
        return base_filename

    def overlay_hex_on_map(i: int,
                           global_xlim: tuple[float, float],
                           global_ylim: tuple[float, float],
                           previous_filename: str,
                           hexagon_values: list[dict],
                           hex_map_shapes: list[tuple[str, Polygon]],
                           casualty_locations: set,
                           casualty_detected: dict[str, bool]) -> str:
        """
        Overlay a single hexagon onto an existing image.
        """

        # Open the base image (or the previous frame) with PIL
        img = Image.open(previous_filename)
        draw = ImageDraw.Draw(img)

        # Convert the current hexagon to vertices
        hex_idx = hexagon_values[i]["hex_idx"]
        vertices = [(int((pt[1]-global_xlim[0])/(global_xlim[1]-global_xlim[0])*img.width), int((1-(pt[0] -
                     global_ylim[0])/(global_ylim[1]-global_ylim[0]))*img.height)) for pt in h3.h3_to_geo_boundary(hex_idx)]

        if hex_idx in casualty_locations:
            if casualty_detected[hex_idx]:
                color = "green"
            else:
                color = "red"
            draw.polygon(vertices, fill=color, outline="black")
        else:
            draw.polygon(vertices, fill="#D3D3D3", outline="black")

        filename = os.path.join(os.getcwd(), f"frame_{i}.png")
        filenames.append(filename)
        img.save(filename)

        return filename

    hex_map_shapes = [(hex_id, Polygon([(pt[1], pt[0]) for pt in h3.h3_to_geo_boundary(
        hex_id)])) for hex_id in hexagon_map.keys()]
    all_boundaries = [h3.h3_to_geo_boundary(hv) for hv in hexagon_map.keys()]
    all_lons = [pt[1] for boundary in all_boundaries for pt in boundary]
    all_lats = [pt[0] for boundary in all_boundaries for pt in boundary]
    global_xlim = (min(all_lons), max(all_lons))
    global_ylim = (min(all_lats), max(all_lats))

    # Step 1: Create the base map image
    base_filename = create_base_map_image(
        hex_map_shapes, global_xlim, global_ylim, casualty_locations, dpi)
    # Step 2: Overlay hexagons on the base map
    previous_filename = base_filename
    for i, hexagon in (pbar :=tqdm(enumerate(hexagon_values))):
        pbar.set_description(f"Overlay hex {i} on map")
        previous_filename = overlay_hex_on_map(
            i, global_xlim, global_ylim, previous_filename, hexagon_values, hex_map_shapes, casualty_locations, casualty_detected)

    with imageio.get_writer(output_filename, mode="I", duration=1) as writer:
        for filename in filenames:
            image = imageio.imread(filename)
            writer.append_data(image)

    for filename in filenames:
        os.remove(filename)

if __name__ == "__main__":
    current_working_directory = os.getcwd()

    print(current_working_directory)
    generate_gif("../gif/")