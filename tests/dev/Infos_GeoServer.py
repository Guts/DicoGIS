#! python3  # noqa: E265


# ----------------------------------------------------------------------------
# Name:         InfosWFS
# Purpose:      Uses OGR to read GeoServer
#
# Author:       Julien Moura (https://github.com/Guts/)
# ----------------------------------------------------------------------------

# ############################################################################
# ########## Libraries #############
# ##################################

# 3rd party libraries
from geoserver.catalog import Catalog

# ############################################################################
# ########## Classes #############
# ################################


class ReadGeoServer:
    def __init__(self, gs_axx, dico_gs, tipo, txt=""):
        """Uses OGR functions to extract basic informations about
        geographic Web Features Services.

        gs_axx = tuple like {url of a geoserver, user, password)
        dico_gs = dictionary to store
        tipo = format
        text = dictionary of text in the selected language
        """
        # connection
        cat = Catalog(gs_axx[0], gs_axx[1], gs_axx[2])
        # print(dir(cat))

        # workspaces
        workspaces = cat.get_workspaces()
        for wk in workspaces:
            # print(wk.name, wk.enabled, , wk.resource_type, wk.wmsstore_url)
            dico_gs[wk.name] = wk.href
        # print(dir(wk))

        # stores
        stores = cat.get_stores()
        for st in stores:
            # print(st.name, st.enabled, st.href, st.resource_type)
            dico_gs[st.name] = st.href

        print(dir(st))

        # layers
        layers = cat.get_layers()
        for layer in layers:
            # print(layer.name, layer.enabled, layer.resource._store.name, layer.resource._workspace.name)
            title = layer.resource.title
            print(
                (
                    layer.resource._workspace.name
                    + "/wms?layers={}:{};".format(
                        layer.resource._workspace.name, layer.name
                    ),
                    title.encode("utf8"),
                )
            )
            # print(title.encode("utf8"))
            # dico_layers[layer.name] = layer.enabled, layer.resource.title, layer.resource.abstract, layer.resource.keywords
            # dico_stores[layer.resource._store.name] = dico_layers
            # dico_gs[layer.resource._workspace] = dico_stores
        print(dir(layer.resource))


# ############################################################################
# ##### Stand alone program ########
# ##################################

if __name__ == "__main__":
    """Standalone execution."""
    pass
