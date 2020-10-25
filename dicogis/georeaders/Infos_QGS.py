#! python3  # noqa: E265


# ----------------------------------------------------------------------------
# Name:         QGS Reader
# Purpose:      Get some metadata about QGIS .qgs files without using QGIS.
#
# Author:       Julien Moura (https://github.com/Guts)
# ----------------------------------------------------------------------------

# ############################################################################
# ######### Libraries #############
# #################################

# Standard library
import logging
from os import chdir, listdir, path  # files and folder managing
from time import localtime, strftime

# 3rd party
import xmltodict

# custom submodules
try:
    from .geoutils import Utils
except ValueError:
    from geoutils import Utils

# ############################################################################
# ######### Globals ############
# ##############################

logger = logging.getLogger(__name__)
youtils = Utils(ds_type="flat")

# ############################################################################
# ######### Classes #############
# ###############################


class ReadQGS:
    """QGIS projects files (*.qgs) independant reader."""

    def __init__(self, src_path, dico_qgs, tipo, txt=""):
        """Parse QGS files which are XML based files.

        qgspath = path to the qgs file
        dico_qgs = dictionary for global informations
        tipo = format
        text = dictionary of text in the selected language
        """
        # changing working directory to layer folder
        chdir(path.dirname(src_path))
        # initializing errors counter
        self.alert = 0

        # context metadata
        dico_qgs["name"] = path.basename(src_path)
        dico_qgs["folder"] = path.dirname(src_path)
        dico_qgs["date_crea"] = strftime("%Y/%m/%d", localtime(path.getctime(src_path)))
        dico_qgs["date_actu"] = strftime("%Y/%m/%d", localtime(path.getmtime(src_path)))
        dico_qgs["total_size"] = youtils.sizeof(src_path)
        # opening qgs
        with open(qgspath, "r") as fd:
            in_xml = xmltodict.parse(fd.read())
            logger.debug("QGIS file opened.")
            xml_qgis = in_xml.get("qgis", {})
            print(xml_qgis.keys())
            # BASICS
            dico_qgs["title"] = xml_qgis.get("title")
            dico_qgs["description"] = xml_qgis.get("@projectname")
            dico_qgs["version"] = xml_qgis.get("@version")
            # MAP CANVAS
            qgs_map = xml_qgis.get("mapcanvas")
            if len(qgs_map) > 1:
                logging.info("QGS file has more than 1 mapcanvas markup.")
                qgs_map = qgs_map[0]
            else:
                pass
            dico_qgs["units"] = qgs_map.get("units")

            qgs_extent = qgs_map.get("extent")
            dico_qgs["Xmin"] = round(float(qgs_extent.get("xmin")), 2)
            dico_qgs["Xmax"] = round(float(qgs_extent.get("xmax")), 2)
            dico_qgs["Ymin"] = round(float(qgs_extent.get("ymin")), 2)
            dico_qgs["Ymax"] = round(float(qgs_extent.get("ymax")), 2)

            # SRS
            qgs_srs = qgs_map.get("destinationsrs").get("spatialrefsys")
            print(qgs_srs.keys())
            dico_qgs["srs"] = qgs_srs.get("description")
            if qgs_srs.get("geographicflag") == "false":
                dico_qgs["srs_type"] = "Projected"
            else:
                dico_qgs["srs_type"] = "Geographic"
            dico_qgs["EPSG"] = qgs_srs.get("authid")

            # LAYERS
            # print(xml_qgis.get("projectlayers").get("maplayer"))
            qgs_lyrs = xml_qgis.get("projectlayers").get("maplayer")
            dico_qgs["layers_count"] = len(qgs_lyrs)
            # print(len(qgs_lyrs))
            # print(xml_qgis.get("mapcanvas")[1].keys())

        # qgs = ElementTree.parse(src_path).getroot()
        # # print(qgs.getroot().attrib["version"])
        # # print(qgs.find( 'title').text)

    #     # basics
    #     dico_qgs['creator_prod'] = qgs.author
    # dico_qgs['version'] = qgs.attrib["version"]
    #     dico_qgs['credits'] = qgs.credits
    #     dico_qgs['subject'] = qgs.summary
    #     dico_qgs['relpath'] = qgs.relativePaths
    #     dico_qgs['url'] = qgs.hyperlinkBase
    #     dico_qgs['date_export'] = qgs.dateExported
    #     dico_qgs['date_print'] = qgs.datePrinted
    #     dico_qgs['date_actu'] = qgs.dateSaved

    #     # by default let's start considering there is only one layer
    #     dframes = ListDataFrames(qgs)
    #     dico_qgs['subdatasets_count'] = len(dframes)

    #     li_dframes_names = []
    #     dico_qgs['dframes_names'] = li_dframes_names

    #     x = 0
    #     for dframe in dframes:
    #         x += 1
    #         # dictionary where will be stored informations
    #         dico_dframe = OrderedDict()
    #         # parent GDB
    #         dico_dframe[u'name'] = dframe.name

    #         # getting layer globlal informations
    #         self.infos_dataframe(dframe, dico_dframe)

    #         # storing layer into the GDB dictionary
    #         dico_qgs['{0}_{1}'.format(x,
    #                                   dico_dframe.get('name'))] = dico_dframe

    #         # reset
    #         del dico_dframe
    # # SRS
    # qgs_dest_srs = qgs_canvas.find("destinationsrs").getchildren()
    # # print(dir(qgs_dest_srs), qgs_dest_srs[0][1].tag)
    # # dico_qgs['srs'] = qgs_dest_srs.find("srsid").text

    # scale
    # dico_qgs['maxScale'] = layer_obj.maxScale
    # dico_qgs['minScale'] = layer_obj.minScale

    #     # # secondary
    #     # dico_qgs['license'] = layer_obj.credits
    #     # dico_qgs['broken'] = layer_obj.isBroken

    #     # # total fields count
    #     # total_fields = 0
    #     # dico_qgs['total_fields'] = total_fields

    #     # # total objects count
    #     # total_objs = 0
    #     # dico_qgs['total_objs'] = total_objs

    #     # # parsing layers
    #     return

    # def infos_dataframe(self, dataframe, dico_dframe):
    #     u"""
    #     Gets informations about geography and geometry
    #     """

    #     # map settings
    #     dico_dframe[u'mapUnits'] = dataframe.mapUnits

    #     # SRS
    #     srs = extent.spatialReference
    #     dico_dframe[u'srs'] = srs.name
    #     dico_dframe[u'srs_type'] = srs.type
    #     if srs.type == u'Projected':
    #         dico_dframe[u'EPSG'] = srs.PCSCode, srs.PCSName, srs.projectionCode, srs.projectionName
    #     elif srs.type == u'Geographic':
    #         dico_dframe[u'EPSG'] = srs.GCSCode, srs.GCSName, srs.datumCode, srs.datumName
    #     else:
    #         dico_dframe[u'EPSG'] = (srs.PCSCode, srs.PCSName, srs.projectionCode, srs.projectionName),\
    #                                (srs.GCSCode, srs.GCSName, srs.datumCode, srs.datumName)

    #     # layers
    #     li_layers = ListLayers(dataframe)
    #     dico_dframe['layers_count'] = len(li_layers)
    #     dico_dframe['layers_names'] = [layer.name for layer in li_layers]

    #     # end of function
    #     return


# ############################################################################
# #### Stand alone program ########
# #################################

if __name__ == "__main__":
    """
    Standalone execution for development and tests. Paths are relative considering
    a test within the official repository (https://github.com/Guts/DicoGIS/)
    """
    # specific imports
    from collections import OrderedDict

    # searching for qgs Files
    dir_qgs = path.abspath(r"..\..\test\datatest\maps_docs\qgs")
    # dir_qgs = path.abspath(r'\\Copernic\SIG_RESSOURCES\1_qgs\ADMINISTRATIF')
    chdir(path.abspath(dir_qgs))
    li_qgs = listdir(path.abspath(dir_qgs))
    li_qgs = [
        path.abspath(qgs) for qgs in li_qgs if path.splitext(qgs)[1].lower() == ".qgs"
    ]

    # recipient datas
    dico_qgs = OrderedDict()

    # test text dictionary
    textos = dict()
    textos["srs_comp"] = "Compound"
    textos["srs_geoc"] = "Geocentric"
    textos["srs_geog"] = "Geographic"
    textos["srs_loca"] = "Local"
    textos["srs_proj"] = "Projected"
    textos["srs_vert"] = "Vertical"
    textos["geom_point"] = "Point"
    textos["geom_ligne"] = "Line"
    textos["geom_polyg"] = "Polygon"

    # read qgs
    for qgspath in li_qgs:
        dico_qgs.clear()
        if path.isfile(qgspath):
            # print("\n{0}: ".format(qgspath))
            ReadQGS(qgspath, dico_qgs, "QGIS Document", txt=textos)
            # print results
            print(dico_qgs)
        else:
            print("{0} is not a recognized file".format(qgspath))
            continue
