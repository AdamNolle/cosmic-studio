// SPDX-License-Identifier: GPL-3.0-only
// Original COSMIC backdrop optics inspired by ryohsuke1231/liquid-glass.
// Analytic GPU lens rays through two optical interfaces and a backdrop plane.
// The cached native backdrop supplies the scene; foreground text stays separate.
#version 100
//_DEFINES_
#if defined(EXTERNAL)
#extension GL_OES_EGL_image_external : require
#endif
precision highp float;
#if defined(EXTERNAL)
uniform samplerExternalOES tex;
#else
uniform sampler2D tex;
#endif
uniform float alpha;
varying vec2 v_coords;
#if defined(DEBUG_FLAGS)
uniform float tint;
#endif
uniform vec2 geo_size;
uniform vec4 corner_radius;
uniform mat3 input_to_geo;
uniform mat3 geo_to_input;
uniform float pool_inset;
uniform float pool_radius;
uniform float material_type;
uniform float noise;

float rounded_distance(vec2 p, vec2 size, float radius) {
    vec2 q = abs(p - size * 0.5) - (size * 0.5 - radius);
    return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - radius;
}

vec2 rounded_normal(vec2 p, vec2 size, float radius) {
    vec2 centered = p - size * 0.5;
    vec2 q = abs(centered) - (size * 0.5 - radius);
    vec2 direction = mix(vec2(-1.0), vec2(1.0), step(vec2(0.0), centered));
    vec2 outside = max(q, 0.0);
    if (dot(outside, outside) > 0.00001)
        return normalize(outside) * direction;
    return q.x > q.y ? vec2(direction.x, 0.0) : vec2(0.0, direction.y);
}

float outer_alpha(vec2 p) {
    float r = p.x < geo_size.x * 0.5
        ? (p.y < geo_size.y * 0.5 ? corner_radius.x : corner_radius.w)
        : (p.y < geo_size.y * 0.5 ? corner_radius.y : corner_radius.z);
    r = min(r, min(geo_size.x, geo_size.y) * 0.5);
    return 1.0 - smoothstep(-0.5, 0.5, rounded_distance(p, geo_size, r));
}

float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

vec2 limited_offset(vec2 offset, float limit) {
    return offset * min(1.0, limit / max(length(offset), 0.0001));
}

// Snell refraction through a curved entrance and a flat rear face. There is
// no scene depth buffer in a desktop: the native backdrop is the image plane.
vec2 trace_lens(vec3 normal, float height, float depth, float ior,
                float limit, out float internal_reflection) {
    vec3 inside = refract(vec3(0.0, 0.0, -1.0), normal, 1.0 / ior);
    vec3 outgoing = refract(inside, vec3(0.0, 0.0, 1.0), ior);
    internal_reflection = 1.0 - step(0.00001, dot(outgoing, outgoing));
    vec2 rear_hit = inside.xy * height / max(-inside.z, 0.08);
    vec2 plane_hit = outgoing.xy * depth / max(-outgoing.z, 0.12);
    return limited_offset(rear_hit + plane_hit, limit);
}

vec4 backdrop(vec2 p) {
    vec2 uv = (geo_to_input * vec3(p / geo_size, 1.0)).xy;
    return texture2D(tex, clamp(uv, vec2(0.0), vec2(1.0)));
}

void main() {
    if (alpha <= 0.0) discard;
    vec2 p = (input_to_geo * vec3(v_coords, 1.0)).xy * geo_size;
    if (any(lessThan(p, vec2(0.0))) || any(greaterThan(p, geo_size))) discard;
    float mask = outer_alpha(p);
    if (mask <= 0.0) discard;
    vec2 inner_size = max(geo_size - pool_inset * 2.0, vec2(1.0));
    vec2 inner_p = p - pool_inset;
    float native_radius = p.x < geo_size.x * 0.5
        ? (p.y < geo_size.y * 0.5 ? corner_radius.x : corner_radius.w)
        : (p.y < geo_size.y * 0.5 ? corner_radius.y : corner_radius.z);
    float radius = min(material_type > 1.5 || material_type < 0.5 ? native_radius : pool_radius,
                       min(inner_size.x, inner_size.y) * 0.5);
    float distance_to_rim = rounded_distance(inner_p, inner_size, radius);
    vec2 normal = rounded_normal(inner_p, inner_size, radius);
    float inward = max(-distance_to_rim, 0.0);
    bool dock = material_type > 0.5 && material_type < 1.5;
    bool floating = material_type > 1.5;
    bool window = material_type > 2.5;
    float max_shift = window ? 3.0 : (dock ? 18.0 : (floating ? 8.0 : 5.0));
    float thickness = window ? 2.5 : (dock ? 8.5 : (floating ? 6.0 : 3.5));
    float scene_depth = window ? 7.0 : (dock ? 27.0 : (floating ? 16.0 : 11.0));
    float band = min(window ? 12.0 : (dock ? 24.0 : (floating ? 17.0 : 10.0)),
                     min(inner_size.x, inner_size.y) * 0.5);
    float edge = 1.0 - clamp(inward / max(band, 1.0), 0.0, 1.0);
    float sag = sqrt(max(1.0 - edge * edge, 0.012));
    float slope = min(thickness * edge / max(band * sag, 0.01), 2.2);
    vec3 bevel_normal = normalize(vec3(normal * slope, 1.0));
    float surface_height = thickness * sag;
    float coverage = 1.0 - smoothstep(-0.25, 0.5, distance_to_rim);
    float total_reflection;
    vec2 ray = trace_lens(bevel_normal, surface_height, scene_depth,
                          1.46, max_shift, total_reflection) * coverage;
    // Mild wavelength dispersion, strongest at grazing edges. Three bounded
    // transmission samples plus one reflection sample, with no ray-march loop.
    float ignored;
    vec2 red_ray = trace_lens(bevel_normal, surface_height, scene_depth,
                              1.452, max_shift, ignored) * coverage;
    vec2 blue_ray = trace_lens(bevel_normal, surface_height, scene_depth,
                               1.468, max_shift, ignored) * coverage;
    vec4 green = backdrop(p + ray);
    vec4 red = backdrop(p + red_ray);
    vec4 blue = backdrop(p + blue_ray);
    vec4 color = vec4(red.r, green.g, blue.b, green.a);
#if defined(NO_ALPHA)
    color.a = 1.0;
#endif
    if (color.a <= 0.0) discard;
    vec2 light_direction = normalize(vec2(-0.65, -0.76));
    float directional_light = max(dot(normal, light_direction), 0.0);
    float rim = exp(-abs(distance_to_rim + 0.7) * 1.15);
    vec3 half_vector = normalize(vec3(-0.40, -0.58, 0.72) + vec3(0.0, 0.0, 1.0));
    float specular = pow(max(dot(bevel_normal, half_vector), 0.0), 42.0) * edge;
    float f0 = pow((1.46 - 1.0) / (1.46 + 1.0), 2.0);
    float fresnel = f0 + (1.0 - f0) * pow(1.0 - bevel_normal.z, 5.0);
    fresnel = mix(fresnel, 1.0, total_reflection);
    vec3 reflected_ray = reflect(vec3(0.0, 0.0, -1.0), bevel_normal);
    vec2 reflection_offset = limited_offset(reflected_ray.xy * scene_depth,
                                             max_shift);
    vec4 reflected = backdrop(p + reflection_offset);
    color.rgb = mix(color.rgb, reflected.rgb, fresnel * coverage);
    float material_strength = window ? 0.45 : (dock ? 1.0 : (floating ? 0.78 : 0.65));
    float highlight = material_strength * (
        rim * (0.055 + 0.20 * pow(directional_light, 3.0))
        + specular * 0.30 + fresnel * 0.10);
    float inner_shade = exp(-inward / 6.0)
        * (1.0 - directional_light) * edge * 0.045;
    color.rgb *= 1.0 - inner_shade;
    color.rgb += vec3(0.98) * highlight * color.a;
    // Stable grain; no clock, animation, CPU reads or per-frame random seed.
    color.rgb += (hash(floor(p * 2.0)) - 0.5) * noise * color.a;
    color.rgb = clamp(color.rgb, vec3(0.0), vec3(color.a));
    color *= mask * alpha;
#if defined(DEBUG_FLAGS)
    if (tint == 1.0) color = vec4(0.0, 0.2, 0.0, 0.2) + color * 0.8;
#endif
    gl_FragColor = color;
}
