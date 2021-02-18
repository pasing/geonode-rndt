import json
import re

from django.http import HttpResponse
from geonode.base.models import ThesaurusKeywordLabel
from geonode.layers.views import (_PERMISSION_MSG_METADATA, _resolve_layer,
                                  check_keyword_write_perms)
from geonode.layers.views import layer_metadata as geonode_layer_view
from geonode.layers.views import logger, login_required
from rndt.layers.forms import LayerRNDTForm
from rndt.models import LayerRNDT


@login_required
@check_keyword_write_perms
def layer_metadata(
    request,
    layername,
    template="layers/layer_metadata.html",
    ajax=True,
    *args,
    **kwargs,
):
    if request.method == "POST":
        layer = _resolve_layer(
            request,
            layername,
            "base.change_resourcebase_metadata",
            _PERMISSION_MSG_METADATA,
        )
        constraint_form = LayerRNDTForm(request.POST)
        if not constraint_form.is_valid():
            logger.error(
                f"Additional Contraints form is not valid: {constraint_form.errors}"
            )
            out = {
                "success": False,
                "errors": [
                    re.sub(re.compile("<.*?>"), "", str(err))
                    for err in constraint_form.errors
                ],
            }
            return HttpResponse(
                json.dumps(out), content_type="application/json", status=400
            )

        #  get cleaned form values
        items = constraint_form.cleaned_data
        #  create the constraints_other required for RNDT
        constraints_other = f"{items['access_contraints'].keyword.about}+{items['access_contraints'].label}"
        #  get the layer available or create it
        available = LayerRNDT.objects.get(layer=layer)
        #  if the object does not exists, will save it for the first time
        if available is None:
            available = LayerRNDT(
                layer=layer,
                constraints_other=constraints_other
            )
             #  save the new value in the DB
            available.save()
        else:
            #  if the object exists and the constraing_other is changed
            #  the value will be updated
            if available.is_changed(constraints_other):
                available.constraints_other = constraints_other
                #  save the new value in the DB
                available.save()

        #  get the value to be saved in constraints_other
        layer_constraint = (
            items["free_text"]
            if items["use_constraints"] == "freetext"
            else items["use_constraints"]
        )
        #  cloning acutal request to make it mutable
        request.POST = request.POST.copy()
        #  oerride fields needed for rndt
        request.POST['resource-restriction_code_type'] = '8'
        if layer_constraint.isnumeric():
            klobj = ThesaurusKeywordLabel.objects.get(id=layer_constraint)
            request.POST['resource-constraints_other'] = f"{klobj.keyword.about}+{klobj.label}"
        else:
            request.POST['resource-constraints_other'] = layer_constraint
        #  reset the request as immutable
        request.POST._mutable = False

    return geonode_layer_view(request, layername, template, ajax, *args, **kwargs)
