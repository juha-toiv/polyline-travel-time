# Copyright (c) 2022 Juha Toivola
# Licensed under the terms of the MIT License

import arcpy



class CalculatePolyLineTravelTimeException(Exception):
    error_msg = ""

    def __init__(self, error_msg, *args):
        super().__init__(args)
        self.error_msg = error_msg

    def __str__(self):
        return 'Exception: ' + self.error_msg


def convert_seconds_to_string(s):
    s = s % (24 * 3600)
    h = s // 3600
    s %= 3600
    m = s // 60
    s %= 60
    return "%02d:%02d:%02d" % (h, m, s)


def is_wkt(spatial_ref):
    if "[" in spatial_ref:
        return True
    else:
        return False


# This is used to execute code if the file was run but not imported
if __name__ == '__main__':
    polyline = arcpy.GetParameterAsText(0)
    speed_ms = int(arcpy.GetParameterAsText(1))
    spatial_ref = arcpy.GetParameterAsText(2)

    count_polyline = int(arcpy.GetCount_management(polyline).getOutput(0))
    if count_polyline == 0:
        raise CalculatePolyLineTravelTimeException("Input polyline feature class contains no records")
    if count_polyline > 1:
        raise CalculatePolyLineTravelTimeException("Input polyline feature class must contain only one record")

    if is_wkt(spatial_ref):
        sr = arcpy.SpatialReference(text=spatial_ref)
    else:
        sr = arcpy.SpatialReference(spatial_ref)

    desc = arcpy.Describe(polyline)
    if desc.hasZ:
        arcpy.management.CalculateGeometryAttributes(polyline, [["length_metres", "LENGTH_3D"]], length_unit="METERS", coordinate_system=sr)
    else:
        arcpy.management.CalculateGeometryAttributes(polyline, [["length_metres", "LENGTH"]], length_unit="METERS", coordinate_system=spatial_ref)

    cursor = arcpy.SearchCursor(polyline)
    row = cursor.next()
    while row:
        distance = float(row.getValue("length_metres"))
        row = cursor.next()
        break

    time_s = distance/speed_ms

    time_txt = convert_seconds_to_string(time_s)

    is_time_s_field = False
    is_time_txt_field = False

    lst_fields = arcpy.ListFields(polyline)
    for field in lst_fields:
        if field.name == "travel_time_s":
            is_time_s_field = True
        if field.name == "travel_time_text":
            is_time_txt_field = True

    if not is_time_s_field:
        arcpy.management.AddField(polyline, "travel_time_s", "LONG", field_alias="Travel Time in Seconds")
    if not is_time_txt_field:
        arcpy.management.AddField(polyline, "travel_time_text", "TEXT", field_alias="Travel Time")

    with arcpy.da.UpdateCursor(polyline, ["travel_time_s", "travel_time_text"]) as cursor:
        for row in cursor:
            row[0] = time_s
            row[1] = time_txt
            cursor.updateRow(row)
            break
