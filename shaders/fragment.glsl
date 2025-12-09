#version 330

in vec3 v_position;
in vec3 v_normal;

out vec4 frag_color;

struct Material {
    vec3 diffuse;
    vec3 specular;
    float shininess;
    float alpha;
    vec3 emission;
};

struct Light {
    vec3 position;
    vec3 color;
    float intensity;
};

uniform Material material;
uniform Light lights[4];
uniform int numLights;
uniform vec3 viewPos;

void main() {
    vec3 normal = normalize(v_normal);
    vec3 view_dir = normalize(viewPos - v_position);
    vec3 result = material.emission;
    
    for (int i = 0; i < numLights; i++) {
        vec3 light_dir = normalize(lights[i].position - v_position);
        float diff = max(dot(normal, light_dir), 0.0);
        vec3 diffuse = lights[i].color * diff * material.diffuse * lights[i].intensity;
        
        vec3 reflect_dir = reflect(-light_dir, normal);
        float spec = pow(max(dot(view_dir, reflect_dir), 0.0), material.shininess);
        vec3 specular = lights[i].color * spec * material.specular * lights[i].intensity;
        
        float distance = length(lights[i].position - v_position);
        float attenuation = 1.0 / (1.0 + 0.1 * distance + 0.01 * distance * distance);
        
        result += (diffuse + specular) * attenuation;
    }
    
    vec3 ambient = vec3(0.1) * material.diffuse;
    result += ambient;
    
    frag_color = vec4(result, material.alpha);
}