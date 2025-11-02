package main

import (
	_ "embed"
	"fmt"
	"math"
	"os"
	"strings"
	"time"
)

//go:embed actual-front.ti3
var cti3Content string

type Patch struct {
	SampleID  string
	SampleLoc string
	RGB_R     float64
	RGB_G     float64
	RGB_B     float64
	XYZ_X     float64
	XYZ_Y     float64
	XYZ_Z     float64
}

// Bradford chromatic adaptation matrix: D50 -> D65
var bradfordD50toD65 = [3][3]float64{
	{0.9555766, -0.0230393, 0.0631636},
	{-0.0282895, 1.0099416, 0.0210077},
	{0.0122982, -0.020483, 1.3299098},
}

// XYZ to sRGB conversion matrix (D65 white point)
// Standard sRGB/ITU-R BT.709 primaries
var xyzToRGBMatrix = [3][3]float64{
	{3.2404542, -1.5371385, -0.4985314},
	{-0.9692660, 1.8760108, 0.0415560},
	{0.0556434, -0.2040259, 1.0572252},
}

func xyzToLinearRGB(x, y, z float64) (float64, float64, float64) {
	// Normalize XYZ (assuming Y=100 is white)
	xn := x / 100.0
	yn := y / 100.0
	zn := z / 100.0

	// Chromatic adaptation from D50 to D65 using Bradford
	xd65 := bradfordD50toD65[0][0]*xn + bradfordD50toD65[0][1]*yn + bradfordD50toD65[0][2]*zn
	yd65 := bradfordD50toD65[1][0]*xn + bradfordD50toD65[1][1]*yn + bradfordD50toD65[1][2]*zn
	zd65 := bradfordD50toD65[2][0]*xn + bradfordD50toD65[2][1]*yn + bradfordD50toD65[2][2]*zn

	// Apply matrix transformation
	r := xyzToRGBMatrix[0][0]*xd65 + xyzToRGBMatrix[0][1]*yd65 + xyzToRGBMatrix[0][2]*zd65
	g := xyzToRGBMatrix[1][0]*xd65 + xyzToRGBMatrix[1][1]*yd65 + xyzToRGBMatrix[1][2]*zd65
	b := xyzToRGBMatrix[2][0]*xd65 + xyzToRGBMatrix[2][1]*yd65 + xyzToRGBMatrix[2][2]*zd65

	return r, g, b
}

func srgbGamma(linear float64) float64 {
	if linear <= 0.0031308 {
		return 12.92 * linear
	}
	return 1.055*math.Pow(linear, 1.0/2.4) - 0.055
}

func xyzToSRGB(x, y, z float64) (float64, float64, float64) {
	r, g, b := xyzToLinearRGB(x, y, z)

	// Apply gamma correction
	r = srgbGamma(r)
	g = srgbGamma(g)
	b = srgbGamma(b)

	// Clamp to [0, 1] and scale to [0, 100]
	r = math.Max(0, math.Min(1, r)) * 100.0
	g = math.Max(0, math.Min(1, g)) * 100.0
	b = math.Max(0, math.Min(1, b)) * 100.0

	return r, g, b
}

// D50 white point (ICC PCS)
const (
	D50_X = 96.42
	D50_Y = 100.0
	D50_Z = 82.49
)

func stretchXYZ(patches []Patch) []Patch {
	if len(patches) < 6 {
		return patches
	}

	// Reference: patch 1 (index 0) is white, patch 6 (index 5) is black
	whiteRef := patches[0]
	blackRef := patches[5]

	stretched := make([]Patch, len(patches))

	for i, p := range patches {
		stretched[i] = p

		// Linear stretch: (measured - black) / (white - black) * target_white
		stretched[i].XYZ_X = (p.XYZ_X - blackRef.XYZ_X) / (whiteRef.XYZ_X - blackRef.XYZ_X) * D50_X
		stretched[i].XYZ_Y = (p.XYZ_Y - blackRef.XYZ_Y) / (whiteRef.XYZ_Y - blackRef.XYZ_Y) * D50_Y
		stretched[i].XYZ_Z = (p.XYZ_Z - blackRef.XYZ_Z) / (whiteRef.XYZ_Z - blackRef.XYZ_Z) * D50_Z

		// Clamp to valid range
		stretched[i].XYZ_X = math.Max(0, stretched[i].XYZ_X)
		stretched[i].XYZ_Y = math.Max(0, stretched[i].XYZ_Y)
		stretched[i].XYZ_Z = math.Max(0, stretched[i].XYZ_Z)
	}

	return stretched
}

func calculateWhitePoint(patches []Patch) (float64, float64, float64) {
	// After stretching, use D50 white point
	return D50_X, D50_Y, D50_Z
}

func neutralizeGray(r, g, b float64) (float64, float64, float64) {
	// Average the RGB values to make neutral gray
	avg := (r + g + b) / 3.0
	return avg, avg, avg
}

func generateCTI1(patches []Patch, outputFile string) error {
	wpX, wpY, wpZ := calculateWhitePoint(patches)

	f, err := os.Create(outputFile)
	if err != nil {
		return err
	}
	defer f.Close()

	// SECTION 1: Main patches
	fmt.Fprintln(f, "CTI1   ")
	fmt.Fprintln(f)
	fmt.Fprintln(f, `DESCRIPTOR "Argyll Calibration Target chart information 1"`)
	fmt.Fprintln(f, `ORIGINATOR "Argyll targen"`)
	fmt.Fprintf(f, "CREATED \"%s\"\n", time.Now().Format("Mon Jan 2 15:04:05 2006"))
	fmt.Fprintf(f, "APPROX_WHITE_POINT \"%.6f %.6f %.6f\"\n", wpX, wpY, wpZ)
	fmt.Fprintln(f, `COLOR_REP "iRGB"`)
	fmt.Fprintln(f, `TOTAL_INK_LIMIT "300.0"`)
	fmt.Fprintln(f, `WHITE_COLOR_PATCHES "4"`)
	fmt.Fprintln(f, `BLACK_COLOR_PATCHES "4"`)
	fmt.Fprintln(f, `OFPS_PATCHES "16"`)
	fmt.Fprintln(f)

	fmt.Fprintln(f, "NUMBER_OF_FIELDS 7")
	fmt.Fprintln(f, "BEGIN_DATA_FORMAT")
	fmt.Fprintln(f, "SAMPLE_ID RGB_R RGB_G RGB_B XYZ_X XYZ_Y XYZ_Z ")
	fmt.Fprintln(f, "END_DATA_FORMAT")
	fmt.Fprintln(f)

	fmt.Fprintf(f, "NUMBER_OF_SETS %d\n", len(patches))
	fmt.Fprintln(f, "BEGIN_DATA")

	for i, p := range patches {
		r, g, b := xyzToSRGB(p.XYZ_X, p.XYZ_Y, p.XYZ_Z)

		// First 6 patches are neutral grays
		if i < 6 {
			r, g, b = neutralizeGray(r, g, b)
		}

		fmt.Fprintf(f, "%d %.4f %.4f %.4f %.6f %.6f %.6f \n",
			i+1, r, g, b, p.XYZ_X, p.XYZ_Y, p.XYZ_Z)
	}

	fmt.Fprintln(f, "END_DATA")

	// SECTION 2: DENSITY_EXTREME_VALUES
	fmt.Fprintln(f, "CTI1   ")
	fmt.Fprintln(f)
	fmt.Fprintln(f, `DESCRIPTOR "Argyll Calibration Target chart information 1"`)
	fmt.Fprintln(f, `ORIGINATOR "Argyll targen"`)
	fmt.Fprintln(f, `DENSITY_EXTREME_VALUES "8"`)
	fmt.Fprintf(f, "CREATED \"%s\"\n", time.Now().Format("January 2, 2006"))
	fmt.Fprintln(f)

	fmt.Fprintln(f, "NUMBER_OF_FIELDS 7")
	fmt.Fprintln(f, "BEGIN_DATA_FORMAT")
	fmt.Fprintln(f, "INDEX RGB_R RGB_G RGB_B XYZ_X XYZ_Y XYZ_Z ")
	fmt.Fprintln(f, "END_DATA_FORMAT")
	fmt.Fprintln(f)

	// Identify key patches for DENSITY_EXTREME_VALUES
	// 0: White (patch 1), 1: Cyan (patch 12), 2: Magenta (patch 14), 3: Blue (patch 10)
	// 4: Yellow (patch 9), 5: Green (patch 13), 6: Red (patch 11), 7: Black (patch 6)
	densityIndices := []int{0, 11, 13, 9, 8, 12, 10, 5} // 0-indexed patch numbers

	fmt.Fprintln(f, "NUMBER_OF_SETS 8")
	fmt.Fprintln(f, "BEGIN_DATA")

	for i, idx := range densityIndices {
		p := patches[idx]
		r, g, b := xyzToSRGB(p.XYZ_X, p.XYZ_Y, p.XYZ_Z)

		// Neutralize white and black
		if i == 0 || i == 7 {
			r, g, b = neutralizeGray(r, g, b)
		}

		fmt.Fprintf(f, "%d %.4f %.4f %.4f %.6f %.6f %.6f \n",
			i, r, g, b, p.XYZ_X, p.XYZ_Y, p.XYZ_Z)
	}

	fmt.Fprintln(f, "END_DATA")

	// SECTION 3: DEVICE_COMBINATION_VALUES
	fmt.Fprintln(f, "CTI1   ")
	fmt.Fprintln(f)
	fmt.Fprintln(f, `DESCRIPTOR "Argyll Calibration Target chart information 1"`)
	fmt.Fprintln(f, `ORIGINATOR "Argyll targen"`)
	fmt.Fprintln(f, `DEVICE_COMBINATION_VALUES "9"`)
	fmt.Fprintf(f, "CREATED \"%s\"\n", time.Now().Format("January 2, 2006"))
	fmt.Fprintln(f)

	fmt.Fprintln(f, "NUMBER_OF_FIELDS 7")
	fmt.Fprintln(f, "BEGIN_DATA_FORMAT")
	fmt.Fprintln(f, "INDEX RGB_R RGB_G RGB_B XYZ_X XYZ_Y XYZ_Z ")
	fmt.Fprintln(f, "END_DATA_FORMAT")
	fmt.Fprintln(f)

	// 0: White, 1: Cyan, 2: Magenta, 3: Blue, 4: Yellow, 5: Green, 6: Red, 7: Black, 8: 50% Gray
	comboIndices := []int{0, 11, 13, 9, 8, 12, 10, 5, 21} // Using patch 22 for 50% gray

	fmt.Fprintln(f, "NUMBER_OF_SETS 9")
	fmt.Fprintln(f, "BEGIN_DATA")

	for i, idx := range comboIndices {
		p := patches[idx]
		r, g, b := xyzToSRGB(p.XYZ_X, p.XYZ_Y, p.XYZ_Z)

		// Neutralize white, black, and gray
		if i == 0 || i == 7 || i == 8 {
			r, g, b = neutralizeGray(r, g, b)
		}

		fmt.Fprintf(f, "%d %.4f %.4f %.4f %.6f %.6f %.6f \n",
			i, r, g, b, p.XYZ_X, p.XYZ_Y, p.XYZ_Z)
	}

	fmt.Fprintln(f, "END_DATA")
	fmt.Fprintln(f)

	return nil
}

func parseCTI3(content string) []Patch {
	lines := strings.Split(content, "\n")
	var patches []Patch
	inData := false

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "BEGIN_DATA" {
			inData = true
			continue
		}
		if line == "END_DATA" {
			break
		}
		if !inData || line == "" {
			continue
		}

		var p Patch
		_, err := fmt.Sscanf(line, "%s %q %f %f %f %f %f %f",
			&p.SampleID, &p.SampleLoc, &p.RGB_R, &p.RGB_G, &p.RGB_B,
			&p.XYZ_X, &p.XYZ_Y, &p.XYZ_Z)
		if err != nil {
			continue
		}
		patches = append(patches, p)
	}

	return patches
}

func main() {
	patches := parseCTI3(cti3Content)
	if len(patches) == 0 {
		fmt.Println("No patches parsed")
		return
	}

	// Stretch XYZ values: patch 1 -> D50 white, patch 6 -> black
	patches = stretchXYZ(patches)

	err := generateCTI1(patches, "/mnt/user-data/outputs/converted.cti1")
	if err != nil {
		fmt.Printf("Error generating CTI1: %v\n", err)
		return
	}

	fmt.Printf("Successfully converted %d patches to CTI1 format\n", len(patches))
	fmt.Printf("Stretched to D50 white (%.2f, %.2f, %.2f)\n", D50_X, D50_Y, D50_Z)
	fmt.Println("Output: /mnt/user-data/outputs/converted.cti1")
}
