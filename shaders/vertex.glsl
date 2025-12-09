#version 330

in vec3 in_position;
in vec3 in_normal;

out vec3 v_position;
out vec3 v_normal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main() {
    vec4 world_pos = model * vec4(in_position, 1.0);
    v_position = world_pos.xyz;
    v_normal = mat3(transpose(inverse(model))) * in_normal;
    gl_Position = projection * view * world_pos;
}