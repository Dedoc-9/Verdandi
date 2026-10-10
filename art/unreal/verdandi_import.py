# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# art/unreal/verdandi_import.py — ART-GENERATION-0's Unreal side: a Verðandi scene into the open level.
#
# Run inside the Unreal Editor (5.8, Python Editor Script Plugin enabled), from the Output Log's Cmd box:
#
#   py "C:/path/to/Verdandi/art/unreal/verdandi_import.py" "C:/path/to/Verdandi/art/build/plaza-night/scene.json"
#
# What it does, in one editor transaction (Ctrl+Z undoes it):
#   - materials: one parameterised surface material, and one instance per material of the scene (updated in place
#     when a look revision changes them)
#   - play geometry: C's boxes, visible, with collision. The only collision this script creates
#   - dressing: the art's boxes, with collision switched off
#   - light and air: rect and point lights, the moon or sun, sky, sky light, height fog, one post-process volume
#   - the spawn as a PlayerStart, and each critique view as a camera
#
# Every actor it makes carries the tag VerdandiArt, its scene id and a hash of what it was made from. Run it again on
# a revised scene and it keeps every actor whose item did not change, removes the ones that went, and makes the new
# and changed ones: the engine shows the revision's locality, actor by actor. It then checks the level against the
# scene — the collision actors laid back onto the grid must be C, and no dressing may have collision — and writes
# a report beside the scene (unreal-report.txt).
#
# Written against the Unreal Python API 5.8 documentation. Its first run on an engine is its first test: anything it
# could not do is in the report, not hidden.

import hashlib
import json
import math
import os
import sys

import unreal

TAG = "VerdandiArt"
MAT_DIR = "/Game/Verdandi/Materials"
MASTER = "M_VerdandiSurface"
REPORT = []


def say(line):
    REPORT.append(line)
    unreal.log("[verdandi] " + line)


def warn(line):
    REPORT.append("WARNING " + line)
    unreal.log_warning("[verdandi] " + line)


def h12(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:12]


def lin(c):
    """sRGB 0-255 to linear 0-1."""
    out = []
    for v in c:
        s = v / 255.0
        out.append(s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4)
    return out


def V(x, y, z):
    """Scene metres (x east, y up, z south) to Unreal centimetres (X east, Y south, Z up)."""
    return unreal.Vector(x * 100.0, z * 100.0, y * 100.0)


def ue_yaw(scene_yaw):
    """Scene yaw (0 north, 90 east) to Unreal yaw (0 along +X, east)."""
    return scene_yaw - 90.0


# -------------------------------------------------------------------------------------------- materials
def master_material():
    path = MAT_DIR + "/" + MASTER
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mat = tools.create_asset(MASTER, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary

    def vec(name, x, y, default):
        e = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, x, y)
        e.set_editor_property("parameter_name", name)
        e.set_editor_property("default_value", unreal.LinearColor(*default))
        return e

    def sca(name, x, y, default):
        e = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, x, y)
        e.set_editor_property("parameter_name", name)
        e.set_editor_property("default_value", default)
        return e

    base = vec("BaseColor", -600, -300, (0.2, 0.2, 0.2, 1.0))
    rough = sca("Roughness", -600, -100, 0.8)
    metal = sca("Metallic", -600, 0, 0.0)
    emis = vec("Emissive", -800, 150, (0.0, 0.0, 0.0, 1.0))
    strength = sca("EmissiveStrength", -800, 300, 0.0)
    mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -500, 200)
    mel.connect_material_expressions(emis, "", mul, "A")
    mel.connect_material_expressions(strength, "", mul, "B")
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    say("made the surface material %s" % path)
    return mat


def material_instances(scene, master):
    mel = unreal.MaterialEditingLibrary
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    out, made, updated = {}, 0, 0
    for name, m in sorted(scene["materials"].items()):
        aname = "MI_V_" + name
        path = MAT_DIR + "/" + aname
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            mi = unreal.EditorAssetLibrary.load_asset(path)
        else:
            mi = tools.create_asset(aname, MAT_DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
            mel.set_material_instance_parent(mi, master)
            made += 1
        b, e = lin(m["base"]), lin(m["emissive"])
        mel.set_material_instance_vector_parameter_value(mi, "BaseColor", unreal.LinearColor(b[0], b[1], b[2], 1.0))
        mel.set_material_instance_scalar_parameter_value(mi, "Roughness", float(m["roughness"]))
        mel.set_material_instance_scalar_parameter_value(mi, "Metallic", float(m["metallic"]))
        mel.set_material_instance_vector_parameter_value(mi, "Emissive", unreal.LinearColor(e[0], e[1], e[2], 1.0))
        mel.set_material_instance_scalar_parameter_value(mi, "EmissiveStrength", float(m["emissive_strength"]))
        mel.update_material_instance(mi)
        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        updated += 1
        out[name] = mi
    say("materials: %d instance(s), %d new, all set from the scene" % (updated, made))
    return out


# -------------------------------------------------------------------------------------------- actors
def tagged():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    have = {}
    for a in eas.get_all_level_actors():
        tags = [str(t) for t in a.get_editor_property("tags")]
        if TAG in tags:
            vid = next((t[4:] for t in tags if t.startswith("vid=")), None)
            vh = next((t[3:] for t in tags if t.startswith("vh=")), None)
            have[vid] = (a, vh)
    return have


def mark(actor, vid, vh, folder, label):
    actor.set_editor_property("tags", [unreal.Name(TAG), unreal.Name("vid=" + vid), unreal.Name("vh=" + vh)])
    actor.set_folder_path(unreal.Name("Verdandi/" + folder))
    actor.set_actor_label(label)


def box_actor(eas, cube, b, mi, collide):
    x0, y0, z0, x1, y1, z1 = b
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, V((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
    a.set_actor_scale3d(unreal.Vector(x1 - x0, z1 - z0, y1 - y0))
    c = a.get_editor_property("static_mesh_component")
    c.set_static_mesh(cube)
    c.set_material(0, mi)
    if collide:
        c.set_collision_profile_name("BlockAll")
        c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    else:
        c.set_collision_profile_name("NoCollision")
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return a


def light_actor(eas, L):
    p = L["pos"]
    d = L.get("dir", [0, -1, 0])
    X, Y, Z = d[0], d[2], d[1]
    rot = unreal.Rotator(roll=0.0, pitch=math.degrees(math.atan2(Z, math.hypot(X, Y))), yaw=math.degrees(math.atan2(Y, X)))
    cls = unreal.RectLight if L["type"] == "rect" else unreal.PointLight
    a = eas.spawn_actor_from_class(cls, V(p[0], p[1], p[2]), rot)
    c = a.get_editor_property("light_component")
    c.set_mobility(unreal.ComponentMobility.MOVABLE)
    try:
        c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    except Exception as e:  # noqa: BLE001
        warn("intensity units not set on %s: %s" % (L["id"], e))
    c.set_editor_property("intensity", float(L["candela"]))
    col = [v / 255.0 for v in L["color"]]
    c.set_light_color(unreal.LinearColor(col[0], col[1], col[2], 1.0), True)
    c.set_editor_property("attenuation_radius", float(L["radius"]) * 100.0)
    if L["type"] == "rect":
        c.set_editor_property("source_width", float(L["width"]) * 100.0)
        c.set_editor_property("source_height", float(L["height"]) * 100.0)
    return a


def environment(eas, scene, have, keep):
    env = scene["environment"]
    vh = h12(env)
    made = []
    old = [vid for vid in have if vid and vid.startswith("env:")]
    if old and all(have[v][1] == vh for v in old) and len(old) == 4 + (1 if env.get("light") else 0):
        keep.update(old)
        say("air and sky unchanged")
        return
    for v in old:
        eas.destroy_actor(have.pop(v)[0])
    L = env.get("light")
    if L:
        a, e = L["azimuth"], L["elevation"]
        ra, re_ = math.radians(a), math.radians(e)
        fwd = (-math.sin(ra) * math.cos(re_), math.cos(ra) * math.cos(re_), -math.sin(re_))
        rot = unreal.Rotator(roll=0.0, pitch=math.degrees(math.atan2(fwd[2], math.hypot(fwd[0], fwd[1]))), yaw=math.degrees(math.atan2(fwd[1], fwd[0])))
        d = eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 3000), rot)
        c = d.get_editor_property("light_component")
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_editor_property("intensity", float(L["lux"]))
        col = [v / 255.0 for v in L["color"]]
        c.set_light_color(unreal.LinearColor(col[0], col[1], col[2], 1.0), True)
        try:
            c.set_editor_property("atmosphere_sun_light", True)
        except Exception as ex:  # noqa: BLE001
            warn("the %s is not the atmosphere's light: %s" % (L["kind"], ex))
        made.append(("env:light", d, "the " + L["kind"]))
    sky = eas.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
    made.append(("env:atmosphere", sky, "sky atmosphere"))
    sl = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 2000), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
    slc = sl.get_editor_property("light_component")
    slc.set_mobility(unreal.ComponentMobility.MOVABLE)
    try:
        slc.set_editor_property("real_time_capture", True)
    except Exception as ex:  # noqa: BLE001
        warn("the sky light does not capture in real time: %s" % ex)
    made.append(("env:skylight", sl, "sky light"))
    F = env.get("fog")
    fog = eas.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
    fc = fog.get_editor_property("component")
    if F:
        fc.set_editor_property("fog_density", float(F["density"]))
        fc.set_editor_property("fog_height_falloff", 0.2)
        col = lin(F["color"])
        try:
            fc.set_fog_inscattering_color(unreal.LinearColor(col[0], col[1], col[2], 1.0))
        except Exception as ex:  # noqa: BLE001
            warn("the fog's colour was not set: %s" % ex)
        fc.set_editor_property("enable_volumetric_fog", bool(F["volumetric"]))
        if F["volumetric"]:
            fc.set_editor_property("volumetric_fog_scattering_distribution", 0.3)
    made.append(("env:fog", fog, "height fog"))
    pp = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
    pp.set_editor_property("unbound", True)
    s = pp.get_editor_property("settings")
    s.set_editor_property("override_auto_exposure_bias", True)
    s.set_editor_property("auto_exposure_bias", float(env["exposure"]))
    s.set_editor_property("override_bloom_intensity", True)
    s.set_editor_property("bloom_intensity", float(env["bloom"]))
    s.set_editor_property("override_vignette_intensity", True)
    s.set_editor_property("vignette_intensity", 0.45)
    pp.set_editor_property("settings", s)
    made.append(("env:post", pp, "post process"))
    for vid, actor, label in made:
        mark(actor, vid, vh, "Environment", "V " + label)
        keep.add(vid)
    if env.get("rain"):
        warn("rain %.1f is asked for: the surfaces are wet, but no rain particles are made (a Niagara system is an asset for "
             "the kit to bring)" % env["rain"])
    say("air and sky made: %s" % ", ".join(label for _v, _a, label in made))


def import_scene(path):
    scene = json.load(open(path, encoding="utf-8"))
    if scene.get("format") != "VERDANDI-ART-SCENE 0":
        raise RuntimeError("%s is not a VERDANDI-ART-SCENE 0 scene" % path)
    say("engine %s; scene %s (%s), map %s" % (unreal.SystemLibrary.get_engine_version(), scene["name"], scene.get("title", ""), scene["map"]))
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    cube_path = scene["assets"]["cube"]["path"]
    cube = unreal.EditorAssetLibrary.load_asset(cube_path)
    if cube is None:
        raise RuntimeError("the mesh %s did not load" % cube_path)
    master = master_material()
    mis = material_instances(scene, master)
    have = tagged()
    keep, made, same = set(), {"Play": 0, "Dressing": 0, "Lights": 0, "Views": 0}, [0]
    with unreal.ScopedEditorTransaction("Verdandi: import %s" % scene["name"]):
        def want(vid, item, folder, build, label):
            vh = h12(item)
            if vid in have and have[vid][1] == vh:
                keep.add(vid)
                same[0] += 1
                return
            if vid in have:
                eas.destroy_actor(have[vid][0])
            a = build()
            mark(a, vid, vh, folder, label)
            keep.add(vid)
            made[folder] += 1

        for b in scene["collision"]:
            want("c=" + b["id"], b, "Play", lambda b=b: box_actor(eas, cube, b["box"], mis[b["material"]], True), "V play " + b["id"])
        for v in scene["visuals"]:
            want("v=" + v["id"], v, "Dressing", lambda v=v: box_actor(eas, cube, v["box"], mis[v["material"]], False), "V " + v["id"])
        for L in scene["lights"]:
            want("l=" + L["id"], L, "Lights", lambda L=L: light_actor(eas, L), "V light " + L["id"])
        for k, sp in sorted(scene["spawns"].items()):
            def start(sp=sp):
                return eas.spawn_actor_from_class(unreal.PlayerStart, V(sp["x"], sp["y"] + 0.92, sp["z"]), unreal.Rotator(roll=0.0, pitch=0.0, yaw=ue_yaw(sp["yaw"])))
            if k == "A":
                want("spawn=" + k, sp, "Views", start, "V spawn " + k)
        for name, vw in sorted(scene.get("views", {}).items()):
            def cam(vw=vw):
                return eas.spawn_actor_from_class(unreal.CameraActor, V(vw["x"], vw["y"], vw["z"]), unreal.Rotator(roll=0.0, pitch=vw["pitch"], yaw=ue_yaw(vw["yaw"])))
            want("view=" + name, vw, "Views", cam, "V view " + name)
        environment(eas, scene, have, keep)
        gone = [vid for vid in have if vid not in keep]
        for vid in gone:
            eas.destroy_actor(have[vid][0])
    say("actors: %d kept unchanged, %d made or remade (play %d, dressing %d, lights %d, views %d), %d removed"
        % (same[0], sum(made.values()), made["Play"], made["Dressing"], made["Lights"], made["Views"], len(gone)))
    self_check(scene)
    player_check(scene)


def self_check(scene):
    """The level against the scene: collision actors laid back onto the grid are C; dressing has no collision."""
    g = scene["grid"]
    w, h, cell = g["w"], g["h"], g["cell"]
    top = [0.0] * (w * h)
    dressing_collide = []
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors():
        tags = [str(t) for t in a.get_editor_property("tags")]
        if TAG not in tags:
            continue
        vid = next((t[4:] for t in tags if t.startswith("vid=")), "")
        if vid.startswith("c=") and vid != "c=ground":
            origin, ext = a.get_actor_bounds(False)
            x0, x1 = (origin.x - ext.x) / 100.0, (origin.x + ext.x) / 100.0
            z0, z1 = (origin.y - ext.y) / 100.0, (origin.y + ext.y) / 100.0
            ytop = (origin.z + ext.z) / 100.0
            for z in range(int(round(z0 / cell)), int(round(z1 / cell))):
                for x in range(int(round(x0 / cell)), int(round(x1 / cell))):
                    if 0 <= x < w and 0 <= z < h:
                        top[z * w + x] = max(top[z * w + x], ytop)
        elif vid.startswith("v="):
            c = a.get_editor_property("static_mesh_component")
            if c.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION:
                dressing_collide.append(vid)
    bad = [k for k in range(w * h) if abs(top[k] - scene["tops"][k]) > 0.005]
    if bad:
        warn("FAIL collision is not C: %d cell(s) differ (first %d,%d: %.3f m in the level, %.3f m in C)"
             % (len(bad), bad[0] % w, bad[0] // w, top[bad[0]], scene["tops"][bad[0]]))
    else:
        say("PASS collision is C: the level's collision actors lay back onto all %d cells" % (w * h))
    if dressing_collide:
        warn("FAIL %d piece(s) of dressing have collision (first %s)" % (len(dressing_collide), dressing_collide[0]))
    else:
        say("PASS no dressing has collision")


def player_check(scene):
    """The checks' reach ceiling assumes the graybox player. Report the First Person template's character against it."""
    P = scene["player"]
    want = {"max_walk_speed": P["speed"] * 100.0, "jump_z_velocity": P["jump"] * 100.0, "gravity_scale": P["gravity"] / 9.8,
            "max_step_height": P["step"] * 100.0}
    found = None
    for path in unreal.EditorAssetLibrary.list_assets("/Game", recursive=True, include_folder=False):
        if path.split("/")[-1].split(".")[0].endswith("FirstPersonCharacter"):
            found = path
            break
    if not found:
        warn("no FirstPersonCharacter blueprint found: set the character's movement to the scene's player by hand")
        return
    bp = unreal.EditorAssetLibrary.load_asset(found)
    try:
        cdo = unreal.get_default_object(bp.generated_class())
        cm = cdo.get_editor_property("character_movement")
        rows = []
        for k, v in want.items():
            have = float(cm.get_editor_property(k))
            rows.append("%s %.2f (the checks assume %.2f)%s" % (k, have, v, "" if abs(have - v) < 0.01 * max(1.0, abs(v)) else "  <- differs"))
        say("the character %s: %s" % (found, "; ".join(rows)))
        if any("differs" in r for r in rows):
            warn("the character moves differently from the graybox player the checks assume: in the Blueprint's Character "
                 "Movement set Max Walk Speed %.0f, Jump Z Velocity %.0f, Gravity Scale %.2f, Max Step Height %.0f"
                 % (want["max_walk_speed"], want["jump_z_velocity"], want["gravity_scale"], want["max_step_height"]))
    except Exception as e:  # noqa: BLE001
        warn("the character's movement could not be read (%s): check it by hand" % e)


def main():
    args = [a for a in sys.argv[1:] if a]
    if not args:
        unreal.log_error("[verdandi] usage: py verdandi_import.py <scene.json>")
        return
    path = os.path.abspath(args[0])
    try:
        import_scene(path)
    except Exception as e:  # noqa: BLE001
        warn("stopped: %s" % e)
        raise
    finally:
        rpath = os.path.join(os.path.dirname(path), "unreal-report.txt")
        with open(rpath, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(REPORT) + "\n")
        unreal.log("[verdandi] report written to %s" % rpath)


main()
