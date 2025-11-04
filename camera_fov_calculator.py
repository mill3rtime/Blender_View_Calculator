bl_info = {
    "name": "Camera FOV Calculator",
    "author": "Claude",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Camera FOV",
    "description": "Calculate and display camera field of view and ground coverage",
    "category": "Camera",
}

import bpy
import math
from mathutils import Vector, Matrix
from bpy.types import Panel, Operator
from bpy.props import StringProperty


class CameraFOVCalculator:
    """Calculate camera FOV and ground plane intersections"""

    @staticmethod
    def get_camera_fov(camera):
        """Calculate vertical and horizontal field of view in degrees"""
        if camera is None or camera.type != 'CAMERA':
            return None, None

        cam_data = camera.data

        # Get sensor dimensions
        if cam_data.sensor_fit == 'VERTICAL':
            sensor_height = cam_data.sensor_height
            sensor_width = cam_data.sensor_height * bpy.context.scene.render.resolution_x / bpy.context.scene.render.resolution_y
        else:  # HORIZONTAL or AUTO
            sensor_width = cam_data.sensor_width
            sensor_height = cam_data.sensor_width * bpy.context.scene.render.resolution_y / bpy.context.scene.render.resolution_x

        # Calculate FOV
        focal_length = cam_data.lens

        # Vertical FOV
        vfov = 2 * math.atan(sensor_height / (2 * focal_length))
        vfov_deg = math.degrees(vfov)

        # Horizontal FOV
        hfov = 2 * math.atan(sensor_width / (2 * focal_length))
        hfov_deg = math.degrees(hfov)

        return vfov_deg, hfov_deg

    @staticmethod
    def ray_plane_intersection(ray_origin, ray_direction, plane_point=Vector((0, 0, 0)), plane_normal=Vector((0, 0, 1))):
        """Find intersection point of a ray with a plane"""
        # Ray: P = ray_origin + t * ray_direction
        # Plane: (P - plane_point) . plane_normal = 0

        denom = ray_direction.dot(plane_normal)

        # Check if ray is parallel to plane
        if abs(denom) < 1e-6:
            return None

        t = (plane_point - ray_origin).dot(plane_normal) / denom

        # Only return intersection if it's in front of the ray origin
        if t < 0:
            return None

        intersection = ray_origin + t * ray_direction
        return intersection

    @staticmethod
    def get_camera_frustum_corners(camera, aspect_ratio=None):
        """Get the four corners of the camera frustum at near plane"""
        if camera is None or camera.type != 'CAMERA':
            return None

        cam_data = camera.data

        # Get aspect ratio from render settings if not provided
        if aspect_ratio is None:
            scene = bpy.context.scene
            aspect_ratio = scene.render.resolution_x / scene.render.resolution_y

        # Get sensor dimensions
        if cam_data.sensor_fit == 'VERTICAL':
            sensor_height = cam_data.sensor_height
            sensor_width = sensor_height * aspect_ratio
        else:  # HORIZONTAL or AUTO
            sensor_width = cam_data.sensor_width
            sensor_height = sensor_width / aspect_ratio

        # Calculate half angles
        focal_length = cam_data.lens
        half_height = sensor_height / (2 * focal_length)
        half_width = sensor_width / (2 * focal_length)

        # Define corners in camera space (normalized direction vectors)
        # Using a reference distance of 1 unit
        corners = [
            Vector((-half_width, 1, half_height)),   # Top-left
            Vector((half_width, 1, half_height)),    # Top-right
            Vector((half_width, 1, -half_height)),   # Bottom-right
            Vector((-half_width, 1, -half_height)),  # Bottom-left
        ]

        return corners

    @staticmethod
    def calculate_ground_coverage(camera_obj, ego_car_obj=None):
        """Calculate where the camera view intersects the ground plane (z=0)"""
        if camera_obj is None or camera_obj.type != 'CAMERA':
            return None

        # Get camera world matrix
        cam_matrix = camera_obj.matrix_world
        cam_location = cam_matrix.to_translation()

        # Get frustum corners in camera space
        corners_cam_space = CameraFOVCalculator.get_camera_frustum_corners(camera_obj)
        if corners_cam_space is None:
            return None

        # Transform corners to world space and normalize as directions
        corners_world = []
        for corner in corners_cam_space:
            # Transform direction to world space
            direction_world = cam_matrix.to_quaternion() @ corner.normalized()
            corners_world.append(direction_world)

        # Find intersections with ground plane (z=0)
        ground_plane_point = Vector((0, 0, 0))
        ground_plane_normal = Vector((0, 0, 1))

        intersections = []
        for direction in corners_world:
            intersection = CameraFOVCalculator.ray_plane_intersection(
                cam_location,
                direction,
                ground_plane_point,
                ground_plane_normal
            )
            if intersection is not None:
                intersections.append(intersection)

        if len(intersections) == 0:
            return None

        # Calculate bounding box of intersections
        min_x = min(p.x for p in intersections)
        max_x = max(p.x for p in intersections)
        min_y = min(p.y for p in intersections)
        max_y = max(p.y for p in intersections)

        # Calculate distances relative to ego_car if provided
        ego_y = 0
        if ego_car_obj is not None:
            ego_y = ego_car_obj.matrix_world.to_translation().y

        results = {
            'intersections': intersections,
            'min_x': min_x,
            'max_x': max_x,
            'min_y': min_y,
            'max_y': max_y,
            'horizontal_distance': max_x - min_x,
            'vertical_distance': max_y - min_y,
            'ego_to_top': max_y - ego_y,
            'ego_to_bottom': min_y - ego_y,
            'ego_y': ego_y
        }

        return results


class CAMERA_OT_calculate_fov(Operator):
    """Calculate camera FOV and ground coverage"""
    bl_idname = "camera.calculate_fov"
    bl_label = "Calculate FOV"
    bl_options = {'REGISTER'}

    def execute(self, context):
        scene = context.scene

        # Try to find main_cam
        camera_obj = bpy.data.objects.get("main_cam")
        if camera_obj is None:
            self.report({'WARNING'}, "Camera 'main_cam' not found in scene")
            return {'CANCELLED'}

        # Try to find ego_car
        ego_car_obj = bpy.data.objects.get("ego_car")
        if ego_car_obj is None:
            self.report({'WARNING'}, "Object 'ego_car' not found in scene. Measurements will be relative to world origin.")

        # Calculate FOV
        vfov, hfov = CameraFOVCalculator.get_camera_fov(camera_obj)
        if vfov is None:
            self.report({'ERROR'}, "Failed to calculate FOV")
            return {'CANCELLED'}

        # Store in scene properties
        scene.camera_vfov = f"{vfov:.2f}°"
        scene.camera_hfov = f"{hfov:.2f}°"

        # Calculate ground coverage
        coverage = CameraFOVCalculator.calculate_ground_coverage(camera_obj, ego_car_obj)
        if coverage is None:
            self.report({'ERROR'}, "Failed to calculate ground coverage. Camera may not be looking at the ground plane.")
            return {'CANCELLED'}

        # Store in scene properties
        scene.camera_ego_to_top = f"{coverage['ego_to_top']:.2f} m"
        scene.camera_ego_to_bottom = f"{coverage['ego_to_bottom']:.2f} m"
        scene.camera_horizontal_dist = f"{coverage['horizontal_distance']:.2f} m"
        scene.camera_vertical_dist = f"{coverage['vertical_distance']:.2f} m"

        self.report({'INFO'}, "Camera FOV calculated successfully")
        return {'FINISHED'}


class CAMERA_PT_fov_panel(Panel):
    """Panel to display camera FOV information"""
    bl_label = "Camera FOV Calculator"
    bl_idname = "CAMERA_PT_fov_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Camera FOV'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Calculate button
        layout.operator("camera.calculate_fov", text="Calculate FOV & Coverage", icon='CAMERA_DATA')

        layout.separator()

        # Display results
        box = layout.box()
        box.label(text="Field of View:", icon='AXIS_ANGLE')
        row = box.row()
        row.label(text=f"Vertical FOV:")
        row.label(text=getattr(scene, 'camera_vfov', 'N/A'))

        row = box.row()
        row.label(text=f"Horizontal FOV:")
        row.label(text=getattr(scene, 'camera_hfov', 'N/A'))

        layout.separator()

        box = layout.box()
        box.label(text="Ground Coverage (from ego_car):", icon='EMPTY_AXIS')

        row = box.row()
        row.label(text=f"Forward Distance:")
        row.label(text=getattr(scene, 'camera_ego_to_top', 'N/A'))

        row = box.row()
        row.label(text=f"Backward Distance:")
        row.label(text=getattr(scene, 'camera_ego_to_bottom', 'N/A'))

        layout.separator()

        box = layout.box()
        box.label(text="Total Coverage:", icon='FULLSCREEN_ENTER')

        row = box.row()
        row.label(text=f"Horizontal Distance:")
        row.label(text=getattr(scene, 'camera_horizontal_dist', 'N/A'))

        row = box.row()
        row.label(text=f"Vertical Distance:")
        row.label(text=getattr(scene, 'camera_vertical_dist', 'N/A'))


def register():
    """Register addon classes and properties"""
    bpy.utils.register_class(CAMERA_OT_calculate_fov)
    bpy.utils.register_class(CAMERA_PT_fov_panel)

    # Register scene properties to store calculation results
    bpy.types.Scene.camera_vfov = StringProperty(
        name="Vertical FOV",
        default="N/A"
    )
    bpy.types.Scene.camera_hfov = StringProperty(
        name="Horizontal FOV",
        default="N/A"
    )
    bpy.types.Scene.camera_ego_to_top = StringProperty(
        name="Ego to Top Distance",
        default="N/A"
    )
    bpy.types.Scene.camera_ego_to_bottom = StringProperty(
        name="Ego to Bottom Distance",
        default="N/A"
    )
    bpy.types.Scene.camera_horizontal_dist = StringProperty(
        name="Horizontal Distance",
        default="N/A"
    )
    bpy.types.Scene.camera_vertical_dist = StringProperty(
        name="Vertical Distance",
        default="N/A"
    )


def unregister():
    """Unregister addon classes and properties"""
    bpy.utils.unregister_class(CAMERA_PT_fov_panel)
    bpy.utils.unregister_class(CAMERA_OT_calculate_fov)

    # Unregister scene properties
    del bpy.types.Scene.camera_vfov
    del bpy.types.Scene.camera_hfov
    del bpy.types.Scene.camera_ego_to_top
    del bpy.types.Scene.camera_ego_to_bottom
    del bpy.types.Scene.camera_horizontal_dist
    del bpy.types.Scene.camera_vertical_dist


if __name__ == "__main__":
    register()
