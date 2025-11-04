# Camera FOV Calculator for Blender

A Blender add-on that calculates and displays camera field of view and ground coverage information for the "main_cam" camera relative to the "ego_car" object.

## Features

This add-on calculates and displays:

1. **Vertical Field of View** - The vertical viewing angle of the camera in degrees
2. **Horizontal Field of View** - The horizontal viewing angle of the camera in degrees
3. **Forward Distance (Y-axis)** - Distance from "ego_car" to the end/top of the camera's viewable area on the ground (forward)
4. **Backward Distance (Y-axis)** - Distance from "ego_car" to the start/bottom of the camera's viewable area on the ground (backward)
5. **Total Horizontal Distance** - The total horizontal (X-axis) coverage on the ground in meters
6. **Total Vertical Distance** - The total vertical (Y-axis) coverage on the ground in meters

**Note:** All measurements assume a flat ground plane at Z=0 (world origin height).

## Installation

1. Download the `camera_fov_calculator.py` file
2. Open Blender
3. Go to `Edit` → `Preferences` → `Add-ons`
4. Click `Install...` button
5. Navigate to and select the `camera_fov_calculator.py` file
6. Enable the add-on by checking the checkbox next to "Camera: Camera FOV Calculator"

## Requirements

Your Blender scene must have:
- A camera object named **"main_cam"** - The camera to analyze
- An object named **"ego_car"** - The reference point for distance measurements (optional, will use world origin if not found)

## Usage

1. Set up your scene with the required objects ("main_cam" camera and "ego_car" object)
2. In the 3D Viewport, press `N` to open the sidebar (if not already visible)
3. Click on the **"Camera FOV"** tab in the sidebar
4. Click the **"Calculate FOV & Coverage"** button

The panel will display all calculated measurements:

### Field of View Section
- Vertical FOV (in degrees)
- Horizontal FOV (in degrees)

### Ground Coverage Section
- **Forward Distance**: How far forward from ego_car the camera can see on the ground (positive Y direction)
- **Backward Distance**: How far backward from ego_car the camera can see on the ground (negative Y direction)

### Total Coverage Section
- **Horizontal Distance**: Total left-to-right coverage on the ground
- **Vertical Distance**: Total front-to-back coverage on the ground

## How It Works

The add-on:
1. Reads the camera's lens focal length and sensor size to calculate FOV angles
2. Projects the camera's frustum corners onto the ground plane (Z=0)
3. Calculates the bounding box of the visible ground area
4. Measures distances from the ego_car position to various points in the visible area

## Technical Details

- The ground plane is assumed to be at Z=0 in world coordinates
- Distance measurements are in Blender units (typically meters)
- The calculation accounts for camera position, rotation, and lens properties
- The add-on uses ray-plane intersection mathematics to determine where the camera view meets the ground

## Troubleshooting

**"Camera 'main_cam' not found in scene"**
- Make sure you have a camera object named exactly "main_cam" (case-sensitive)

**"Object 'ego_car' not found in scene"**
- The add-on will still work but will measure distances from the world origin (0, 0, 0)
- Create an object named "ego_car" for accurate distance measurements

**"Failed to calculate ground coverage"**
- Ensure the camera is positioned and angled so it can see the ground plane
- The camera must be above the ground plane (positive Z) and pointing downward
- If the camera is looking at the horizon or upward, it may not intersect the ground plane

## Compatibility

- Blender 2.80 or higher
- Tested with Blender 3.x and 4.x

## License

This add-on is provided as-is for use in Blender projects.

## Author

Created by Claude
