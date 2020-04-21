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
        if ((data.get("width") and data.get("scale")) or
                (data.get("height") and data.get("scale"))):
            err_msg = 'Please select correct arguments combination: 1)scale 2)height 3)width 4)height and width'
            raise ValidationError(err_msg)

