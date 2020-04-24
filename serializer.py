from marshmallow import Schema, fields, validate, post_load, validates, validates_schema, ValidationError


class ImageSchema(Schema):
    scale = fields.Int(
        validate=validate.Range(min=1, max=100),
        required=False,
    )
    width = fields.Int(
        required=False,
    )
    height = fields.Int(
        required=False,
    )

    @validates_schema
    def validates_schema(self, data, **kwargs):
        err_msg = 'Please select correct arguments combination: 1)scale 2)height 3)width 4)height and width'
        width = data.get("width")
        scale = data.get("scale")
        height = data.get("height")
        if not any([width, scale, height]):
            raise ValidationError(err_msg, field_name="error")
        if ((width and scale) or
                (height and scale)):
            raise ValidationError(err_msg, field_name="error")
