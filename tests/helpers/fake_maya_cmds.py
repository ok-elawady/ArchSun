import sys
import types


class FakeMayaCmds:
    def __init__(self):
        self.plugins_loaded = {"mtoa": False}
        self.nodes = {}
        self.attrs = {}
        self.connections = set()
        self.undo_chunks = []

    def pluginInfo(self, plugin_name, query=False, loaded=False):
        if query and loaded:
            return self.plugins_loaded.get(plugin_name, False)
        raise NotImplementedError("FakeMayaCmds only supports query=True, loaded=True")

    def loadPlugin(self, plugin_name, quiet=False):
        self.plugins_loaded[plugin_name] = True
        return plugin_name

    def undoInfo(self, openChunk=False, closeChunk=False):
        if openChunk:
            self.undo_chunks.append("open")
        if closeChunk:
            self.undo_chunks.append("close")

    def group(self, em=False, name=None):
        if not em:
            raise NotImplementedError("FakeMayaCmds only supports empty group creation")
        self._create_node(name, "transform")
        return name

    def shadingNode(self, node_type, asLight=False, asTexture=False, name=None):
        if asLight:
            transform_name = name
            shape_name = f"{name}Shape"
            self._create_node(transform_name, "transform")
            self._create_node(shape_name, node_type)
            self.nodes[transform_name]["shapes"] = [shape_name]
            self.nodes[shape_name]["parent"] = transform_name
            return transform_name

        if asTexture:
            self._create_node(name, node_type)
            return name

        raise NotImplementedError("Unsupported shadingNode configuration")

    def parent(self, child, parent_group):
        child_node = self.nodes[child]
        old_parent = child_node["parent"]

        if old_parent and child in self.nodes[old_parent]["children"]:
            self.nodes[old_parent]["children"].remove(child)

        child_node["parent"] = parent_group
        if child not in self.nodes[parent_group]["children"]:
            self.nodes[parent_group]["children"].append(child)

        return [child]

    def objExists(self, name):
        return name in self.nodes

    def listRelatives(
        self, node_name, children=False, shapes=False, parent=False, fullPath=False
    ):
        if node_name not in self.nodes:
            return []

        node = self.nodes[node_name]

        if children:
            return list(node["children"])
        if shapes:
            return list(node["shapes"])
        if parent:
            return [node["parent"]] if node["parent"] else []

        return []

    def nodeType(self, node_name):
        return self.nodes[node_name]["type"]

    def isConnected(self, source_attr, destination_attr):
        return (source_attr, destination_attr) in self.connections

    def connectAttr(self, source_attr, destination_attr, force=False):
        self.connections.add((source_attr, destination_attr))

    def setAttr(self, attr_name, value):
        self.attrs[attr_name] = value

    def get_attr(self, attr_name):
        return self.attrs.get(attr_name)

    def _create_node(self, name, node_type):
        self.nodes[name] = {
            "type": node_type,
            "parent": None,
            "children": [],
            "shapes": [],
        }


def install_fake_maya(
    monkeypatch,
    include_ui=False,
    main_window_ptr=1001,
    control_ptrs=None,
):
    fake_cmds = FakeMayaCmds()
    control_ptrs = control_ptrs or {}

    maya_module = types.ModuleType("maya")
    cmds_module = types.ModuleType("maya.cmds")

    exported_names = (
        "pluginInfo",
        "loadPlugin",
        "undoInfo",
        "group",
        "shadingNode",
        "parent",
        "objExists",
        "listRelatives",
        "nodeType",
        "isConnected",
        "connectAttr",
        "setAttr",
    )

    for name in exported_names:
        setattr(cmds_module, name, getattr(fake_cmds, name))

    cmds_module._state = fake_cmds
    maya_module.cmds = cmds_module

    monkeypatch.setitem(sys.modules, "maya", maya_module)
    monkeypatch.setitem(sys.modules, "maya.cmds", cmds_module)

    if include_ui:
        omui_module = types.ModuleType("maya.OpenMayaUI")

        class FakeMQtUtil:
            @staticmethod
            def mainWindow():
                return main_window_ptr

            @staticmethod
            def findControl(control_name):
                return control_ptrs.get(control_name)

        omui_module.MQtUtil = FakeMQtUtil
        maya_module.OpenMayaUI = omui_module
        monkeypatch.setitem(sys.modules, "maya.OpenMayaUI", omui_module)

    return fake_cmds
