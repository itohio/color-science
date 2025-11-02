import sys
import subprocess
import argparse
import matplotlib.pyplot as plt
from colour.plotting import plot_chromaticity_diagram_CIE1931
import colour

def xyz_to_xy(X, Y, Z):
    """Converts XYZ tristimulus values to xy chromaticity coordinates."""
    if (X + Y + Z) == 0:
        return 0, 0
    x = X / (X + Y + Z)
    y = Y / (X + Y + Z)
    return x, y

def get_profile_primaries(profile_path):
    """Uses xicclu to extract primaries from an ICC profile."""
    primaries = {}
    rgb_values = {"red": "255 0 0", "green": "0 255 0", "blue": "0 0 255"}

    try:
        for name, value in rgb_values.items():
            process = subprocess.run(
                ["xicclu", "-ir", "-f", profile_path],
                input=value.encode(),
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            output = process.stdout.strip().split()
            if len(output) >= 3:
                X, Y, Z = map(float, output[:3])
                primaries[name] = xyz_to_xy(X, Y, Z)
            else:
                raise ValueError(f"Unexpected output from xicclu for {name} in {profile_path}")
        return primaries
    except FileNotFoundError:
        raise FileNotFoundError(f"ArgyllCMS `xicclu` tool not found. Make sure ArgyllCMS is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error processing profile {profile_path}: {e.stderr.strip()}")
    except Exception as e:
        raise RuntimeError(f"An error occurred: {e}")

def plot_gamut(primaries, label, color):
    """Plots a gamut triangle on the CIE 1931 chromaticity diagram."""
    if not primaries:
        return

    points = [primaries["red"], primaries["green"], primaries["blue"]]
    # Close the triangle for plotting
    x, y = zip(*points)
    plt.plot(x + (x[0],), y + (y[0],), label=label, color=color)

def main():
    """Parses arguments and plots the gamuts."""
    parser = argparse.ArgumentParser(description="View and compare ICC profile chromaticity diagrams.")
    parser.add_argument("profiles", nargs='+', help="Paths to one or more ICC profiles to plot.")
    parser.add_argument("-r", "--reference", action="store_true", help="Include the sRGB gamut as a reference.")

    args = parser.parse_args()

    # Set up the CIE 1931 Chromaticity Diagram
    fig, ax = plot_chromaticity_diagram_CIE1931(
        standalone=False,
        show_spectral_locus=True,
        show_gamut_colours=True,
        title="ICC Profile Chromaticity Diagram Comparison"
    )

    # Plot sRGB reference if requested
    if args.reference:
        colour.plotting.plot_RGB_colourspaces_in_chromaticity_diagram_CIE1931(
            ["sRGB"], standalone=False, axes=ax, plot_primaries=True,
            show_whitepoints=False
        )

    colors = ['b', 'g', 'r', 'c', 'm', 'y'] # Colors for plotting
    for i, profile_path in enumerate(args.profiles):
        try:
            primaries = get_profile_primaries(profile_path)
            color = colors[i % len(colors)]
            plot_gamut(primaries, f"{profile_path}", color)
        except RuntimeError as e:
            print(e, file=sys.stderr)
        except FileNotFoundError as e:
            print(e, file=sys.stderr)

    plt.legend(title="Profiles")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
