import moderngl as mgl


class Renderer:
    def __init__(self, standalone: bool = False):
        self.ctx = mgl.create_context(standalone=standalone)

    def set_blend(self, enable: bool = True):
        if enable:
            self.ctx.enable(mgl.BLEND)
            self.ctx.blend_func = (
                mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA,
                mgl.ONE, mgl.ONE
            )
        else:
            self.ctx.disable(mgl.BLEND)
