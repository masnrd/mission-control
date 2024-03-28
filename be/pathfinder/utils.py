import numpy as np
import h3  # Assuming you're using the h3 library for hexagons
from scipy.spatial.distance import euclidean

def hex_to_binary(hex_string):
    try:
        # Remove the '0x' prefix if it exists
        hex_string = hex_string.lstrip('0x')
        # Convert the hexadecimal string to an integer
        decimal_value = int(hex_string, 16)
        # Convert the integer to a binary string
        binary_string = bin(decimal_value)
        return binary_string
    except ValueError:
        return "Invalid hexadecimal input"

def octal_list_to_binary(octal_list):
    binary_result = ''
    for octal_digit in octal_list:
        # Convert each octal digit to its binary representation and append to the result
        binary_digit = bin(octal_digit)[2:].zfill(3)
        binary_result += binary_digit
    return binary_result

def binary_to_octal_list(binary_string, n):
    try:
        # Remove the '0b' prefix if it exists
        binary_string = binary_string.lstrip('0b')
        # Get the last 'n' characters from the binary string
        last_n_binary = binary_string[-n*3:]
        # Pad the binary string with zeros if its length is not a multiple of 3
        while len(last_n_binary) % 3 != 0:
            last_n_binary = '0' + last_n_binary
        # Split the binary string into groups of 3 characters
        binary_groups = [last_n_binary[i:i+3] for i in range(0, len(last_n_binary), 3)]
        # Convert each group to decimal and store in a list
        octal_list = [int(group, 2) for group in binary_groups]
        return octal_list
    except ValueError:
        return "Invalid binary input"

def binary_to_hex(binary_string):
    try:
        # Remove the '0b' prefix if it exists
        binary_string = binary_string.lstrip('0b')
        # Convert the binary string to an integer
        decimal_value = int(binary_string, 2)
        # Convert the integer to a hexadecimal string
        hex_string = hex(decimal_value)[2:]
        return hex_string
    except ValueError:
        return "Invalid binary input"

def hex_to_array_index(hex_string: str, prob_map: np.ndarray) -> tuple[int, int, int, int]:
    """Convert a hexagon's H3 string index into an array index.

    Args:
        hex_string (str): The H3 index of the hexagon in string.
        prob_map (np.ndarray): A numpy array of (7,7,7,7) representing the probability in each hexagon.

    Returns:
        tuple[int, int, int, int]: Corresponding indices in the `prob_map` for the given hexagon.
    """
    binary_input = hex_to_binary(hex_string)
    octal_output = binary_to_octal_list(binary_input, len(prob_map.shape))
    return tuple(octal_output)

def array_index_to_hex(centre_hex: str, indices: tuple[int, int, int, int] ,prob_map: np.ndarray) -> str:
    """Convert a array index of size 4 into the corresponding hexagon's H3 string index.

    Args:
        centre_hex (str): The H3 index of the central reference hexagon in string format needed for the prefix.
        indices (tuple[int, int, int, int]): Indices of size 4 in the `prob_map` to be converted.
        prob_map (np.ndarray): A numpy array of (7,7,7,7) representing the probability in each hexagon.

    Returns:
        str: The corresponding H3 index of the given array indices.
    """
    centre_bin = hex_to_binary(centre_hex)
    bin_prefix = centre_bin[:-len(prob_map.shape) * 3]
    hex_binary = bin_prefix + octal_list_to_binary(indices)
    hex_idx = binary_to_hex(hex_binary)
    return hex_idx

def distance_between_2_hexas(a: str, b: str) -> float:
    """Calculate the Euclidean distance between the centers of two hexagons.

    Args:
        a (str): The H3 index of the first hexagon in string.
        b (str): The H3 index of the second hexagon in string.

    Returns:
        float: The Euclidean distance between the two hexagon centers using latitude and longitude in the unit of the input
    """
    dist = euclidean(h3.h3_to_geo(a), h3.h3_to_geo(b))
    return dist