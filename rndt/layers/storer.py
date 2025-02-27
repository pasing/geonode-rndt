from geonode.catalogue.models import catalogue_post_save
from geonode.layers.models import Layer
from rndt.models import LayerRNDT


def rndt_storer(layer, custom):
    rndt_dict = custom.get('rndt', None)
    if rndt_dict is not None:
        rndt, created = LayerRNDT.objects.get_or_create(
            layer=layer,
            constraints_other=rndt_dict.get("constraints_other", None),
            resolution=rndt_dict.get("resolution", None),
            accuracy=rndt_dict.get("accuracy", None),
        )

        if not created:
            rndt.constraints_other=rndt_dict.get("constraints_other", None)
            rndt.resolution=rndt_dict.get("resolution", None)
            rndt.accuracy=rndt_dict.get("accuracy", None)
            rndt.save()
    
    catalogue_post_save(layer, Layer)
    return layer
