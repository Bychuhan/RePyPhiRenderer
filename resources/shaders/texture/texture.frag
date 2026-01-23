#version 330 core

in vec2 texCoord;

out vec4 fragColor;

uniform sampler2D texture;
uniform vec4 color;

void main() {
    fragColor = texture2D(texture, texCoord) * color;
}