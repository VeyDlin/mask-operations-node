from PIL import ImageOps, Image, ImageChops
from typing import Literal

from invokeai.app.services.image_records.image_records_common import ImageCategory, ResourceOrigin
from invokeai.app.invocations.baseinvocation import (
    BaseInvocation,
    InputField,
    invocation,
    InvocationContext,
    WithMetadata,
    WithWorkflow,
)

from invokeai.app.invocations.primitives import (
    ImageField,
    ImageOutput
)

OP_MODES = Literal[
    "OR",
    "SUB",
    "AND"
]


@invocation(
    "mask_operations",
    title="Mask Operations",
    tags=["image", "mask"],
    category="image",
    version="1.0.0",
)
class MaskOperationsIvocation(BaseInvocation, WithMetadata, WithWorkflow):
    """Mask Operations"""
    mask_a: ImageField = InputField(default=None, description="A mask")
    mask_b: ImageField = InputField(default=None, description="B mask")
    operation: OP_MODES = InputField(default="OR", description="Operation")
    invert_a: bool = InputField(default=False, description="Invert A input mask before the operation")
    invert_b: bool = InputField(default=False, description="Invert b input mask before the operation")
    invert_output: bool = InputField(default=False, description="Inverted output")

    def invoke(self, context: InvocationContext) -> ImageOutput:
        mask_a = context.services.images.get_pil_image(self.mask_a.image_name).convert('L')
        mask_b = context.services.images.get_pil_image(self.mask_b.image_name).convert('L')
 
        if mask_a.size != mask_b.size:
            mask_b = mask_b.resize(mask_a.size)
        
        if self.invert_a:
            mask_a = ImageOps.invert(mask_a)

        if self.invert_b:
            mask_b = ImageOps.invert(mask_b)


        if self.operation == "OR":
            result = ImageChops.lighter(mask_a, mask_b)

        if self.operation == "SUB":
            result = ImageChops.subtract(mask_a, mask_b, scale=1.0, offset=0)

        if self.operation == "AND":
            result = ImageChops.darker(mask_a, mask_b)


        if self.invert_output:
            result = ImageOps.invert(result)

        image_dto = context.services.images.create(
            image=result.convert('RGBA'),
            image_origin=ResourceOrigin.INTERNAL,
            image_category=ImageCategory.GENERAL,
            node_id=self.id,
            session_id=context.graph_execution_state_id,
            is_intermediate=self.is_intermediate,
            workflow=self.workflow,
        )

        return ImageOutput(
            image=ImageField(image_name=image_dto.image_name),
            width=image_dto.width,
            height=image_dto.height,
        )
    