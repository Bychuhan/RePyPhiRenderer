from typing import Any

import moderngl as mgl
import numpy as np
from loguru import logger


class Shader:
    def __init__(self, ctx: mgl.Context, vertices: list[float],
                 vertex_code: str, fragment_code: str,
                 in_types: str, in_vars: list[str] = [],
                 indices: list[int] = []):

        self.vbo = ctx.buffer(np.array(vertices, dtype="f4"))

        self.ibo: mgl.Buffer = None
        if indices:
            self.ibo = ctx.buffer(np.array(indices, dtype="i4"))

        self.vertex_code = vertex_code
        self.fragment_code = fragment_code

        self.program = ctx.program(vertex_shader=self.vertex_code,
                                   fragment_shader=self.fragment_code)

        self.vao: mgl.VertexArray = None
        if indices:
            self.vao = ctx.vertex_array(
                self.program,
                [[self.vbo, in_types] + in_vars],
                index_buffer=self.ibo
            )
        else:
            self.vao = ctx.vertex_array(
                self.program,
                [[self.vbo, in_types] + in_vars]
            )

    def set_uniform(self, key: str, value: Any):
        if key in self.program:
            self.program[key] = value
        else:
            logger.warning(f"不存在 Uniform {key}")
            return

    def render(self, mode: int | None = mgl.TRIANGLES):
        self.vao.render(mode=mode)

    def release(self):
        self.vao.release()
        self.program.release()

        if not self.self.ibo is None:
            self.ibo.release()

        self.vbo.release()


class ShaderManager:
    def __init__(self):
        self.shaders: dict[str, Shader] = {}

    def create_shader(self, ctx: mgl.Context, name: str, vertices: list[float],
                      vertex_code: str, fragment_code: str,
                      in_types: str, in_vars: list[str] = [],
                      indices: list[int] = [], replace: bool = True) -> None:

        if name in self.shaders:
            logger.warning(f"着色器 {name} 已存在")

            if not replace:
                return

        new_shader = Shader(ctx, vertices,
                            vertex_code, fragment_code,
                            in_types=in_types, in_vars=in_vars,
                            indices=indices)

        self.shaders[name] = new_shader

    def use_shader(self, name: str, mode: int | None = mgl.TRIANGLES):
        if not name in self.shaders:
            logger.warning(f"着色器 {name} 不存在")

            return

        shader = self.shaders[name]

        shader.render(mode=mode)

    def set_shader_uniform(self, name: str, key: str, value: Any):
        if not name in self.shaders:
            logger.warning(f"着色器 {name} 不存在")

            return

        shader = self.shaders[name]

        shader.set_uniform(key, value)

    def destroy_shader(self, name: str):
        if not name in self.shaders:
            logger.warning(f"销毁的着色器 {name} 不存在")

            return

        shader = self.shaders[name]

        shader.release()

        self.shaders.pop(name)
